#!/usr/bin/env bash
set -e
echo "Seeding backend data and starting services in safe mode..."
export SAFE_MODE=true
export SMS_PROVIDER=mock
python backend/manage.py seed
echo "Start backend: uvicorn backend.main:app --reload --port 8000"
echo "Start frontend: cd frontend && npm ci && npm run dev"
#!/usr/bin/env bash
export DEMO_MODE=true
export SMS_PROVIDER=mock
python manage.py seed-demo
streamlit run app.py
