from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User, Group
from django.contrib.auth.password_validation import validate_password
from decimal import Decimal

from shopping.models import ShoppingCart
from .models import ShippingAddress, Wallet


class LoginForm(AuthenticationForm):
    def clean_username(self):
        account_id = self.cleaned_data.get('username')
        try:
            username = User.objects.get(email=account_id).username
        except User.DoesNotExist:
            username = account_id

        return username

class SignUpForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password')

    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True, label='First Name')
    last_name = forms.CharField(max_length=30, required=True, label='Last Name')
    user_type = forms.ChoiceField(
        choices=[('customer', 'Customer'), ('vendor', 'Vendor')],
        widget=forms.RadioSelect,
        label='Account Type',
        required=True,
        initial='customer'
    )

    def clean_password(self):
        password = self.cleaned_data.get('password')
        try:
            validate_password(password, self.instance)
        except forms.ValidationError as e:
            raise forms.ValidationError(e.messages, code='invalid')
        return password

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email already exists')
        return email

    def save(self, commit=True):
        user_type = self.cleaned_data.pop('user_type')
        user = User.objects.create_user(**self.cleaned_data)

        if user_type == 'customer':
            customer_group, _ = Group.objects.get_or_create(name='Customer')
            user.groups.add(customer_group)
            ShoppingCart.objects.create(customer=user)
        else:
            vendor_group, _ = Group.objects.get_or_create(name='Vendor')
            user.groups.add(vendor_group)

        Wallet.objects.get_or_create(user=user)
        return user


class DepositForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'})
    )


class WithdrawForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'})
    )

    def __init__(self, *args, **kwargs):
        self.wallet = kwargs.pop('wallet')
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and self.wallet and amount > self.wallet.balance:
            raise forms.ValidationError('Insufficient balance')
        return amount


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = tuple()

    def save(self, commit = True):
        self.instance.groups.clear()
        self.instance.groups.add(Group.objects.get(name='Vendor'))
        return super().save(commit)


class ShippingAddressUpdateForm(forms.ModelForm):
    class Meta:
        model = ShippingAddress
        fields = ('address', 'is_default')
        widgets = {
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'id': 'id_address',
                'placeholder': 'Enter full address (street, city, state, zip)',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        try:
            self.addr = ShippingAddress.objects.get(pk=kwargs.pop('pk'))
        except KeyError:
            self.addr = None
        super().__init__(*args, **kwargs)

    def clean_address(self):
        address = self.cleaned_data.get('address')
        if ShippingAddress.objects.filter(user=self.user, address=address).exists() and 'address' in self.changed_data:
            raise forms.ValidationError('Address already exists')
        return address

    def clean_is_default(self):
        is_default = self.cleaned_data.get('is_default')
        if is_default:
            ShippingAddress.objects.filter(user=self.user).update(is_default=False)
        return is_default

    def clean(self):
        if self.addr is not None and len(self.changed_data) == 0:
            raise forms.ValidationError('No Changed')
        return super().clean()

    def save(self, commit = True):
        data = self.cleaned_data
        if self.addr is not None:
            instance = self.addr
            if instance.user != self.user:
                raise forms.ValidationError('No Permission')
            instance.address = data.get('address')
            instance.is_default = data.get('is_default')
            instance.save()
            return instance
        else:
            return ShippingAddress.objects.create(user=self.user, **data)