#!/usr/bin/env python
import argparse
import os
import json
import uuid
import time
from integrations.db_adapters import get_db_adapter


def seed(adapter, count=5):
    created = 0
    people = []
    for i in range(count):
        pid = str(uuid.uuid4())
        p = {
            'id': pid,
            'name': f'User {i+1}',
            'phone': f'555000{100+i}',
            'telegram_id': '',
            'consent': 1,
            'consent_ts': time.strftime('%Y-%m-%d %H:%M:%S'),
            'last_notified': None
        }
        adapter.update_person(pid, p)
        people.append(p)
        created += 1
    return created, people


def main():
    p = argparse.ArgumentParser()
    p.add_argument('command', choices=['seed', 'migrate-data'])
    p.add_argument('--from', dest='src', default='csv')
    p.add_argument('--to', dest='dst', default=os.getenv('DATA_BACKEND', 'sqlite'))
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()
    if args.command == 'seed':
        adapter = get_db_adapter()
        created, people = seed(adapter)
        print(f'Created {created} people')
    elif args.command == 'migrate-data':
        src = args.src
        dst = args.dst
        print(f'Migrate from {src} to {dst} (dry_run={args.dry_run})')
        src_adapter = get_db_adapter(src)
        dst_adapter = get_db_adapter(dst)
        # attempt migrate
        if args.dry_run:
            print('Dry run: counting rows to migrate...')
            # naive count
            if hasattr(src_adapter, 'list_people'):
                rows = src_adapter.list_people()
                print('Would migrate', len(rows), 'rows')
        else:
            count = dst_adapter.migrate_from_csv(getattr(src_adapter, 'path', ''))
            print('Migrated', count, 'rows')


if __name__ == '__main__':
    main()
