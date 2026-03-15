from django.urls import path

from .views import ProductDetailView, ShoppingCartListView, CartItemCreateView,CartItemEditView

app_name = 'shopping'

urlpatterns = [
    path('products/', ProductDetailView.as_view(), name='product_list_create'),
    path('cart/', ShoppingCartListView.as_view(), name='shopping_cart'),
    path('cart/create/item/<slug:pk>', CartItemCreateView.as_view(), name='cart_item_create'),
    path('cart/edit/item/<int:pk>', CartItemEditView.as_view(), name='cart_item_edit')
]