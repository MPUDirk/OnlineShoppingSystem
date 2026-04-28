"""D4/D5: resolve ProductSKU from selected ProductProperty ids; labels for orders."""
from __future__ import annotations

from typing import List, Optional

from django.db import transaction

from .models import Product, ProductPropertyTitle, ProductSKU, SKUProductProperty


def get_groups_with_options(product: Product) -> List[ProductPropertyTitle]:
    out = []
    for t in ProductPropertyTitle.objects.filter(product=product).prefetch_related('properties').order_by('pk'):
        if t.properties.exists():
            out.append(t)
    return out


def _delete_linkless_placeholder_skus(product: Product) -> None:
    """Remove *-DEFAULT and other SKU rows not tied to variants (inventory page cleanup)."""
    for sku in ProductSKU.objects.filter(product=product).prefetch_related('property_links'):
        if sku.property_links.count() == 0:
            sku.delete()


def sync_product_skus(product: Product) -> None:
    """
    Keep ProductSKU rows in sync with configurable options.

    - No attribute groups with options → one linkless SKU (``{product_id}-DEFAULT``).
    - Exactly one dimension (e.g. only Size): one SKU per option, codes ``{product_id}-P{property_pk}``.
    - More than one dimension: no automatic matrix; remove placeholder/linkless SKUs only.
    """
    groups = get_groups_with_options(product)

    if not groups:
        ensure_default_sku(product)
        return

    if len(groups) > 1:
        _delete_linkless_placeholder_skus(product)
        return

    g = groups[0]
    for prop in g.properties.all():
        code = f'{product.product_id}-P{prop.pk}'
        sku, _ = ProductSKU.objects.get_or_create(
            product=product,
            sku=code,
            defaults={'in_stock': True},
        )
        SKUProductProperty.objects.get_or_create(sku=sku, product_property=prop)

    _delete_linkless_placeholder_skus(product)


def ensure_default_sku(product: Product) -> Optional[ProductSKU]:
    """One SKU with no property links for simple products only (no attribute options)."""
    if get_groups_with_options(product):
        return None
    for sku in ProductSKU.objects.filter(product=product).prefetch_related('property_links'):
        if sku.property_links.count() == 0:
            return sku
    return ProductSKU.objects.create(
        product=product,
        sku=f'{product.product_id}-DEFAULT',
        in_stock=True,
    )


def find_sku_for_selection(product: Product, property_ids: Optional[List[int]]) -> Optional[ProductSKU]:
    """
    Find ProductSKU whose linked ProductProperty set exactly matches property_ids.
    property_ids empty [] means simple product (no attribute groups with options).
    """
    ids = list(property_ids or [])
    groups = get_groups_with_options(product)
    if not groups:
        for sku in ProductSKU.objects.filter(product=product).prefetch_related('property_links'):
            if sku.property_links.count() == 0:
                return sku
        return None

    if len(ids) != len(groups):
        return None

    want = set(ids)
    if len(want) != len(ids):
        return None

    for sku in ProductSKU.objects.filter(product=product).prefetch_related('property_links'):
        linked = {pl.product_property_id for pl in sku.property_links.all()}
        if linked == want:
            return sku
    return None


def property_ids_from_sku(sku: ProductSKU) -> List[int]:
    return list(
        sku.property_links.values_list('product_property_id', flat=True).order_by('product_property__title_id', 'pk')
    )


def get_configuration_label(sku: Optional[ProductSKU]) -> str:
    if sku is None:
        return ''
    parts = []
    for link in sku.property_links.select_related('product_property__title').order_by(
        'product_property__title_id',
        'pk',
    ):
        prop = link.product_property
        title_name = prop.title.title if prop.title_id else ''
        if title_name:
            parts.append(f'{title_name}: {prop.name}')
        else:
            parts.append(prop.name)
    return '; '.join(parts) if parts else ''


def property_in_stock_map(product: Product) -> dict:
    """
    For a single attribute group, map each ProductProperty.pk -> bool (SKU exists and in_stock).
    Empty dict if multiple groups (client must rely on submit-time validation).
    """
    groups = get_groups_with_options(product)
    if len(groups) != 1:
        return {}
    out = {}
    for prop in groups[0].properties.all():
        sku = (
            ProductSKU.objects.filter(product=product, property_links__product_property=prop)
            .distinct()
            .prefetch_related('property_links')
            .first()
        )
        if sku is None:
            out[prop.pk] = False
        elif sku.property_links.count() == 1:
            out[prop.pk] = sku.in_stock
        else:
            out[prop.pk] = sku.in_stock
    return out


@transaction.atomic
def seed_skus_for_single_group_products():
    """Bulk backfill helper: normalize SKUs for every product."""
    for product in Product.objects.all():
        sync_product_skus(product)
