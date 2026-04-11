import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from dashboard.views import owner_required
from menu.models import MenuItem, Topping
from tables.models import Table
from .models import Order, OrderItem, Receipt
import os
from django.shortcuts import render, redirect



def _get_cart(request):
    return request.session.get('cart', {})


def _save_cart(request, cart):
    request.session['cart'] = cart
    request.session.modified = True


def cart(request):
    cart_data  = _get_cart(request)
    cart_items = []
    total      = 0

    for key, data in cart_data.items():
        try:
            item       = MenuItem.objects.get(pk=data['item_id'])
            tops       = Topping.objects.filter(pk__in=data.get('toppings', []))
            tops_price = sum(float(t.price) for t in tops)
            subtotal   = (float(item.price) + tops_price) * data['quantity']
            total     += subtotal
            cart_items.append({
                'key':      key,
                'item':     item,
                'toppings': tops,
                'quantity': data['quantity'],
                'notes':    data.get('notes', ''),
                'subtotal': round(subtotal, 2),
            })
        except MenuItem.DoesNotExist:
            pass

    return render(request, 'orders/cart.html', {
        'cart_items':   cart_items,
        'total':        round(total, 2),
        'table_number': request.session.get('table_number'),
    })


@require_POST
def add_to_cart(request):
    try:
        data     = json.loads(request.body)
        item_id  = data.get('item_id')
        quantity = int(data.get('quantity', 1))
        toppings = data.get('toppings', [])
        notes    = data.get('notes', '')

        item         = MenuItem.objects.get(pk=item_id, is_available=True)
        weight_grams = int(data.get('weight_grams', 0)) if item.sold_by_weight else 0
        cart         = _get_cart(request)
        key          = f"{item_id}_{weight_grams}_{'_'.join(str(t) for t in sorted(toppings))}"

        if key in cart and not item.sold_by_weight:
            cart[key]['quantity'] += quantity
        else:
            cart[key] = {
                'item_id':     item_id,
                'quantity':    quantity,
                'toppings':    toppings,
                'notes':       notes,
                'weight_grams': weight_grams,
            }

        _save_cart(request, cart)
        cart_count = sum(v['quantity'] for v in cart.values())
        return JsonResponse({'success': True, 'cart_count': cart_count})

    except MenuItem.DoesNotExist:
        return JsonResponse({'error': 'Item not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_POST
def remove_from_cart(request):
    try:
        data = json.loads(request.body)
        key  = data.get('key')
        cart = _get_cart(request)
        cart.pop(key, None)
        _save_cart(request, cart)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def set_language(request):
    """Save language preference to session"""
    lang = request.POST.get('lang', 'ar')
    request.session['lang'] = lang
    request.session.modified = True
    from django.http import JsonResponse
    return JsonResponse({'lang': lang})


def checkout(request):
    cart_data = _get_cart(request)
    if not cart_data:
        return redirect('menu:home')

    cart_items = []
    total = 0
    for key, data in cart_data.items():
        try:
            item       = MenuItem.objects.get(pk=data['item_id'])
            tops       = Topping.objects.filter(pk__in=data.get('toppings', []))
            tops_price = sum(float(t.price) for t in tops)
            subtotal   = (float(item.price) + tops_price) * data['quantity']
            total     += subtotal
            cart_items.append({
                'key':      key,
                'item':     item,
                'toppings': tops,
                'quantity': data['quantity'],
                'subtotal': round(subtotal, 2),
            })
        except MenuItem.DoesNotExist:
            pass

    table_id     = request.session.get('table_id')
    table        = Table.objects.filter(pk=table_id).first() if table_id else None
    table_number = request.session.get('table_number')

    return render(request, 'orders/checkout.html', {
        'cart_items':   cart_items,
        'total':        round(total, 2),
        'table':        table,
        'table_number': table_number,
    })


@require_POST
def confirm_order(request):
    cart_data = _get_cart(request)

    if not cart_data:
        return redirect('menu:home')

    # Table is optional — None means cashier order
    table_id = request.session.get('table_id')
    table    = Table.objects.filter(pk=table_id).first() if table_id else None

    # Create order — table can be null (cashier order)
    order = Order.objects.create(
        table          = table,   # None = cashier/takeaway
        payment_method = request.POST.get('payment_method', 'cash'),
        customer_name  = request.POST.get('customer_name', ''),
        customer_phone = request.POST.get('customer_phone', ''),
        notes          = request.POST.get('notes', ''),
        status         = 'new',
    )

    # Create order items
    for key, data in cart_data.items():
        try:
            menu_item  = MenuItem.objects.get(pk=data['item_id'])
            order_item = OrderItem.objects.create(
                order        = order,
                menu_item    = menu_item,
                quantity     = data['quantity'],
                unit_price   = menu_item.price,
                notes        = data.get('notes', ''),
                weight_grams = data.get('weight_grams') or None,
            )
            if data.get('toppings'):
                tops = Topping.objects.filter(pk__in=data['toppings'])
                order_item.toppings.set(tops)
        except MenuItem.DoesNotExist:
            pass

    # Calculate total & create receipt
    order.calculate_total()
    Receipt.objects.create(order=order)

    # Clear cart
    request.session['cart'] = {}
    request.session.modified = True

    # Print to thermal printer (silent — won't crash if printer offline)
    try:
        from .printing import print_order
        print_order(order)
    except Exception:
        pass  # Printer offline is OK, order still saved

    return redirect('orders:status', pk=order.pk)


def order_status(request, pk):
    order = get_object_or_404(
        Order.objects.prefetch_related(
            'items__menu_item', 'items__toppings'
        ).select_related('table'),
        pk=pk
    )
    return render(request, 'orders/order_status.html', {'order': order})


def _get_printer_config():
    """Read printer config from .env file"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    config = {
        'type': 'none', 'host': '', 'port': '9100',
        'vendor_id': '', 'product_id': '', 'auto_print': 'yes',
    }
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, val = line.split('=', 1)
                    key, val = key.strip(), val.strip()
                    if key == 'PRINTER_TYPE':
                        config['type'] = val
                    elif key == 'PRINTER_HOST':
                        config['host'] = val
                    elif key == 'PRINTER_PORT':
                        config['port'] = val
                    elif key == 'PRINTER_VENDOR_ID':
                        config['vendor_id'] = val
                    elif key == 'PRINTER_PRODUCT_ID':
                        config['product_id'] = val
                    elif key == 'AUTO_PRINT':
                        config['auto_print'] = val
    return config


def _get_restaurant_config():
    """Read restaurant info from .env file"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    config = {'name_ar': '', 'name_he': '', 'city': '', 'phone': ''}
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, val = line.split('=', 1)
                    key, val = key.strip(), val.strip()
                    if key == 'REST_NAME_AR':
                        config['name_ar'] = val
                    elif key == 'REST_NAME_HE':
                        config['name_he'] = val
                    elif key == 'REST_CITY':
                        config['city'] = val
                    elif key == 'REST_PHONE':
                        config['phone'] = val
    return config


def _update_env(updates: dict):
    """Update specific keys in .env file"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    lines = []
    updated_keys = set()
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                stripped = line.strip()
                if '=' in stripped and not stripped.startswith('#'):
                    key = stripped.split('=', 1)[0].strip()
                    if key in updates:
                        lines.append(f"{key}={updates[key]}\n")
                        updated_keys.add(key)
                        continue
                lines.append(line)
    # Add any new keys not yet in file
    for key, val in updates.items():
        if key not in updated_keys:
            lines.append(f"{key}={val}\n")
    with open(env_path, 'w') as f:
        f.writelines(lines)


@owner_required
def settings_view(request):
    saved = False
    error = None

    if request.method == 'POST':
        section = request.POST.get('section')

        if section == 'printer':
            ptype = request.POST.get('printer_type', 'none')
            updates = {
                'PRINTER_TYPE': ptype,
                'AUTO_PRINT': request.POST.get('auto_print', 'yes'),
            }
            if ptype == 'network':
                host = request.POST.get('printer_host', '').strip()
                port = request.POST.get('printer_port', '9100').strip()
                if not host:
                    error = 'يرجى إدخال عنوان IP الطابعة'
                else:
                    updates['PRINTER_HOST'] = host
                    updates['PRINTER_PORT'] = port
            elif ptype == 'usb':
                vid = request.POST.get('printer_vendor_id', '').strip()
                pid = request.POST.get('printer_product_id', '').strip()
                if not vid or not pid:
                    error = 'يرجى إدخال Vendor ID و Product ID'
                else:
                    updates['PRINTER_VENDOR_ID'] = vid
                    updates['PRINTER_PRODUCT_ID'] = pid

            if not error:
                _update_env(updates)
                # Reload env vars in memory
                import dotenv
                dotenv.load_dotenv(override=True)
                saved = True

        elif section == 'restaurant':
            updates = {
                'REST_NAME_AR': request.POST.get('rest_name_ar', '').strip(),
                'REST_NAME_HE': request.POST.get('rest_name_he', '').strip(),
                'REST_CITY': request.POST.get('rest_city', '').strip(),
                'REST_PHONE': request.POST.get('rest_phone', '').strip(),
            }
            _update_env(updates)
            saved = True

    return render(request, 'dashboard/settings.html', {
        'printer': _get_printer_config(),
        'restaurant': _get_restaurant_config(),
        'saved': saved,
        'error': error,
    })
