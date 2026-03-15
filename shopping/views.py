from django.contrib.auth.mixins import UserPassesTestMixin
from django.forms.models import model_to_dict
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, DeleteView, UpdateView, DetailView

from OnlineShoppingSys.modules import CustomLoginRequiredMixin
from .forms import CartItemUpdateForm, ProductCreateForm, ProductUpdateForm
from .models import Product, ShoppingCart, CartItem


class VendorOrAdminRequiredMixin(CustomLoginRequiredMixin, UserPassesTestMixin):
    """Allow Vendor group or staff/superuser."""
    def test_func(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return True
        return self.request.user.groups.filter(name='Vendor').exists()


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
            qs = qs.filter(name__icontains=q)
        if category:
            qs = qs.filter(category__name__icontains=category)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['category'] = self.request.GET.get('category', '')
        return context


class ProductCreateView(VendorOrAdminRequiredMixin, CreateView):
    model = Product
    form_class = ProductCreateForm
    template_name = 'store/product_add.html'
    success_url = reverse_lazy('shopping:product_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class ProductEditPermissionMixin(CustomLoginRequiredMixin, UserPassesTestMixin):
    """Admin can edit any product; Vendor can only edit products they created."""
    def test_func(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return True
        if not self.request.user.groups.filter(name='Vendor').exists():
            return False
        product = self.get_object()
        return product.created_by_id == self.request.user.id


class ProductUpdateView(ProductEditPermissionMixin, UpdateView):
    model = Product
    form_class = ProductUpdateForm
    template_name = 'store/product_edit.html'
    context_object_name = 'product'

    def get_success_url(self):
        return reverse('shopping:product_detail', kwargs={'pk': self.object.pk})


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

    def get_queryset(self):
        cart = ShoppingCart.objects.get(customer_id=self.request.user.id)
        return CartItem.objects.filter(cart_id=cart.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cart_items = self.get_queryset()
        map_products = {item.id: Product.objects.get(id=item.product_id) for item in cart_items}
        context['products'] = map_products

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
    pass

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
