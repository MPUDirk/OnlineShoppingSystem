from django.urls import path
from .views import ProductView, ProductDetailView, ShoppingCartView, ShoppingCartListView

urlpatterns = [
    path('products/', ProductDetailView.as_view(), name='product_list_create'),
    path('products/<int:id>/', ProductView.as_view(), name='product_update_delete'),
    path('cart/', ShoppingCartListView.as_view(), name='shopping_cart'),
    path('cart/<int:id>/', ShoppingCartView.as_view(), name='cart_item_update_delete'),
]