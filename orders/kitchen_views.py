from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Order



def kitchen_required(view_func):
    """Allow kitchen workers, cashiers and owners"""
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        if hasattr(request.user, 'profile'):
            return view_func(request, *args, **kwargs)
        from django.shortcuts import redirect
        return redirect('accounts:login')
    return wrapper


@kitchen_required
def kitchen_display(request):
    """
    Kitchen screen — shows orders that are not yet done.
    Order stays visible until BOTH ready AND paid.
    """
    # Show: new, in_progress, and ready-but-not-paid
    orders = Order.objects.filter(
        status__in=['new', 'in_progress', 'ready']
    ).prefetch_related(
        'items__menu_item', 'items__toppings'
    ).select_related('table').order_by('created_at')

    return render(request, 'kitchen/display.html', {'orders': orders})


@kitchen_required
@require_POST
def update_status(request, pk):
    """Worker updates order status — marks done only if also paid"""
    order      = get_object_or_404(Order, pk=pk)
    new_status = request.POST.get('status')
    new_payment = request.POST.get('payment_status')

    valid_status = ['new', 'in_progress', 'ready', 'done', 'cancelled']
    if new_status and new_status not in valid_status:
        return JsonResponse({'error': 'Invalid status'}, status=400)

    if new_status:
        order.status = new_status
    if new_payment:
        order.payment_status = new_payment

    # Auto-mark done if both ready and paid
    if order.status == 'ready' and order.payment_status == 'paid':
        order.status = 'done'

    order.save()
    return JsonResponse({
        'success': True,
        'status': order.status,
        'payment_status': order.payment_status,
    })


@kitchen_required
def worker_orders(request):
    """Simple orders list for kitchen/cashier workers"""
    from orders.models import Order
    from django.shortcuts import render
    qs = Order.objects.select_related('table').order_by('-created_at')[:50]
    return render(request, 'kitchen/worker_orders.html', {'orders': qs})


@login_required
def orders_json(request):
    """
    Returns current active order IDs as JSON.
    Used by kitchen display to detect new orders for auto-print.
    """
    active_statuses = ['new', 'in_progress', 'ready']
    order_ids = list(
        Order.objects.filter(status__in=active_statuses)
        .values_list('id', flat=True)
        .order_by('-created_at')
    )
    return JsonResponse({'order_ids': order_ids})