# Remove legacy Product.total_sku (inventory managed via ProductSKU).

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shopping', '0010_productpropertytitle_unique_product_title'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='total_sku',
        ),
    ]
