import qrcode
import base64
from io import BytesIO


def generate_qr(table, base_url):
    """
    Generate QR code for a table.
    base_url is passed dynamically from the view using request.build_absolute_uri('/')
    so it always works on local, Railway, or any custom domain.
    """
    url = f"{base_url.rstrip('/')}/table/{table.qr_token}/"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#0a0a0a", back_color="#FFD600")

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    img_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{img_b64}"


def get_qr_url(table, base_url):
    return f"{base_url.rstrip('/')}/table/{table.qr_token}/"