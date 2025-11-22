import os
import json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def read_jsonl(path):
    if not os.path.exists(path):
        return None
    out = []
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                out.append(json.loads(ln))
            except Exception as e:
                out.append({'_parse_error': str(e), '_raw': ln})
    return out

def pick(path_candidates):
    for p in path_candidates:
        full = os.path.join(ROOT, p)
        if os.path.exists(full):
            return full
    return None

def show(name, candidates):
    p = pick(candidates)
    print('-'*60)
    if not p:
        print(f'{name}: NONE of {candidates} found')
        return
    data = read_jsonl(p)
    if data is None:
        print(f'{name}: file present but unreadable: {p}')
        return
    print(f'{name}: {len(data)} records in {os.path.basename(p)}')
    for i, item in enumerate(data[:3]):
        print(f'  [{i}]', json.dumps(item, ensure_ascii=False))

if __name__ == '__main__':
    show('Decision Logs', ['fraudshield_logs.jsonl', 'fraudshield_logs.jsonl'])
    show('Notifications', ['fraudshield_notifications.jsonl', 'fraudshield_logs_notifications.jsonl'])
    show('Replies', ['fraudshield_replies.jsonl', 'fraudshield_logs_replies.jsonl'])
