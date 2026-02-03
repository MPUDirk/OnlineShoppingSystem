from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, FormView, FormMixin

# Create your views here.
class CustomFormMixin(FormMixin):
    def form_invalid(self:FormView, form:forms.ModelForm):
        return self.render_to_response({"errors": form.errors.as_data()})

class OSSLoginView(LoginView, CustomFormMixin):
    template_name = "registration/login.html"

class SignUpView(CreateView, CustomFormMixin):
    model = User
    template_name = "registration/signup.html"
    fields = ['first_name', 'last_name', 'username', 'email', 'password']
    success_url = reverse_lazy('user:login')

    def form_valid(self, form:forms.ModelForm):
        User.objects.create_user(**form.cleaned_data)
        return HttpResponseRedirect(self.success_url)