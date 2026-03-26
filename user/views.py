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
from .forms import SignUpForm, LoginForm, UserEditForm, ShippingAddressUpdateForm, DepositForm, WithdrawForm
from .models import ShippingAddress, Wallet, Transaction


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
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        context['wallet'] = wallet
        return context

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

class WalletDepositView(CustomLoginRequiredMixin, FormView):
    form_class = DepositForm
    template_name = 'user/wallet_deposit.html'
    success_url = reverse_lazy('user:detail')

    def form_valid(self, form):
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        amount = form.cleaned_data['amount']
        wallet.balance += amount
        wallet.save()
        Transaction.objects.create(
            user=self.request.user,
            amount=amount,
            transaction_type=Transaction.DEPOSIT,
            balance_after=wallet.balance,
            description='Deposit'
        )
        return redirect(self.success_url)


class WalletWithdrawView(CustomLoginRequiredMixin, FormView):
    form_class = WithdrawForm
    template_name = 'user/wallet_withdraw.html'
    success_url = reverse_lazy('user:detail')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        context['wallet'] = wallet
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        kwargs['wallet'] = wallet
        return kwargs

    def form_valid(self, form):
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        amount = form.cleaned_data['amount']
        wallet.balance -= amount
        wallet.save()
        Transaction.objects.create(
            user=self.request.user,
            amount=-amount,
            transaction_type=Transaction.WITHDRAW,
            balance_after=wallet.balance,
            description='Withdraw'
        )
        return redirect(self.success_url)


class TransactionListView(CustomLoginRequiredMixin, TemplateView):
    template_name = 'user/transaction_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transactions'] = Transaction.objects.filter(user=self.request.user)[:50]
        return context


class OSSLoginView(LoginView, CustomFormMixin):
    form_class = LoginForm
    template_name = "registration/login.html"

class SignUpView(CreateView, CustomFormMixin):
    model = User
    form_class = SignUpForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy('user:login')


class OSSLogoutView(View):
    """登出仅支持 POST，防止通过链接/图片等方式诱导用户被动登出"""
    http_method_names = ['post']

    def post(self, request):
        logout(request)
        return redirect('user:login')