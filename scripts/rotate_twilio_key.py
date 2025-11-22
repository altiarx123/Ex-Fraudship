"""
Rotate Twilio API key helper.

USAGE (PowerShell):
$env:TWILIO_ACCOUNT_SID='AC...'; $env:TWILIO_AUTH_TOKEN='your_auth_token'; python .\scripts\rotate_twilio_key.py --friendly "FraudShield key" --revoke OLD_KEY_SID

This script will:
- Create a new API Key (returns SID and SECRET) and print it.
- Optionally revoke an old key SID (if provided with --revoke).

IMPORTANT: The SECRET is only shown once. Save it to your `.env` immediately and revoke any compromised keys.

WARNING: Running this requires your Account SID and Auth Token. Do NOT paste those credentials into public chat.
"""

print("Twilio API key rotation logic removed. Update this script for Nexmo or other provider.")
