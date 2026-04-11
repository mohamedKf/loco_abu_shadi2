"""
Thermal Printer Support — Epson TM-T20 (and compatible)
========================================================
Supports USB and LAN connections.
Uses python-escpos library.

Install: pip install python-escpos

Usage:
    from orders.printing import print_order
    print_order(order)
"""

import os
import logging

logger = logging.getLogger(__name__)

# ── Printer config — change these to match your setup ──
PRINTER_TYPE = os.getenv('PRINTER_TYPE', 'usb')   # 'usb' or 'network'
PRINTER_HOST = os.getenv('PRINTER_HOST', '192.168.1.200')  # LAN IP
PRINTER_PORT = int(os.getenv('PRINTER_PORT', 9100))
PRINTER_USB_VENDOR  = int(os.getenv('PRINTER_USB_VENDOR', '0x04b8'), 16)   # Epson
PRINTER_USB_PRODUCT = int(os.getenv('PRINTER_USB_PRODUCT', '0x0202'), 16)  # TM-T20


def get_printer():
    """Get printer instance based on config"""
    try:
        from escpos.printer import Usb, Network
        if PRINTER_TYPE == 'network':
            return Network(PRINTER_HOST, PRINTER_PORT)
        else:
            return Usb(PRINTER_USB_VENDOR, PRINTER_USB_PRODUCT)
    except ImportError:
        logger.warning("python-escpos not installed. Run: pip install python-escpos")
        return None
    except Exception as e:
        logger.error(f"Printer connection failed: {e}")
        return None


def print_order(order):
    """
    Print order receipt to thermal printer.
    Called automatically when order is confirmed.
    """
    p = get_printer()
    if not p:
        logger.warning(f"Printer unavailable — order #{order.id} not printed")
        return False

    try:
        # Header
        p.set(align='center', bold=True, height=2, width=2)
        p.text("LOCO\n")
        p.set(align='center', bold=False, height=1, width=1)
        p.text("Abu Shadi - Nazareth\n")
        p.text("-" * 32 + "\n")

        # Order info
        p.set(align='center', bold=True)
        p.text(f"Order #{order.id}\n")
        p.set(align='center', bold=False)

        if order.table:
            p.text(f"Table: {order.table.number}\n")
        else:
            p.text("Cashier Order\n")

        from django.utils import timezone
        dt = order.created_at
        p.text(f"{dt.strftime('%d/%m/%Y  %H:%M')}\n")
        p.text("-" * 32 + "\n")

        # Items
        p.set(align='right', bold=False)
        for item in order.items.all():
            name = item.menu_item.name_ar if item.menu_item else "-"
            qty  = item.quantity
            sub  = item.get_subtotal()

            # Item line
            line = f"{name} x{qty}"
            price_str = f"NIS {sub}"
            spaces = 32 - len(line) - len(price_str)
            p.text(f"{line}{' ' * max(1, spaces)}{price_str}\n")

            # Toppings
            tops = item.toppings.all()
            if tops:
                tops_str = "+ " + ", ".join(t.name_ar for t in tops)
                p.set(align='right', bold=False)
                p.text(f"  {tops_str}\n")

            # Notes
            if item.notes:
                p.text(f"  * {item.notes}\n")

        p.text("-" * 32 + "\n")

        # Total
        p.set(align='center', bold=True, height=2, width=2)
        p.text(f"NIS {order.total_price}\n")
        p.set(align='center', bold=False, height=1, width=1)

        # Payment
        payment_map = {
            'cash':         'Cash',
            'cashier_card': 'Card at Cashier',
            'online':       'Online Payment',
        }
        p.text(f"{payment_map.get(order.payment_method, order.payment_method)}\n")

        # Customer
        if order.customer_name:
            p.text(f"{order.customer_name}\n")
        if order.notes:
            p.text(f"Note: {order.notes}\n")

        p.text("-" * 32 + "\n")
        p.set(align='center', bold=True)
        p.text("Thank you! Beteavon!\n")
        p.set(align='center', bold=False)
        p.text("This is not a tax invoice\n")

        # Cut paper
        p.cut()

        # Mark receipt as printed
        try:
            order.receipt.printed = True
            order.receipt.save(update_fields=['printed'])
        except Exception:
            pass

        logger.info(f"✅ Order #{order.id} printed successfully")
        return True

    except Exception as e:
        logger.error(f"Print failed for order #{order.id}: {e}")
        return False


def test_printer():
    """Test printer connection — call from Django shell"""
    p = get_printer()
    if not p:
        print("❌ Printer not found")
        return False
    try:
        p.set(align='center', bold=True)
        p.text("LOCO - Test Print\n")
        p.text("Printer OK!\n")
        p.cut()
        print("✅ Test print sent!")
        return True
    except Exception as e:
        print(f"❌ Print failed: {e}")
        return False