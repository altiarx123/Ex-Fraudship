import requests
import os
import smtplib
from email.message import EmailMessage
from nexmo import Sms

# phone normalization helper: prefer phonenumbers if installed
try:
    import phonenumbers
    def normalize_phone(phone, default_region=None):
        try:
            p = phonenumbers.parse(phone, default_region)
            if phonenumbers.is_possible_number(p):
                return phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.E164)
        except Exception:
            pass
        # fallback to digit-only
        digits = ''.join(ch for ch in (phone or '') if ch.isdigit())
        if digits:
            # try to return with leading + if it looks international
            if phone.strip().startswith('+'):
                return '+' + digits
            return digits
        return phone
except Exception:
    def normalize_phone(phone, default_region=None):
        digits = ''.join(ch for ch in (phone or '') if ch.isdigit())
        if not digits:
            return phone
        if phone.strip().startswith('+'):
            return '+' + digits
        return digits


def send_via_textbelt(phone_number, message, api_key=None, timeout=10):
    """
    Send SMS via Textbelt API. Returns dict with status and detail.
    """
    api_key = api_key or os.getenv("TEXTBELT_API_KEY", "textbelt")
    # normalize to E.164 where possible (Textbelt prefers international format)
    phone_norm = normalize_phone(phone_number)
    try:
        resp = requests.post('https://textbelt.com/text', {
            'phone': phone_norm,
            'message': message,
            'key': api_key,
        }, timeout=timeout)
    except Exception as e:
        return {"status": "failed", "detail": f"request_error: {e}"}
    try:
        result = resp.json()
    except Exception:
        return {"status": "failed", "detail": f"invalid_response: {resp.text[:200]}"}

    if result.get('success'):
        return {"status": "sent", "detail": result}
    else:
        return {"status": "failed", "detail": result.get('error') or result}


def send_via_email_gateway(phone_number, message, smtp_host=None, smtp_port=None, smtp_user=None, smtp_pass=None, sms_domain=None, timeout=10):
    """
    Send SMS by using an email-to-SMS gateway. Requires phone_number (digits only or with +)
    and an sms_domain like 'txt.att.net' or a full mapping provided via SMS_FALLBACK_DOMAIN env var.

    Returns dict with status and detail.
    """
    # Determine smtp settings from env if not provided
    smtp_host = smtp_host or os.getenv('SMTP_HOST')
    smtp_port = int(smtp_port or os.getenv('SMTP_PORT') or 587)
    smtp_user = smtp_user or os.getenv('SMTP_USER')
    smtp_pass = smtp_pass or os.getenv('SMTP_PASS')
    sms_domain = sms_domain or os.getenv('SMS_FALLBACK_DOMAIN')

    if not sms_domain:
        return {"status": "failed", "detail": "sms_domain_missing"}
    if not smtp_host or not smtp_user or not smtp_pass:
        return {"status": "failed", "detail": "smtp_credentials_missing"}

    # Normalize phone -> email address. Use digits for gateway addresses.
    # phonenumbers may produce +1555...; gateways usually want only digits
    phone_digits = ''.join(ch for ch in normalize_phone(phone_number) if ch.isdigit())
    if not phone_digits:
        return {"status": "failed", "detail": "invalid_phone_number"}
    to_addr = f"{phone_digits}@{sms_domain}"

    try:
        em = EmailMessage()
        em['Subject'] = ''
        em['From'] = smtp_user
        em['To'] = to_addr
        em.set_content(message)
        with smtplib.SMTP(smtp_host, smtp_port, timeout=timeout) as s:
            try:
                s.starttls()
            except Exception:
                pass
            s.login(smtp_user, smtp_pass)
            s.send_message(em)
        return {"status": "sent", "detail": f"email_gateway:{to_addr}"}
    except Exception as e:
        return {"status": "failed", "detail": str(e)}


def send_via_nexmo(phone_number, message, api_key=None, api_secret=None, timeout=10):
    """
    Send SMS via Nexmo API. Returns dict with status and detail.
    """
    api_key = api_key or os.getenv("NEXMO_API_KEY")
    api_secret = api_secret or os.getenv("NEXMO_API_SECRET")
    from_number = os.getenv("NEXMO_FROM")
    if not all([api_key, api_secret, from_number]):
        return {"status": "failed", "detail": "Nexmo credentials missing"}

    try:
        client = Sms(key=api_key, secret=api_secret)
        response = client.send_message({
            'from': from_number,
            'to': phone_number,
            'text': message
        })
        if response["messages"][0]["status"] == "0":
            return {"status": "sent", "detail": response["messages"][0]["message-id"]}
        else:
            return {"status": "failed", "detail": response["messages"][0]["error-text"]}
    except Exception as e:
        return {"status": "failed", "detail": str(e)}


def send_sms(phone_number, message):
    """
    Backwards-compatible wrapper kept for scripts that call this module directly.
    Attempts Textbelt and prints a simple message (original behaviour).
    """
    res = send_via_textbelt(phone_number, message)
    if res.get('status') == 'sent':
        print("SMS sent successfully!")
    else:
        print(f"Failed to send SMS: {res.get('detail')}")


if __name__ == "__main__":
    # Example usage
    send_sms("+1234567890", "Hello! This is a test message.")
