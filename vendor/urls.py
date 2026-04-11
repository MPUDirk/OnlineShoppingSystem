from django.urls import path

from .views import (
    ProductCreateView,
    ProductUpdateView,
    OrderUpdateView,
    ProductDeleteView,
    VendorProductListView,
    VendorOrderListView,
    VendorSalesReportView,
    ProductPropertyTitleCreateView,
    ProductPropertyTitleUpdateView,
    ProductPropertyTitleDeleteView,
    ProductPropertyCreateView,
    ProductPropertyUpdateView,
    ProductPropertyDeleteView,
    ProductSkuListView,
    ProductSkuToggleStockView,
)

app_name = 'vendor'

urlpatterns = [
    path('', VendorProductListView.as_view(), name='home'),
    path('reports/', VendorSalesReportView.as_view(), name='sales_reports'),
    path('orders/', VendorOrderListView.as_view(), name='order_list'),
    path('orders/<int:pk>/update/', OrderUpdateView.as_view(), name='order_update'),
    path('products/add/', ProductCreateView.as_view(), name='product_add'),
    path('products/<int:pk>/edit/', ProductUpdateView.as_view(), name='product_edit'),
    path('products/<int:pk>/skus/', ProductSkuListView.as_view(), name='product_skus'),
    path('products/<int:pk>/skus/<int:sku_pk>/toggle/', ProductSkuToggleStockView.as_view(), name='product_sku_toggle'),
    path('products/<int:pk>/types/add/', ProductPropertyTitleCreateView.as_view(), name='property_type_add'),
    path('products/<int:pk>/types/<int:title_pk>/edit/', ProductPropertyTitleUpdateView.as_view(), name='property_type_edit'),
    path('products/<int:pk>/types/<int:title_pk>/delete/', ProductPropertyTitleDeleteView.as_view(), name='property_type_delete'),
    path('products/<int:pk>/types/<int:title_pk>/options/add/', ProductPropertyCreateView.as_view(), name='property_option_add'),
    path('products/<int:pk>/properties/<int:prop_pk>/edit/', ProductPropertyUpdateView.as_view(), name='property_option_edit'),
    path('products/<int:pk>/properties/<int:prop_pk>/delete/', ProductPropertyDeleteView.as_view(), name='property_option_delete'),
    path('products/<int:pk>/delete/', ProductDeleteView.as_view(), name='product_delete'),
]
