"""Simulate several transactions to populate decision logs for dynamic dashboard testing.

This script mirrors the model training and decision logging logic from `app.py` without
requiring the Streamlit UI. Run it before/after starting the Streamlit app to see
live metrics update.

Usage (PowerShell):
    python scripts/simulate_transactions.py --n 25 --seed 123

Outputs:
 - Appends decisions to `fraudshield_logs.jsonl` (or CSV fallback)
 - Prints aggregate metrics using `integrations.live_metrics`
"""
from __future__ import annotations
import argparse
import os
import sys
import json
import pathlib
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import shap
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from integrations.live_metrics import load_decision_logs, compute_metrics

LOG_JSONL = "fraudshield_logs.jsonl"
LOG_CSV = "fraudshield_logs.csv"

def build_dataset(n: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "Amount": rng.lognormal(mean=7, sigma=1.4, size=n),
        "Location_Change": rng.integers(0, 2, size=n),
        "Time_Diff_Last_Tx": rng.gamma(shape=2, scale=10, size=n),
        "Device_Change": rng.integers(0, 2, size=n),
    })
    base = (
        (df["Amount"] > 1500) &
        (df["Location_Change"] == 1) &
        (df["Time_Diff_Last_Tx"] < 5)
    ).astype(int)
    # inject some noise to mimic real world random pattern
    noise_mask = rng.random(n) < 0.08
    df["Is_Fraud"] = np.where(noise_mask, 1, base)
    return df

def train(df: pd.DataFrame):
    x = df.drop("Is_Fraud", axis=1)
    y = df["Is_Fraud"]
    x_train, _, y_train, _ = train_test_split(x, y, test_size=0.3, random_state=42)
    model = RandomForestClassifier(n_estimators=120, max_depth=6, random_state=42)
    model.fit(x_train, y_train)
    explainer = shap.TreeExplainer(model)
    return model, explainer, list(x.columns)

def append_log(obj):
    try:
        with open(LOG_JSONL, 'a', encoding='utf-8') as f:
            f.write(json.dumps(obj) + "\n")
    except Exception:
        entry = pd.DataFrame([obj])
        if os.path.exists(LOG_CSV):
            entry.to_csv(LOG_CSV, mode='a', header=False, index=False)
        else:
            entry.to_csv(LOG_CSV, index=False)

def simulate(model, explainer, feature_names, df_ref: pd.DataFrame, n: int, seed: int):
    rng = np.random.default_rng(seed + 99)
    for i in range(n):
        # sample plausible values from reference distribution
        row_vals = [
            float(rng.lognormal(mean=7, sigma=1.4)),                    # Amount
            int(rng.integers(0,2)),                                     # Location_Change
            float(rng.gamma(shape=2, scale=10)),                        # Time_Diff_Last_Tx
            int(rng.integers(0,2)),                                     # Device_Change
        ]
        row_df = pd.DataFrame([row_vals], columns=feature_names)
        prob = float(model.predict_proba(row_df)[0][1])
        pred = int(model.predict(row_df)[0])
        raw = explainer.shap_values(row_df)
        arr = raw[1] if isinstance(raw, list) and len(raw) > 1 else raw[0]
        arr = np.array(arr)
        if arr.ndim == 3:
            arr = arr[1,0,:] if arr.shape[0] > 1 else arr[0,0,:]
        elif arr.ndim == 2:
            arr = arr[0]
        shap_vals = [float(x) for x in arr.tolist()]
        obj = {
            "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            "transaction_id": f"SIM-{seed}-{i}",
            "prediction": pred,
            "probability": prob,
            "shap_values": shap_vals,
            "inputs": row_vals,
        }
        append_log(obj)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=25, help='Number of simulated decisions to append')
    ap.add_argument('--seed', type=int, default=123, help='Random seed')
    args = ap.parse_args()
    base_df = build_dataset(400, args.seed)
    model, explainer, feats = train(base_df)
    simulate(model, explainer, feats, base_df, args.n, args.seed)
    logs = load_decision_logs(limit=500)
    m = compute_metrics(logs)
    print("Simulation complete. Metrics:")
    print(json.dumps(m, indent=2))
    print(f"Log entries now: {len(logs)} (tail shown below)")
    print(logs.tail(5).to_string())

if __name__ == '__main__':
    main()
