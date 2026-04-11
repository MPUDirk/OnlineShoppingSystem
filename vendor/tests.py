from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.files.base import ContentFile
from django.test import Client, TestCase
from django.utils import timezone

from shopping.models import Category, Order, OrderItem, Product

_TINY_PNG = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06'
    b'\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00'
    b'\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
)


class VendorSalesReportViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.vendor = User.objects.create_user('vreports', 'v@v.com', 'secret')
        self.other_vendor = User.objects.create_user('vother', 'o@o.com', 'secret')
        self.customer = User.objects.create_user('creports', 'c@c.com', 'secret')
        g, _ = Group.objects.get_or_create(name='Vendor')
        self.vendor.groups.add(g)
        self.other_vendor.groups.add(g)

        cat = Category.objects.create(name='ReportsCat')
        thumb = ContentFile(_TINY_PNG, name='tr.png')
        self.product = Product.objects.create(
            name='VendorA Product',
            price=Decimal('10.00'),
            description='d',
            category=cat,
            thumbnail=thumb,
            created_by=self.vendor,
        )
        thumb_b = ContentFile(_TINY_PNG, name='tr2.png')
        self.product_b = Product.objects.create(
            name='VendorB Product',
            price=Decimal('5.00'),
            description='d',
            category=cat,
            thumbnail=thumb_b,
            created_by=self.other_vendor,
        )

    def _line(self, product, days_ago, subtotal, status='delivered'):
        o = Order.objects.create(
            customer=self.customer,
            shipping_address_text='x',
            total_amount=subtotal,
            status=status,
        )
        Order.objects.filter(pk=o.pk).update(
            purchase_date=timezone.now() - timedelta(days=days_ago, hours=2)
        )
        OrderItem.objects.create(
            order=o,
            product=product,
            quantity=1,
            unit_price=subtotal,
            subtotal=subtotal,
        )

    def test_vendor_sees_only_own_lines_excludes_cancelled(self):
        self._line(self.product, 0, Decimal('25.00'))
        self._line(self.product, 0, Decimal('99.00'), status='cancelled')
        self._line(self.product_b, 0, Decimal('50.00'))

        self.client.login(username='vreports', password='secret')
        response = self.client.get('/vendor/reports/', {'period': 'today'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['kpi_revenue'], Decimal('25.00'))
        self.assertEqual(response.context['kpi_orders'], 1)

    def test_staff_sees_all_vendor_lines(self):
        staff = User.objects.create_user('staffrep', 's@s.com', 'secret', is_staff=True)
        self._line(self.product, 0, Decimal('10.00'))
        self._line(self.product_b, 0, Decimal('30.00'))

        self.client.login(username='staffrep', password='secret')
        response = self.client.get('/vendor/reports/', {'period': 'today'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['kpi_revenue'], Decimal('40.00'))
        self.assertEqual(response.context['kpi_orders'], 2)

    def test_invalid_period_defaults_to_month(self):
        self._line(self.product, 0, Decimal('7.00'))
        self.client.login(username='vreports', password='secret')
        response = self.client.get('/vendor/reports/', {'period': 'not-a-period'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['report_period'], 'month')
