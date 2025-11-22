import os
import json
import time
import logging
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.getcwd(), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
AUDIT_FILE = os.path.join(LOG_DIR, 'audit.jsonl')

logger = logging.getLogger('integrations.audit')
if not logger.handlers:
    handler = RotatingFileHandler(os.path.join(LOG_DIR, 'audit.log'), maxBytes=1024*1024, backupCount=3)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def log_audit_event(actor: str, action: str, person_id: str, notify_attempted: bool, notify_sent_status: str, detail: dict = None):
    obj = {
        'timestamp': time.time(),
        'actor': actor,
        'action': action,
        'person_id': person_id,
        'notify_attempted': bool(notify_attempted),
        'notify_sent_status': notify_sent_status,
        'detail': detail or {}
    }
    # append to JSONL for UI reading
    try:
        with open(AUDIT_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(obj) + '\n')
    except Exception:
        logger.exception('Failed to write audit jsonl')
    logger.info('AUDIT %s', obj)
    return obj
