# Demo playbook

1. Start backend:

```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

2. Seed data and run:

```bash
python backend/manage.py seed
```

3. Start frontend:

```bash
cd frontend
npm ci
npm run dev
```

4. Open the frontend at `http://localhost:3000` and test person views. The backend will log simulated notifications to `logs/simulated_notifications.jsonl` by default.
# E-X FraudShield Demo Instructions

This document explains how to run the demo (safe defaults) and exercise the notification flow.

Prereqs
- Python 3.8+
- Optional: create a venv and install `pip install -r requirements.txt`

Quick start (recommended):

PowerShell / Bash:

```bash
export DEMO_MODE=true
export SMS_PROVIDER=mock
python manage.py seed-demo
streamlit run app.py
```

Demo steps
1. Open the app in your browser (Streamlit prints the Local URL).
2. You should see a small `Location service: ACTIVE` badge at top-left. Toggle it in the Admin UI or via session state.
3. Go to the `Demo Users` tab. Click `View` on a seeded user.
   - An audit event will be written and, because defaults are `DEMO_MODE=true` and `SMS_PROVIDER=mock`, a simulated notification will be appended to `logs/simulated_notifications.jsonl`.
   - The sidebar `Demo Notifications` panel shows recent simulated messages.
4. Toggle consent off for the person and save, then `View` again — no notification will be attempted (audit will show `no_consent`).

Notes & safety
- Defaults are safe: `DEMO_MODE=true` and `SMS_PROVIDER=mock` to avoid sending real messages.
- To test real providers you must set `DEMO_MODE=false` and configure `SMS_PROVIDER` and provider credentials. Do NOT do this in public demos without consent.

Optional tests
- Run unit tests (they run without network):
```bash
pytest -q
```
