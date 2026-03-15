from django import forms
from django.contrib.auth import logout
from django.contrib.auth.models import User, Group
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, UpdateView, DeleteView
from django.views.generic.edit import CreateView, FormView, FormMixin

from OnlineShoppingSys.modules import CustomLoginRequiredMixin
from .forms import SignUpForm, LoginForm, UserEditForm, ShippingAddressUpdateForm
from .models import ShippingAddress


class CustomFormMixin(FormMixin):
    def form_invalid(self:FormView, form:forms.ModelForm):
        context = self.get_context_data()
        context['errors'] = form.errors.as_data()
        return self.render_to_response(context)

# Create your views here.
class UserDetailView(CustomLoginRequiredMixin, TemplateView):
    model = User
    template_name = "user.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        context['shipping_addresses'] = ShippingAddress.objects.filter(user=context['user'])
        context['is_vendor'] = self.request.user.groups.filter(name='Vendor').exists()
        return context


class RoleSwitchView(CustomLoginRequiredMixin, View):
    """买家/卖家身份切换"""
    http_method_names = ['post']

    def post(self, request):
        user = request.user
        customer_group, _ = Group.objects.get_or_create(name='Customer')
        vendor_group, _ = Group.objects.get_or_create(name='Vendor')

        if user.groups.filter(name='Vendor').exists():
            user.groups.clear()
            user.groups.add(customer_group)
            return redirect('user:detail')
        else:
            user.groups.clear()
            user.groups.add(vendor_group)
            # 若项目已配置 /merchant/ 路由，可改为 redirect('/merchant/dashboard/')
            return redirect('user:detail')


class AccountEditView(CustomLoginRequiredMixin, UpdateView):
    form_class = UserEditForm
    template_name = "account_edit.html"
    success_url = reverse_lazy('user:detail')

    def get_object(self, queryset = ...):
        return self.request.user

class ShippingAddressCreateView(CustomLoginRequiredMixin, FormView, CustomFormMixin):
    form_class = ShippingAddressUpdateForm
    template_name = "shipping_address_create.html"
    success_url = reverse_lazy('user:detail')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

class ShippingAddressUpdateView(CustomLoginRequiredMixin, UpdateView, CustomFormMixin):
    form_class = ShippingAddressUpdateForm
    template_name = "shipping_address_edit.html"
    success_url = reverse_lazy('user:detail')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['pk'] = self.kwargs['pk']
        return kwargs

    def get_object(self, queryset = None):
        return get_object_or_404(ShippingAddress, pk=self.kwargs['pk'], user=self.request.user)

class ShippingAddressDeleteView(CustomLoginRequiredMixin, DeleteView):
    http_method_names = ['post']
    model = ShippingAddress
    success_url = reverse_lazy('user:detail')

    def get_object(self, queryset=None):
        return get_object_or_404(ShippingAddress, pk=self.kwargs['pk'], user=self.request.user)

class OSSLoginView(LoginView, CustomFormMixin):
    form_class = LoginForm
    template_name = "registration/login.html"

class SignUpView(CreateView, CustomFormMixin):
    model = User
    form_class = SignUpForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy('user:login')


class OSSLogoutView(View):
    """支持 GET 和 POST 的登出视图，兼容直接访问 /user/logout/"""
    def get(self, request):
        logout(request)
        return redirect('user:login')

    def post(self, request):
        logout(request)
        return redirect('user:login')