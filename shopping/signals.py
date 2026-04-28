from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Product, ProductProperty, ProductPropertyTitle
from .sku_catalog import sync_product_skus


@receiver(post_save, sender=Product)
def product_saved_sync_skus(sender, instance, **kwargs):
    sync_product_skus(instance)


@receiver([post_save, post_delete], sender=ProductProperty)
def product_property_changed_sync_skus(sender, instance, **kwargs):
    sync_product_skus(instance.title.product)


@receiver(post_delete, sender=ProductPropertyTitle)
def property_title_deleted_sync_skus(sender, instance, **kwargs):
    sync_product_skus(instance.product)
