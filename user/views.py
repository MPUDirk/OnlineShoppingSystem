from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, FormView, FormMixin

from .forms import SignUpForm, LoginForm

# Create your views here.
class CustomFormMixin(FormMixin):
    def form_invalid(self:FormView, form:forms.ModelForm):
        context = self.get_context_data()
        context['errors'] = form.errors.as_data()
        return self.render_to_response(context)

class OSSLoginView(LoginView, CustomFormMixin):
    form_class = LoginForm
    template_name = "registration/login.html"

class SignUpView(CreateView, CustomFormMixin):
    model = User
    form_class = SignUpForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy('user:login')