# supermarket/utils.py
import qrcode
from io import BytesIO
import requests
import re
from django.conf import settings

def generate_promptpay_qr(amount, payee="0123456789"):
    """
    Generate a PromptPay QR code.

    :param amount: float, the amount to be paid
    :param payee: str, PromptPay ID (phone number or tax ID)
    :return: BytesIO buffer containing QR image
    """
    # PromptPay QR payload (simple version)
    payload = f"00020101021129370016A000000677010111{payee}5802TH6304"
    # Append amount in the format of XXXX.XX
    payload += f"{amount:.2f}".replace(".", "")  # e.g., 125.50 → "12550"

    # Calculate CRC (for production, use full PromptPay spec; simplified here)
    payload += "0000"

    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(payload)
    qr.make(fit=True)

    img = qr.make_image(fill="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def send_whatsapp_via_twilio(to_number: str, body: str) -> bool:
    """
    Send a WhatsApp message via Twilio REST API.

    Returns True on success, False otherwise.
    Requires these settings to be configured in Django settings:
      - WHATSAPP_NOTIFICATIONS_ENABLED (bool)
      - TWILIO_ACCOUNT_SID
      - TWILIO_AUTH_TOKEN
      - TWILIO_WHATSAPP_FROM (e.g. 'whatsapp:+1415...')
    """
    if not getattr(settings, 'WHATSAPP_NOTIFICATIONS_ENABLED', False):
        return False

    account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
    from_whatsapp = getattr(settings, 'TWILIO_WHATSAPP_FROM', '')
    if not (account_sid and auth_token and from_whatsapp):
        return False

    # Normalize recipient number: ensure it starts with '+' and digits only
    digits = re.sub(r"\D", "", to_number or "")
    if not digits:
        return False
    if not to_number.strip().startswith('+'):
        to_whatsapp = f"+{digits}"
    else:
        to_whatsapp = to_number

    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    data = {
        'To': f'whatsapp:{to_whatsapp}',
        'From': from_whatsapp if from_whatsapp.startswith('whatsapp:') else f'whatsapp:{from_whatsapp}',
        'Body': body,
    }

    try:
        resp = requests.post(url, data=data, auth=(account_sid, auth_token), timeout=10)
        return resp.status_code in (200, 201)
    except Exception:
        return False