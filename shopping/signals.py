from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Product
from .sku_catalog import ensure_default_sku


@receiver(post_save, sender=Product)
def product_after_save(sender, instance, created, **kwargs):
    ensure_default_sku(instance)
