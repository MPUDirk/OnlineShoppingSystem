from django.urls import path

from .views import (OSSLoginView, OSSLogoutView, SignUpView, AccountEditView, UserDetailView,
                    RoleSwitchView, ShippingAddressCreateView, ShippingAddressUpdateView, ShippingAddressDeleteView)

app_name = 'user'

urlpatterns = [
    path('', UserDetailView.as_view(), name='detail'),
    path('login/', OSSLoginView.as_view(), name='login'),
    path('logout/', OSSLogoutView.as_view(), name='logout'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('role/switch/', RoleSwitchView.as_view(), name='role_switch'),
    path('changetype/', AccountEditView.as_view(), name='account_edit'),
    path('create/addr/', ShippingAddressCreateView.as_view(), name='shipping_address_create'),
    path('edit/addr/<int:pk>/', ShippingAddressUpdateView.as_view(), name='shipping_address_edit'),
    path('del/addr/<int:pk>/', ShippingAddressDeleteView.as_view(), name='shipping_address_delete'),
]