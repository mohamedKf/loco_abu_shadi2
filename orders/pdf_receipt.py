"""
PDF Receipt — 80mm thermal printer
Uses only standard fonts (no Arabic font needed on server)
RTL text handled via python-bidi + arabic-reshaper
"""
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from io import BytesIO

W = 80 * mm  # 80mm thermal paper width


def _rtl(text):
    """Convert Arabic/Hebrew text for correct display."""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(str(text)))
    except Exception:
        try:
            from bidi.algorithm import get_display
            return get_display(str(text))
        except Exception:
            return str(text)


def _cfg(lang):
    if lang == 'he':
        return {
            'rtl':     True,
            'sub':     _rtl('אבו שאדי — נצרת'),
            'table':   _rtl('שולחן'),
            'cashier': _rtl('הזמנת קופה'),
            'total':   _rtl('סה"כ'),
            'pay': {
                'cash':         _rtl('מזומן'),
                'cashier_card': _rtl('כרטיס בקופה'),
                'online':       _rtl('תשלום אונליין'),
            },
            'thanks':  _rtl('תודה על ביקורכם!'),
            'note':    _rtl('קבלה פנימית — לא חשבונית מס'),
        }
    elif lang == 'en':
        return {
            'rtl':     False,
            'sub':     'Abu Shadi — Nazareth',
            'table':   'Table',
            'cashier': 'Cashier Order',
            'total':   'TOTAL',
            'pay': {
                'cash':         'Cash',
                'cashier_card': 'Card at Cashier',
                'online':       'Online Payment',
            },
            'thanks':  'Thank you for visiting!',
            'note':    'Internal receipt — not a tax invoice',
        }
    else:  # ar
        return {
            'rtl':     True,
            'sub':     _rtl('أبو شادي — الناصرة'),
            'table':   _rtl('طاولة'),
            'cashier': _rtl('طلب كاشير'),
            'total':   _rtl('المجموع'),
            'pay': {
                'cash':         _rtl('كاش'),
                'cashier_card': _rtl('بطاقة كاشير'),
                'online':       _rtl('دفع اونلاين'),
            },
            'thanks':  _rtl('شكراً لزيارتكم!'),
            'note':    _rtl('وصل داخلي — ليس فاتورة ضريبية'),
        }


def _safe_name(item, lang):
    """Get item name safely even if item is None."""
    if not item:
        return '-'
    try:
        if lang == 'he':
            return item.name_he or item.name_ar or item.name or '-'
        elif lang == 'en':
            return item.name or item.name_ar or '-'
        return item.name_ar or item.name or '-'
    except Exception:
        return '-'


def _safe_top_name(t, lang):
    try:
        if lang == 'he':
            return t.name_he or t.name_ar or t.name or ''
        elif lang == 'en':
            return t.name or t.name_ar or ''
        return t.name_ar or t.name or ''
    except Exception:
        return ''


def generate_order_pdf(order, lang=None):
    if lang is None:
        lang = getattr(order, 'language', 'ar') or 'ar'

    cfg = _cfg(lang)
    rtl = cfg['rtl']

    # Collect all items first to calculate height
    items_data = []
    try:
        for oi in order.items.prefetch_related('toppings').all():
            try:
                name = _safe_name(oi.menu_item, lang)
                if rtl:
                    name = _rtl(name)
                qty = f'{oi.weight_grams}g' if oi.weight_grams else f'x{oi.quantity}'
                price = f'NIS {oi.get_subtotal()}'
                tops = []
                for t in oi.toppings.all():
                    tname = _safe_top_name(t, lang)
                    if tname:
                        if rtl:
                            tname = _rtl(tname)
                        tprice = float(t.price) if t.price else 0
                        tops.append((tname, f'+NIS {t.price}' if tprice > 0 else ''))
                notes = oi.notes or ''
                items_data.append({
                    'name': name, 'qty': qty, 'price': price,
                    'tops': tops, 'notes': notes,
                })
            except Exception:
                pass
    except Exception:
        pass

    # Calculate dynamic height
    lines = 20  # header + footer
    for item in items_data:
        lines += 2 + len(item['tops']) + (1 if item['notes'] else 0)
    H = max(120, lines * 5) * mm

    buf = BytesIO()
    c   = canvas.Canvas(buf, pagesize=(W, H))

    PAD   = 4 * mm
    BLACK = colors.black
    WHITE = colors.white
    GRAY  = colors.HexColor('#555555')
    LGRAY = colors.HexColor('#888888')

    BOLD = 'Helvetica-Bold'
    REG  = 'Helvetica'

    y = H - 4 * mm

    def sp(n=2):
        nonlocal y
        y -= n * mm

    def hline(col=GRAY, lw=0.3):
        nonlocal y
        c.setStrokeColor(col)
        c.setLineWidth(lw)
        c.line(PAD, y, W - PAD, y)
        y -= 3 * mm

    def cen(txt, size, bold=False, col=BLACK):
        nonlocal y
        c.setFont(BOLD if bold else REG, size)
        c.setFillColor(col)
        c.drawCentredString(W / 2, y, str(txt))
        y -= size * 0.42 + 1.5 * mm

    def left_right(ltxt, rtxt, size, bold_l=False, bold_r=True, col=BLACK):
        nonlocal y
        c.setFont(BOLD if bold_l else REG, size)
        c.setFillColor(col)
        c.drawString(PAD, y, str(ltxt))
        c.setFont(BOLD if bold_r else REG, size)
        c.drawRightString(W - PAD, y, str(rtxt))
        y -= size * 0.42 + 1.5 * mm

    # ══ HEADER ══
    c.setFillColor(BLACK)
    c.rect(0, H - 20*mm, W, 20*mm, fill=1, stroke=0)
    c.setFont(BOLD, 18)
    c.setFillColor(WHITE)
    c.drawCentredString(W/2, H - 10*mm, 'LOCO')
    c.setFont(REG, 7)
    c.drawCentredString(W/2, H - 16*mm, cfg['sub'])

    y = H - 24*mm
    sp(1)

    # Order # + location
    c.setFont(BOLD, 13)
    c.setFillColor(BLACK)
    c.drawCentredString(W/2, y, f'#{str(order.id).zfill(4)}')
    y -= 7*mm

    if order.table:
        loc = cfg['table'] + ' ' + str(order.table.number)
    else:
        loc = cfg['cashier']
    cen(loc, 8, col=GRAY)

    dt = order.created_at
    cen(dt.strftime('%d/%m/%Y   %H:%M'), 8, col=GRAY)

    sp(1)
    hline(BLACK, 0.8)

    # ══ ITEMS ══
    for item in items_data:
        name  = item['name']
        qty   = item['qty']
        price = item['price']

        if rtl:
            # RTL: name on right, price on left
            c.setFont(BOLD, 9)
            c.setFillColor(BLACK)
            c.drawRightString(W - PAD, y, name)
            c.setFont(BOLD, 9)
            c.drawString(PAD, y, price)
            c.setFont(REG, 8)
            c.setFillColor(LGRAY)
            c.drawString(PAD + c.stringWidth(price, BOLD, 9) + 2*mm, y, qty)
        else:
            c.setFont(BOLD, 9)
            c.setFillColor(BLACK)
            c.drawString(PAD, y, f'{qty}  {name}')
            c.setFont(BOLD, 9)
            c.drawRightString(W - PAD, y, price)

        y -= 5*mm

        # Toppings
        for (tname, tprice) in item['tops']:
            c.setFont(REG, 7.5)
            c.setFillColor(LGRAY)
            if rtl:
                c.drawRightString(W - PAD - 3*mm, y, f'+ {tname}')
                if tprice:
                    c.drawString(PAD, y, tprice)
            else:
                c.drawString(PAD + 3*mm, y, f'+ {tname}')
                if tprice:
                    c.drawRightString(W - PAD, y, tprice)
            y -= 4*mm

        # Notes
        if item['notes']:
            c.setFont(REG, 7)
            c.setFillColor(LGRAY)
            note = f'* {item["notes"]}'
            if rtl:
                c.drawRightString(W - PAD - 3*mm, y, _rtl(note))
            else:
                c.drawString(PAD + 3*mm, y, note)
            y -= 4*mm

        # Item divider
        c.setStrokeColor(colors.HexColor('#cccccc'))
        c.setLineWidth(0.2)
        c.line(PAD + 4*mm, y + 1*mm, W - PAD - 4*mm, y + 1*mm)
        y -= 3*mm

    sp(1)
    hline(BLACK, 0.8)
    sp(1)

    # ══ TOTAL ══
    box_h = 10*mm
    c.setFillColor(BLACK)
    c.rect(PAD, y - box_h + 3*mm, W - 2*PAD, box_h, fill=1, stroke=0)

    total_lbl = cfg['total']
    total_val = f'NIS {order.total_price}'

    c.setFont(BOLD, 10)
    c.setFillColor(WHITE)
    if rtl:
        c.drawRightString(W - PAD - 2*mm, y - 4*mm, total_lbl)
        c.setFont(BOLD, 12)
        c.drawString(PAD + 2*mm, y - 4*mm, total_val)
    else:
        c.drawString(PAD + 2*mm, y - 4*mm, total_lbl)
        c.setFont(BOLD, 12)
        c.drawRightString(W - PAD - 2*mm, y - 4*mm, total_val)

    y -= box_h + 4*mm

    # ══ PAYMENT ══
    pm  = order.payment_method or 'cash'
    pay = cfg['pay'].get(pm, pm)
    cen(pay, 8, col=GRAY)

    if order.customer_name:
        cen(order.customer_name, 8, col=GRAY)
    if order.customer_phone:
        cen(order.customer_phone, 8, col=GRAY)
    if order.notes:
        sp(1)
        note_rtl = _rtl(order.notes) if rtl else order.notes
        cen(f'* {note_rtl}', 7, col=LGRAY)

    sp(2)
    hline(LGRAY, 0.3)
    sp(1)

    # ══ FOOTER ══
    cen(cfg['thanks'], 9, bold=True)
    sp(1)
    cen(cfg['note'], 6, col=LGRAY)
    sp(2)

    c.save()
    buf.seek(0)
    return buf