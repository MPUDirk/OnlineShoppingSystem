"""Seed Order/OrderItem rows spread over recent days for vendor sales reports demos."""
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from shopping.models import Category, Order, OrderItem, Product, ProductSKU

# 1×1 transparent PNG
_TINY_PNG = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06'
    b'\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00'
    b'\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
)


class Command(BaseCommand):
    help = (
        'Creates demo orders and line items for the vendor sales reports page. '
        'Spreads one delivered order per day over the last N days (default 14). '
        'Assigns a Vendor user and product if missing.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=14,
            help='Number of days back to create one order each (default 14).',
        )
        parser.add_argument(
            '--vendor-username',
            default='demo_vendor',
            help='Vendor account username (created if missing).',
        )
        parser.add_argument(
            '--customer-username',
            default='demo_customer',
            help='Customer account username (created if missing).',
        )
        parser.add_argument(
            '--password',
            default='demo123456',
            help='Password set when creating demo users.',
        )

    def handle(self, *args, **options):
        days = max(1, options['days'])
        vname = options['vendor_username']
        cname = options['customer_username']
        password = options['password']

        vendor, v_created = User.objects.get_or_create(
            username=vname,
            defaults={'email': f'{vname}@example.com'},
        )
        if v_created:
            vendor.set_password(password)
            vendor.save()
        grp, _ = Group.objects.get_or_create(name='Vendor')
        vendor.groups.add(grp)

        customer, c_created = User.objects.get_or_create(
            username=cname,
            defaults={'email': f'{cname}@example.com'},
        )
        if c_created:
            customer.set_password(password)
            customer.save()

        category, _ = Category.objects.get_or_create(
            name='Demo category (sales reports)',
            defaults={'description': 'Seeded for reports demo'},
        )

        product = (
            Product.objects.filter(created_by=vendor)
            .order_by('pk')
            .first()
        )
        if not product:
            thumb = ContentFile(_TINY_PNG, name='demo_thumb.png')
            product = Product.objects.create(
                name='Demo product (sales reports)',
                price=Decimal('19.99'),
                description='Seeded for vendor analytics demo.',
                category=category,
                thumbnail=thumb,
                created_by=vendor,
                is_active=True,
            )
            self.stdout.write(self.style.SUCCESS(f'Created product pk={product.pk}'))

        sku = ProductSKU.objects.filter(product=product).first()
        if not sku:
            sku = ProductSKU.objects.create(
                product=product,
                sku=f'DEMO-{product.pk}-DEFAULT',
                in_stock=True,
            )
            self.stdout.write(self.style.SUCCESS(f'Created default SKU {sku.sku}'))

        created_orders = 0
        now = timezone.now()
        for i in range(days):
            when = now - timedelta(days=i, hours=10)
            base = Decimal('10.00') + Decimal(i)
            order = Order.objects.create(
                customer=customer,
                shipping_address=None,
                shipping_address_text='Demo seed address',
                total_amount=base,
                status='delivered',
            )
            Order.objects.filter(pk=order.pk).update(purchase_date=when)
            OrderItem.objects.create(
                order=order,
                product=product,
                product_sku=sku,
                quantity=1,
                unit_price=base,
                subtotal=base,
                property_summary='Demo',
                sku_code=sku.sku,
                configuration_label='Demo',
            )
            created_orders += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {created_orders} delivered order(s) for vendor {vname!r} / product {product.name!r}.'
            )
        )
        self.stdout.write(
            'Open /vendor/reports/ as that vendor (or staff) to view charts and KPIs.'
        )
