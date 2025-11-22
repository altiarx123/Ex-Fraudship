import os
from integrations.notify_providers import MockProvider, SIMULATED_FILE


def test_mock_does_not_network(tmp_path, monkeypatch):
    # ensure simulated file is in tmp path
    monkeypatch.setenv('SIMULATED_FILE', str(tmp_path / 'sim.jsonl'))
    # import provider and send
    p = MockProvider()
    res = p.send_notification({'id':'1','phone':'5551234'}, 'hi')
    assert res['status'] == 'mocked'
