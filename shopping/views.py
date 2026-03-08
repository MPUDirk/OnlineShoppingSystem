from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import ListView

from .models import Product, ShoppingCart, CartItem


class ProductDetailView(ListView):
    model = Product
    allow_empty = True
    template_name = 'store/product_list.html'
    paginate_by = 20 # twenty products per page

    def get_context_data(self, *, object_list = ..., **kwargs):
        context = super().get_context_data(object_list=self.object_list, **kwargs)

        context['page_list'] = context['page_obj'].object_list

        return context

class ShoppingCartListView(LoginRequiredMixin, ListView):
    model = CartItem
    template_name = 'store/cart.html'
    login_url = 'user:login'

    def get_queryset(self):
        cart = ShoppingCart.objects.get(customer_id=self.request.user.id)
        return CartItem.objects.filter(cart_id=cart.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cart_items = self.get_queryset()
        map_products = {item.id: Product.objects.get(id=item.product_id) for item in cart_items}
        context['products'] = map_products

        return context

class ProductView(View):
    def get(self, request, *args, **kwargs):
        # Retrieve all products
        products = Product.objects.all()
        data = [model_to_dict(product, fields=['id', 'name', 'price', 'description', 'is_active', 'category']) for product in products]
        return JsonResponse({'products': data})

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
    def get(self, request, *args, **kwargs):
        # Retrieve the shopping cart for the logged-in user
        cart, _ = ShoppingCart.objects.get_or_create(customer=request.user)
        items = cart.items.select_related('product')
        data = {
            'cart': model_to_dict(cart, fields=['id', 'created_at', 'updated_at']),
            'items': [
                {
                    'id': item.id,
                    'product': model_to_dict(item.product, fields=['id', 'name', 'price']),
                    'quantity': item.quantity,
                    'subtotal': item.get_subtotal()
                } for item in items
            ],
            'total': cart.get_total()
        }
        return JsonResponse(data)

    def post(self, request, *args, **kwargs):
        # Add a product to the shopping cart
        data = request.POST
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        product = get_object_or_404(Product, id=product_id)
        cart, _ = ShoppingCart.objects.get_or_create(customer=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()
        return JsonResponse({'message': 'Product added to cart', 'cart_item': model_to_dict(cart_item, fields=['id', 'quantity'])})

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
