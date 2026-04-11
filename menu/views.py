from django.shortcuts import render, get_object_or_404
from django.db.models import Prefetch
from .models import Category, MenuItem, ToppingGroup, Topping


def _get_topping_groups():
    available_toppings = Topping.objects.filter(is_available=True)
    return ToppingGroup.objects.prefetch_related(
        Prefetch('toppings', queryset=available_toppings)
    ).all()


def home(request):
    from tables.models import Table
    categories     = Category.objects.filter(is_active=True).prefetch_related('items__toppings')
    topping_groups = _get_topping_groups()
    cart_count     = sum(v['quantity'] for v in request.session.get('cart', {}).values())

    return render(request, 'menu/home.html', {
        'categories':     categories,
        'topping_groups': topping_groups,
        'cart_count':     cart_count,
        'table_number':   request.session.get('table_number'),
        'tables':         Table.objects.filter(is_active=True),
    })


def item_detail(request, pk):
    item           = get_object_or_404(MenuItem, pk=pk, is_available=True)
    topping_groups = _get_topping_groups()
    cart_count     = sum(v['quantity'] for v in request.session.get('cart', {}).values())

    return render(request, 'menu/item_detail.html', {
        'item':           item,
        'topping_groups': topping_groups,
        'cart_count':     cart_count,
        'table_number':   request.session.get('table_number'),
    })