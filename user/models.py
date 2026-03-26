from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal


class Wallet(models.Model):
    """User wallet for balance (both Customer and Vendor)."""
    user = models.OneToOneField(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='wallet'
    )
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - ${self.balance}"


class Transaction(models.Model):
    """Transaction record for deposit/withdraw/purchase ledger."""
    DEPOSIT = 'deposit'
    WITHDRAW = 'withdraw'
    REFUND = 'refund'
    PURCHASE = 'purchase'

    TYPE_CHOICES = [
        (DEPOSIT, 'Deposit'),
        (WITHDRAW, 'Withdraw'),
        (PURCHASE, 'Purchase'),
    ]

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    description = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} ${self.amount}"


class ShippingAddress(models.Model):
    user = models.ForeignKey(
        'auth.User',
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