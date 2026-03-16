from django.urls import path

from .views import (ProductListView, ProductDetailPageView, ShoppingCartListView,
                    CartItemCreateView, CartItemEditView, CartItemDeleteView,
                    CheckoutView, OrderListView, OrderDetailView)

app_name = 'shopping'

urlpatterns = [
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/<int:pk>/', ProductDetailPageView.as_view(), name='product_detail'),
    path('cart/', ShoppingCartListView.as_view(), name='shopping_cart'),
    path('cart/create/item/<slug:pk>', CartItemCreateView.as_view(), name='cart_item_create'),
    path('cart/edit/item/<int:pk>', CartItemEditView.as_view(), name='cart_item_edit'),
    path('cart/delete/item/<int:pk>', CartItemDeleteView.as_view(), name='cart_item_delete'),
    path('cart/checkout/', CheckoutView.as_view(), name='checkout'),
    path('orders/', OrderListView.as_view(), name='order_list'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
]