# src Directory

This directory will house the reorganized Python package structure for E-X FraudShield.

Planned migration (non-breaking phased approach):
1. Move reusable modules into `src/fraudshield/`.
2. Update `app.py` and other scripts to use `from fraudshield import <module>` imports.
3. Retain legacy paths until confirmed stable, then delete originals.

Current aggregation lives in `fraudshield/__init__.py` with lazy re-export of top-level modules for backwards compatibility.

Next suggested steps:
- Move `bias_monitoring.py`, `reply_tracker.py`, `user_consent_panel.py` here.
- Adjust imports and run tests.
