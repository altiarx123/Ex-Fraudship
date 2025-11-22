# FraudShield Quickstart

## 1. Prerequisites
- Python 3.9+ (confirm via `python --version`)
- (Optional) Docker & Docker Compose for container deployment

## 2. Clone & Enter
```powershell
git clone <your-fork-or-repo-url> fraudshield; cd fraudshield
```

## 3. Install Dependencies
Use the provided requirements file:
```powershell
pip install -r requirements.txt
```
If unavailable, fall back to `requirements.example.txt`:
```powershell
pip install -r requirements.example.txt
```

## 4. Run the Application
Several entry options exist:
```powershell
python app.py
python run_app.py
python manage.py  # if it provides management commands
```
For Windows helper scripts:
```powershell
./start_fraudshield.bat
```

## 5. Run in Docker
```powershell
docker compose up --build
```
For a clean variant:
```powershell
docker compose -f docker-compose.clean.yml up --build
```

## 6. Migrate / Prepare Data
Convert legacy CSV notification data to JSONL:
```powershell
python scripts/migrate_csv_to_jsonl.py
# or
python scripts/migrate_to_jsonl.py
```
Preview dataset:
```powershell
python scripts/preview_dataset.py
```

## 7. Send / Mock Notifications
Simulate a notification flow:
```powershell
python scripts/mock_notify.py
```
Send SMS (requires valid provider credentials):
```powershell
python scripts/send_sms.py
```

## 8. Rotate Keys (Security)
```powershell
python scripts/rotate_twilio_key.py
```

## 9. Run Tests
```powershell
pytest -q
```
Target a single test module:
```powershell
pytest tests/test_notify_mock.py -q
```

## 10. Logs & Monitoring
- Audit log: `logs/audit.jsonl`
- Simulated notifications: `logs/simulated_notifications.jsonl`
- Bias monitoring: `bias_monitoring.py` (extend for additional metrics)

## 11. Next Steps
- Explore `integrations/` directory for rate limiting & provider logic.
- Review `ARCHITECTURE.md` for conceptual overview.
- Use `STRUCTURE.md` (below) to orient new contributors.

## 12. Troubleshooting
| Issue | Suggestion |
|-------|------------|
| Missing dependency | Re-run `pip install -r requirements.txt` |
| Import errors | Ensure working directory is project root when running scripts |
| Credential failures | Verify environment variables / secrets before running provider scripts |
| Docker build fails | Clear cache: `docker compose build --no-cache` |

Enjoy building with FraudShield!
