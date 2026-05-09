"""
PDF Receipt — 80mm thermal printer
Embeds Arial font from project static/fonts/ folder
Falls back to system fonts or Helvetica
"""
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import os

W = 80 * mm  # 80mm thermal paper width

# ── Font setup ────────────────────────────────────────────
_fonts_ready = False

def _setup_fonts():
    global _fonts_ready
    if _fonts_ready:
        return

    # Base directory of the Django project
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    font_searches = {
        'Receipt-Regular': [
            # Project bundled fonts (works everywhere)
            os.path.join(base, 'static', 'fonts', 'arial.ttf'),
            os.path.join(base, 'staticfiles', 'fonts', 'arial.ttf'),
            # Linux (Railway)
            '/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf',
            '/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            # Windows
            'C:/Windows/Fonts/arial.ttf',
            'C:/Windows/Fonts/tahoma.ttf',
        ],
        'Receipt-Bold': [
            os.path.join(base, 'static', 'fonts', 'arialbd.ttf'),
            os.path.join(base, 'staticfiles', 'fonts', 'arialbd.ttf'),
            '/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf',
            '/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            'C:/Windows/Fonts/arialbd.ttf',
            'C:/Windows/Fonts/tahomabd.ttf',
        ],
    }

    for font_name, paths in font_searches.items():
        for path in paths:
            if os.path.exists(path):
                try:
                    pdfmetrics.registerFont(TTFont(font_name, path))
                    break
                except Exception:
                    continue

    _fonts_ready = True


def _get_fonts():
    """Return (bold_font, regular_font) names."""
    _setup_fonts()
    try:
        pdfmetrics.getFont('Receipt-Bold')
        return 'Receipt-Bold', 'Receipt-Regular'
    except Exception:
        return 'Helvetica-Bold', 'Helvetica'


def _rtl(text):
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


def _cfg(lang, BOLD, REG):
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

    BOLD, REG = _get_fonts()
    cfg = _cfg(lang, BOLD, REG)
    rtl = cfg['rtl']

    # Collect all items
    items_data = []
    try:
        for oi in order.items.prefetch_related('toppings').all():
            try:
                name = _safe_name(oi.menu_item, lang)
                if rtl:
                    name = _rtl(name)
                qty   = f'{oi.weight_grams}g' if oi.weight_grams else f'x{oi.quantity}'
                price = f'NIS {oi.get_subtotal()}'
                tops  = []
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

    # Dynamic height
    lines = 22
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

    c.setFont(BOLD, 13)
    c.setFillColor(BLACK)
    c.drawCentredString(W/2, y, f'#{str(order.id).zfill(4)}')
    y -= 7*mm

    loc = (cfg['table'] + ' ' + str(order.table.number)) if order.table else cfg['cashier']
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
            c.setFont(BOLD, 9)
            c.setFillColor(BLACK)
            c.drawRightString(W - PAD, y, name)
            c.drawString(PAD, y, price)
            c.setFont(REG, 7.5)
            c.setFillColor(LGRAY)
            pw = c.stringWidth(price, BOLD, 9)
            c.drawString(PAD + pw + 1.5*mm, y, qty)
        else:
            c.setFont(BOLD, 9)
            c.setFillColor(BLACK)
            c.drawString(PAD, y, f'{qty}  {name}')
            c.drawRightString(W - PAD, y, price)

        y -= 5*mm

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

        if item['notes']:
            c.setFont(REG, 7)
            c.setFillColor(LGRAY)
            note = f'* {item["notes"]}'
            if rtl:
                c.drawRightString(W - PAD - 3*mm, y, _rtl(note))
            else:
                c.drawString(PAD + 3*mm, y, note)
            y -= 4*mm

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

    c.setFont(BOLD, 10)
    c.setFillColor(WHITE)
    if rtl:
        c.drawRightString(W - PAD - 2*mm, y - 4*mm, cfg['total'])
        c.setFont(BOLD, 12)
        c.drawString(PAD + 2*mm, y - 4*mm, f'NIS {order.total_price}')
    else:
        c.drawString(PAD + 2*mm, y - 4*mm, cfg['total'])
        c.setFont(BOLD, 12)
        c.drawRightString(W - PAD - 2*mm, y - 4*mm, f'NIS {order.total_price}')

    y -= box_h + 4*mm

    pm  = order.payment_method or 'cash'
    pay = cfg['pay'].get(pm, pm)
    cen(pay, 8, col=GRAY)

    if order.customer_name:
        cen(order.customer_name, 8, col=GRAY)
    if order.customer_phone:
        cen(order.customer_phone, 8, col=GRAY)
    if order.notes:
        sp(1)
        cen(f'* {_rtl(order.notes) if rtl else order.notes}', 7, col=LGRAY)

    sp(2)
    hline(LGRAY, 0.3)
    sp(1)
    cen(cfg['thanks'], 9, bold=True)
    sp(1)
    cen(cfg['note'], 6, col=LGRAY)
    sp(2)

    c.save()
    buf.seek(0)
    return buf