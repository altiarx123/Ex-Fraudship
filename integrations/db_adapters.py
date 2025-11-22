import os
import csv
import sqlite3
import json
import uuid
from typing import List, Dict, Optional

DEFAULT_CSV = os.path.join(os.getcwd(), 'data', 'people.csv')
DEFAULT_SQLITE = os.path.join(os.getcwd(), 'data', 'people.db')

os.makedirs(os.path.join(os.getcwd(), 'data'), exist_ok=True)


class CSVAdapter:
    def __init__(self, path: str = None):
        self.path = path or DEFAULT_CSV
        # ensure file exists
        if not os.path.exists(self.path):
            with open(self.path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'name', 'phone', 'telegram_id', 'consent', 'consent_ts', 'last_notified'])
                writer.writeheader()

    def list_people(self) -> List[Dict]:
        rows = []
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for r in reader:
                    r['consent'] = r.get('consent') in ('1', 'True', 'true', True)
                    rows.append(r)
        except FileNotFoundError:
            return []
        return rows

    def get_person(self, person_id: str) -> Optional[Dict]:
        for p in self.list_people():
            if p.get('id') == person_id:
                return p
        return None

    def update_person(self, person_id: str, updates: Dict) -> Dict:
        people = self.list_people()
        found = False
        for p in people:
            if p.get('id') == person_id:
                p.update({k: (v if not isinstance(v, bool) else str(int(v))) for k, v in updates.items()})
                found = True
                break
        if not found:
            new = {'id': person_id}
            new.update(updates)
            people.append(new)
        with open(self.path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'name', 'phone', 'telegram_id', 'consent', 'consent_ts', 'last_notified'])
            writer.writeheader()
            for r in people:
                writer.writerow(r)
        return updates

    def migrate_from_csv(self, src_path: str) -> int:
        # copy rows from another csv into this adapter
        if not os.path.exists(src_path):
            return 0
        count = 0
        with open(src_path, 'r', encoding='utf-8') as sf:
            reader = csv.DictReader(sf)
            people = self.list_people()
            existing_ids = {p['id'] for p in people}
            for r in reader:
                if not r.get('id'):
                    r['id'] = str(uuid.uuid4())
                if r['id'] in existing_ids:
                    continue
                people.append(r)
                count += 1
        with open(self.path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'name', 'phone', 'telegram_id', 'consent', 'consent_ts', 'last_notified'])
            writer.writeheader()
            for r in people:
                writer.writerow(r)
        return count


class SQLiteAdapter:
    def __init__(self, path: str = None):
        self.path = path or DEFAULT_SQLITE
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self._ensure_schema()

    def _ensure_schema(self):
        c = self.conn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS people (
            id TEXT PRIMARY KEY,
            name TEXT,
            phone TEXT,
            telegram_id TEXT,
            consent INTEGER DEFAULT 0,
            consent_ts TEXT,
            last_notified INTEGER
        )
        ''')
        self.conn.commit()

    def list_people(self) -> List[Dict]:
        c = self.conn.cursor()
        c.execute('SELECT id, name, phone, telegram_id, consent, consent_ts, last_notified FROM people')
        rows = []
        for r in c.fetchall():
            rows.append({
                'id': r[0], 'name': r[1], 'phone': r[2], 'telegram_id': r[3],
                'consent': bool(r[4]), 'consent_ts': r[5], 'last_notified': r[6]
            })
        return rows

    def get_person(self, person_id: str) -> Optional[Dict]:
        c = self.conn.cursor()
        c.execute('SELECT id, name, phone, telegram_id, consent, consent_ts, last_notified FROM people WHERE id=?', (person_id,))
        r = c.fetchone()
        if not r:
            return None
        return {'id': r[0], 'name': r[1], 'phone': r[2], 'telegram_id': r[3], 'consent': bool(r[4]), 'consent_ts': r[5], 'last_notified': r[6]}

    def update_person(self, person_id: str, updates: Dict) -> Dict:
        # ensure person exists
        p = self.get_person(person_id)
        if not p:
            # insert
            cols = ['id', 'name', 'phone', 'telegram_id', 'consent', 'consent_ts', 'last_notified']
            vals = [person_id, updates.get('name'), updates.get('phone'), updates.get('telegram_id'), int(updates.get('consent', 0)), updates.get('consent_ts'), updates.get('last_notified')]
            c = self.conn.cursor()
            c.execute('INSERT OR REPLACE INTO people (id,name,phone,telegram_id,consent,consent_ts,last_notified) VALUES (?,?,?,?,?,?,?)', vals)
            self.conn.commit()
            return updates
        # update existing
        set_parts = []
        vals = []
        for k, v in updates.items():
            if k == 'consent':
                v = int(bool(v))
            set_parts.append(f"{k}=?")
            vals.append(v)
        vals.append(person_id)
        c = self.conn.cursor()
        c.execute(f"UPDATE people SET {', '.join(set_parts)} WHERE id=?", vals)
        self.conn.commit()
        return updates

    def migrate_from_csv(self, src_path: str) -> int:
        if not os.path.exists(src_path):
            return 0
        count = 0
        with open(src_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                pid = r.get('id') or str(uuid.uuid4())
                if self.get_person(pid):
                    continue
                self.update_person(pid, {'name': r.get('name'), 'phone': r.get('phone'), 'telegram_id': r.get('telegram_id'), 'consent': int(r.get('consent') in ('1','True','true')),'consent_ts': r.get('consent_ts'), 'last_notified': r.get('last_notified')})
                count += 1
        return count


class MongoAdapter:
    def __init__(self, uri: str = None, dbname: str = 'fraudshield'):
        try:
            from pymongo import MongoClient
        except Exception:
            raise RuntimeError('pymongo not installed')
        uri = uri or os.getenv('MONGODB_URI')
        self.client = MongoClient(uri)
        self.db = self.client[dbname]

    def list_people(self):
        return list(self.db.people.find({}, {'_id':0}))

    def get_person(self, person_id: str):
        return self.db.people.find_one({'id': person_id}, {'_id':0})

    def update_person(self, person_id: str, updates: Dict):
        self.db.people.update_one({'id': person_id}, {'$set': updates}, upsert=True)
        return updates

    def migrate_from_csv(self, src_path: str) -> int:
        if not os.path.exists(src_path):
            return 0
        import csv
        count = 0
        with open(src_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                pid = r.get('id') or str(uuid.uuid4())
                if self.get_person(pid):
                    continue
                self.update_person(pid, r)
                count += 1
        return count


def get_db_adapter(backend: str = None):
    backend = backend or os.getenv('DATA_BACKEND', 'sqlite')
    backend = backend.lower()
    if backend == 'csv':
        return CSVAdapter()
    if backend == 'sqlite':
        return SQLiteAdapter()
    if backend == 'mongodb':
        return MongoAdapter()
    raise ValueError('Unknown DATA_BACKEND: ' + str(backend))
