"""
PDF Receipt — single language based on order.language
"""
from reportlab.lib.pagesizes import A5
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from io import BytesIO
import os

# ── Font registration ─────────────────────────────────────
_fonts_registered = False

def _reg():
    global _fonts_registered
    if _fonts_registered:
        return
    paths = {
        'AR_B': ['/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf',
                 'C:/Windows/Fonts/arialbd.ttf'],
        'AR_R': ['/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf',
                 'C:/Windows/Fonts/arial.ttf'],
        'HE_B': ['/usr/share/fonts/truetype/noto/NotoSansHebrew-Bold.ttf',
                 'C:/Windows/Fonts/arialbd.ttf'],
        'HE_R': ['/usr/share/fonts/truetype/noto/NotoSansHebrew-Regular.ttf',
                 'C:/Windows/Fonts/arial.ttf'],
    }
    for name, tries in paths.items():
        for p in tries:
            if os.path.exists(p):
                try:
                    pdfmetrics.registerFont(TTFont(name, p))
                    break
                except Exception:
                    pass
    _fonts_registered = True

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

# ── Language config ───────────────────────────────────────
def _cfg(lang):
    """Return font names and strings for the given language."""
    _reg()
    if lang == 'he':
        return {
            'bold':  'HE_B' if _font_exists('HE_B') else 'Helvetica-Bold',
            'reg':   'HE_R' if _font_exists('HE_R') else 'Helvetica',
            'rtl':   True,
            'sub':   'אבו שאדי — נצרת',
            'table': 'שולחן',
            'cash_order': 'הזמנת קופה',
            'total': 'סה"כ',
            'pay':   {'cash': 'מזומן', 'cashier_card': 'כרטיס בקופה', 'online': 'תשלום אונליין'},
            'thanks': 'תודה על ביקורכם! 🔥',
            'note':  'זהו קבלה פנימית — לא חשבונית מס',
        }
    elif lang == 'en':
        return {
            'bold':  'Helvetica-Bold',
            'reg':   'Helvetica',
            'rtl':   False,
            'sub':   'Abu Shadi — Nazareth',
            'table': 'Table',
            'cash_order': 'Cashier Order',
            'total': 'TOTAL',
            'pay':   {'cash': 'Cash', 'cashier_card': 'Card at Cashier', 'online': 'Online Payment'},
            'thanks': 'Thank you for visiting! 🔥',
            'note':  'Internal receipt — not a tax invoice',
        }
    else:  # ar
        return {
            'bold':  'AR_B' if _font_exists('AR_B') else 'Helvetica-Bold',
            'reg':   'AR_R' if _font_exists('AR_R') else 'Helvetica',
            'rtl':   True,
            'sub':   'أبو شادي — الناصرة',
            'table': 'طاولة',
            'cash_order': 'طلب كاشير',
            'total': 'المجموع',
            'pay':   {'cash': 'كاش', 'cashier_card': 'بطاقة كاشير', 'online': 'دفع اونلاين'},
            'thanks': 'شكراً لزيارتكم! 🔥',
            'note':  'هذا وصل داخلي — ليس فاتورة ضريبية',
        }

def _font_exists(name):
    try:
        pdfmetrics.getFont(name)
        return True
    except Exception:
        return False

def _item_name(item, lang):
    if lang == 'he':
        return item.name_he or item.name_ar or item.name
    elif lang == 'en':
        return item.name or item.name_ar
    return item.name_ar or item.name

def _top_name(t, lang):
    if lang == 'he':
        return t.name_he or t.name_ar or t.name
    elif lang == 'en':
        return t.name or t.name_ar
    return t.name_ar or t.name


# ── Main generator ────────────────────────────────────────
def generate_order_pdf(order, lang=None):
    if lang is None:
        lang = getattr(order, 'language', 'ar') or 'ar'

    cfg = _cfg(lang)
    rtl = cfg['rtl']

    buf = BytesIO()
    W, H = A5
    c = canvas.Canvas(buf, pagesize=A5)

    PAD   = 10 * mm
    # B&W printer safe colors
    YELLOW = colors.black          # header background → solid black
    BLACK  = colors.black
    GRAY   = colors.HexColor('#444444')
    ORANGE = colors.HexColor('#222222')  # toppings → dark gray
    WHITE  = colors.white

    y = H - 5 * mm

    def sp(n=3):
        nonlocal y
        y -= n * mm

    def hline(col=GRAY, w=0.4):
        nonlocal y
        c.setStrokeColor(col)
        c.setLineWidth(w)
        c.line(PAD, y, W - PAD, y)
        y -= 4 * mm

    def cen(txt, font, size, col):
        nonlocal y
        c.setFont(font, size)
        c.setFillColor(col)
        s = _rtl(txt) if rtl else str(txt)
        c.drawCentredString(W / 2, y, s)
        y -= size * 0.5 + 2 * mm

    # ── HEADER ──
    c.setFillColor(YELLOW)
    c.rect(0, H - 28*mm, W, 28*mm, fill=1, stroke=0)
    c.setFont('Helvetica-Bold', 30)
    c.setFillColor(WHITE)        # white text on black header
    c.drawCentredString(W/2, H - 14*mm, 'LOCO')
    c.setFont(cfg['bold'], 10)
    sub = _rtl(cfg['sub']) if rtl else cfg['sub']
    c.drawCentredString(W/2, H - 22*mm, sub)

    y = H - 33*mm
    sp(2)

    # Order number
    c.setFont('Helvetica-Bold', 22)
    c.setFillColor(BLACK)
    c.drawCentredString(W/2, y, '#' + str(order.id).zfill(6))
    y -= 10*mm

    # Location
    if order.table:
        loc = cfg['table'] + ' ' + str(order.table.number)
    else:
        loc = cfg['cash_order']
    cen(loc, cfg['reg'], 9, GRAY)

    # Date
    dt = order.created_at
    c.setFont('Helvetica', 9)
    c.setFillColor(GRAY)
    c.drawCentredString(W/2, y, dt.strftime('%d/%m/%Y   %H:%M'))
    y -= 7*mm

    sp(1)
    hline(BLACK, 1.0)

    # ── ITEMS ──
    for oi in order.items.all():
        name = _item_name(oi.menu_item, lang)
        if oi.weight_grams:
            display_qty = str(oi.weight_grams) + 'g'
        else:
            display_qty = 'x' + str(oi.quantity)

        price_str = 'NIS ' + str(oi.get_subtotal())

        # Item row: name left/right, price opposite
        c.setFont(cfg['bold'], 10)
        c.setFillColor(BLACK)

        name_display = _rtl(name) if rtl else name
        qty_str = display_qty + '  '

        if rtl:
            # Name on right, price on left
            c.drawRightString(W - PAD, y, name_display)
            c.setFont('Helvetica-Bold', 9)
            c.drawString(PAD, y, price_str)
            # qty next to price
            c.setFont(cfg['reg'], 8)
            c.setFillColor(GRAY)
            pw = c.stringWidth(price_str, 'Helvetica-Bold', 9)
            c.drawString(PAD + pw + 2*mm, y, qty_str)
        else:
            c.drawString(PAD, y, name_display)
            c.setFont('Helvetica-Bold', 9)
            c.drawRightString(W - PAD, y, price_str)
            c.setFont(cfg['reg'], 8)
            c.setFillColor(GRAY)
            c.drawString(PAD + c.stringWidth(name_display, cfg['bold'], 10) + 2*mm, y, qty_str)

        y -= 6*mm

        # Each topping on its own line
        for t in oi.toppings.all():
            tname = _top_name(t, lang)
            tprice = float(t.price) if t.price else 0
            if tprice > 0:
                tline = '+ ' + tname + '  +NIS ' + str(t.price)
            else:
                tline = '+ ' + tname

            c.setFont(cfg['reg'], 8.5)
            c.setFillColor(ORANGE)
            if rtl:
                c.drawRightString(W - PAD - 4*mm, y, _rtl(tline))
            else:
                c.drawString(PAD + 4*mm, y, tline)
            y -= 5*mm

        # Item notes
        if oi.notes:
            c.setFont(cfg['reg'], 8)
            c.setFillColor(GRAY)
            note_txt = '* ' + oi.notes
            if rtl:
                c.drawRightString(W - PAD - 4*mm, y, _rtl(note_txt))
            else:
                c.drawString(PAD + 4*mm, y, note_txt)
            y -= 5*mm

        # Thin line between items
        c.setStrokeColor(colors.HexColor('#1e1e1e'))
        c.setLineWidth(0.3)
        c.line(PAD + 6*mm, y + 2*mm, W - PAD - 6*mm, y + 2*mm)
        y -= 3*mm

    sp(1)
    hline(BLACK, 1.0)
    sp(2)

    # ── TOTAL BOX ──
    box_h = 13*mm
    c.setFillColor(BLACK)
    c.rect(PAD, y - box_h + 3*mm, W - 2*PAD, box_h, fill=1, stroke=0)

    total_lbl = _rtl(cfg['total']) if rtl else cfg['total']
    c.setFont(cfg['bold'], 11)
    c.setFillColor(WHITE)        # white text on black box
    if rtl:
        c.drawRightString(W - PAD - 3*mm, y - 3*mm, total_lbl)
        c.setFont('Helvetica-Bold', 14)
        c.drawString(PAD + 3*mm, y - 3*mm, 'NIS ' + str(order.total_price))
    else:
        c.drawString(PAD + 3*mm, y - 3*mm, total_lbl)
        c.setFont('Helvetica-Bold', 14)
        c.drawRightString(W - PAD - 3*mm, y - 3*mm, 'NIS ' + str(order.total_price))
    y -= box_h + 2*mm

    sp(3)

    # ── PAYMENT ──
    pm  = order.payment_method
    pay = cfg['pay'].get(pm, pm)
    cen(pay, cfg['reg'], 9, GRAY)

    if order.customer_name:
        cen(order.customer_name, 'Helvetica', 9, GRAY)
    if order.customer_phone:
        cen(order.customer_phone, 'Helvetica', 9, GRAY)
    if order.notes:
        sp(1)
        cen('* ' + order.notes, cfg['reg'], 8, ORANGE)

    sp(4)
    hline(GRAY, 0.3)
    sp(2)

    # ── FOOTER ──
    cen(cfg['thanks'], cfg['bold'], 10, BLACK)
    sp(1)
    cen(cfg['note'], cfg['reg'], 7, GRAY)

    c.save()
    buf.seek(0)
    return buf