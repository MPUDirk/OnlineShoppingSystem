from django.urls import path

from .views import ProductCreateView, ProductUpdateView, VendorProductListView

app_name = 'vendor'

urlpatterns = [
    path('', VendorProductListView.as_view(), name='home'),
    path('products/add/', ProductCreateView.as_view(), name='product_add'),
    path('products/<int:pk>/edit/', ProductUpdateView.as_view(), name='product_edit'),
]
