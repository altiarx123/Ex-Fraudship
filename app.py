import streamlit as st
import bias_monitoring  # added for Bias Monitoring tab integration
import user_consent_panel  # added for Consent Control tab integration
import reply_tracker  # added for Reply Tracker tab integration

# Provide aliases for Streamlit caching decorators. Use the real decorators
# when Streamlit is present; otherwise provide no-op fallbacks so the
# module can be imported and used in environments without Streamlit.
try:
    cache_data = st.cache_data
except Exception:
    def cache_data(func):
        return func
try:
    cache_resource = st.cache_resource
except Exception:
    def cache_resource(func):
        return func
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import shap
import time
import uuid
import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv
import config as cfg
from integrations.db_adapters import get_db_adapter
from integrations.notify_providers import get_notify_provider
from integrations.audit import log_audit_event
from integrations.rate_limiter import RateLimiter
import requests
try:
    from scripts.send_sms import send_via_textbelt, send_via_email_gateway
except Exception:
    import os
    def send_via_textbelt(phone, message, api_key=None):
        """
        Send SMS via Textbelt (https://textbelt.com/)
        Uses env TEXTBELT_KEY if available; falls back to default key 'textbelt'.
        Returns a dict with status and detail (response JSON or error).
        """
        key = api_key or os.getenv('TEXTBELT_KEY') or 'textbelt'
        try:
            import requests
        except Exception:
            return {"status": "failed", "detail": "requests_not_available"}
        try:
            resp = requests.post(
                "https://textbelt.com/text",
                data={"phone": str(phone), "message": str(message), "key": key},
                timeout=10
            )
            try:
                j = resp.json()
            except Exception:
                return {"status": "failed", "detail": f"textbelt_invalid_response:{resp.text}"}
            if j.get("success"):
                return {"status": "sent", "detail": j}
            else:
                # include response JSON for diagnostics
                return {"status": "failed", "detail": j}
        except Exception as e:
            return {"status": "failed", "detail": str(e)}

    def send_via_email_gateway(contact, message, smtp_host=None, smtp_port=None, smtp_user=None, smtp_pass=None):
        """
        Send message via SMTP to an email or email-to-sms gateway.
        If contact contains '@' -> treat as email.
        If contact is numeric and SMS_GATEWAY_DOMAIN env var is set -> construct phone@gateway_domain.
        Uses SMTP_* env vars if parameters not provided.
        Returns dict with status and detail.
        """
        try:
            import smtplib
            from email.message import EmailMessage
        except Exception:
            return {"status": "failed", "detail": "smtplib_not_available"}

        # use provided params or environment
        smtp_host = smtp_host or os.getenv("SMTP_HOST")
        smtp_port = int(smtp_port or os.getenv("SMTP_PORT") or 587)
        smtp_user = smtp_user or os.getenv("SMTP_USER")
        smtp_pass = smtp_pass or os.getenv("SMTP_PASS")
        from_addr = os.getenv("FROM_EMAIL") or smtp_user or "fraudshield@example.com"

        # determine destination: email or gateway
        dest = str(contact).strip()
        if "@" not in dest:
            gw = os.getenv("SMS_GATEWAY_DOMAIN")
            if gw:
                dest = f"{re.sub(r'[^0-9]', '', dest)}@{gw}"
            else:
                return {"status": "failed", "detail": "no_gateway_domain_and_contact_not_email"}

        if not smtp_host or not smtp_user or not smtp_pass:
            return {"status": "failed", "detail": "smtp_credentials_missing"}

        try:
            em = EmailMessage()
            em["Subject"] = "Fraud Alert"
            em["From"] = from_addr
            em["To"] = dest
            em.set_content(message)
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as s:
                try:
                    s.starttls()
                except Exception:
                    pass
                s.login(smtp_user, smtp_pass)
                s.send_message(em)
            return {"status": "sent", "detail": f"mailto:{dest}"}
        except Exception as e:
            return {"status": "failed", "detail": str(e)}

# External mock API and EmailJS verification integration removed.

# Initialize environment, page config, and adapters.
load_dotenv()
st.set_page_config(layout="wide", page_title="E-X FraudShield", initial_sidebar_state="collapsed")
st.markdown("""
<style>
[data-testid="stSidebar"] {display:none !important;}
[data-testid="collapsedControl"] {display:none !important;}
</style>
""", unsafe_allow_html=True)
db = get_db_adapter()
notify = get_notify_provider()
rate_limiter = RateLimiter(window_seconds=cfg.RATE_LIMIT_SECONDS)

# session state for location badge and simulated notifications
if 'location_active' not in st.session_state:
    st.session_state['location_active'] = True
if 'sim_messages_last' not in st.session_state:
    st.session_state['sim_messages_last'] = 0
if 'email_verified' not in st.session_state:
    st.session_state['email_verified'] = False
if 'email_verification_code' not in st.session_state:
    st.session_state['email_verification_code'] = None
if 'email_for_verification' not in st.session_state:
    st.session_state['email_for_verification'] = ""
# placeholder for location-service badge (updated later when privacy choices are known)
location_badge = st.empty()
# render a small pulsing location badge top-left when active
def _render_location_badge(active: bool):
    if not active:
        location_badge.markdown("", unsafe_allow_html=True)
        return
    html = """
    <div style='position:fixed;top:12px;left:12px;z-index:9999;padding:6px 10px;border-radius:6px;background:#0b5; color:#023; font-weight:600; box-shadow:0 2px 6px rgba(0,0,0,0.2);'>
      <span style='display:inline-block;width:10px;height:10px;margin-right:8px;border-radius:50%;background:#0a0;box-shadow:0 0 8px rgba(0,255,0,0.6);animation:pulse 1.6s infinite'></span>
      Location service: ACTIVE
    </div>
    <style>@keyframes pulse{0%{transform:scale(0.9);opacity:0.6}50%{transform:scale(1);opacity:1}100%{transform:scale(0.9);opacity:0.6}}</style>
    """
    location_badge.markdown(html, unsafe_allow_html=True)

# render initially
_render_location_badge(st.session_state.get('location_active', True))
LOG_CSV = "fraudshield_logs.csv"
LOG_JSONL = "fraudshield_logs.jsonl"
NOTIF_CSV = "fraudshield_logs_notifications.csv"
NOTIF_JSONL = "fraudshield_notifications.jsonl"
NOTIF_JSONL_LEGACY = "fraudshield_logs_notifications.jsonl"
REPLIES_CSV = "fraudshield_logs_replies.csv"
REPLIES_JSONL = "fraudshield_replies.jsonl"
REPLIES_JSONL_LEGACY = "fraudshield_logs_replies.jsonl"
@cache_data
def load_data():
    csv_path = "fraud_dataset-1.csv"
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        df.columns = [c.strip() for c in df.columns]
        for cand in ("is_fraud", "Is_Fraud", "isFraud", "fraud"):
            if cand in df.columns and cand != "Is_Fraud":
                df = df.rename(columns={cand: "Is_Fraud"})
                break
        if "Is_Fraud" not in df.columns and "is_fraud" in df.columns:
            df = df.rename(columns={"is_fraud": "Is_Fraud"})
        # ensure numeric types where possible
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col])
            except Exception:
                pass
        return df

    np.random.seed(42)
    n = 1000
    df = pd.DataFrame({
        "Amount": np.random.lognormal(mean=7, sigma=1.5, size=n),
        "Location_Change": np.random.randint(0, 2, size=n),
        "Time_Diff_Last_Tx": np.random.gamma(shape=2, scale=10, size=n),
        "Device_Change": np.random.randint(0, 2, size=n)
    })
    df["Is_Fraud"] = (
        (df["Amount"] > 1500) &
        (df["Location_Change"] == 1) &
        (df["Time_Diff_Last_Tx"] < 5)
    ).astype(int)
    df["Is_Fraud"] = df.apply(lambda r: 1 if np.random.rand() < 0.1 else r["Is_Fraud"], axis=1)
    return df
@cache_resource
#model traingng happens here
def train_model(df):
    x = df.drop("Is_Fraud", axis=1)
    y = df["Is_Fraud"]
    x_train, _, y_train, _ = train_test_split(x, y, test_size=0.3, random_state=42)
    model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    model.fit(x_train, y_train)
    explainer = shap.TreeExplainer(model)
    return model, explainer, x.columns.tolist()
def log_event(pred, prob, shap_vals, inp, transaction_id=None):
    # normalize numpy types to native python
    try:
        shap_list = [float(x) for x in list(shap_vals)]
    except Exception:
        shap_list = list(shap_vals)
    try:
        inp_list = [float(x) if isinstance(x, (int, float, np.floating, np.integer)) else x for x in list(inp)]
    except Exception:
        inp_list = list(inp)

    obj = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "transaction_id": transaction_id,
        "prediction": int(pred) if pred is not None else None,
        "probability": float(prob) if prob is not None else None,
        "shap_values": shap_list,
        "inputs": inp_list
    }
    # append to JSONL
    try:
        with open(LOG_JSONL, 'a', encoding='utf-8') as f:
            f.write(json.dumps(obj) + '\n')
    except Exception:
        # fallback to CSV if needed
        entry = pd.DataFrame([obj])
        if os.path.exists(LOG_CSV):
            entry.to_csv(LOG_CSV, mode="a", header=False, index=False)
        else:
            entry.to_csv(LOG_CSV, index=False)


def send_notification(method, contact, message, transaction_id=None):
    """Notification system disabled per user request; returns a disabled status without side effects."""
    return {"status": "disabled", "detail": "notification feature removed"}


def record_customer_reply(contact, reply):
    """Record a customer reply (YES/NO) to notifications."""
    try:
        # attempt to map this reply to the most recent notification for this contact
        tx_id = None
        # prefer JSONL notifications
        # prefer the new notifications JSONL, but fall back to legacy name if present
        notif_file_to_read = None
        if os.path.exists(NOTIF_JSONL):
            notif_file_to_read = NOTIF_JSONL
        elif os.path.exists(NOTIF_JSONL_LEGACY):
            notif_file_to_read = NOTIF_JSONL_LEGACY
        if notif_file_to_read:
            try:
                with open(notif_file_to_read, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                # iterate reversed to find most recent for contact
                for ln in reversed(lines):
                    try:
                        o = json.loads(ln)
                        if o.get('contact') == contact:
                            tx_id = o.get('transaction_id')
                            break
                    except Exception:
                        continue
            except Exception:
                pass
        else:
            # fallback to CSV
            notif_file = NOTIF_CSV
            if os.path.exists(notif_file):
                nd = pd.read_csv(notif_file)
                ndc = nd[nd['contact'] == contact]
                if not ndc.empty:
                    tx_id = ndc.sort_values('timestamp', ascending=False).iloc[0].get('transaction_id')

        note_obj = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "contact": contact,
            "transaction_id": tx_id,
            "reply": reply
        }
        try:
            # write to the new replies JSONL
            with open(REPLIES_JSONL, 'a', encoding='utf-8') as f:
                f.write(json.dumps(note_obj) + '\n')
            return {"status": "recorded", "detail": REPLIES_JSONL, "transaction_id": tx_id}
        except Exception:
            file = REPLIES_CSV
            note = pd.DataFrame([note_obj])
            if os.path.exists(file):
                note.to_csv(file, mode='a', header=False, index=False)
            else:
                note.to_csv(file, index=False)
            return {"status": "recorded", "detail": file, "transaction_id": tx_id}
    except Exception as e:
        return {"status": "failed", "detail": str(e)}
def generate_explanation(shap_vals, names, tx):
    # Generic explanation builder: list positively contributing features
    try:
        total = np.sum(shap_vals)
    except Exception:
        total = 0
    if total <= 0:
        return "Transaction appears normal based on available patterns."
    reasons = []
    for i, name in enumerate(names):
        try:
            val = tx.get(name, None) if isinstance(tx, dict) else None
        except Exception:
            val = None
        if shap_vals[i] > 0.01:
            if val is None:
                reasons.append(f"Feature '{name}' contributed to increased risk.")
            else:
                reasons.append(f"Feature '{name}' (value: {val}) increased fraud risk.")
    if not reasons:
        return "Multiple small risk indicators combined to increase suspicion."

    return "This transaction was flagged because:\n- " + "\n- ".join(reasons)
df = load_data()
model, explainer, feature_names = train_model(df)
expected = explainer.expected_value
tree_base = float(expected[1] if isinstance(expected, (list, np.ndarray)) and len(expected) > 1 else expected)
st.title("E-X FraudShield — Fraud Detection & Explainability")
st.markdown("---")
tab_names = ["Transaction Check", "Bias Monitoring", "AI Governance Logs", "Users", "Reply Tracker", "Consent Control"]
tabs = st.tabs(tab_names)
with tabs[0]:
    left, right = st.columns([1,2])
    with left:
        st.subheader("Transaction Inputs")
        inputs = {}
        privacy = {}
        def ask(label):
            return st.radio(f"Allow use of {label}?", ["Allow", "Deny"], horizontal=True)
        # build input widgets dynamically based on trained feature columns
        for feat in feature_names:
            # show sensible widget based on data type / unique values
            if feat not in df.columns:
                inputs[feat] = st.text_input(feat, "")
                privacy[feat] = ask(feat)
                continue
            col = df[feat]
            uniques = pd.unique(col.dropna())
            try:
                unique_set = set(np.unique(uniques))
            except Exception:
                unique_set = set()
            if unique_set.issubset({0,1}) and len(unique_set) <= 3:
                inputs[feat] = st.selectbox(feat, [0,1], index=0)
            else:
                # numeric-ish
                try:
                    minv = float(col.min())
                    maxv = float(col.max())
                    med = float(col.median())
                except Exception:
                    minv, maxv, med = 0.0, 100.0, 50.0
                # use slider for moderate ranges, number_input otherwise
                if maxv - minv <= 10000:
                    try:
                        inputs[feat] = st.slider(feat, min_value=minv, max_value=maxv, value=med)
                    except Exception:
                        inputs[feat] = st.number_input(feat, value=med)
                else:
                    inputs[feat] = st.number_input(feat, value=med)
            privacy[feat] = ask(feat)
        # Show an aesthetic indicator if a location service feature is allowed
        # Detect common location-related feature names (case-insensitive)
        location_keys = {"location", "location_change", "is_international", "locationchange", "location_changed"}
        loc_allowed = False
        for k, v in privacy.items():
            if any(lk in k.lower() for lk in location_keys):
                if v == "Allow":
                    loc_allowed = True
                    break
        if loc_allowed:
            # update the small fixed badge in the top-left instead of rendering the larger box inline
            location_badge.markdown(
                "<div style='position:fixed;top:12px;left:12px;z-index:9999;border:1px solid #2ecc71;background:#eafaf1;padding:6px 10px;border-radius:6px;font-size:12px;font-weight:600;'>"
                "<span style='color:#117a4b'>Location service active</span>"
                "</div>", unsafe_allow_html=True)
        else:
            # clear the badge if not allowed
            location_badge.markdown("", unsafe_allow_html=True)
        # simplified transaction check (notifications removed)
        st.markdown("---")
        if st.button("Check Transaction", type="primary"):
            # prepare input row honoring privacy choices
            inp = []
            for feat in feature_names:
                if privacy.get(feat) == "Allow":
                    val = inputs.get(feat)
                else:
                    # substitute dataset median or mode
                    if feat in df.columns:
                        try:
                            val = float(df[feat].median())
                        except Exception:
                            try:
                                val = df[feat].mode().iloc[0]
                            except Exception:
                                val = 0
                    else:
                        val = 0
                inp.append(val)
            feature_cols = feature_names
            row = pd.DataFrame([inp], columns=feature_cols)
            with st.spinner("Analyzing..."):
                time.sleep(1)
                prob = float(model.predict_proba(row)[0][1])
                pred = int(model.predict(row)[0])
                raw = explainer.shap_values(row)
                arr = np.array(raw, dtype=object)
                if isinstance(raw, list):
                    arr = raw[1] if len(raw) > 1 else raw[0]
                    arr = np.array(arr)
                if arr.ndim == 3:
                    arr = arr[1,0,:] if arr.shape[0] > 1 else arr[0,0,:]
                elif arr.ndim == 2:
                    arr = arr[0]
                arr = arr.astype(float).reshape(-1)
                if len(arr) < len(feature_cols):
                    tmp = np.zeros(len(feature_cols))
                    tmp[:len(arr)] = arr
                    arr = tmp
                shap_vals = arr[:len(feature_cols)]
                # generate transaction id and attempt notification if enabled and flagged
                tx_id = str(uuid.uuid4())
                st.session_state["res"] = {
                    "transaction_id": tx_id,
                    "shap": shap_vals,
                    "prob": prob,
                    "pred": pred,
                    "inp": inp,
                    "notif": None,
                }
                # log the decision (notification logging handled by send_notification when used)
                log_event(pred, prob, shap_vals, inp, transaction_id=tx_id)
        with right:
            if "res" in st.session_state:
                r = st.session_state["res"]
                if r["pred"] == 1:
                    st.error("High Fraud Risk")
                else:
                    st.success("Transaction Approved")
                st.write(f"Risk Probability: {r['prob']*100:.2f}%")
                expl = generate_explanation(r["shap"], feature_names, dict(zip(feature_names, r["inp"])) )
                st.subheader("Explanation")
                st.markdown(expl)
                st.subheader("SHAP Contributions")
                sdf = pd.DataFrame({"Feature": feature_names, "SHAP": np.round(r["shap"],4)})
                st.dataframe(sdf.sort_values("SHAP", ascending=False), width="stretch")
                # Notification & reply tracking removed.
with tabs[1]:
    # Delegate full rendering to the reusable module function.
    bias_monitoring.render_bias_monitoring_page()
with tabs[2]:
    st.header("AI Governance Logs")
    # show model decision logs
    # prefer JSONL logs
    if os.path.exists(LOG_JSONL):
        try:
            with open(LOG_JSONL, 'r', encoding='utf-8') as f:
                lines = [json.loads(l) for l in f if l.strip()]
            logs = pd.DataFrame(lines)
            st.subheader('Decision Logs (JSONL)')
            st.dataframe(logs)
        except Exception as e:
            st.error(f"Failed to parse `{LOG_JSONL}`: {e}")
            try:
                with open(LOG_JSONL, 'r', encoding='utf-8', errors='replace') as f:
                    sample = f.read(2000)
                st.code(sample)
            except Exception:
                st.warning('Could not read log file contents.')
    elif os.path.exists(LOG_CSV):
        try:
            logs = pd.read_csv(LOG_CSV)
            st.subheader('Decision Logs (CSV)')
            st.dataframe(logs)
        except Exception as e:
            st.error(f"Failed to parse `{LOG_CSV}`: {e}")
            try:
                with open(LOG_CSV, 'r', encoding='utf-8', errors='replace') as f:
                    sample = f.read(2000)
                st.code(sample)
            except Exception:
                st.warning('Could not read log file contents.')
    else:
        st.info("No decision logs available.")

    st.info('Notification feature disabled; notification logs removed.')

    # show replies
    # replies JSONL preferred
    # prefer new replies JSONL name, then legacy, then CSV
    replies_to_show = None
    if os.path.exists(REPLIES_JSONL):
        replies_to_show = REPLIES_JSONL
    elif os.path.exists(REPLIES_JSONL_LEGACY):
        replies_to_show = REPLIES_JSONL_LEGACY
    if replies_to_show:
        try:
            with open(replies_to_show, 'r', encoding='utf-8') as f:
                lines = [json.loads(l) for l in f if l.strip()]
            st.subheader('Customer Replies (JSONL)')
            st.dataframe(pd.DataFrame(lines))
        except Exception as e:
            st.error(f"Failed to parse replies file: {e}")
            try:
                with open(replies_to_show, 'r', encoding='utf-8', errors='replace') as f:
                    sample = f.read(2000)
                st.code(sample)
            except Exception:
                st.warning('Could not read replies file contents.')
    elif os.path.exists(REPLIES_CSV):
        try:
            st.subheader('Customer Replies (CSV)')
            reps = pd.read_csv(REPLIES_CSV)
            st.dataframe(reps)
        except Exception as e:
            st.error(f"Failed to parse replies file: {e}")
            try:
                with open(REPLIES_CSV, 'r', encoding='utf-8', errors='replace') as f:
                    sample = f.read(2000)
                st.code(sample)
            except Exception:
                st.warning('Could not read replies file contents.')
    else:
        st.info('No customer replies recorded yet.')

    # Test notification sender removed.

with tabs[3]:
    st.header('Users')
    # admin controls
    st.subheader('Admin')
    loc_active = st.checkbox('Location service active', value=st.session_state.get('location_active', True))
    if loc_active != st.session_state.get('location_active'):
        st.session_state['location_active'] = loc_active
        _render_location_badge(loc_active)
    st.caption('Toggle the top-left location badge (sample)')
    # list people from configured backend
    people = db.list_people()
    cols = st.columns([2,1,1,1])
    with cols[0]:
        st.subheader('Name')
    with cols[1]:
        st.subheader('Phone')
    with cols[2]:
        st.subheader('Consent')
    with cols[3]:
        st.subheader('Actions')
    for p in people:
        c0, c1, c2, c3 = st.columns([2,1,1,1])
        with c0:
            st.write(p.get('name') or p.get('id'))
        with c1:
            st.write(p.get('phone') or '')
        with c2:
            st.write('Yes' if p.get('consent') else 'No')
        with c3:
            if st.button('View', key=f"view_{p.get('id')}"):
                # show detail modal-like area
                st.session_state['view_person'] = p.get('id')
    # show detail view when selected
    if 'view_person' in st.session_state:
        pid = st.session_state['view_person']
        person = db.get_person(pid)
        if person:
            st.subheader('Person Detail')
            detail_row = {
                'ID': person.get('id'),
                'Name': person.get('name') or '',
                'Phone': person.get('phone') or '',
                'Telegram': person.get('telegram_id') or '',
                'Consent': 'Yes' if person.get('consent') else 'No',
                'Consent Timestamp': person.get('consent_ts') or '',
                'Last Notified': person.get('last_notified') or ''
            }
            st.dataframe(pd.DataFrame([detail_row]), width='stretch')
            consent = st.checkbox('Consent (notifications disabled globally)', value=bool(person.get('consent')))
            if st.button('Save Consent'):
                person['consent'] = int(bool(consent))
                person['consent_ts'] = time.strftime('%Y-%m-%d %H:%M:%S') if consent else None
                db.update_person(pid, person)
                st.success('Saved')
            # minimal audit log without notification attempt
            log_audit_event(actor='viewer', action='view', person_id=pid, notify_attempted=False, notify_sent_status='disabled', detail={})
            st.caption('Personal details displayed in structured table. Notification logic removed.')

with tabs[4]:
    reply_tracker.render_reply_tracker_page()
with tabs[5]:
    user_consent_panel.render_user_consent_panel()

# Sidebar removed: all former sidebar UI replaced by main-page components or omitted.
