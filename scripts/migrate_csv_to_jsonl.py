import os
import csv
import json
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def parse_number_list(s):
    # extract numeric literals (ints/floats) from a string
    if s is None:
        return []
    nums = re.findall(r"[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?", s)
    out = []
    for n in nums:
        if '.' in n or 'e' in n or 'E' in n:
            try:
                out.append(float(n))
            except:
                out.append(n)
        else:
            try:
                out.append(int(n))
            except:
                out.append(n)
    return out

def migrate_logs(csv_path, jsonl_path):
    if not os.path.exists(csv_path):
        print('No', csv_path)
        return
    bak = csv_path + '.bak'
    print('Backing up', csv_path, '->', bak)
    os.replace(csv_path, bak)
    with open(bak, 'r', encoding='utf-8', errors='replace') as f, open(jsonl_path, 'w', encoding='utf-8') as out:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if not row:
                continue
            # detect header
            low = [c.lower() for c in row]
            if i == 0 and ('timestamp' in low and ('prediction' in low or 'transaction_id' in low)):
                continue
            # normalize row
            if len(row) == 5:
                timestamp, prediction, probability, shap_s, inputs_s = row
                tx = None
            elif len(row) == 6:
                timestamp, tx, prediction, probability, shap_s, inputs_s = row
            elif len(row) > 6:
                # join extras into inputs
                timestamp = row[0]
                tx = row[1] if row[1] else None
                prediction = row[2] if len(row) > 2 else None
                probability = row[3] if len(row) > 3 else None
                shap_s = row[4] if len(row) > 4 else ''
                inputs_s = ','.join(row[5:])
            else:
                # pad
                pad = row + ['']*(6-len(row))
                timestamp, tx, prediction, probability, shap_s, inputs_s = pad
            try:
                pred = int(prediction) if prediction not in (None, '') else None
            except:
                pred = None
            try:
                prob = float(probability) if probability not in (None, '') else None
            except:
                prob = None
            shap_vals = parse_number_list(shap_s)
            inputs = parse_number_list(inputs_s)
            obj = {
                'timestamp': timestamp,
                'transaction_id': tx,
                'prediction': pred,
                'probability': prob,
                'shap_values': shap_vals,
                'inputs': inputs
            }
            out.write(json.dumps(obj) + '\n')
    print('Wrote', jsonl_path)

def migrate_notifications(csv_path, jsonl_path):
    if not os.path.exists(csv_path):
        print('No', csv_path)
        return
    bak = csv_path + '.bak'
    print('Backing up', csv_path, '->', bak)
    os.replace(csv_path, bak)
    with open(bak, 'r', encoding='utf-8', errors='replace') as f, open(jsonl_path, 'w', encoding='utf-8') as out:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if not row:
                continue
            low = [c.lower() for c in row]
            if i == 0 and ('timestamp' in low and ('method' in low or 'transaction_id' in low)):
                continue
            # map: timestamp,transaction_id,method,contact,message  (some rows may miss tx)
            if len(row) == 4:
                timestamp, method, contact, message = row
                tx = None
            elif len(row) == 5:
                timestamp, tx, method, contact, message = row
            elif len(row) > 5:
                timestamp = row[0]
                tx = row[1]
                method = row[2]
                contact = row[3]
                message = ','.join(row[4:])
            else:
                row2 = row + ['']*(5-len(row))
                timestamp, tx, method, contact, message = row2
            obj = {
                'timestamp': timestamp,
                'transaction_id': tx,
                'method': method,
                'contact': contact,
                'message': message
            }
            out.write(json.dumps(obj) + '\n')
    print('Wrote', jsonl_path)

def migrate_replies(csv_path, jsonl_path):
    if not os.path.exists(csv_path):
        print('No', csv_path)
        return
    bak = csv_path + '.bak'
    print('Backing up', csv_path, '->', bak)
    os.replace(csv_path, bak)
    with open(bak, 'r', encoding='utf-8', errors='replace') as f, open(jsonl_path, 'w', encoding='utf-8') as out:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if not row:
                continue
            low = [c.lower() for c in row]
            if i == 0 and ('timestamp' in low and ('reply' in low or 'contact' in low)):
                continue
            # possible formats: timestamp,contact,transaction_id,reply OR timestamp,contact,reply
            if len(row) == 3:
                timestamp, contact, reply = row
                tx = None
            elif len(row) == 4:
                timestamp, contact, tx, reply = row
            elif len(row) > 4:
                timestamp = row[0]
                contact = row[1]
                tx = row[2]
                reply = ','.join(row[3:])
            else:
                row2 = row + ['']*(4-len(row))
                timestamp, contact, tx, reply = row2
            obj = {
                'timestamp': timestamp,
                'contact': contact,
                'transaction_id': tx,
                'reply': reply
            }
            out.write(json.dumps(obj) + '\n')
    print('Wrote', jsonl_path)


if __name__ == '__main__':
    migrate_logs(os.path.join(ROOT, 'fraudshield_logs.csv'), os.path.join(ROOT, 'fraudshield_logs.jsonl'))
    migrate_notifications(os.path.join(ROOT, 'fraudshield_logs_notifications.csv'), os.path.join(ROOT, 'fraudshield_notifications.jsonl'))
    migrate_replies(os.path.join(ROOT, 'fraudshield_logs_replies.csv'), os.path.join(ROOT, 'fraudshield_replies.jsonl'))
