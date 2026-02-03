from django.contrib import admin
from .models import ShippingAddress


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
	list_display = ('user', 'address', 'is_default', 'created_at')
	list_filter = ('is_default',)
	search_fields = ('user__username', 'address')
