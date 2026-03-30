from django.apps import AppConfig


class ProductsConfig(AppConfig):
    name = 'shopping'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        import shopping.signals  # noqa: F401
