import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import timedelta
from menu.models import Category, MenuItem, Topping, ToppingGroup
from orders.models import Order, OrderItem, Receipt
from tables.models import Table
from tables.qr_generator import generate_qr
from .reports import get_sales_summary, get_top_items, get_revenue_by_category
from .forms import MenuItemForm, CategoryForm, ToppingForm


def owner_required(view_func):
    """Only owners and superusers can access dashboard"""
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        if hasattr(request.user, 'profile') and request.user.profile.role == 'owner':
            return view_func(request, *args, **kwargs)
        # Kitchen/cashier workers go to kitchen page
        return redirect('kitchen')
    return wrapper


def staff_required(view_func):
    """Allow owners, cashiers and kitchen workers"""
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        if hasattr(request.user, 'profile'):
            return view_func(request, *args, **kwargs)
        return redirect('accounts:login')
    return wrapper


@owner_required
def overview(request):
    today   = timezone.now().date()
    # Allow switching between today / this week / all time
    period  = request.GET.get('period', 'today')
    if period == 'week':
        start = today - timedelta(days=6)
    elif period == 'month':
        start = today.replace(day=1)
    elif period == 'all':
        start = today - timedelta(days=3650)
    else:
        start = today

    summary = get_sales_summary(start, today)
    top     = get_top_items(limit=5, days=30)
    recent  = Order.objects.select_related('table').order_by('-created_at')[:10]
    return render(request, 'dashboard/overview.html', {
        'summary':    summary,
        'top_items':  top,
        'recent_orders': recent,
        'period':     period,
        'today':      today,
    })



@owner_required
def order_receipt_pdf(request, pk):
    """Generate and return PDF receipt for an order"""
    from django.http import FileResponse
    from orders.pdf_receipt import generate_order_pdf

    order = get_object_or_404(
        Order.objects.prefetch_related(
            'items__menu_item', 'items__toppings'
        ).select_related('table'),
        pk=pk
    )

    buffer = generate_order_pdf(order)
    filename = f"receipt_{order.id}.pdf"

    return FileResponse(
        buffer,
        as_attachment=False,  # open in browser, not download
        filename=filename,
        content_type='application/pdf'
    )

@staff_required
def orders_list(request):
    from datetime import date as date_type
    qs = Order.objects.select_related('table').prefetch_related('items').order_by('-created_at')

    # Period quick filter
    period = request.GET.get('period', 'all')
    today  = timezone.now().date()

    if period == 'today':
        qs = qs.filter(created_at__date=today)
    elif period == 'week':
        qs = qs.filter(created_at__date__gte=today - timedelta(days=6))
    elif period == 'month':
        qs = qs.filter(created_at__date__gte=today.replace(day=1))
    elif period == 'year':
        qs = qs.filter(created_at__date__gte=today.replace(month=1, day=1))

    # Custom date range
    date_from = request.GET.get('date_from', '')
    date_to   = request.GET.get('date_to', '')
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    # Summary stats for filtered results
    from django.db.models import Sum
    agg = qs.aggregate(total=Sum('total_price'))
    total_revenue = agg['total'] or 0

    return render(request, 'dashboard/orders.html', {
        'orders':        qs,
        'status_filter': status_filter,
        'period':        period,
        'date_from':     date_from,
        'date_to':       date_to,
        'total_count':   qs.count(),
        'total_revenue': total_revenue,
        'paid_count':    qs.filter(payment_status='paid').count(),
        'pending_count': qs.filter(payment_status='pending').count(),
    })


@staff_required
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__menu_item', 'items__toppings').select_related('table'), pk=pk
    )
    if request.method == 'POST':
        new_status = request.POST.get('status')
        new_payment = request.POST.get('payment_status')
        if new_status: order.status = new_status
        if new_payment: order.payment_status = new_payment
        order.save()
        return redirect('dashboard:order_detail', pk=pk)
    return render(request, 'dashboard/order_detail.html', {'order': order})


@owner_required
def menu_management(request):
    categories = Category.objects.prefetch_related('items').all()
    return render(request, 'dashboard/menu.html', {'categories': categories})


@owner_required
def item_add(request):
    form = MenuItemForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        return redirect('dashboard:menu')
    return render(request, 'dashboard/item_form.html', {'form': form, 'action': 'إضافة'})


@owner_required
def item_edit(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    form = MenuItemForm(request.POST or None, request.FILES or None, instance=item)
    if form.is_valid():
        form.save()
        return redirect('dashboard:menu')
    return render(request, 'dashboard/item_form.html', {'form': form, 'action': 'تعديل', 'item': item})


@owner_required
def item_delete(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    if request.method == 'POST':
        item.delete()
        return redirect('dashboard:menu')
    return render(request, 'dashboard/confirm_delete.html', {'obj': item, 'type': 'الصنف'})


@owner_required
def item_toggle(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    item.is_available = not item.is_available
    item.save(update_fields=['is_available'])
    return JsonResponse({'is_available': item.is_available})


# ── Categories ────────────────────────────────────────────
@owner_required
def category_list(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard:categories')
    else:
        form = CategoryForm()
    categories = Category.objects.all()
    return render(request, 'dashboard/categories.html', {'categories': categories, 'form': form})


@owner_required
def category_edit(request, pk):
    cat  = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, instance=cat)
    if form.is_valid():
        form.save()
        return redirect('dashboard:categories')
    return render(request, 'dashboard/category_form.html', {'form': form, 'cat': cat})


@owner_required
def category_delete(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        cat.delete()
        return redirect('dashboard:categories')
    return render(request, 'dashboard/confirm_delete.html', {'obj': cat, 'type': 'الفئة'})


# ── Toppings ──────────────────────────────────────────────
@owner_required
def topping_list(request):
    if request.method == 'POST':
        # Manual save to handle group field
        name_ar = request.POST.get('name_ar', '')
        name_he = request.POST.get('name_he', '')
        name    = request.POST.get('name', '')
        price   = request.POST.get('price', 0)
        group_id = request.POST.get('group')
        is_available = 'is_available' in request.POST

        if name_ar:
            topping = Topping(
                name_ar=name_ar, name_he=name_he, name=name,
                price=price, is_available=is_available
            )
            if group_id:
                topping.group_id = int(group_id)
            topping.save()
        return redirect('dashboard:toppings')

    groups   = ToppingGroup.objects.prefetch_related('toppings').all()
    toppings = Topping.objects.select_related('group').all()
    return render(request, 'dashboard/toppings.html', {
        'groups':   groups,
        'toppings': toppings,
    })


@owner_required
def topping_edit(request, pk):
    topping = get_object_or_404(Topping, pk=pk)
    form    = ToppingForm(request.POST or None, instance=topping)
    if form.is_valid():
        form.save()
        return redirect('dashboard:toppings')
    return render(request, 'dashboard/topping_form.html', {'form': form, 'topping': topping})


@owner_required
def topping_delete(request, pk):
    topping = get_object_or_404(Topping, pk=pk)
    if request.method == 'POST':
        topping.delete()
        return redirect('dashboard:toppings')
    return render(request, 'dashboard/confirm_delete.html', {'obj': topping, 'type': 'الإضافة'})


@owner_required
def topping_toggle(request, pk):
    topping = get_object_or_404(Topping, pk=pk)
    topping.is_available = not topping.is_available
    topping.save(update_fields=['is_available'])
    return JsonResponse({'is_available': topping.is_available})


# ── Tables ────────────────────────────────────────────────
@owner_required
def tables_management(request):
    tables = Table.objects.all()
    return render(request, 'dashboard/tables.html', {'tables': tables})


@owner_required
def table_add(request):
    if request.method == 'POST':
        number = request.POST.get('number')
        if number:
            Table.objects.get_or_create(number=int(number))
        return redirect('dashboard:tables')
    return render(request, 'dashboard/table_add.html')


@owner_required
def table_qr(request, pk):
    table = get_object_or_404(Table, pk=pk)
    base_url = request.build_absolute_uri('/').rstrip('/')
    qr_img = generate_qr(table, base_url)
    qr_url = f"{base_url}/table/{table.qr_token}/"
    return render(request, 'dashboard/table_qr.html', {
        'table': table,
        'qr_img': qr_img,
        'qr_url': qr_url,
    })


@owner_required
def table_delete(request, pk):
    table = get_object_or_404(Table, pk=pk)
    if request.method == 'POST':
        table.delete()
        return redirect('dashboard:tables')
    return render(request, 'dashboard/confirm_delete.html', {'obj': table, 'type': 'الطاولة'})


# ── Reports ───────────────────────────────────────────────
@owner_required
def reports(request):
    days    = int(request.GET.get('days', 7))
    end     = timezone.now().date()
    start   = end - timedelta(days=days - 1)
    summary = get_sales_summary(start, end)
    top     = get_top_items(limit=10, days=days)
    by_cat  = get_revenue_by_category(start, end)
    return render(request, 'dashboard/reports.html', {
        'summary': summary, 'top_items': top, 'by_category': by_cat, 'days': days,
    })


@owner_required
def export_csv(request):
    days   = int(request.GET.get('days', 7))
    end    = timezone.now().date()
    start  = end - timedelta(days=days - 1)
    orders = Order.objects.filter(
        created_at__date__gte=start, created_at__date__lte=end
    ).select_related('table')
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="loco_orders_{start}_{end}.csv"'
    w = csv.writer(response)
    w.writerow(['#', 'طاولة', 'الحالة', 'الدفع', 'المبلغ', 'التاريخ', 'العميل', 'الجوال'])
    for o in orders:
        w.writerow([o.id, o.table.number if o.table else '-', o.get_status_display(),
                    o.get_payment_method_display(), o.total_price,
                    o.created_at.strftime('%Y-%m-%d %H:%M'), o.customer_name, o.customer_phone])
    return response


@owner_required
def printer_test(request):
    from orders.printing import test_printer
    success = test_printer()
    msg = "✅ الطابعة تعمل بشكل صحيح!" if success else "❌ تعذر الاتصال بالطابعة — تحقق من الإعدادات"

    from dashboard.models import PrinterConfig, RestaurantConfig
    printer = PrinterConfig.get()
    restaurant = RestaurantConfig.get()

    printer_ctx = {
        'type': printer.printer_type,
        'host': printer.host,
        'port': printer.port,
        'vendor_id': printer.vendor_id,
        'product_id': printer.product_id,
        'auto_print': 'yes' if printer.auto_print else 'no',
    }
    restaurant_ctx = {
        'name_ar': restaurant.name_ar,
        'name_he': restaurant.name_he,
        'city': restaurant.city,
        'phone': restaurant.phone,
    }

    return render(request, 'dashboard/settings.html', {
        'printer': printer_ctx,
        'restaurant': restaurant_ctx,
        'printer_msg': msg,
    })


@owner_required
def site_settings(request):
    from dashboard.models import PrinterConfig, RestaurantConfig

    printer = PrinterConfig.get()
    restaurant = RestaurantConfig.get()
    saved = False
    error = None

    if request.method == 'POST':
        section = request.POST.get('section')

        if section == 'printer':
            ptype = request.POST.get('printer_type', 'none')
            printer.printer_type = ptype
            printer.auto_print = request.POST.get('auto_print') == 'yes'

            if ptype == 'network':
                host = request.POST.get('printer_host', '').strip()
                port = request.POST.get('printer_port', '9100').strip()
                if not host:
                    error = 'يرجى إدخال عنوان IP الطابعة'
                else:
                    printer.host = host
                    printer.port = int(port)
            elif ptype == 'usb':
                vid = request.POST.get('printer_vendor_id', '').strip()
                pid = request.POST.get('printer_product_id', '').strip()
                if not vid or not pid:
                    error = 'يرجى إدخال Vendor ID و Product ID'
                else:
                    printer.vendor_id = vid
                    printer.product_id = pid

            if not error:
                printer.save()
                saved = True

        elif section == 'restaurant':
            restaurant.name_ar = request.POST.get('rest_name_ar', '').strip()
            restaurant.name_he = request.POST.get('rest_name_he', '').strip()
            restaurant.city = request.POST.get('rest_city', '').strip()
            restaurant.phone = request.POST.get('rest_phone', '').strip()
            restaurant.save()
            saved = True

    # Build context dicts for template
    printer_ctx = {
        'type': printer.printer_type,
        'host': printer.host,
        'port': printer.port,
        'vendor_id': printer.vendor_id,
        'product_id': printer.product_id,
        'auto_print': 'yes' if printer.auto_print else 'no',
    }
    restaurant_ctx = {
        'name_ar': restaurant.name_ar,
        'name_he': restaurant.name_he,
        'city': restaurant.city,
        'phone': restaurant.phone,
    }

    return render(request, 'dashboard/settings.html', {
        'printer': printer_ctx,
        'restaurant': restaurant_ctx,
        'saved': saved,
        'error': error,
    })
