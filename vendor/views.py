from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

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


class VendorProductListView(VendorOrAdminRequiredMixin, ListView):
    """Vendor homepage: list products created by the current user (or all for admin)."""
    model = Product
    template_name = 'vendor/home.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        qs = Product.objects.select_related('category')
        if self.request.user.is_staff or self.request.user.is_superuser:
            qs = qs.all()
        else:
            qs = qs.filter(created_by=self.request.user)
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(product_id__icontains=q))
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context


class ProductCreateView(VendorOrAdminRequiredMixin, CreateView):
    model = Product
    form_class = ProductCreateForm
    template_name = 'vendor/product_add.html'
    success_url = reverse_lazy('vendor:home')

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
