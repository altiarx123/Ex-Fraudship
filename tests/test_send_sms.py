import unittest
from unittest.mock import patch, MagicMock
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts import send_sms

class TestSendSmsHelpers(unittest.TestCase):
    def test_normalize_phone_digits(self):
        # Without phonenumbers library, normalize_phone should strip to digits
        p = send_sms.normalize_phone('(555) 123-4567')
        self.assertIn('5551234567', p)

    @patch('scripts.send_sms.requests.post')
    def test_textbelt_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'success': True, 'id': 'abc'}
        mock_post.return_value = mock_resp
        res = send_sms.send_via_textbelt('+15551234567', 'hello')
        self.assertEqual(res['status'], 'sent')

    @patch('scripts.send_sms.requests.post')
    def test_textbelt_failure(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'success': False, 'error': 'quota exceeded'}
        mock_post.return_value = mock_resp
        res = send_sms.send_via_textbelt('+15551234567', 'hello')
        self.assertEqual(res['status'], 'failed')

    @patch('scripts.send_sms.smtplib.SMTP')
    def test_email_gateway_success(self, mock_smtp):
        mock_conn = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_conn
        os.environ['SMTP_HOST'] = 'smtp.example.com'
        os.environ['SMTP_PORT'] = '587'
        os.environ['SMTP_USER'] = 'u'
        os.environ['SMTP_PASS'] = 'p'
        os.environ['SMS_FALLBACK_DOMAIN'] = 'vtext.com'
        res = send_sms.send_via_email_gateway('+15551234567', 'test')
        self.assertEqual(res['status'], 'sent')

    @patch('scripts.send_sms.smtplib.SMTP')
    def test_email_gateway_missing_env(self, mock_smtp):
        # remove any smtp env to simulate missing configuration
        for k in ('SMTP_HOST','SMTP_USER','SMTP_PASS','SMS_FALLBACK_DOMAIN'):
            os.environ.pop(k, None)
        res = send_sms.send_via_email_gateway('+15551234567', 'test')
        self.assertEqual(res['status'], 'failed')

if __name__ == '__main__':
    unittest.main()

