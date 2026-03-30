from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView, DeleteView, FormView

from OnlineShoppingSys.modules import CustomLoginRequiredMixin
from shopping.models import Product, Order, OrderStatusHistory, ProductPropertyTitle, ProductProperty, ProductSKU
from shopping.sku_catalog import get_configuration_label
from user.models import Wallet, Transaction
from .forms import ProductCreateForm, ProductUpdateForm, PropertyTitleForm, PropertyOptionForm


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
        product = get_object_or_404(Product, pk=self.kwargs['pk'])
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
        def fmt_purchase_date(o):
            if not o.purchase_date:
                return ''
            dt = o.purchase_date
            if timezone.is_aware(dt):
                dt = timezone.localtime(dt)
            return dt.strftime('%Y-%m-%d %H:%M')

        return [
            {
                'id': o.id,
                'customer': o.customer.username,
                'order_number': o.order_number,
                'purchase_date': fmt_purchase_date(o),
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


class ProductPropertyTitleCreateView(ProductEditPermissionMixin, CreateView):
    model = ProductPropertyTitle
    form_class = PropertyTitleForm
    template_name = 'vendor/property_type_form.html'

    def get_product(self):
        return get_object_or_404(Product, pk=self.kwargs['pk'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['product'] = self.get_product()
        return kwargs

    def form_valid(self, form):
        form.instance.product = self.get_product()
        messages.success(self.request, f'Attribute type “{form.instance.title}” added.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.get_product()
        context['form_heading'] = 'Add attribute type'
        return context

    def get_success_url(self):
        return reverse('vendor:product_edit', kwargs={'pk': self.kwargs['pk']})


class ProductPropertyTitleUpdateView(ProductEditPermissionMixin, UpdateView):
    model = ProductPropertyTitle
    form_class = PropertyTitleForm
    template_name = 'vendor/property_type_form.html'
    pk_url_kwarg = 'title_pk'

    def get_queryset(self):
        return ProductPropertyTitle.objects.filter(product_id=self.kwargs['pk'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['product'] = self.get_object().product
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Attribute type updated.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.get_object().product
        context['form_heading'] = 'Edit attribute type'
        return context

    def get_success_url(self):
        return reverse('vendor:product_edit', kwargs={'pk': self.kwargs['pk']})


class ProductPropertyTitleDeleteView(ProductEditPermissionMixin, View):
    def post(self, request, pk, title_pk):
        ptitle = get_object_or_404(ProductPropertyTitle, pk=title_pk, product_id=pk)
        name = ptitle.title
        ptitle.delete()
        messages.success(request, f'Attribute type “{name}” and its options were removed.')
        return redirect('vendor:product_edit', pk=pk)


class ProductPropertyCreateView(ProductEditPermissionMixin, CreateView):
    model = ProductProperty
    form_class = PropertyOptionForm
    template_name = 'vendor/property_submit.html'

    def dispatch(self, request, *args, **kwargs):
        self.title_obj = get_object_or_404(
            ProductPropertyTitle,
            pk=self.kwargs['title_pk'],
            product_id=self.kwargs['pk'],
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.title_obj.product
        context['form_heading'] = f'Add option — {self.title_obj.title}'
        return context

    def form_valid(self, form):
        form.instance.title = self.title_obj
        if not self.request.FILES.get('image'):
            form.instance.image = self.title_obj.product.thumbnail
        messages.success(self.request, 'Option added.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('vendor:product_edit', kwargs={'pk': self.kwargs['pk']})


class ProductPropertyUpdateView(ProductEditPermissionMixin, UpdateView):
    model = ProductProperty
    form_class = PropertyOptionForm
    template_name = 'vendor/property_submit.html'
    pk_url_kwarg = 'prop_pk'

    def get_queryset(self):
        return ProductProperty.objects.filter(title__product_id=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.object.title.product
        context['form_heading'] = f'Edit option — {self.object.title.title}'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Option updated.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('vendor:product_edit', kwargs={'pk': self.kwargs['pk']})


class ProductPropertyDeleteView(ProductEditPermissionMixin, View):
    def post(self, request, pk, prop_pk):
        prop = get_object_or_404(ProductProperty, pk=prop_pk, title__product_id=pk)
        label = prop.name
        prop.delete()
        messages.success(request, f'Option “{label}” removed.')
        return redirect('vendor:product_edit', pk=pk)

class ProductUpdateView(ProductEditPermissionMixin, UpdateView):
    model = Product
    form_class = ProductUpdateForm
    template_name = 'vendor/product_edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.get_object()
        context['property_groups'] = (
            ProductPropertyTitle.objects.filter(product=self.object)
            .prefetch_related('properties')
            .order_by('pk')
        )
        return context

    def get_success_url(self):
        return reverse('shopping:product_detail', kwargs={'pk': self.kwargs['pk']})

class ProductDeleteView(ProductEditPermissionMixin, DeleteView):
    model = Product
    context_object_name = 'product'

    def get_object(self, queryset=None):
        return Product.objects.get(id=self.kwargs['pk'])


class ProductSkuListView(ProductEditPermissionMixin, ListView):
    """D4: list SKU rows per product; toggle stock on detail page."""
    model = ProductSKU
    template_name = 'vendor/product_skus.html'
    context_object_name = 'skus'

    def get_queryset(self):
        return ProductSKU.objects.filter(product_id=self.kwargs['pk']).prefetch_related(
            'property_links__product_property__title',
        ).order_by('sku')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = get_object_or_404(Product, pk=self.kwargs['pk'])
        context['sku_rows'] = [
            {'obj': s, 'label': get_configuration_label(s)} for s in context['skus']
        ]
        return context


class ProductSkuToggleStockView(ProductEditPermissionMixin, View):
    def post(self, request, pk, sku_pk):
        sku = get_object_or_404(ProductSKU, pk=sku_pk, product_id=pk)
        sku.in_stock = not sku.in_stock
        sku.save(update_fields=['in_stock'])
        messages.success(
            request,
            f'SKU {sku.sku} is now {"in stock" if sku.in_stock else "out of stock"}.',
        )
        return redirect('vendor:product_skus', pk=pk)
