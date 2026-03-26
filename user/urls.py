from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import (OSSLoginView, SignUpView, UserDetailView,
                    ShippingAddressCreateView, ShippingAddressUpdateView, ShippingAddressDeleteView,
                    WalletDepositView, WalletWithdrawView, TransactionListView)

app_name = 'user'

urlpatterns = [
    path('', UserDetailView.as_view(), name='detail'),
    path('login/', OSSLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('create/addr/', ShippingAddressCreateView.as_view(), name='shipping_address_create'),
    path('edit/addr/<int:pk>/', ShippingAddressUpdateView.as_view(), name='shipping_address_edit'),
    path('del/addr/<int:pk>/', ShippingAddressDeleteView.as_view(), name='shipping_address_delete'),
    path('wallet/deposit/', WalletDepositView.as_view(), name='wallet_deposit'),
    path('wallet/withdraw/', WalletWithdrawView.as_view(), name='wallet_withdraw'),
    path('wallet/transactions/', TransactionListView.as_view(), name='transaction_list'),
]