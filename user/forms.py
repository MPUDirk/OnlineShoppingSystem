from email.policy import default

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache


class LoginForm(AuthenticationForm):
    def clean_username(self):
        account_id = self.cleaned_data.get('username')
        try:
            username = User.objects.get(email=account_id).username
        except User.DoesNotExist:
            username = account_id

        return  username

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
        return User.objects.create_user(**self.cleaned_data)
