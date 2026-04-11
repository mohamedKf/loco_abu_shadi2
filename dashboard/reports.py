from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import timedelta
from orders.models import Order, OrderItem


def get_sales_summary(start_date, end_date):
    # Use __date lookup which Django converts using TIME_ZONE setting
    orders = Order.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
    ).exclude(status='cancelled')

    total_revenue = orders.aggregate(t=Sum('total_price'))['t'] or 0
    total_orders  = orders.count()
    avg_order     = round(float(total_revenue) / total_orders, 2) if total_orders else 0

    return {
        'total_revenue':  total_revenue,
        'total_orders':   total_orders,
        'avg_order':      avg_order,
        'paid_orders':    orders.filter(payment_status='paid').count(),
        'pending_orders': orders.filter(payment_status='pending').count(),
        'by_status': {
            'new':         orders.filter(status='new').count(),
            'in_progress': orders.filter(status='in_progress').count(),
            'ready':       orders.filter(status='ready').count(),
            'done':        orders.filter(status='done').count(),
        },
        'start_date': start_date,
        'end_date':   end_date,
    }


def get_top_items(limit=10, days=7):
    since = timezone.now().date() - timedelta(days=days)
    return (
        OrderItem.objects
        .filter(order__created_at__date__gte=since)
        .exclude(order__status='cancelled')
        .values('menu_item__id', 'menu_item__name_ar')
        .annotate(
            total_qty     = Sum('quantity'),
            total_revenue = Sum(F('quantity') * F('unit_price')),
        )
        .order_by('-total_qty')[:limit]
    )


def get_revenue_by_category(start_date, end_date):
    return (
        OrderItem.objects
        .filter(
            order__created_at__date__gte=start_date,
            order__created_at__date__lte=end_date,
        )
        .exclude(order__status='cancelled')
        .values('menu_item__category__name_ar')
        .annotate(
            total_revenue = Sum(F('quantity') * F('unit_price')),
            total_qty     = Sum('quantity'),
        )
        .order_by('-total_revenue')
    )