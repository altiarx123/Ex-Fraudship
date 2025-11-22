# E-X FraudShield — React + FastAPI Separation

This branch scaffolds a React (Vite + TypeScript + Tailwind) frontend and a FastAPI backend that wrap the existing Python business logic.

Safe defaults: `SAFE_MODE=true`, `SMS_PROVIDER=mock`, `DATA_BACKEND=sqlite` — no real SMS is sent by default.

Project layout
```

See `DOCKER-SETUP.md` for Docker build and run instructions (includes `docker build`, `docker run -p 8501:8501`, and `docker-compose up`).
/feature/react-frontend-separation
├─ frontend/       # React + Vite app (TypeScript + Tailwind)
├─ backend/        # FastAPI backend wrappers and manage scripts
├─ integrations/   # existing business logic (re-used)
├─ docs/
├─ docker-compose.yml
├─ .env.example
├─ README.md
```

Quick start (local dev)

1. Backend (local python):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

2. Frontend (local):

```bash
cd frontend
npm ci
npm run dev
```

Mock backend (if you don't want to run the Python backend):

```powershell
cd backend_mock
npm install
npm start
```

Use the mock backend for local testing of SMS/email flows.

3. Docker-compose (full stack):

```bash
docker compose up --build
```

Notes about Docker setup
- The `backend` service uses Python 3.11 (Dockerfile in `backend/`) to avoid local build issues on Windows with newer Python releases.
- The `mock-backend` service runs `backend_mock/server.js` (Node) and is exposed on container port 8000 (mapped to host 8001 in compose) so you can run either the mock or real backend.

Running locally without Docker
- If you prefer not to use Docker, the `backend_mock` is the fastest way to test the front-end. Start it with:

```powershell
cd backend_mock
npm install
npm start
```

Then start the frontend dev server from the `frontend` folder:

```powershell
cd frontend
npm install --legacy-peer-deps
npm run dev
```

Running the Python backend (optional)
- If you want the Python backend (recommended for production-like behavior) use the Docker compose stack or create a Python 3.11 venv and install `backend/requirements.txt`.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```


How this was mapped
- Existing `integrations/` modules at repo root are re-used by `backend/main.py` via imports. Files preserved.
- Backend endpoints mirror the prior Streamlit interactions (list persons, view person, consent toggle, audit, notifications).
- WebSocket endpoint `/ws` broadcasts `audit.new` events to connected clients.

Files created (high level)
- `backend/main.py` — FastAPI app exposing REST + WebSocket wrappers.
- `backend/requirements.txt`, `backend/Dockerfile`, `backend/manage.py`.
- `frontend/` — Vite app skeleton, Tailwind, basic components and pages.
- `docker-compose.yml`, top-level `.env.example`, `README.md`, `docs/USAGE.md`.

Notes and manual adjustments
- Streamlit UI logic was not deleted. Instead, business logic in `integrations/` was reused. If you have Streamlit-specific UI code, review `app.py` for any UI-only calls that cannot run in backend — those were left intact.
- You may need to tune CORS (environment `FRONTEND_URL`) for production.

Next steps
- Flesh out React components, add tests, and extend the FastAPI endpoints to return richer data shapes as needed.
# E-X FraudShield – Ethical, Explainable & Customer-Centric Fraud Detection System

**Tagline:**
“Making fraud detection transparent, fair, and accountable — because trust is the new currency.”

## Objective

To create an AI-based fraud detection system that not only catches fraud but also explains its decisions clearly, respects user privacy, and builds trust between customers and banks.

---

In today’s digital world, banks depend heavily on Artificial Intelligence for tasks like fraud detection, credit evaluation, and customer personalization. While this makes financial operations faster and smarter, it has also created a serious concern — a lack of understanding and trust. Most customers have no idea how or why an AI system marks a transaction as suspicious or rejects a loan request. When money is involved, this lack of clarity often turns into frustration, and frustration slowly grows into distrust.

E-X FraudShield was born from this real and rising problem. We wanted to design a fraud detection system that goes beyond accuracy and security — one that also values transparency, fairness, and human understanding. Our goal is simple: to make AI decisions in banking as easy to understand as human reasoning.

Unlike traditional “black box” systems, E-X FraudShield works like a “glass box” — open, clear, and honest. When a transaction is flagged, the user instantly receives a simple explanation, such as:

> “This transaction was marked risky because it came from a new location and was higher than your normal spending.”


This small but powerful step changes everything. Instead of feeling blamed or confused, customers feel informed and in control.

Another highlight of our system is the Dynamic Privacy Panel. In most AI systems, users have no clue how much personal data is being used. E-X FraudShield changes that. The panel allows customers to choose which data — like location, device type, or spending pattern — the system can access. If the AI ever needs additional data, it sends a real-time alert asking for user consent. This gives people a sense of ownership and confidence over their personal information.

For banks and regulators, we developed a Responsible AI Governance Dashboard. It logs every AI decision, version details, factors influencing outcomes, and fairness metrics. This not only ensures compliance with ethical AI standards but also provides full transparency to auditors and governing bodies.

Behind its simplicity, E-X FraudShield runs on a powerful ethical AI engine.
Technically, it uses machine learning algorithms like Random Forest combined with SHAP-based interpretability for explainable results. Built using Python and a Streamlit-based dashboard, it delivers real-time transparency, bias detection, and performance reports. Built-in bias monitoring ensures equal treatment for all users, automatically alerting teams if any unfair trend is detected.

In short, E-X FraudShield transforms fraud detection from a mysterious “black box” into an understandable “glass box.” It blends ethics and innovation to protect users’ money while building trust.

E-X FraudShield doesn’t just detect fraud — it builds trust. It’s proof that in the future of banking, transparency and ethics can be as powerful as technology itself.

## SMS providers and setup

The project supports three notification SMS paths (tried in order):

1. Twilio (preferred for production)
2. Textbelt (quick free/low-volume testing)
3. Email-to-SMS (SMTP) fallback — send email to `digits@carrier-gateway` (e.g. `15551234567@vtext.com`)

Environment variables

- Twilio (optional):
  - `TWILIO_SID` — Twilio account SID
  - `TWILIO_TOKEN` — Twilio auth token
  - `TWILIO_FROM` — Twilio phone number to send from (E.164 format)

- Textbelt (optional):
  - `TEXTBELT_API_KEY` — Textbelt API key (default `textbelt` for very limited free use)

- Email-to-SMS (optional fallback):
  - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`
  - `FROM_EMAIL` (optional) — email sender address
  - `SMS_FALLBACK_DOMAIN` — carrier gateway domain (e.g. `vtext.com`, `txt.att.net`)

Testing locally

- The repo includes `scripts/demo_sms.py` which simulates Textbelt and SMTP sends without network calls and shows the fallback behavior. Run:

```bash
python scripts/demo_sms.py
```

- To try real sends, set the appropriate environment variables and use the Streamlit UI's "Send Test Notification" or call the helper functions from the Python REPL.

Notes

- Textbelt free key is strictly rate-limited. For production use Twilio, Vonage, MessageBird, or a paid Textbelt plan.
- Email-to-SMS depends on carrier gateways and may truncate messages.
- For proper phone formatting, the project uses `phonenumbers` if available; otherwise it strips to digits as a fallback.
