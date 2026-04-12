from datetime import timedelta
from decimal import Decimal

from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


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
    # SEO / Block Y: search-friendly URL segment (unique, auto-filled from name)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
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

    def _make_unique_slug(self) -> str:
        base = slugify(self.name)[:200] or 'product'
        if base.isdigit():
            base = f'item-{base}'
        candidate = base
        n = 0
        while Product.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
            n += 1
            candidate = f'{base}-{n}'
        return candidate

    def save(self, *args, **kwargs):
        """Auto-generate unique product ID and URL slug when missing."""
        if not self.product_id:
            # Format: PROD-{timestamp}-{random}
            import time
            import random
            timestamp = int(time.time())
            random_num = random.randint(1000, 9999)
            self.product_id = f"PROD-{timestamp}-{random_num}"
        if not self.slug:
            self.slug = self._make_unique_slug()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('shopping:product_detail', kwargs={'slug': self.slug})


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


class ProductSKU(models.Model):
    """D4: one row per sellable configuration; simple products use a single SKU (often no property links)."""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='skus',
    )
    sku = models.CharField(max_length=80, unique=True)
    in_stock = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sku']
        verbose_name = 'Product SKU'
        verbose_name_plural = 'Product SKUs'

    def __str__(self):
        return self.sku


class SKUProductProperty(models.Model):
    """Links a SKU to one ProductProperty per attribute dimension."""
    sku = models.ForeignKey(
        ProductSKU,
        on_delete=models.CASCADE,
        related_name='property_links',
    )
    product_property = models.ForeignKey(
        'ProductProperty',
        on_delete=models.CASCADE,
    )

    class Meta:
        unique_together = [('sku', 'product_property')]

    def __str__(self):
        return f'{self.sku.sku} → {self.product_property}'


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
    # One ProductProperty id per attribute group (e.g. Type, Color), in group order
    selected_property_ids = models.JSONField(default=list, blank=True)
    product_sku = models.ForeignKey(
        'ProductSKU',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cart_items',
    )
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['cart', 'product']),
        ]
    
    def __str__(self):
        return f"{self.cart.customer.username} - {self.product.name} x{self.quantity}"
    
    def get_subtotal(self):
        """Calculate subtotal for this cart item (A8)"""
        unit = self.product.price
        for pid in self.selected_property_ids or []:
            try:
                prop = ProductProperty.objects.get(pk=pid)
            except ProductProperty.DoesNotExist:
                continue
            if prop.title.product_id == self.product_id:
                unit += prop.change_value or 0
        return unit * self.quantity

    def get_property_summary_display(self) -> str:
        from shopping.property_selection import format_property_summary

        return format_property_summary(list(self.selected_property_ids or []))

    def get_line_image_url(self):
        """
        Thumbnail for cart/checkout: first selected option with an image, else SKU-linked
        property image, else product thumbnail.
        """
        ids = list(self.selected_property_ids or [])
        if ids:
            props = ProductProperty.objects.filter(pk__in=ids, title__product_id=self.product_id)
            by_id = {p.pk: p for p in props}
            for pid in ids:
                p = by_id.get(pid)
                if p and p.image:
                    return p.image.url
        sku = self.product_sku
        if sku:
            for link in sku.property_links.select_related('product_property').all():
                if link.product_property.image:
                    return link.product_property.image.url
        if self.product.thumbnail:
            return self.product.thumbnail.url
        return None


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
    property_summary = models.CharField(max_length=500, blank=True)
    product_sku = models.ForeignKey(
        'ProductSKU',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items',
    )
    sku_code = models.CharField(max_length=80, blank=True)
    configuration_label = models.CharField(max_length=500, blank=True)
    
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

class ProductPropertyTitle(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='property_titles'
    )
    title = models.CharField(max_length=50)
    is_main = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ['pk']
        unique_together = [('product', 'title')]

    def save(
        self,
        *,
        force_insert = False,
        force_update = False,
        using = None,
        update_fields = None,
    ):
        super().save()

    def __str__(self):
        return self.title

class ProductProperty(models.Model):
    title = models.ForeignKey(
        ProductPropertyTitle,
        on_delete=models.CASCADE,
        related_name='properties'
    )
    image = models.ImageField(upload_to='product_properties/', blank=True)
    name = models.CharField(max_length=255)
    change_value = models.DecimalField(default=0, max_digits=10, decimal_places=2, blank=True, null=True)
    sku = models.IntegerField(validators=[MinValueValidator(0)])

    class Meta:
        ordering = ['pk']

    def __str__(self):
        return f"{self.title}: {self.name}"

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
