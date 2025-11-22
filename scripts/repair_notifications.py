import csv
import os

NOTIF = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fraudshield_logs_notifications.csv')
BACKUP = NOTIF + '.bak'

if not os.path.exists(NOTIF):
    print('No notifications file found at', NOTIF)
    raise SystemExit(1)

print('Backing up', NOTIF, 'to', BACKUP)
with open(NOTIF, 'r', encoding='utf-8', errors='replace') as f:
    data = f.read()
with open(BACKUP, 'w', encoding='utf-8') as b:
    b.write(data)

rows = []
with open(NOTIF, 'r', encoding='utf-8', errors='replace') as f:
    reader = csv.reader(f)
    for i, row in enumerate(reader):
        # skip empty lines
        if not row:
            continue
        rows.append(row)

# Determine header
header = ['timestamp','transaction_id','method','contact','message']
new_rows = [header]

for i, row in enumerate(rows):
    # if first row looks like header, skip it
    if i == 0 and ('timestamp' in [c.lower() for c in row] or 'method' in [c.lower() for c in row]):
        continue
    if len(row) == 4:
        # assume: timestamp,method,contact,message
        timestamp, method, contact, message = row
        tx = ''
    elif len(row) == 5:
        # assume: timestamp,transaction_id,method,contact,message
        timestamp, tx, method, contact, message = row
    elif len(row) > 5:
        # join extras into message
        timestamp = row[0]
        tx = row[1]
        method = row[2]
        contact = row[3]
        message = ','.join(row[4:])
    else:
        # unexpected row, pad
        row2 = row + [''] * (5 - len(row))
        timestamp, tx, method, contact, message = row2
    new_rows.append([timestamp, tx, method, contact, message])

# write repaired file
with open(NOTIF, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(new_rows)

print('Repaired notifications file written to', NOTIF)
print('Backup at', BACKUP)
