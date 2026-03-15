from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User, Group
from django.contrib.auth.password_validation import validate_password

from shopping.models import ShoppingCart
from .models import ShippingAddress


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
        fields = ('full_name', 'username', 'email', 'password')

    email = forms.EmailField(required=True)
    full_name = forms.CharField(max_length=61, required=True)

    def clean_full_name(self):
        name = self.data['full_name'].split(' ')

        if len(name) != 2:
            raise forms.ValidationError('Invalid full_name: it only contain first and last name and split by space')

        self.cleaned_data['first_name'] = name[0]
        self.cleaned_data['last_name'] = name[1]

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

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data.pop('full_name')
        return cleaned_data

    def save(self, commit=True):
        user = User.objects.create_user(**self.cleaned_data)
        user.save()

        customer_group, _ = Group.objects.get_or_create(name='Customer')
        user.groups.add(customer_group)
        ShoppingCart.objects.create(customer=user)

        return user

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = tuple()

    def save(self, commit = True):
        self.instance.groups.clear()
        self.instance.groups.add(Group.objects.get(name='Merchant'))
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
                'placeholder': '请输入省市区及详细地址',
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
        # 仅编辑时检查是否有修改；新建时跳过
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