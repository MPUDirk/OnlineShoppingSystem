from django.urls import path

from .views import ProductCreateView, ProductUpdateView

app_name = 'vendor'

urlpatterns = [
    path('products/add/', ProductCreateView.as_view(), name='product_add'),
    path('products/<int:pk>/edit/', ProductUpdateView.as_view(), name='product_edit'),
]
