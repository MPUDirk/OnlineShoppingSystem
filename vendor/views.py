from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView

from OnlineShoppingSys.modules import CustomLoginRequiredMixin
from shopping.models import Product

from .forms import ProductCreateForm, ProductUpdateForm


class VendorOrAdminRequiredMixin(CustomLoginRequiredMixin, UserPassesTestMixin):
    """Allow Vendor group or staff/superuser."""
    def test_func(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return True
        return self.request.user.groups.filter(name='Vendor').exists()


class ProductEditPermissionMixin(CustomLoginRequiredMixin, UserPassesTestMixin):
    """Admin can edit any product; Vendor can only edit products they created."""
    def test_func(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return True
        if not self.request.user.groups.filter(name='Vendor').exists():
            return False
        product = self.get_object()
        return product.created_by_id == self.request.user.id


class ProductCreateView(VendorOrAdminRequiredMixin, CreateView):
    model = Product
    form_class = ProductCreateForm
    template_name = 'vendor/product_add.html'
    success_url = reverse_lazy('shopping:product_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class ProductUpdateView(ProductEditPermissionMixin, UpdateView):
    model = Product
    form_class = ProductUpdateForm
    template_name = 'vendor/product_edit.html'
    context_object_name = 'product'

    def get_success_url(self):
        return reverse('shopping:product_detail', kwargs={'pk': self.object.pk})
