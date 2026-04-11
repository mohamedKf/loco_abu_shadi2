from django.shortcuts import render, redirect, get_object_or_404
from .models import Table


def scan_qr(request, token):
    """
    Customer scans QR code → session starts → redirect to menu
    """
    table = get_object_or_404(Table, qr_token=token, is_active=True)

    # Start session for this table
    request.session['table_id']     = table.id
    request.session['table_number'] = table.number
    request.session['cart']         = {}   # fresh cart

    return redirect('menu:menu_list')
