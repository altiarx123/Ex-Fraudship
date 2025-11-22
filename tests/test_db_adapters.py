from integrations.db_adapters import SQLiteAdapter, CSVAdapter
import os


def test_sqlite_adapter_tmp(tmp_path):
    dbfile = tmp_path / 'people.db'
    adapter = SQLiteAdapter(path=str(dbfile))
    pid = 'p1'
    adapter.update_person(pid, {'name':'Alice','phone':'5551','consent':1})
    p = adapter.get_person(pid)
    assert p['name'] == 'Alice'


def test_csv_adapter_tmp(tmp_path):
    csvf = tmp_path / 'people.csv'
    adapter = CSVAdapter(path=str(csvf))
    pid = 'p2'
    adapter.update_person(pid, {'name':'Bob','phone':'5552','consent':1})
    p = adapter.get_person(pid)
    assert p['name'] == 'Bob'
