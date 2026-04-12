from django.urls import path

from .views import (IndexView, ProductListView, ProductDetailPageView, product_detail_pk_redirect,
                    ShoppingCartListView,
                    CartItemCreateView, CartItemEditView, CartItemDeleteView,
                    CheckoutView, OrderListView, OrderDetailView, OrderUpdateCancelView)

app_name = 'shopping'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/<int:pk>/', product_detail_pk_redirect, name='product_detail_legacy'),
    path('products/<slug:slug>/', ProductDetailPageView.as_view(), name='product_detail'),
    path('cart/', ShoppingCartListView.as_view(), name='shopping_cart'),
    path('cart/create/item/<slug:pk>', CartItemCreateView.as_view(), name='cart_item_create'),
    path('cart/edit/item/<int:pk>', CartItemEditView.as_view(), name='cart_item_edit'),
    path('cart/delete/item/<int:pk>', CartItemDeleteView.as_view(), name='cart_item_delete'),
    path('cart/checkout/', CheckoutView.as_view(), name='checkout'),
    path('orders/', OrderListView.as_view(), name='order_list'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    path('order/<int:pk>/cancel/', OrderUpdateCancelView.as_view(), name='order_cancel')
]