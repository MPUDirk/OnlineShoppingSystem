from django.urls import path
from .views import ProductView, ShoppingCartView

urlpatterns = [
    path('products/', ProductView.as_view(), name='product_list_create'),
    path('products/<int:id>/', ProductView.as_view(), name='product_update_delete'),
    path('cart/', ShoppingCartView.as_view(), name='shopping_cart'),
    path('cart/<int:id>/', ShoppingCartView.as_view(), name='cart_item_update_delete'),
]