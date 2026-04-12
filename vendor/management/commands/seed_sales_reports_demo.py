"""Seed Order/OrderItem rows for vendor sales reports demos (days, months, years)."""
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


def _datetime_in_month(now, months_before: int):
    """months_before=0 → current month; 1 → previous month, etc. Uses day 15, 14:00 local."""
    y, m = now.year, now.month
    for _ in range(months_before):
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return now.replace(year=y, month=m, day=15, hour=14, minute=0, second=0, microsecond=0)


def _datetime_in_year(now, years_before: int):
    """years_before=0 → current calendar year (June 10); 1 → previous year, etc."""
    y = now.year - years_before
    return now.replace(year=y, month=6, day=10, hour=12, minute=0, second=0, microsecond=0)


class Command(BaseCommand):
    help = (
        'Creates demo delivered orders for /vendor/reports/. '
        'Use --days for daily spread; --months for one order per past month (Month chart); '
        '--years for one order per past year (Year chart). Combine as needed.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=14,
            help='One order per day for the last N days (default 14). Set 0 to skip.',
        )
        parser.add_argument(
            '--months',
            type=int,
            default=0,
            help='Also create one order per month for the last N months (0=skip). Typical: 12 for Month view.',
        )
        parser.add_argument(
            '--years',
            type=int,
            default=0,
            help='Also create one order per year for the last N calendar years (0=skip). Typical: 5 for Year view.',
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
        days = max(0, options['days'])
        months_n = max(0, options['months'])
        years_n = max(0, options['years'])
        vname = options['vendor_username']
        cname = options['customer_username']
        password = options['password']

        # Always (re)set password so login works even if the user already existed
        # with a different password or was created without set_password.
        vendor, v_created = User.objects.get_or_create(
            username=vname,
            defaults={'email': f'{vname}@example.com'},
        )
        vendor.set_password(password)
        vendor.is_active = True
        if not vendor.email:
            vendor.email = f'{vname}@example.com'
        vendor.save()
        grp, _ = Group.objects.get_or_create(name='Vendor')
        vendor.groups.add(grp)

        customer, c_created = User.objects.get_or_create(
            username=cname,
            defaults={'email': f'{cname}@example.com'},
        )
        customer.set_password(password)
        customer.is_active = True
        if not customer.email:
            customer.email = f'{cname}@example.com'
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

        def create_one_order(when, subtotal: Decimal):
            order = Order.objects.create(
                customer=customer,
                shipping_address=None,
                shipping_address_text='Demo seed address',
                total_amount=subtotal,
                status='delivered',
            )
            Order.objects.filter(pk=order.pk).update(purchase_date=when)
            OrderItem.objects.create(
                order=order,
                product=product,
                product_sku=sku,
                quantity=1,
                unit_price=subtotal,
                subtotal=subtotal,
                property_summary='Demo',
                sku_code=sku.sku,
                configuration_label='Demo',
            )
            return 1

        created = 0
        now = timezone.now()

        for i in range(days):
            when = now - timedelta(days=i, hours=10)
            base = Decimal('10.00') + Decimal(i)
            created += create_one_order(when, base)

        for mb in range(months_n):
            when = _datetime_in_month(now, mb)
            if when > now:
                when = now - timedelta(hours=2)
            base = Decimal('80.00') + Decimal(mb * 17)
            created += create_one_order(when, base)

        for yb in range(years_n):
            when = _datetime_in_year(now, yb)
            if when > now:
                when = now - timedelta(hours=2)
            base = Decimal('200.00') + Decimal(yb * 55)
            created += create_one_order(when, base)

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {created} delivered order(s) for vendor {vname!r} / product {product.name!r} '
                f'(days={days}, months={months_n}, years={years_n}).'
            )
        )
        self.stdout.write(
            'Log in as that vendor and open /vendor/reports/?period=month or period=year to see multi-period bars.'
        )
