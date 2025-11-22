import os
import json
from typing import Dict, Any, List
import pandas as pd

DECISION_LOG_JSONL = "fraudshield_logs.jsonl"
DECISION_LOG_CSV = "fraudshield_logs.csv"
REPLIES_LOG_JSONL = "fraudshield_replies.jsonl"
REPLIES_LOG_JSONL_LEGACY = "fraudshield_logs_replies.jsonl"
REPLIES_LOG_CSV = "fraudshield_logs_replies.csv"

def load_decision_logs(limit: int | None = None) -> pd.DataFrame:
    """Load decision logs from JSONL (preferred) or CSV.
    Returns DataFrame with most recent rows (chronological).
    """
    rows: List[Dict[str, Any]] = []
    if os.path.exists(DECISION_LOG_JSONL):
        try:
            with open(DECISION_LOG_JSONL, 'r', encoding='utf-8') as f:
                for ln in f:
                    ln = ln.strip()
                    if not ln:
                        continue
                    try:
                        rows.append(json.loads(ln))
                    except Exception:
                        continue
        except Exception:
            pass
    elif os.path.exists(DECISION_LOG_CSV):
        try:
            df = pd.read_csv(DECISION_LOG_CSV)
            return df.tail(limit) if limit else df
        except Exception:
            return pd.DataFrame()
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if limit:
        df = df.tail(limit)
    return df.reset_index(drop=True)

def compute_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty:
        return {
            "total": 0,
            "fraud_count": 0,
            "fraud_rate": 0.0,
            "last_probability": None,
            "last_is_fraud": None
        }
    fraud_series = df.get("prediction")
    prob_series = df.get("probability")
    fraud_count = int(fraud_series.sum()) if fraud_series is not None else 0
    total = int(len(df))
    fraud_rate = float(fraud_count / total) if total else 0.0
    last_probability = float(prob_series.iloc[-1]) if prob_series is not None else None
    last_is_fraud = int(fraud_series.iloc[-1]) if fraud_series is not None else None
    return {
        "total": total,
        "fraud_count": fraud_count,
        "fraud_rate": fraud_rate,
        "last_probability": last_probability,
        "last_is_fraud": last_is_fraud
    }

def build_probability_timeseries(df: pd.DataFrame, limit: int = 200) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    sub = df.tail(limit).reset_index(drop=True)
    return pd.DataFrame({
        "Index": list(range(len(sub))),
        "Probability": sub.get("probability", [])
    })

def build_shap_aggregate(df: pd.DataFrame, limit: int = 400) -> pd.DataFrame:
    if df.empty or "shap_values" not in df.columns:
        return pd.DataFrame()
    sub = df.tail(limit)
    contrib: Dict[int, List[float]] = {}
    for _, row in sub.iterrows():
        vals = row.get("shap_values")
        if not isinstance(vals, list):
            continue
        for i, v in enumerate(vals):
            contrib.setdefault(i, []).append(abs(float(v)))
    agg = {i: (sum(vs)/len(vs)) for i, vs in contrib.items() if vs}
    df_out = pd.DataFrame({"FeatureIndex": list(agg.keys()), "MeanAbsSHAP": list(agg.values())})
    return df_out.sort_values("MeanAbsSHAP", ascending=False)

def load_reply_logs(limit: int | None = None) -> pd.DataFrame:
    """Load customer reply logs (YES/NO) from JSONL preferred, fallback CSV."""
    rows: List[Dict[str, Any]] = []
    target = None
    if os.path.exists(REPLIES_LOG_JSONL):
        target = REPLIES_LOG_JSONL
    elif os.path.exists(REPLIES_LOG_JSONL_LEGACY):
        target = REPLIES_LOG_JSONL_LEGACY
    if target:
        try:
            with open(target, 'r', encoding='utf-8') as f:
                for ln in f:
                    ln = ln.strip()
                    if not ln:
                        continue
                    try:
                        rows.append(json.loads(ln))
                    except Exception:
                        continue
        except Exception:
            pass
    elif os.path.exists(REPLIES_LOG_CSV):
        try:
            df = pd.read_csv(REPLIES_LOG_CSV)
            return df.tail(limit) if limit else df
        except Exception:
            return pd.DataFrame()
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if limit:
        df = df.tail(limit)
    return df.reset_index(drop=True)
