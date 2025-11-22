import os

# Safe defaults
SAFE_MODE = os.getenv('SAFE_MODE', os.getenv('DEMO_MODE', 'true')).lower() in ('1', 'true', 'yes')
DATA_BACKEND = os.getenv('DATA_BACKEND', 'sqlite')
SMS_PROVIDER = os.getenv('SMS_PROVIDER', 'mock')
RATE_LIMIT_SECONDS = int(os.getenv('RATE_LIMIT_SECONDS', '60'))

# SMTP / Telegram settings are read from environment when needed
