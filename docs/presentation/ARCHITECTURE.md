# FraudShield Architecture

## Overview
FraudShield is a Python-based system for monitoring, notifying, and auditing potential fraud-related events. It provides:
- Multiple entrypoints (`app.py`, `manage.py`, `run_app.py`, `start_fraudshield.bat`) for running the service.
- Integration modules in `integrations/` handling notifications, rate limiting, auditing, and database adapters.
- Data ingestion and migration scripts in `scripts/` for moving CSV datasets to JSONL and previewing or repairing notification data.
- A lightweight logging and audit trail stored in JSONL files under `logs/`.

## Core Components
| Component | Path | Responsibility |
|-----------|------|----------------|
| Web/App Entrypoints | `app.py`, `run_app.py`, `manage.py` | Start application / orchestration tasks |
| Bias Monitoring | `bias_monitoring.py` | Monitor and report bias metrics (e.g., model fairness) |
| Notification System | `integrations/notify_providers.py` | Send notifications via provider adapters |
| Rate Limiter | `integrations/rate_limiter.py` | Throttle outbound notification volume |
| Audit Trail | `integrations/audit.py` | Persist structured audit events to `logs/audit.jsonl` |
| Database Adapters | `integrations/db_adapters.py` | Abstract persistence / storage access |
| Migration Utilities | `scripts/migrate_csv_to_jsonl.py`, `scripts/migrate_to_jsonl.py` | Convert legacy CSV data to JSONL |
| Mock + Testing Utilities | `scripts/mock_notify.py`, tests in `tests/` | Simulate and validate notification flows |

## Data Flow (High-Level)
1. Incoming event or trigger occurs (manual script run or scheduled job).
2. Event is parsed and normalized.
3. Rate limiter validates throughput constraints.
4. Notification provider selected and invoked.
5. Audit entry appended to `logs/audit.jsonl`.
6. Bias metrics updated (optional, via `bias_monitoring.py`).

## Logging & Auditing
- Primary audit log: `logs/audit.jsonl` (append-only, structured JSON per line).
- Notification log (mock/simulated): `logs/simulated_notifications.jsonl`.
- Legacy backups: CSV / JSONL files at repo root (e.g., `fraudshield_logs.csv.bak`).

## Extensibility Points
- Add new notification channel: implement provider and register in `notify_providers.py`.
- Add storage backend: extend `db_adapters.py` with new adapter class/function.
- Enhance fairness metrics: expand `bias_monitoring.py` with new computations.

## Deployment Notes
- `Dockerfile` and `docker-compose.yml` enable containerized deployment.
- Environment configuration likely lives in `config.py` & related demo config.
- Ensure required secrets (e.g., Twilio keys) are rotated using `scripts/rotate_twilio_key.py`.

## Testing Strategy
- Targeted tests in `tests/` cover adapters and notification mock flow.
- Extend tests for new integrations before production use.

## Future Improvements (Suggested)
- Central configuration loader + validation schema.
- Unified CLI entrypoint replacing multiple starter scripts.
- Structured metrics endpoint for bias + throughput.
- Automated log rotation & archival.
