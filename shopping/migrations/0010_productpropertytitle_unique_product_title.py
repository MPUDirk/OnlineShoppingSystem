# Generated manually for multi-attribute-type support

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shopping', '0009_product_sku_d4_d5'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='productproperty',
            options={'ordering': ['pk']},
        ),
        migrations.AlterModelOptions(
            name='productpropertytitle',
            options={'ordering': ['pk']},
        ),
        migrations.AlterUniqueTogether(
            name='productpropertytitle',
            unique_together={('product', 'title')},
        ),
    ]
