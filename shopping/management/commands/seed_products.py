"""
Create sample product data in the database.
Run: python manage.py seed_products
"""
import base64
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from shopping.models import Category, Product


# Minimal 1x1 transparent PNG for placeholder thumbnails
PLACEHOLDER_PNG = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='
)


SAMPLE_PRODUCTS = [
    # Electronics
    {"name": "Smartphone", "price": 2999, "description": "Latest smartphone with high-performance processor and premium camera", "category": "Electronics"},
    {"name": "Wireless Earbuds", "price": 299, "description": "High-quality wireless Bluetooth earbuds with excellent noise cancellation", "category": "Electronics"},
    {"name": "4K Monitor", "price": 1599, "description": "27-inch 4K ultra HD monitor with accurate color reproduction", "category": "Electronics"},
    {"name": "Mechanical Keyboard", "price": 499, "description": "RGB backlit mechanical keyboard with crisp blue switch feel", "category": "Electronics"},
    # Clothing
    {"name": "Running Shoes", "price": 599, "description": "Comfortable and breathable running shoes for daily sports and casual wear", "category": "Clothing"},
    {"name": "Cotton T-Shirt", "price": 59, "description": "100% cotton basic t-shirt, comfortable and absorbent", "category": "Clothing"},
    {"name": "Jeans", "price": 199, "description": "Classic straight-leg jeans, durable and long-lasting", "category": "Clothing"},
    {"name": "Backpack", "price": 199, "description": "Large capacity backpack, ideal for travel and daily use", "category": "Clothing"},
    # Books
    {"name": "Programming Book", "price": 89, "description": "Python programming from beginner to advanced, suitable for beginners", "category": "Books"},
    {"name": "Sci-Fi Novel Collection", "price": 128, "description": "Classic sci-fi novel collection, exploring the future world", "category": "Books"},
    {"name": "Cooking Guide", "price": 68, "description": "1000 home recipes with illustrations", "category": "Books"},
    # Home
    {"name": "Coffee Machine", "price": 1299, "description": "Full automatic coffee machine, one-touch delicious coffee", "category": "Home"},
    {"name": "Air Purifier", "price": 899, "description": "Quiet home air purifier, removes formaldehyde and PM2.5", "category": "Home"},
    {"name": "Robot Vacuum", "price": 1999, "description": "Smart path planning, auto recharge robot vacuum", "category": "Home"},
]


class Command(BaseCommand):
    help = "Create sample categories and products in the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing products and categories before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            Product.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing products and categories."))

        # Create categories
        category_names = ["Electronics", "Clothing", "Books", "Home"]
        categories = {}
        for name in category_names:
            cat, created = Category.objects.get_or_create(name=name)
            categories[name] = cat
            if created:
                self.stdout.write(f"  Created category: {name}")

        # Create products
        created_count = 0
        for i, data in enumerate(SAMPLE_PRODUCTS):
            if Product.objects.filter(name=data["name"]).exists():
                continue

            category = categories.get(data["category"])
            product = Product(
                name=data["name"],
                price=data["price"],
                description=data["description"],
                category=category,
                is_active=True,
            )
            product.thumbnail.save(
                f"placeholder_{i}.png",
                ContentFile(PLACEHOLDER_PNG),
                save=False,
            )
            product.save()
            created_count += 1
            self.stdout.write(f"  Created product: {data['name']}")

        self.stdout.write(self.style.SUCCESS(f"Done. Created {created_count} new products."))
