"""Dynamic User Consent & Privacy Control Panel

Provides interactive consent management for data categories used in a banking fraud
detection context. Features:
- Toggles for data categories with persistent session state.
- Live summary table of consent states.
- Toast notifications on change events.
- Audit log in session_state['audit_log'] with timestamp, category, old/new values, source.
- Download audit log as CSV.
- Modal-like popup for requesting extra consent (Allow once / Always allow / Deny).
- Simulated model column filtering: blocked categories remove mapped features from input set.
- Displays synthetic sample data restricted to allowed (and one-time) columns.

Run:
    streamlit run user_consent_panel.py
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# -------------------------------------------------
# Configuration
# -------------------------------------------------
DATA_CATEGORIES = [
    'location',
    'device_info',
    'spending_history',
    'transaction_amount',
    'region',
    'age_group',
    'contact_details'
]
# Mapping from consent category to synthetic model feature columns
CATEGORY_FEATURE_MAP = {
    'location': ['location_change'],
    'device_info': ['device_change'],
    'spending_history': ['avg_spend_30d', 'txn_freq_7d'],
    'transaction_amount': ['amount'],
    'region': ['region'],
    'age_group': ['age_group'],
    'contact_details': ['contact_risk_score']
}
# Columns that would form the model baseline if fully allowed
ALL_BASE_FEATURES = [f for lst in CATEGORY_FEATURE_MAP.values() for f in lst]

# -------------------------------------------------
# Session State Initialization
# -------------------------------------------------
if 'consent' not in st.session_state:
    # Default policy: conservative allow only core transactional fields
    st.session_state['consent'] = {
        'location': False,
        'device_info': True,
        'spending_history': True,
        'transaction_amount': True,
        'region': True,
        'age_group': False,
        'contact_details': False,
    }
if 'audit_log' not in st.session_state:
    st.session_state.audit_log = []  # list of dicts
if 'consent_once' not in st.session_state:
    st.session_state.consent_once = set()  # categories allowed once
if 'show_request_modal' not in st.session_state:
    st.session_state.show_request_modal = False
if 'last_prediction_used_columns' not in st.session_state:
    st.session_state.last_prediction_used_columns = []

# -------------------------------------------------
# Helpers
# -------------------------------------------------

def log_audit_event(category: str, old: bool, new: bool, source: str, note: str = ''):
    st.session_state.audit_log.append({
        'timestamp': datetime.utcnow().isoformat(timespec='seconds'),
        'category': category,
        'old_value': 'Allowed' if old else 'Blocked',
        'new_value': 'Allowed' if new else 'Blocked',
        'source': source,
        'note': note,
    })


def effective_allowed_categories() -> set:
    # Combine permanent consent and one-time allowances
    consent_map = st.session_state.get('consent', {})
    allowed = {c for c, v in consent_map.items() if v}
    allowed |= st.session_state.consent_once
    return allowed


def compute_model_features() -> list:
    allowed_categories = effective_allowed_categories()
    used = []
    for cat in allowed_categories:
        used.extend(CATEGORY_FEATURE_MAP.get(cat, []))
    return sorted(used)


def build_synthetic_dataset(n: int = 50) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    data = {
        'location_change': rng.integers(0, 2, size=n),
        'device_change': rng.integers(0, 2, size=n),
        'avg_spend_30d': rng.normal(450, 120, size=n).round(2),
        'txn_freq_7d': rng.integers(0, 40, size=n),
        'amount': rng.lognormal(6.5, 1.0, size=n).round(2),
        'region': rng.choice(['North','South','East','West'], size=n),
        'age_group': rng.choice(['18-25','26-35','36-45','46-55','56+'], size=n),
        'contact_risk_score': rng.random(size=n).round(3),
        'label': rng.integers(0, 2, size=n),
    }
    return pd.DataFrame(data)


def render_consent_toggle(category: str):
    consent_map = st.session_state.get('consent', {})
    current = consent_map.get(category, False)
    new_val = st.toggle(f"{category.replace('_',' ').title()}", value=current, key=f"toggle_{category}")
    if new_val != current:
        consent_map[category] = new_val
        st.session_state['consent'] = consent_map
        log_audit_event(category, current, new_val, source='toggle')
        msg = f"{category.replace('_',' ').title()} access {'granted' if new_val else 'revoked'}"
        try:
            st.toast(msg)
        except Exception:
            st.info(msg)


def prediction_simulation():
    used_columns = compute_model_features()
    st.session_state.last_prediction_used_columns = used_columns
    df = build_synthetic_dataset()
    filtered_df = df[used_columns] if used_columns else pd.DataFrame({'no_features': []})
    st.subheader('Sample Data (Filtered by Consent)')
    if used_columns:
        st.dataframe(filtered_df.head(10), width='stretch')
    else:
        st.warning('No features available: all categories blocked.')
    st.caption(f"Model currently uses {len(used_columns)} / {len(ALL_BASE_FEATURES)} potential features.")
    # Consume one-time allowances after a simulated prediction
    if st.session_state.consent_once:
        consumed = list(st.session_state.consent_once)
        st.session_state.consent_once.clear()
        if consumed:
            try:
                st.toast(f"One-time consent consumed for: {', '.join(consumed)}")
            except Exception:
                st.info(f"One-time consent consumed for: {', '.join(consumed)}")
            for cat in consumed:
                log_audit_event(cat, True, False, source='allow_once_consumed', note='One-time use consumed')


def open_request_modal():
    st.session_state.show_request_modal = True


def close_request_modal():
    st.session_state.show_request_modal = False


def render_request_modal():
    st.markdown("""<div style='position:fixed;top:0;left:0;width:100%;height:100%;\n        background:rgba(0,0,0,0.45);z-index:1000;padding-top:10vh;'>""", unsafe_allow_html=True)
    box = st.container()
    with box:
        st.markdown("""<div style='margin:0 auto;background:#fff;padding:24px 28px;\n            width:520px;border-radius:12px;box-shadow:0 6px 22px rgba(0,0,0,0.25);'>""", unsafe_allow_html=True)
        st.subheader('Request Extra Consent')
        st.write('The AI detection engine requests temporary access to additional data to refine risk scoring for this transaction.')
        requested_categories = st.multiselect('Requested Categories', DATA_CATEGORIES, key='request_cats')
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button('Allow Once'):
                for cat in requested_categories:
                    consent_map = st.session_state.get('consent', {})
                    if cat not in consent_map or not consent_map[cat]:
                        st.session_state.consent_once.add(cat)
                        log_audit_event(cat, False, True, source='modal_allow_once')
                close_request_modal()
                try:
                    st.toast('Granted one-time access.')
                except Exception:
                    st.info('Granted one-time access.')
        with col_b:
            if st.button('Always Allow'):
                consent_map = st.session_state.get('consent', {})
                for cat in requested_categories:
                    prev = consent_map.get(cat, False)
                    consent_map[cat] = True
                    log_audit_event(cat, prev, True, source='modal_always')
                st.session_state['consent'] = consent_map
                close_request_modal()
                try:
                    st.toast('Permanent access granted.')
                except Exception:
                    st.info('Permanent access granted.')
        with col_c:
            if st.button('Deny'):
                consent_map = st.session_state.get('consent', {})
                for cat in requested_categories:
                    prev = consent_map.get(cat, False)
                    if prev:
                        consent_map[cat] = False
                        log_audit_event(cat, prev, False, source='modal_deny')
                st.session_state['consent'] = consent_map
                close_request_modal()
                try:
                    st.toast('Access denied.')
                except Exception:
                    st.info('Access denied.')
        st.button('Close', on_click=close_request_modal)
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------
# Layout
# -------------------------------------------------
def render_user_consent_panel():
    """Render the Dynamic User Consent & Privacy Control panel (for tab or standalone)."""
    # Defensive initialization in case module-level init didn't run (e.g. hot-reload or state reset)
    if 'consent' not in st.session_state:
        st.session_state.consent = {
            'location': False,
            'device_info': True,
            'spending_history': True,
            'transaction_amount': True,
            'region': True,
            'age_group': False,
            'contact_details': False,
        }
    if 'audit_log' not in st.session_state:
        st.session_state.audit_log = []
    if 'consent_once' not in st.session_state:
        st.session_state.consent_once = set()
    if 'show_request_modal' not in st.session_state:
        st.session_state.show_request_modal = False
    if 'last_prediction_used_columns' not in st.session_state:
        st.session_state.last_prediction_used_columns = []
    # Sidebar hidden globally by main app; no local CSS needed.
    st.title('Dynamic User Consent & Privacy Control')
    consent_col, status_col = st.columns([2,1])
    with consent_col:
        st.header('Consent Toggles')
        for cat in DATA_CATEGORIES:
            render_consent_toggle(cat)
        st.markdown('---')
        st.button('Simulate Prediction with Current Consent', on_click=prediction_simulation, type='primary')
        st.button('Request Extra Consent', on_click=open_request_modal)
    with status_col:
        st.header('Current Access Status')
        summary_rows = []
        effective = effective_allowed_categories()
        for cat in DATA_CATEGORIES:
            base = st.session_state.consent.get(cat, False)
            one_time = cat in st.session_state.consent_once
            effective_state = ('Allowed (Permanent)' if base else ('Allowed (Once)' if one_time else 'Blocked'))
            summary_rows.append({
                'Category': cat,
                'Permanent': 'Yes' if base else 'No',
                'One-Time': 'Yes' if one_time else 'No',
                'Effective Status': effective_state
            })
        summary_df = pd.DataFrame(summary_rows)
        st.dataframe(summary_df, width='stretch')
        st.subheader('Model Feature Usage')
        used_cols = compute_model_features()
        if used_cols:
            st.code('\n'.join(used_cols))
        else:
            st.warning('No columns available to model.')
    st.markdown('---')
    st.header('Audit Log')
    if st.session_state.audit_log:
        audit_df = pd.DataFrame(st.session_state.audit_log)
        st.dataframe(audit_df, width='stretch')
        csv_bytes = audit_df.to_csv(index=False).encode('utf-8')
        st.download_button('Download Audit Log CSV', data=csv_bytes, file_name='consent_audit_log.csv', mime='text/csv')
    else:
        st.info('No consent change events recorded yet.')
    if st.session_state.show_request_modal:
        render_request_modal()
    st.header('Data Request Popup')
    st.write('Use the "Request Extra Consent" button above to open a modal asking users for temporary or permanent access to additional data categories required for a specific transaction risk evaluation.')
    if st.session_state.last_prediction_used_columns:
        st.subheader('Last Prediction Used Columns')
        st.code('\n'.join(st.session_state.last_prediction_used_columns))
    st.caption('Consent preferences persist via session_state across navigation within this running app instance.')

if __name__ == '__main__':
    st.set_page_config(page_title='User Consent Control', layout='wide')
    render_user_consent_panel()
