from django.views.generic import CreateView

from .forms import SignUpForm

# Create your views here.
class SignUpView(CreateView):
    template_name = "registration/signup.html"
    form_class = SignUpForm
