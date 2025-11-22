# E-X FraudShield Instructions

This document explains how to run the application (safe defaults) and exercise the notification flow.

Prereqs
- Python 3.8+
- Optional: create a venv and install `pip install -r requirements.txt`

Quick start (recommended):

PowerShell / Bash:

```bash
export SAFE_MODE=true
export SMS_PROVIDER=mock
python manage.py seed
streamlit run app.py
```

Steps
1. Open the app in your browser (Streamlit prints the Local URL).
2. You should see a small `Location service: ACTIVE` badge at top-left. Toggle it in the Admin UI or via session state.
3. Go to the `Users` tab. Click `View` on a seeded user.
   - An audit event will be written and, because defaults are `SAFE_MODE=true` and `SMS_PROVIDER=mock`, a simulated notification will be appended to `logs/simulated_notifications.jsonl`.
   - The sidebar `Notifications` panel shows recent simulated messages.
4. Toggle consent off for the person and save, then `View` again — no notification will be attempted (audit will show `no_consent`).

Notes & safety
- Defaults are safe: `SAFE_MODE=true` and `SMS_PROVIDER=mock` to avoid sending real messages.
- To test real providers you must set `SAFE_MODE=false` and configure `SMS_PROVIDER` and provider credentials. Do NOT do this in public environments without consent.

Optional tests
- Run unit tests (they run without network):
```bash
pytest -q
```
