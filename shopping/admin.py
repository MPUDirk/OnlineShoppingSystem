from django.contrib import admin

from .models import (
    Category,
    Product,
    ProductImage,
    ProductSKU,
    SKUProductProperty,
    ShoppingCart,
    CartItem,
    Order,
    OrderItem,
)


class SKUProductPropertyInline(admin.TabularInline):
    model = SKUProductProperty
    extra = 0
    raw_id_fields = ['product_property']


@admin.register(ProductSKU)
class ProductSKUAdmin(admin.ModelAdmin):
    list_display = ('sku', 'product', 'in_stock', 'created_at')
    list_filter = ('in_stock',)
    search_fields = ('sku', 'product__name', 'product__product_id')
    inlines = [SKUProductPropertyInline]
    raw_id_fields = ['product']


# Register your models here.
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(ShoppingCart)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)
