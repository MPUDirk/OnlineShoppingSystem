from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.files.base import ContentFile
from django.test import Client, TestCase
from django.utils import timezone

from shopping.models import (
    Category,
    Order,
    OrderItem,
    Product,
    ProductProperty,
    ProductPropertyTitle,
    ProductSKU,
)
from shopping.sku_catalog import sync_product_skus

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


class VendorProductDeleteViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.vendor = User.objects.create_user('vdel', 'vdel@v.com', 'secret')
        self.other = User.objects.create_user('vother2', 'o2@o.com', 'secret')
        self.customer = User.objects.create_user('cdel', 'c@c.com', 'secret')
        g, _ = Group.objects.get_or_create(name='Vendor')
        self.vendor.groups.add(g)
        self.other.groups.add(g)

        cat = Category.objects.create(name='DelCat')
        thumb = ContentFile(_TINY_PNG, name='vdel.png')
        self.product = Product.objects.create(
            name='Deletable',
            price=Decimal('10.00'),
            description='d',
            category=cat,
            thumbnail=thumb,
            created_by=self.vendor,
        )

    def test_vendor_deletes_product_without_orders(self):
        pk = self.product.pk
        self.client.login(username='vdel', password='secret')
        response = self.client.post(f'/vendor/products/{pk}/delete/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/vendor/')
        self.assertFalse(Product.objects.filter(pk=pk).exists())

    def test_vendor_cannot_delete_product_with_order_line(self):
        o = Order.objects.create(
            customer=self.customer,
            shipping_address_text='x',
            total_amount=Decimal('10.00'),
            status='pending',
        )
        OrderItem.objects.create(
            order=o,
            product=self.product,
            quantity=1,
            unit_price=Decimal('10.00'),
            subtotal=Decimal('10.00'),
        )
        pk = self.product.pk
        self.client.login(username='vdel', password='secret')
        response = self.client.post(f'/vendor/products/{pk}/delete/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Product.objects.filter(pk=pk).exists())

    def test_other_vendor_gets_404_on_delete(self):
        self.client.login(username='vother2', password='secret')
        response = self.client.post(f'/vendor/products/{self.product.pk}/delete/')
        self.assertEqual(response.status_code, 404)

    def test_get_not_allowed(self):
        self.client.login(username='vdel', password='secret')
        response = self.client.get(f'/vendor/products/{self.product.pk}/delete/')
        self.assertEqual(response.status_code, 405)


class SkuCatalogSyncTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name='SyncCat')
        thumb = ContentFile(_TINY_PNG, name='sync.png')
        self.product = Product.objects.create(
            name='Hoodie',
            price=Decimal('39.99'),
            description='warm',
            category=cat,
            thumbnail=thumb,
        )

    def test_simple_product_has_only_default_row(self):
        sync_product_skus(self.product)
        skus = list(ProductSKU.objects.filter(product=self.product).order_by('sku'))
        self.assertEqual(len(skus), 1)
        self.assertIn('DEFAULT', skus[0].sku)

    def test_single_attribute_group_has_one_row_per_option(self):
        size = ProductPropertyTitle.objects.create(product=self.product, title='Size')
        for label in ('M', 'L'):
            ProductProperty.objects.create(title=size, name=label)
        sync_product_skus(self.product)
        qs = ProductSKU.objects.filter(product=self.product).prefetch_related('property_links').order_by('sku')
        self.assertEqual(qs.count(), 2)
        self.assertFalse(ProductSKU.objects.filter(product=self.product, sku__contains='DEFAULT').exists())
        for sku in qs:
            self.assertEqual(sku.property_links.count(), 1)
            self.assertRegex(sku.sku, r'-P\d+$')
