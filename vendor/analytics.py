"""Block V: vendor sales aggregations (OrderItem lines, exclude cancelled orders)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Set, Tuple, Union

from django.contrib.auth.models import User
from django.db.models import Count, Sum
from django.utils import timezone

from shopping.models import OrderItem


def sales_orderitem_queryset(user: User):
    """
    Lines that count as sales. Cancelled orders excluded.
    Vendor: only own products. Staff/superuser: all lines.
    """
    qs = OrderItem.objects.exclude(order__status='cancelled').select_related(
        'order', 'product', 'product__created_by'
    )
    if user.is_staff or user.is_superuser:
        return qs
    return qs.filter(product__created_by=user)


BucketKey = Union[
    Tuple[int],
    Tuple[int, int],
    Tuple[int, int, int],
    Tuple[int, int, int, int],
]


@dataclass
class PeriodBounds:
    start: timezone.datetime
    end: timezone.datetime
    # hour | day | month | year — bucket in Python (no MySQL CONVERT_TZ).
    granularity: str


def _first_day_of_month_months_ago(now: timezone.datetime, months_ago: int) -> timezone.datetime:
    """Return 00:00 on the first day of the month `months_ago` months before now's month."""
    y, m = now.year, now.month
    for _ in range(months_ago):
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return now.replace(year=y, month=m, day=1, hour=0, minute=0, second=0, microsecond=0)


def _purchase_wall_time(dt) -> Optional[timezone.datetime]:
    if dt is None:
        return None
    if timezone.is_aware(dt):
        return timezone.localtime(dt)
    return dt


def _bucket_key(pdate, granularity: str) -> BucketKey:
    d = _purchase_wall_time(pdate)
    if d is None:
        raise ValueError('purchase_date required for bucketing')
    if granularity == 'hour':
        return (d.year, d.month, d.day, d.hour)
    if granularity == 'year':
        return (d.year,)
    if granularity == 'month':
        return (d.year, d.month)
    # day
    return (d.year, d.month, d.day)


def _bucket_label(key: BucketKey, granularity: str) -> str:
    if granularity == 'hour':
        y, m, day, h = key  # type: ignore[misc]
        return f'{y}-{m:02d}-{day:02d} {h:02d}:00'
    if granularity == 'year':
        return str(key[0])
    if granularity == 'month':
        y, m = key  # type: ignore[misc]
        return f'{y}-{m:02d}'
    y, m, day = key  # type: ignore[misc]
    return f'{y}-{m:02d}-{day:02d}'


def resolve_period(period: str) -> PeriodBounds:
    """
    Preset ranges in the active time zone.

    Chart bucket granularity (X-axis):
    - today: hourly
    - week: daily
    - month: last 12 calendar months (from first day of month 11 months ago) — one bar per month
    - year: last 5 calendar years (from Jan 1 four years before current year) — one bar per year
    """
    now = timezone.now()
    period = (period or 'month').lower()
    if period == 'today':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
        return PeriodBounds(start, end, 'hour')
    if period == 'week':
        start = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
        return PeriodBounds(start, end, 'day')
    if period == 'year':
        start = now.replace(
            year=now.year - 4, month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        end = now
        return PeriodBounds(start, end, 'year')
    # month: last 12 months (inclusive), monthly buckets
    start = _first_day_of_month_months_ago(now, 11)
    end = now
    return PeriodBounds(start, end, 'month')


def kpi_for_range(qs, start, end) -> Tuple[Decimal, int, Decimal]:
    """Total revenue, distinct order count, average revenue per order (vendor slice)."""
    filtered = qs.filter(order__purchase_date__gte=start, order__purchase_date__lte=end)
    agg = filtered.aggregate(
        revenue=Sum('subtotal'),
        orders=Count('order_id', distinct=True),
    )
    revenue = agg['revenue'] or Decimal('0')
    orders = agg['orders'] or 0
    avg = (revenue / orders) if orders else Decimal('0')
    return revenue, orders, avg


def timeseries_for_range(qs, bounds: PeriodBounds) -> List[dict]:
    filtered = qs.filter(
        order__purchase_date__gte=bounds.start,
        order__purchase_date__lte=bounds.end,
    )
    rows = filtered.values_list('order__purchase_date', 'order_id', 'subtotal')
    revenue_by: Dict[BucketKey, Decimal] = {}
    orders_by: Dict[BucketKey, Set[int]] = {}
    for pdate, order_id, subtotal in rows:
        if pdate is None or order_id is None:
            continue
        key = _bucket_key(pdate, bounds.granularity)
        sub = subtotal if subtotal is not None else Decimal('0')
        revenue_by[key] = revenue_by.get(key, Decimal('0')) + sub
        orders_by.setdefault(key, set()).add(order_id)
    out = []
    for key in sorted(revenue_by.keys()):
        out.append(
            {
                'label': _bucket_label(key, bounds.granularity),
                'revenue': float(revenue_by[key]),
                'orders': len(orders_by.get(key, ())),
            }
        )
    return out


def top_products(qs, start, end, limit: int = 10) -> List[dict]:
    filtered = qs.filter(
        order__purchase_date__gte=start,
        order__purchase_date__lte=end,
    )
    rows = (
        filtered.values('product_id', 'product__name', 'product__slug')
        .annotate(
            revenue=Sum('subtotal'),
            units=Sum('quantity'),
            line_count=Count('id'),
        )
        .order_by('-revenue')[:limit]
    )
    return [
        {
            'product_id': r['product_id'],
            'slug': r['product__slug'],
            'name': r['product__name'],
            'revenue': r['revenue'] or Decimal('0'),
            'units': r['units'] or 0,
            'lines': r['line_count'],
        }
        for r in rows
    ]
