from django.db import transaction as db_transaction
from django.db.models import Q
from django.forms.models import model_to_dict
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, DeleteView, UpdateView, DetailView, FormView

from OnlineShoppingSys.modules import CustomLoginRequiredMixin
from .forms import CartItemUpdateForm, CheckoutForm
from .models import Product, ShoppingCart, CartItem, Order, OrderItem
from user.models import Wallet, Transaction


class ProductListView(ListView):
    model = Product
    allow_empty = True
    template_name = 'store/product_list.html'
    paginate_by = 20
    context_object_name = 'products'

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True).select_related('category')
        q = self.request.GET.get('q', '').strip()
        category = self.request.GET.get('category', '').strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(product_id__icontains=q))
        if category:
            qs = qs.filter(category__name__icontains=category)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['category'] = self.request.GET.get('category', '')
        return context


class ProductDetailPageView(DetailView):
    model = Product
    template_name = 'store/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        return Product.objects.select_related('category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context['product']
        related = Product.objects.filter(is_active=True).exclude(pk=product.pk)
        if product.category:
            related = related.filter(category=product.category)
        context['related_products'] = list(related[:6])
        # Edit permission: admin can edit all; vendor can only edit own products
        user = self.request.user
        if user.is_authenticated:
            can_edit = (
                user.is_staff or user.is_superuser or
                (user.groups.filter(name='Vendor').exists() and product.created_by_id == user.id)
            )
        else:
            can_edit = False
        context['can_edit'] = can_edit
        return context


class ShoppingCartListView(CustomLoginRequiredMixin, ListView):
    model = CartItem
    template_name = 'store/cart.html'
    context_object_name = 'cart_items'

    def get_queryset(self):
        cart, _ = ShoppingCart.objects.get_or_create(customer=self.request.user)
        return CartItem.objects.filter(cart=cart).select_related('product')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_items = context['cart_items']
        cart = ShoppingCart.objects.filter(customer=self.request.user).first()
        context['cart_total'] = cart.get_total() if cart else 0
        return context

class CartItemCreateView(CustomLoginRequiredMixin, CreateView):
    form_class = CartItemUpdateForm
    template_name = 'item_create.html'
    success_url = reverse_lazy('shopping:shopping_cart')

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['product'] = get_object_or_404(Product, product_id=self.kwargs['pk'])
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['product_id'] = self.kwargs['pk']
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        cart = ShoppingCart.objects.get(customer=self.request.user)
        product = get_object_or_404(Product, product_id=self.kwargs['pk'])
        quantity = form.cleaned_data['quantity']
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        return redirect(self.success_url)

class CartItemEditView(CustomLoginRequiredMixin, UpdateView):
    form_class = CartItemUpdateForm
    template_name = 'item_edit.html'
    success_url = reverse_lazy('shopping:shopping_cart')

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.cart.customer != self.request.user:
            raise Http404('Cart Item Not Found')
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_object(self, queryset = None):
        return CartItem.objects.get(id=self.kwargs['pk'])

class CartItemDeleteView(CustomLoginRequiredMixin, DeleteView):
    model = CartItem
    success_url = reverse_lazy('shopping:shopping_cart')
    http_method_names = ['post']

    def get_object(self, queryset=None):
        return get_object_or_404(CartItem, pk=self.kwargs['pk'], cart__customer=self.request.user)


class CustomerOnlyMixin(CustomLoginRequiredMixin):
    """Restrict to customers only (not vendor, not staff/superuser)."""
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_staff or request.user.is_superuser:
            raise Http404('Not available')
        if request.user.groups.filter(name='Vendor').exists():
            raise Http404('Vendors cannot place orders')
        return super().dispatch(request, *args, **kwargs)


class CheckoutView(CustomerOnlyMixin, FormView):
    """A11: Checkout - create order, deduct wallet, clear selected cart items."""
    form_class = CheckoutForm
    template_name = 'store/checkout.html'
    success_url = reverse_lazy('shopping:order_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def _get_selected_items(self):
        """Return cart items to checkout. From GET ?items=1,2,3 or all if none."""
        cart, _ = ShoppingCart.objects.get_or_create(customer=self.request.user)
        all_items = list(CartItem.objects.filter(cart=cart).select_related('product'))
        ids = self.request.GET.getlist('items')
        if ids:
            try:
                ids = [int(x) for x in ids if x]
            except (ValueError, TypeError):
                ids = []
            if ids:
                valid_ids = {ci.pk for ci in all_items}
                ids = [i for i in ids if i in valid_ids]
                return [ci for ci in all_items if ci.pk in ids]
        return all_items

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_items = self._get_selected_items()
        context['cart_items'] = cart_items
        context['cart_total'] = sum(item.get_subtotal() for item in cart_items)
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        context['wallet'] = wallet
        return context

    def form_valid(self, form):
        cart = ShoppingCart.objects.get(customer=self.request.user)
        ids = form.data.getlist('items') or self.request.GET.getlist('items')
        if ids:
            try:
                ids = [int(x) for x in ids if x]
            except (ValueError, TypeError):
                ids = []
        cart_items = list(CartItem.objects.filter(cart=cart, pk__in=ids).select_related('product')) if ids else list(CartItem.objects.filter(cart=cart).select_related('product'))
        if not cart_items:
            return redirect('shopping:shopping_cart')

        total = sum(item.get_subtotal() for item in cart_items)
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        if wallet.balance < total:
            return redirect('shopping:shopping_cart')

        addr = form.cleaned_data['shipping_address']

        with db_transaction.atomic():
            order = Order.objects.create(
                customer=self.request.user,
                shipping_address=addr,
                shipping_address_text=addr.address,
                total_amount=total,
                status='pending'
            )
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    unit_price=item.product.price,
                    subtotal=item.get_subtotal()
                )
            wallet.balance -= total
            wallet.save()
            Transaction.objects.create(
                user=self.request.user,
                amount=-total,
                transaction_type=Transaction.PURCHASE,
                balance_after=wallet.balance,
                description=f'Order {order.order_number}'
            )
            CartItem.objects.filter(pk__in=[i.pk for i in cart_items]).delete()

        return redirect('shopping:order_detail', pk=order.pk)


class OrderListView(CustomerOnlyMixin, ListView):
    """A12: List purchase orders - P.O. number, date, total, status. Reverse chronological."""
    model = Order
    template_name = 'store/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user).order_by('-purchase_date')


class OrderDetailView(CustomerOnlyMixin, DetailView):
    """A13: Order detail - P.O. number, date, shipping address, total, status, items with name/qty/price/subtotal."""
    model = Order
    template_name = 'store/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user).prefetch_related('items__product')


class ProductView(View):
    def post(self, request, *args, **kwargs):
        # Create a new product
        data = request.POST
        product = Product.objects.create(
            name=data.get('name'),
            price=data.get('price'),
            description=data.get('description'),
            is_active=data.get('is_active', True),
            category_id=data.get('category')
        )
        return JsonResponse({'product': model_to_dict(product, fields=['id', 'name', 'price', 'description', 'is_active', 'category'])})

    def put(self, request, *args, **kwargs):
        # Update an existing product
        data = request.POST
        product_id = kwargs.get('id')
        product = get_object_or_404(Product, id=product_id)
        product.name = data.get('name', product.name)
        product.price = data.get('price', product.price)
        product.description = data.get('description', product.description)
        product.is_active = data.get('is_active', product.is_active)
        product.category_id = data.get('category', product.category_id)
        product.save()
        return JsonResponse({'product': model_to_dict(product, fields=['id', 'name', 'price', 'description', 'is_active', 'category'])})

    def delete(self, request, *args, **kwargs):
        # Delete a product
        product_id = kwargs.get('id')
        product = get_object_or_404(Product, id=product_id)
        product.delete()
        return JsonResponse({'message': 'Product deleted successfully'})

class ShoppingCartView(View):
    def put(self, request, *args, **kwargs):
        # Update the quantity of a product in the shopping cart
        data = request.POST
        item_id = kwargs.get('id')
        quantity = int(data.get('quantity', 1))
        cart_item = get_object_or_404(CartItem, id=item_id, cart__customer=request.user)
        cart_item.quantity = quantity
        cart_item.save()
        return JsonResponse({'message': 'Cart item updated', 'cart_item': model_to_dict(cart_item, fields=['id', 'quantity'])})

    def delete(self, request, *args, **kwargs):
        # Remove a product from the shopping cart
        item_id = kwargs.get('id')
        cart_item = get_object_or_404(CartItem, id=item_id, cart__customer=request.user)
        cart_item.delete()
        return JsonResponse({'message': 'Cart item removed'})
