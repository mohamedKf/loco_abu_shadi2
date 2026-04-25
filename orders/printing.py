"""
Thermal Printer Support — Epson TM-T20 (and compatible)
Supports USB and LAN connections via python-escpos.

Install: pip install python-escpos
"""

import os
import logging

logger = logging.getLogger(__name__)


def get_printer_config():
    """Read printer config from database (set via dashboard settings page)."""
    try:
        from dashboard.models import PrinterConfig
        config = PrinterConfig.objects.first()
        if config:
            return {
                'type':       config.printer_type,
                'host':       config.host,
                'port':       config.port,
                'vendor_id':  config.vendor_id,
                'product_id': config.product_id,
                'auto_print': config.auto_print,
            }
    except Exception:
        pass

    # Fallback to env vars (for local dev)
    return {
        'type':       os.getenv('PRINTER_TYPE', 'none'),
        'host':       os.getenv('PRINTER_HOST', ''),
        'port':       int(os.getenv('PRINTER_PORT', 9100)),
        'vendor_id':  os.getenv('PRINTER_USB_VENDOR', '0x04b8'),
        'product_id': os.getenv('PRINTER_USB_PRODUCT', '0x0202'),
        'auto_print': os.getenv('AUTO_PRINT', 'yes'),
    }


def get_printer():
    """Get printer instance based on saved config."""
    config = get_printer_config()

    if config['type'] == 'none' or not config['type']:
        return None

    try:
        from escpos.printer import Usb, Network
        if config['type'] == 'network':
            if not config['host']:
                logger.warning("Printer type is network but no host configured")
                return None
            return Network(config['host'], int(config['port']))
        elif config['type'] == 'usb':
            vendor  = int(config['vendor_id'], 16) if isinstance(config['vendor_id'], str) else config['vendor_id']
            product = int(config['product_id'], 16) if isinstance(config['product_id'], str) else config['product_id']
            return Usb(vendor, product)
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
    config = get_printer_config()
    if config.get('auto_print') == 'no':
        return False

    p = get_printer()
    if not p:
        logger.warning(f"Printer unavailable — order #{order.id} not printed")
        return False

    try:
        # ── Header ──
        p.set(align='center', bold=True, height=2, width=2)
        p.text("LOCO\n")
        p.set(align='center', bold=False, height=1, width=1)
        p.text("Abu Shadi - Nazareth\n")
        p.text("-" * 32 + "\n")

        # ── Order info ──
        p.set(align='center', bold=True)
        p.text(f"Order #{order.id}\n")
        p.set(align='center', bold=False)

        if order.table:
            p.text(f"Table: {order.table.number}\n")
        else:
            p.text("Cashier Order\n")

        dt = order.created_at
        p.text(f"{dt.strftime('%d/%m/%Y  %H:%M')}\n")
        p.text("-" * 32 + "\n")

        # ── Items ──
        p.set(align='right', bold=False)
        for item in order.items.all():
            name = item.menu_item.name_ar if item.menu_item else "-"
            qty  = item.quantity
            sub  = item.get_subtotal()

            line      = f"{name} x{qty}"
            price_str = f"NIS {sub}"
            spaces    = 32 - len(line) - len(price_str)
            p.text(f"{line}{' ' * max(1, spaces)}{price_str}\n")

            tops = item.toppings.all()
            if tops:
                p.text(f"  + {', '.join(t.name_ar for t in tops)}\n")

            if item.notes:
                p.text(f"  * {item.notes}\n")

        p.text("-" * 32 + "\n")

        # ── Total ──
        p.set(align='center', bold=True, height=2, width=2)
        p.text(f"NIS {order.total_price}\n")
        p.set(align='center', bold=False, height=1, width=1)

        payment_map = {
            'cash':         'Cash',
            'cashier_card': 'Card at Cashier',
            'online':       'Online Payment',
        }
        p.text(f"{payment_map.get(order.payment_method, order.payment_method)}\n")

        if order.customer_name:
            p.text(f"{order.customer_name}\n")
        if order.notes:
            p.text(f"Note: {order.notes}\n")

        p.text("-" * 32 + "\n")
        p.set(align='center', bold=True)
        p.text("Thank you! Beteavon!\n")
        p.set(align='center', bold=False)
        p.text("This is not a tax invoice\n")
        p.cut()

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
    """Test printer connection."""
    p = get_printer()
    if not p:
        return False
    try:
        p.set(align='center', bold=True)
        p.text("LOCO - Test Print\n")
        p.text("Printer OK!\n")
        p.cut()
        return True
    except Exception as e:
        logger.error(f"Test print failed: {e}")
        return False