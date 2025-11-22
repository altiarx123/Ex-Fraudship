"""FraudShield core package.

Aggregated imports for easier access in external code:
    from fraudshield import app, bias_monitoring

Currently modules remain at project root for backward compatibility.
They can be migrated into this package progressively without breaking existing paths.
"""

# Re-export selected top-level modules (lazy import pattern)
from importlib import import_module as _imp

__all__ = [
    "app",
    "bias_monitoring",
    "reply_tracker",
    "user_consent_panel",
    "webhook_server",
    "CRUD",
    "config",
]

def __getattr__(name):  # pragma: no cover
    if name in __all__:
        return _imp(name)
    raise AttributeError(f"module 'fraudshield' has no attribute {name}")
