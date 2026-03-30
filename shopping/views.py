from django.contrib import messages
from django.db import transaction as db_transaction
from django.db.models import Q
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DeleteView, UpdateView, DetailView, FormView, TemplateView

from OnlineShoppingSys.modules import CustomLoginRequiredMixin
from user.models import Wallet, Transaction
from vendor.views import OrderUpdateView
from .forms import CartItemUpdateForm, CheckoutForm
from .property_selection import format_property_summary, parse_property_selection_from_post
from .models import (
    Product,
    ShoppingCart,
    CartItem,
    Order,
    OrderItem,
    Category,
    ProductImage,
    OrderStatusHistory,
)


class IndexView(TemplateView):
    template_name = 'store/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['popular_products'] = Product.objects.filter(is_active=True).order_by('-order_items__quantity')[:3]
        context['new_arrivals'] = Product.objects.filter(is_active=True).order_by('-created_at')[:4]
        return context

class ProductListView(ListView):
    model = Product
    allow_empty = True
    template_name = 'store/product_list.html'
    paginate_by = 12
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
        """
        Public: only active products. Staff: any product. Vendor: active or own (preview off-shelf).
        """
        qs = Product.objects.select_related('category').prefetch_related(
            'property_titles__properties',
        )
        user = self.request.user
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            return qs
        if user.is_authenticated and user.groups.filter(name='Vendor').exists():
            return qs.filter(Q(is_active=True) | Q(created_by=user))
        return qs.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context['product']
        context['images'] = ProductImage.objects.filter(product=product).order_by('display_order')
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
        selection = parse_property_selection_from_post(product, self.request.POST)
        if selection is None:
            messages.error(
                self.request,
                'Please choose an option for each attribute (for example Type).',
            )
            return redirect('shopping:product_detail', pk=product.pk)
        for item in CartItem.objects.filter(cart=cart, product=product):
            if list(item.selected_property_ids or []) == selection:
                item.quantity += quantity
                item.save()
                return redirect(self.success_url)
        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=quantity,
            selected_property_ids=selection,
        )
        return redirect(self.success_url)

class CartItemEditView(CustomLoginRequiredMixin, UpdateView):
    form_class = CartItemUpdateForm
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
        c_wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        if c_wallet.balance < total:
            return redirect('shopping:shopping_cart')

        addr = form.cleaned_data['shipping_address']

        with db_transaction.atomic():
            for item in cart_items:
                subtotal = item.get_subtotal()
                vendor = item.product.created_by
                order = Order.objects.create(
                    customer=self.request.user,
                    shipping_address=addr,
                    shipping_address_text=addr.address,
                    total_amount=subtotal,
                    status='pending'
                )
                OrderStatusHistory.objects.create(
                    order=order,
                    status='pending',
                    note=f'{order.order_number} created by {self.request.user.username}'
                )
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    unit_price=item.get_subtotal() / item.quantity,
                    subtotal=subtotal,
                    property_summary=format_property_summary(item.selected_property_ids or []),
                )
                v_wallet, _ = Wallet.objects.get_or_create(user=vendor)
                v_wallet.balance += subtotal
                v_wallet.save()
                v_trans, _ = Transaction.objects.get_or_create(
                    user=vendor,
                    transaction_type=Transaction.PURCHASE,
                    description=f'Order {order.order_number}',
                    defaults={'amount': 0, 'balance_after': 0}
                )
                v_trans.amount += subtotal
                v_trans.balance_after = v_wallet.balance
                v_trans.save()
                c_wallet.balance -= subtotal
                c_wallet.save()
                Transaction.objects.create(
                    user=self.request.user,
                    amount=-subtotal,
                    transaction_type=Transaction.PURCHASE,
                    balance_after=c_wallet.balance,
                    description=f'Order {order.order_number}'
                )
            CartItem.objects.filter(pk__in=[i.pk for i in cart_items]).delete()

        return HttpResponseRedirect(self.get_success_url())


class OrderListView(CustomerOnlyMixin, ListView):
    """A12: List purchase orders - P.O. number, date, total, status. Reverse chronological."""
    model = Order
    template_name = 'store/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        qs = Order.objects.filter(customer=self.request.user).order_by('-purchase_date')
        status = self.request.GET.get('status', '').strip()
        valid_statuses = {c[0] for c in Order.ORDER_STATUS_CHOICES}
        if status and status in valid_statuses:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        raw = self.request.GET.get('status', '').strip()
        valid_statuses = {c[0] for c in Order.ORDER_STATUS_CHOICES}
        context['status_filter'] = raw if raw in valid_statuses else ''
        context['order_status_choices'] = Order.ORDER_STATUS_CHOICES
        return context


class OrderDetailView(DetailView):
    """A13: Order detail - P.O. number, date, shipping address, total, status, items with name/qty/price/subtotal."""
    model = Order
    template_name = 'store/order_detail.html'
    context_object_name = 'order'

    def dispatch(self, request, *args, **kwargs):
        order = self.get_object()
        items_all = order.items.all()
        vendor = [i.product.created_by for i in items_all]
        user = request.user
        if user not in vendor and not user.is_staff and not user.is_superuser and order.customer != user:
            raise Http404('Not available')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_history'] = OrderStatusHistory.objects.filter(order=self.object).order_by('changed_at')
        context['items'] = self.object.items.all()
        user = self.request.user
        if user.groups.filter(name='Vendor').exists():
            context['vendor_amount'] = self.object.get_vendor_amount(user)
            context['items'] = self.object.items.filter(product__created_by=user)
        elif user.is_staff and user.is_superuser:
            context['vendor_amount'] = self.object.total_amount
            context['items'] = self.object.items.all()
        return context

class OrderUpdateCancelView(OrderUpdateView):
    success_url = reverse_lazy('shopping:order_list')
    def test_func(self):
        instance = self.get_object()
        return instance.status == 'pending' and instance.customer == self.request.user or super().test_func()

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()

        data = form.data.copy()
        data['status'] = 'cancelled'

        form = self.get_form_class()(data=data, instance=self.object)

        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
