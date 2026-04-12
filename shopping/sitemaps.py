from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Product


class HomeSitemap(Sitemap):
    changefreq = 'daily'
    priority = 1.0

    def items(self):
        return ['shopping:index']

    def location(self, item):
        return reverse(item)


class ProductSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Product.objects.filter(is_active=True).order_by('-updated_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()