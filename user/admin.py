from django.contrib import admin
from .models import ShippingAddress, Wallet, Transaction


admin.site.register(ShippingAddress)
admin.site.register(Wallet)
admin.site.register(Transaction)
