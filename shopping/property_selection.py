"""Parse/validate ProductProperty selections from POST (one per attribute group)."""
from typing import List, Optional

from .models import ProductProperty, ProductPropertyTitle


def groups_with_selectable_properties(product):
    out = []
    for t in ProductPropertyTitle.objects.filter(product=product).prefetch_related('properties').order_by('pk'):
        if t.properties.exists():
            out.append(t)
    return out


def parse_property_selection_from_post(product, post) -> Optional[List[int]]:
    """
    Returns ordered list of ProductProperty PKs, or None if invalid/missing.
    Empty list if the product has no groups with options.
    """
    groups = groups_with_selectable_properties(product)
    if not groups:
        return []
    ids = []
    for g in groups:
        raw = post.get(f'prop_{g.pk}')
        if not raw:
            return None
        try:
            pid = int(raw)
        except (ValueError, TypeError):
            return None
        if not ProductProperty.objects.filter(pk=pid, title_id=g.pk).exists():
            return None
        ids.append(pid)
    return ids


def format_property_summary(property_ids: list) -> str:
    if not property_ids:
        return ''
    parts = []
    for pid in property_ids:
        try:
            p = ProductProperty.objects.select_related('title').get(pk=pid)
        except ProductProperty.DoesNotExist:
            continue
        parts.append(f'{p.title.title}: {p.name}')
    return '; '.join(parts)
