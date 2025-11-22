"""Demo for SMS providers without making network calls.
This script patches `requests.post` and `smtplib.SMTP` inside `scripts.send_sms` to simulate
successful and failed sends, and prints the returned dicts.
Run: python scripts/demo_sms.py
"""
import os
import sys
# ensure project root is importable so `scripts` can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import scripts.send_sms as sms

print('--- SMS helpers demo (offline simulation) ---')

# Keep originals to restore later
_orig_post = sms.requests.post
_orig_smtp = sms.smtplib.SMTP

class DummyResponse:
    def __init__(self, data):
        self._data = data
    def json(self):
        return self._data

# 1) Simulate Textbelt success
sms.requests.post = lambda url, data, timeout=10: DummyResponse({'success': True, 'id': 'demo-textbelt-1'})
res = sms.send_via_textbelt('+15551234567', 'Test message via Textbelt (simulated)')
print('Textbelt simulated success ->', res)

# 2) Simulate Textbelt failure
sms.requests.post = lambda url, data, timeout=10: DummyResponse({'success': False, 'error': 'quota exceeded'})
res = sms.send_via_textbelt('+15551234567', 'Test message via Textbelt (simulated failure)')
print('Textbelt simulated failure ->', res)

# 3) Simulate email-to-SMS success via patched SMTP
class DummySMTP:
    def __init__(self, host, port, timeout=None):
        self.host = host
        self.port = port
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False
    def starttls(self):
        pass
    def login(self, user, password):
        pass
    def send_message(self, em):
        # emulate send success
        return True

sms.smtplib.SMTP = DummySMTP
os.environ['SMTP_HOST'] = 'smtp.example.com'
os.environ['SMTP_PORT'] = '587'
os.environ['SMTP_USER'] = 'user@example.com'
os.environ['SMTP_PASS'] = 'secret'
os.environ['SMS_FALLBACK_DOMAIN'] = 'vtext.com'
res = sms.send_via_email_gateway('+15551234567', 'Test message via email gateway (simulated)')
print('Email-to-SMS simulated success ->', res)

# 4) Demonstrate fallback logic combined: simulate Twilio missing, Textbelt failing, email succeeding
# We'll directly call functions in the order the app uses them
sms.requests.post = lambda url, data, timeout=10: DummyResponse({'success': False, 'error': 'quota exceeded'})
# email gateway already patched above
print('\nCombined fallback demo:')
print('Try Textbelt ->', sms.send_via_textbelt('+15551234567', 'combined test'))
print('Then try email gateway ->', sms.send_via_email_gateway('+15551234567', 'combined test'))

# Restore originals for safety
sms.requests.post = _orig_post
sms.smtplib.SMTP = _orig_smtp

print('\n--- Demo complete ---')
