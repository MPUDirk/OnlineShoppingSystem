from django.db import migrations, models
from django.utils.text import slugify


def populate_product_slugs(apps, schema_editor):
    Product = apps.get_model('shopping', 'Product')
    for p in Product.objects.all().only('id', 'name', 'slug'):
        if p.slug:
            continue
        base = slugify(p.name)[:200] or 'product'
        if base.isdigit():
            base = f'item-{base}'
        candidate = base
        n = 0
        while Product.objects.filter(slug=candidate).exclude(pk=p.pk).exists():
            n += 1
            candidate = f'{base}-{n}'
        Product.objects.filter(pk=p.pk).update(slug=candidate)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('shopping', '0011_remove_product_total_sku'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='slug',
            field=models.SlugField(blank=True, db_index=True, max_length=255, null=True),
        ),
        migrations.RunPython(populate_product_slugs, noop_reverse),
        migrations.AlterField(
            model_name='product',
            name='slug',
            field=models.SlugField(db_index=True, max_length=255, unique=True),
        ),
    ]
