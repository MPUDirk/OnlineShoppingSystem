import re

from django.shortcuts import redirect

from user.models import ShippingAddress


class CheckShippAddrMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path_pattens = [
            r'/user/create/addr/',
            r'/user/logout/',
            r'/admin/*'
        ]
        path = request.path
        user = request.user
        match_pattens = [re.match(pattern, path) for pattern in path_pattens]

        if not any(match_pattens) and user.is_authenticated and not user.is_superuser:
            if not ShippingAddress.objects.filter(user=user).exists():
                return redirect('user:shipping_address_create')
        return self.get_response(request)
