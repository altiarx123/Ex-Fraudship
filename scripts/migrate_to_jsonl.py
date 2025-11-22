import os
import csv
import json
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def extract_numbers(s):
    # find floats/ints including scientific notation
    nums = re.findall(r'[-+]?(?:\d*\.)?\d+(?:[eE][-+]?\d+)?', s)
    return [float(n) for n in nums]

def migrate_logs(csv_path, jsonl_path, kind='logs'):
    if not os.path.exists(csv_path):
        print(f'No {kind} CSV at {csv_path}, skipping')
        return
    bak = csv_path + '.bak'
    if not os.path.exists(bak):
        os.rename(csv_path, bak)
        print('Backed up', csv_path, '->', bak)
    else:
        print('Backup already exists at', bak)

    with open(bak, 'r', encoding='utf-8', errors='replace') as f, open(jsonl_path, 'w', encoding='utf-8') as out:
        reader = csv.reader(f)
        header = None
        for i, row in enumerate(reader):
            if not row:
                continue
            # try detect header
            if i == 0 and any('timestamp' in c.lower() for c in row):
                header = [c.strip() for c in row]
                continue
            # normalize by length
            # common cases: 5 cols (timestamp,pred,prob,shap,inputs) or 6 cols (timestamp,tx,pred,prob,shap,inputs)
            if len(row) >= 6:
                timestamp = row[0]
                transaction_id = row[1]
                prediction = row[2]
                probability = row[3]
                shap_s = ','.join(row[4:-1]) if len(row) > 6 else row[4]
                inputs_s = row[-1]
            elif len(row) == 5:
                timestamp, prediction, probability, shap_s, inputs_s = row
                transaction_id = None
            else:
                # fallback: join trailing as message/inputs
                timestamp = row[0] if len(row) > 0 else ''
                transaction_id = row[1] if len(row) > 1 else None
                prediction = row[2] if len(row) > 2 else None
                probability = row[3] if len(row) > 3 else None
                shap_s = row[4] if len(row) > 4 else ''
                inputs_s = ','.join(row[5:]) if len(row) > 5 else ''

            # parse lists of numbers in shap_s and inputs_s
            try:
                shap = extract_numbers(shap_s)
            except Exception:
                shap = []
            try:
                inputs = extract_numbers(inputs_s)
            except Exception:
                inputs = []

            obj = {
                'timestamp': timestamp,
                'transaction_id': transaction_id,
                'prediction': int(prediction) if prediction not in (None, '') else None,
                'probability': float(probability) if probability not in (None, '') else None,
                'shap_values': shap,
                'inputs': inputs
            }
            out.write(json.dumps(obj) + '\n')
    print('Migrated', csv_path, '->', jsonl_path)


def migrate_notifications(csv_path, jsonl_path):
    if not os.path.exists(csv_path):
        print('No notifications CSV, skipping')
        return
    bak = csv_path + '.bak'
    if not os.path.exists(bak):
        os.rename(csv_path, bak)
        print('Backed up', csv_path, '->', bak)
    else:
        print('Backup already exists at', bak)
    with open(bak, 'r', encoding='utf-8', errors='replace') as f, open(jsonl_path, 'w', encoding='utf-8') as out:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if not row:
                continue
            # header detection
            if i == 0 and any('timestamp' in c.lower() for c in row):
                continue
            # support rows with either 4 or 5 columns
            if len(row) >= 5:
                timestamp = row[0]
                tx = row[1]
                method = row[2]
                contact = row[3]
                message = ','.join(row[4:])
            elif len(row) == 4:
                timestamp, method, contact, message = row
                tx = None
            else:
                # join everything after timestamp
                timestamp = row[0]
                tx = None
                method = row[1] if len(row) > 1 else None
                contact = row[2] if len(row) > 2 else None
                message = ','.join(row[3:])
            obj = {
                'timestamp': timestamp,
                'transaction_id': tx,
                'method': method,
                'contact': contact,
                'message': message
            }
            out.write(json.dumps(obj) + '\n')
    print('Migrated', csv_path, '->', jsonl_path)


def migrate_replies(csv_path, jsonl_path):
    if not os.path.exists(csv_path):
        print('No replies CSV, skipping')
        return
    bak = csv_path + '.bak'
    if not os.path.exists(bak):
        os.rename(csv_path, bak)
        print('Backed up', csv_path, '->', bak)
    else:
        print('Backup already exists at', bak)
    with open(bak, 'r', encoding='utf-8', errors='replace') as f, open(jsonl_path, 'w', encoding='utf-8') as out:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if not row:
                continue
            if i == 0 and any('timestamp' in c.lower() for c in row):
                continue
            # expect timestamp,contact,transaction_id,reply or variations
            if len(row) >= 4:
                timestamp = row[0]
                contact = row[1]
                tx = row[2]
                reply = ','.join(row[3:])
            elif len(row) == 3:
                timestamp, contact, reply = row
                tx = None
            else:
                timestamp = row[0]
                contact = row[1] if len(row) > 1 else None
                tx = None
                reply = ','.join(row[2:])
            obj = {
                'timestamp': timestamp,
                'contact': contact,
                'transaction_id': tx,
                'reply': reply
            }
            out.write(json.dumps(obj) + '\n')
    print('Migrated', csv_path, '->', jsonl_path)


if __name__ == '__main__':
    migrate_logs(os.path.join(ROOT, 'fraudshield_logs.csv'), os.path.join(ROOT, 'fraudshield_logs.jsonl'))
    migrate_notifications(os.path.join(ROOT, 'fraudshield_logs_notifications.csv'), os.path.join(ROOT, 'fraudshield_logs_notifications.jsonl'))
    migrate_replies(os.path.join(ROOT, 'fraudshield_logs_replies.csv'), os.path.join(ROOT, 'fraudshield_logs_replies.jsonl'))
    print('Migration complete.')
