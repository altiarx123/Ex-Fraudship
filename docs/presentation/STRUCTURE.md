# Repository Structure Overview

```
.
├── app.py                    # Main application entry (general runner)
├── manage.py                 # Management/utility entrypoint (tasks, admin ops)
├── run_app.py                # Alternate launcher (possibly development convenience)
├── start_fraudshield.bat     # Windows startup helper
├── Dockerfile                # Container build specification
├── docker-compose.yml        # Standard service orchestration
├── docker-compose.clean.yml  # Clean/minimal variant
├── config.py / config_demo.py# Configuration defaults and demo values
├── bias_monitoring.py        # Fairness / bias metrics logic
├── webhook_server.py         # (If used) endpoint for external callbacks
├── user_consent_panel.py     # User consent handling UI/logic (if interactive)
├── CRUD.py                   # Basic create/read/update/delete operations (data layer)
├── requirements.txt          # Primary dependency lock (source of truth)
├── requirements.example.txt  # Fallback or example dependency list
├── logs/                     # Runtime and audit logs (JSONL format)
│   ├── audit.jsonl
│   └── simulated_notifications.jsonl
├── integrations/             # Pluggable integration logic
│   ├── audit.py              # Append structured audit events
│   ├── db_adapters.py        # Storage abstraction layer
│   ├── notify_providers.py   # Notification dispatch providers
│   ├── rate_limiter.py       # Throughput / quota control
├── scripts/                  # Operational + maintenance utilities
│   ├── migrate_csv_to_jsonl.py  # Convert legacy CSV to JSONL
│   ├── migrate_to_jsonl.py      # General migration helper
│   ├── preview_dataset.py       # Inspect dataset contents
│   ├── mock_notify.py           # Simulate notification send
│   ├── send_sms.py              # Real SMS sending (requires creds)
│   ├── demo_sms.py              # Demo script for SMS path
│   ├── verify_migration.py      # Validate migration integrity
│   ├── repair_notifications.py  # Attempt fix of broken notification records
│   ├── rotate_twilio_key.py     # Security key rotation
├── data/                     # (If populated) raw or sample datasets
├── fraudshield_logs.*        # Legacy backup artifacts (CSV/JSONL)
├── tests/                    # Automated test suite
│   ├── test_db_adapters.py
│   ├── test_notify_mock.py
│   ├── test_send_sms.py
├── src/
│   └── fraudshield/          # (Package root) core library code
├── docs/
│   ├── USAGE.md              # Broader usage instructions
│   ├── DEMO.md               # Demonstration scenarios
│   └── presentation/         # New curated overview docs
│       ├── ARCHITECTURE.md
│       ├── QUICKSTART.md
│       └── STRUCTURE.md
```

## Key Conventions
- JSONL logs are append-only; each line is an independent JSON object.
- `scripts/` contains operational lifecycle tasks (migrate, rotate keys, repair).
- `integrations/` centralizes outward-facing or cross-cutting concerns (notifications, audit, rate limiting).
- Tests focus on reliability of adapters and notification mocking; extend here for new domains.

## Suggested Usage Flow
1. Install dependencies (`requirements.txt`).
2. Migrate legacy data if present.
3. Launch app via `app.py` or Docker.
4. Simulate notifications (`mock_notify.py`) before sending real provider messages.
5. Review `logs/` for audit trail and performance insights.
6. Enhance bias metrics by extending `bias_monitoring.py`.

## Adding New Features
- New Notification Channel: Add provider logic in `notify_providers.py` and configuration in `config.py`.
- New Storage Backend: Implement adapter in `db_adapters.py` and update tests.
- New Maintenance Task: Place script in `scripts/` with a concise name and docstring.

## Cleanliness & Presentation
This `presentation/` subfolder provides a quick onboarding path: start at `QUICKSTART.md`, then read `ARCHITECTURE.md` for conceptual context, finally reference this structure map while navigating code.

## Next Enhancements (Optional)
- Consolidate multiple entrypoints into a unified CLI.
- Introduce environment-based config loader (dev/stage/prod).
- Provide metrics endpoint (expose bias + throughput stats).
- Expand test coverage to rate limiting and audit integrity.
