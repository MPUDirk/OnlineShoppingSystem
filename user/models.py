from django.db import models
from django.conf import settings
from django.utils import timezone


class CustomerUser(models.Model):
    """Independent profile-like model linked to Django's User via FK."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer_profiles',
        default=1  # Replace with a valid user ID or adjust logic
    )
    email = models.EmailField(blank=True)

    def __str__(self):
        return getattr(self.user, 'username', '')


class ShippingAddress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shipping_addresses'
    )
    address = models.TextField()
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.address[:40]}"