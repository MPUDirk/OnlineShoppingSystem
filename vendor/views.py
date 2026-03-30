from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import Http404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, UpdateView, DeleteView, FormView

from OnlineShoppingSys.modules import CustomLoginRequiredMixin
from shopping.models import Product, Order, OrderStatusHistory, ProductPropertyTitle, ProductProperty
from user.models import Wallet, Transaction
from .forms import ProductCreateForm, ProductUpdateForm, PropertyTitleEditForm, PropertyEditForm


class VendorOrAdminRequiredMixin(CustomLoginRequiredMixin, UserPassesTestMixin):
    """Allow Vendor group or staff/superuser."""
    def test_func(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return True
        return self.request.user.groups.filter(name='Vendor').exists()


class ProductEditPermissionMixin(CustomLoginRequiredMixin, UserPassesTestMixin):
    raise_exception =  True

    """Admin can edit any product; Vendor can only edit products they created."""
    def test_func(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return True
        if not self.request.user.groups.filter(name='Vendor').exists():
            return False
        product = Product.objects.get(id=self.kwargs['pk'])
        return product.created_by_id == self.request.user.id

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except PermissionDenied:
            return Http404("Product Not Found")


class VendorProductListView(VendorOrAdminRequiredMixin, ListView):
    """Vendor homepage: list products created by the current user (or all for admin)."""
    model = Product
    template_name = 'vendor/home.html'
    context_object_name = 'products'
    paginate_by = 12

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

class VendorOrderListView(VendorOrAdminRequiredMixin, ListView):
    model = Order
    template_name = 'vendor/order_list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return Order.objects.all()

        return Order.objects.filter(
            items__product__created_by=self.request.user
        ).distinct()

    @staticmethod
    def get_js_orders(orders, user) -> list:
        return [
            {
                'id': o.id,
                'customer': o.customer.username,
                'order_number': o.order_number,
                'total_amount': float(o.get_vendor_amount(user)),
                'status': o.get_status_display(),
                'nxt_status': o.get_next_status(),
                'is_finished': o.get_is_finished(),
            }
            for o in orders
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['js_orders'] = self.get_js_orders(context['orders'], self.request.user)
        context['null'] = None
        return context

class OrderUpdateView(VendorOrAdminRequiredMixin, UpdateView):
    model = Order
    fields = ['status']
    context_object_name = 'order'
    success_url = reverse_lazy('vendor:order_list')

    def form_valid(self, form):
        data = form.cleaned_data
        order = self.object
        org_order = Order.objects.get(id=order.id)
        user = self.request.user

        if order.status == 'shipped':
            order.shipped_at = timezone.now()
        elif order.status == 'cancelled':
            c = Wallet.objects.get(user=order.customer)
            v = Wallet.objects.get(user=order.items.first().product.created_by)
            c.balance += order.total_amount
            c.save()
            Transaction.objects.create(
                user=c.user,
                amount=order.total_amount,
                transaction_type=Transaction.REFUND,
                balance_after=c.balance,
                description=f'Order {order.order_number}'
            )
            v.balance -= order.total_amount
            v.save()
            Transaction.objects.create(
                user=v.user,
                amount=order.total_amount,
                transaction_type=Transaction.WITHDRAW,
                balance_after=v.balance,
                description=f'Order {order.order_number}'
            )
            order.cancelled_at = timezone.now()

        if org_order.status == data['status'] == 'hold':
            pre_status = OrderStatusHistory.objects.filter(order=order).order_by('-changed_at')[1]
            order.status = pre_status.status
            data['status'] = pre_status.status

        OrderStatusHistory.objects.create(
            order=order,
            status=data['status'],
            note=f'{order.order_number} updated by {user.username}',
        )
        return super().form_valid(form)

class ProductCreateView(VendorOrAdminRequiredMixin, CreateView):
    model = Product
    form_class = ProductCreateForm
    template_name = 'vendor/product_add.html'
    success_url = reverse_lazy('vendor:home')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class ProductPropertyTitleEditView(ProductEditPermissionMixin, FormView):
    model = ProductPropertyTitle
    form_class = PropertyTitleEditForm
    template_name = 'vendor/product_edit.html'
    context_object_name = 'property_title'

    def get_object(self, queryset=None):
        return Product.objects.get(id=self.kwargs['pk'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['product'] = self.get_object()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context['product'] = product
        context['form'] = ProductUpdateForm(instance=product)
        try:
            context['properties'] = ProductPropertyTitle.objects.get(product=product)
        except ProductPropertyTitle.DoesNotExist:
            context['properties'] = None
        return context

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('vendor:product_edit', kwargs={'pk': self.kwargs['pk']})

class ProductPropertyTitleDeleteView(ProductEditPermissionMixin, DeleteView):
    model = ProductPropertyTitle
    context_object_name = 'property_title'
    success_url = reverse_lazy('vendor:product_edit')

    def get_object(self, queryset=None):
        return ProductPropertyTitle.objects.get(product__id=self.kwargs['pk'])

    def get_success_url(self):
        return reverse('vendor:product_edit', kwargs={'pk': self.kwargs['pk']})

class ProductPropertyEditView(ProductEditPermissionMixin, FormView):
    model = ProductProperty
    form_class = PropertyEditForm
    template_name = 'vendor/property_submit.html'

    def get_object(self, queryset=None):
        return Product.objects.get(id=self.kwargs['pk'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['product'] = self.get_object()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.get_object()
        return context

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('vendor:product_edit', kwargs={'pk': self.kwargs['pk']})

class ProductPropertyDeleteView(ProductEditPermissionMixin, DeleteView):
    model = ProductProperty
    context_object_name = 'property'

    def get_object(self, queryset=None):
        return ProductProperty.objects.get(id=self.kwargs['pk'])

    def get_success_url(self):
        return reverse('vendor:product_edit', kwargs={'pk': self.kwargs['pk']})

class ProductUpdateView(ProductEditPermissionMixin, UpdateView):
    model = Product
    form_class = ProductUpdateForm
    template_name = 'vendor/product_edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.get_object()
        try:
            context['properties'] = ProductPropertyTitle.objects.get(product=self.object)
        except ProductPropertyTitle.DoesNotExist:
            context['properties'] = None
        return context

    def get_success_url(self):
        return reverse('shopping:product_detail', kwargs={'pk': self.kwargs['pk']})

class ProductDeleteView(ProductEditPermissionMixin, DeleteView):
    model = Product
    context_object_name = 'product'

    def get_object(self, queryset=None):
        return Product.objects.get(id=self.kwargs['pk'])
