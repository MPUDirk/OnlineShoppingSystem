from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Category(models.Model):
    """Product category"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """Product model (Block A)"""
    # System-generated unique product ID (A15)
    product_id = models.CharField(max_length=50, unique=True, editable=False)
    
    # Basic information (A3, A6, A16)
    name = models.CharField(max_length=200)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    thumbnail = models.ImageField(upload_to='product_thumbnails/')
    
    # Additional attributes (A6 requires at least two additional attributes)
    description = models.TextField()
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    
    # Enable/disable (A18)
    is_active = models.BooleanField(default=True)
    
    # Track who added the product (for vendor edit permission)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_products'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['product_id']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} (ID: {self.product_id})"
    
    def save(self, *args, **kwargs):
        """Auto-generate unique product ID"""
        if not self.product_id:
            # Format: PROD-{timestamp}-{random}
            import time
            import random
            timestamp = int(time.time())
            random_num = random.randint(1000, 9999)
            self.product_id = f"PROD-{timestamp}-{random_num}"
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    """Product image model (Block B - multiple photos)"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='product_images/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['display_order', 'created_at']
    
    def __str__(self):
        return f"{self.product.name} - Image {self.display_order}"


class ShoppingCart(models.Model):
    """Shopping cart model (Block A - A7, A8, A9, A10)"""
    customer = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shopping_cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Shopping Cart for {self.customer.username}"
    
    def get_total(self):
        """Calculate total amount in shopping cart (A8)"""
        return sum(item.get_subtotal() for item in self.items.all())


class CartItem(models.Model):
    """Cart item model (Block A - A7, A8, A9, A10)"""
    cart = models.ForeignKey(
        ShoppingCart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['cart', 'product']
    
    def __str__(self):
        return f"{self.cart.customer.username} - {self.product.name} x{self.quantity}"
    
    def get_subtotal(self):
        """Calculate subtotal for this cart item (A8)"""
        return self.product.price * self.quantity


class Order(models.Model):
    """Order model (Block A, B - A11, A12, A13)"""
    # Order number (A12)
    order_number = models.CharField(max_length=50, unique=True, editable=False)
    
    # Customer information
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    
    # Order information (A13: shipping address in order detail)
    shipping_address = models.ForeignKey(
        'user.ShippingAddress',
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders'
    )
    shipping_address_text = models.TextField(blank=True)  # Snapshot for display if address deleted
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Order status (Block B2: at least 4 values - pending, shipped, cancelled, hold)
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('hold', 'Hold'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default='pending'
    )
    
    # Timestamps
    purchase_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Block B4: dates for status changes (shipment date, cancel date)
    shipped_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-purchase_date']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['customer']),
            models.Index(fields=['status']),
        ]

    def get_is_finished(self):
        after_7days = self.updated_at + timedelta(days=7)
        is_finished = self.status == 'delivered' and timezone.now() > after_7days
        if is_finished:
            OrderStatusHistory.objects.get_or_create(
                order=self, status='finished',
                defaults={'note':'Order finished automatically','changed_at': after_7days}
            )
        return is_finished

    def get_next_status(self):
        next_map = {
            'pending': 'shipped',
            'shipped': 'delivered',
        }

        return next_map.get(self.status, self.status)

    def get_vendor_amount(self, vendor):
        user = User.objects.get(username=vendor)
        if user.is_staff or user.is_superuser:
            return sum(item.quantity * item.unit_price for item in self.items.all())
        return sum(item.quantity * item.unit_price for item in self.items.filter(product__created_by=vendor))
    
    def __str__(self):
        return f"Order {self.order_number}"
    
    def save(self, *args, **kwargs):
        """Auto-generate order number"""
        if not self.order_number:
            import time
            import random
            timestamp = int(time.time())
            random_num = random.randint(1000, 9999)
            self.order_number = f"PO-{timestamp}-{random_num}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """Order item model (Block A, B - A13)"""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='order_items'
    )
    
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.product.name} x{self.quantity}"
    
    def save(self, *args, **kwargs):
        """Auto-calculate subtotal"""
        if not self.subtotal:
            self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    """
    Block B4: record of order status changes with dates.
    Tracks shipment date, cancel date, etc. for display in order detail.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    status = models.CharField(max_length=20)
    changed_at = models.DateTimeField(default=timezone.now, editable=False)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-changed_at']
        verbose_name_plural = 'Order status history'

    def __str__(self):
        return f"{self.order.order_number} - {self.status} at {self.changed_at}"
