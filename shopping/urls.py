from django.urls import path

from .views import ProductListView, ProductCreateView, ProductDetailPageView, ShoppingCartListView, CartItemCreateView, CartItemEditView

app_name = 'shopping'

urlpatterns = [
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/add/', ProductCreateView.as_view(), name='product_add'),
    path('products/<int:pk>/', ProductDetailPageView.as_view(), name='product_detail'),
    path('cart/', ShoppingCartListView.as_view(), name='shopping_cart'),
    path('cart/create/item/<slug:pk>', CartItemCreateView.as_view(), name='cart_item_create'),
    path('cart/edit/item/<int:pk>', CartItemEditView.as_view(), name='cart_item_edit')
]