from django.urls import path

from .views import (ProductCreateView, ProductUpdateView, OrderUpdateView, ProductDeleteView, VendorProductListView,
    VendorOrderListView, ProductPropertyTitleEditView, ProductPropertyTitleDeleteView, ProductPropertyEditView, ProductPropertyDeleteView)

app_name = 'vendor'

urlpatterns = [
    path('', VendorProductListView.as_view(), name='home'),
    path('orders/', VendorOrderListView.as_view(), name='order_list'),
    path('orders/<int:pk>/update/', OrderUpdateView.as_view(), name='order_update'),
    path('products/add/', ProductCreateView.as_view(), name='product_add'),
    path('products/<int:pk>/edit/', ProductUpdateView.as_view(), name='product_edit'),
    path('products/title/<int:pk>/edit/', ProductPropertyTitleEditView.as_view(), name='property_title_edit'),
    path('products/title/<int:pk>/del/', ProductPropertyTitleDeleteView.as_view(), name='property_title_del'),
    path('products/property/<int:pk>/edit/', ProductPropertyEditView.as_view(), name='property_edit'),
    path('products/property/<int:pk>/del/', ProductPropertyDeleteView.as_view(), name='property_del'),
    path('products/<int:pk>/delete/', ProductDeleteView.as_view(), name='product_delete'),
]
