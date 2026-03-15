from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
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
        return context

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