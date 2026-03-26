from django.contrib import admin

from .models import Category, Product, ProductImage, ShoppingCart, CartItem, Order, OrderItem

# Register your models here.
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(ShoppingCart)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)
