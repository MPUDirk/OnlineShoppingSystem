from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class UserSitemap(Sitemap):
    def items(self):
        return ['user:login', 'user:logout', 'user:signup']

    def location(self, item):
        return reverse(item)