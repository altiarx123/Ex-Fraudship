#!/usr/bin/env bash
export SAFE_MODE=true
export SMS_PROVIDER=mock
python manage.py seed
streamlit run app.py
