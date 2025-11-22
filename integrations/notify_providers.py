import os
import json
import time
from typing import Dict
import logging

LOG_DIR = os.path.join(os.getcwd(), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
SIMULATED_FILE = os.path.join(LOG_DIR, 'simulated_notifications.jsonl')

logger = logging.getLogger('integrations.notify')


class BaseProvider:
    name = 'base'

    def send_notification(self, person: Dict, body: str) -> Dict:
        raise NotImplementedError()


class MockProvider(BaseProvider):
    name = 'mock'

    def send_notification(self, person: Dict, body: str) -> Dict:
        # append to simulated file
        obj = {
            'timestamp': time.time(),
            'provider': self.name,
            'person_id': person.get('id'),
            'phone': person.get('phone'),
            'telegram_id': person.get('telegram_id'),
            'body': body
        }
        with open(SIMULATED_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(obj) + '\n')
        logger.info('Mock send: %s', obj)
        return {'status': 'mocked', 'provider': self.name, 'detail': obj}


class EmailGatewayProvider(BaseProvider):
    name = 'email_gateway'

    def __init__(self, smtp_host=None, smtp_port=587, smtp_user=None, smtp_pass=None, gateway_map=None):
        self.smtp_host = smtp_host or os.getenv('SMTP_HOST')
        self.smtp_port = int(smtp_port or os.getenv('SMTP_PORT') or 587)
        self.smtp_user = smtp_user or os.getenv('SMTP_USER')
        self.smtp_pass = smtp_pass or os.getenv('SMTP_PASS')
        # a mapping of carrier->domain for email-to-sms
        self.gateway_map = gateway_map or {
            'tmobile': 'tmomail.net',
            'verizon': 'vtext.com',
            'att': 'txt.att.net'
        }

    def _phone_to_gateway(self, phone: str, carrier: str = None) -> str:
        if carrier and carrier.lower() in self.gateway_map:
            return f"{phone}@{self.gateway_map[carrier.lower()]}"
        return None

    def send_notification(self, person: Dict, body: str) -> Dict:
        # attempt email-to-sms if phone looks numeric and carrier provided via person.carrier
        try:
            import smtplib
            from email.message import EmailMessage
        except Exception as e:
            return {'status': 'failed', 'provider': self.name, 'detail': 'smtplib_missing'}
        to_addr = None
        phone = person.get('phone')
        carrier = person.get('carrier')
        if phone and phone.isdigit():
            gw = self._phone_to_gateway(phone, carrier)
            if gw:
                to_addr = gw
        if not to_addr and person.get('email'):
            to_addr = person.get('email')
        if not to_addr:
            return {'status': 'failed', 'provider': self.name, 'detail': 'no_destination'}
        msg = EmailMessage()
        msg['Subject'] = 'Alert'
        msg['From'] = self.smtp_user or 'no-reply@example.com'
        msg['To'] = to_addr
        msg.set_content(body)
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=15) as s:
                try:
                    s.starttls()
                except Exception:
                    pass
                if self.smtp_user and self.smtp_pass:
                    s.login(self.smtp_user, self.smtp_pass)
                s.send_message(msg)
            return {'status': 'sent', 'provider': self.name, 'detail': to_addr}
        except Exception as e:
            logger.exception('Email send failed')
            return {'status': 'failed', 'provider': self.name, 'detail': str(e)}


class TelegramProvider(BaseProvider):
    name = 'telegram'

    def __init__(self, bot_token: str = None):
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.base = f'https://api.telegram.org/bot{self.bot_token}' if self.bot_token else None

    def send_notification(self, person: Dict, body: str) -> Dict:
        if not self.base:
            return {'status': 'failed', 'provider': self.name, 'detail': 'no_bot_token'}
        chat_id = person.get('telegram_id')
        if not chat_id:
            return {'status': 'failed', 'provider': self.name, 'detail': 'no_telegram_id'}
        try:
            import requests
        except Exception:
            return {'status': 'failed', 'provider': self.name, 'detail': 'requests_missing'}
        try:
            resp = requests.post(f"{self.base}/sendMessage", json={'chat_id': chat_id, 'text': body}, timeout=10)
            if resp.status_code == 200:
                return {'status': 'sent', 'provider': self.name, 'detail': resp.json()}
            return {'status': 'failed', 'provider': self.name, 'detail': resp.text}
        except Exception as e:
            logger.exception('Telegram send failed')
            return {'status': 'failed', 'provider': self.name, 'detail': str(e)}


def get_notify_provider(name: str = None):
    name = name or os.getenv('SMS_PROVIDER', 'mock')
    name = name.lower()
    if name == 'mock':
        return MockProvider()
    if name == 'email_gateway':
        return EmailGatewayProvider()
    if name == 'telegram':
        return TelegramProvider()
    return MockProvider()
