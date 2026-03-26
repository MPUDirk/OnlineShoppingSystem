from django.urls import path

from .views import ProductCreateView, ProductUpdateView, OrderUpdateView, ProductDeleteView, VendorProductListView, VendorOrderListView

app_name = 'vendor'

urlpatterns = [
    path('', VendorProductListView.as_view(), name='home'),
    path('orders/', VendorOrderListView.as_view(), name='order_list'),
    path('orders/<int:pk>/update/', OrderUpdateView.as_view(), name='order_update'),
    path('products/add/', ProductCreateView.as_view(), name='product_add'),
    path('products/<int:pk>/edit/', ProductUpdateView.as_view(), name='product_edit'),
    path('products/<int:pk>/delete/', ProductDeleteView.as_view(), name='product_delete'),
]
