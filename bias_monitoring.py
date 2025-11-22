
"""
Bias Monitoring Dashboard for Fraud Detection

This Streamlit app section provides:
- Dataset loading (attempts given .rar path, falls back to synthetic generation)
- Metrics by demographic groups (gender, region)
- Visual insights: prediction rate bar chart, confusion matrix heatmap, recall gap trend
- Bias Gap Calculator for selected metric and groups
- Before/After Bias Mitigation toggle (simulated via upsampling + targeted false negative flips)
- Explanatory panel on Demographic Parity & Equalized Odds
- Recommendations section based on observed metric gaps

Columns enforced: ['gender','age_group','region','actual_label','predicted_label','model_score','timestamp']

Libraries: pandas, numpy, scikit-learn, streamlit, plotly
"""
import os
import random
import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score, confusion_matrix
import plotly.express as px
import plotly.graph_objects as go

# -------------------------------------------------
# Configuration / Constants
# -------------------------------------------------
DATASET_RAR_PATH = '/mnt/data/e1bffd62-235c-44d4-b577-def2f735d020.rar'
REQUIRED_COLUMNS = ['gender','age_group','region','actual_label','predicted_label','model_score','timestamp']
GROUP_KEYS = ['gender', 'region']
BIAS_THRESHOLD = 0.10
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# -------------------------------------------------
# Utility Functions
# -------------------------------------------------

def try_load_dataset() -> pd.DataFrame:
    """Attempt to load dataset from the given .rar path.
    Since .rar extraction requires external libs not allowed, fallback if not usable.
    """
    if os.path.exists(DATASET_RAR_PATH):
        # Placeholder: cannot parse .rar with allowed libs; returning synthetic instead
        st.warning('RAR file detected but unsupported for direct read with allowed libraries; using synthetic dataset.')
    return generate_synthetic_dataset()


def generate_synthetic_dataset(n: int = 1500) -> pd.DataFrame:
    """Generate a synthetic fraud-like dataset with required columns."""
    genders = ['Male', 'Female']
    regions = ['North', 'South', 'East', 'West']
    age_groups = ['18-25','26-35','36-45','46-55','56+']

    # Simulate time over last 30 days
    base_date = datetime.utcnow() - timedelta(days=30)
    timestamps = [base_date + timedelta(minutes= i * (30)) for i in range(n)]

    df = pd.DataFrame({
        'gender': np.random.choice(genders, size=n, p=[0.55, 0.45]),
        'region': np.random.choice(regions, size=n),
        'age_group': np.random.choice(age_groups, size=n),
        'actual_label': np.random.binomial(1, 0.35, size=n),  # true fraud about 35%
        'model_score': np.random.rand(n)
    })

    # Simulate thresholding with slight demographic variance
    # Adjust score bias: e.g., regional variation
    region_bias = {r: (0.02 * i) for i, r in enumerate(regions)}
    gender_bias = {'Male': 0.0, 'Female': 0.03}

    adjusted_score = []
    for idx, row in df.iterrows():
        s = row['model_score'] + region_bias[row['region']] + gender_bias[row['gender']]
        adjusted_score.append(min(max(s, 0.0), 1.0))
    df['model_score'] = adjusted_score

    # Predicted label by threshold (0.5)
    df['predicted_label'] = (df['model_score'] >= 0.5).astype(int)
    df['timestamp'] = timestamps

    return df[REQUIRED_COLUMNS]


def compute_group_metrics(df: pd.DataFrame, group_key: str) -> pd.DataFrame:
    """Compute classification metrics per group."""
    records = []
    for group_value, sub in df.groupby(group_key):
        y_true = sub['actual_label']
        y_pred = sub['predicted_label']
        support = len(sub)
        if support == 0:
            continue
        # Handle edge cases gracefully
        try:
            precision = precision_score(y_true, y_pred, zero_division=0)
            recall = recall_score(y_true, y_pred, zero_division=0)
            f1 = f1_score(y_true, y_pred, zero_division=0)
            accuracy = accuracy_score(y_true, y_pred)
        except Exception:
            precision = recall = f1 = accuracy = 0.0
        records.append({
            group_key: group_value,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'support': support
        })
    return pd.DataFrame(records)


def build_prediction_rate_table(df: pd.DataFrame, group_key: str) -> pd.DataFrame:
    rates = df.groupby(group_key).agg(
        predicted_positive=('predicted_label', 'sum'),
        total=('predicted_label', 'count')
    )
    rates['prediction_rate_%'] = 100 * rates['predicted_positive'] / rates['total']
    return rates.reset_index()


def compute_daily_recall(df: pd.DataFrame, group_key: str, group_value: str) -> pd.DataFrame:
    sub = df[df[group_key] == group_value].copy()
    if sub.empty:
        return pd.DataFrame(columns=['date','recall'])
    sub['date'] = pd.to_datetime(sub['timestamp']).dt.date
    rows = []
    for d, day_sub in sub.groupby('date'):
        y_true = day_sub['actual_label']
        y_pred = day_sub['predicted_label']
        r = recall_score(y_true, y_pred, zero_division=0)
        rows.append({'date': d, 'recall': r})
    return pd.DataFrame(rows).sort_values('date')


def mitigate_bias(df: pd.DataFrame) -> pd.DataFrame:
    """Simulate bias mitigation via upsampling minority groups and selective FN correction."""
    balanced = df.copy()
    for key in GROUP_KEYS:
        groups = balanced.groupby(key)
        max_count = groups.size().max()
        augmented_parts = []
        for gv, sub in groups:
            if len(sub) < max_count:
                # Upsample with replacement
                extra = sub.sample(max_count - len(sub), replace=True, random_state=RANDOM_SEED)
                augmented_parts.append(pd.concat([sub, extra], ignore_index=True))
            else:
                augmented_parts.append(sub)
        balanced = pd.concat(augmented_parts, ignore_index=True)

    # Targeted false negative flips to simulate recall improvement
    for key in GROUP_KEYS:
        metrics = compute_group_metrics(balanced, key)
        max_recall = metrics['recall'].max()
        low_groups = metrics[metrics['recall'] < max_recall * 0.95][key].tolist()
        if not low_groups:
            continue
        for gv in low_groups:
            mask_fn = (
                (balanced[key] == gv) &
                (balanced['actual_label'] == 1) &
                (balanced['predicted_label'] == 0)
            )
            fn_indices = balanced[mask_fn].index.tolist()
            # Flip up to 20% of FN to positive
            k = int(len(fn_indices) * 0.2)
            to_flip = random.sample(fn_indices, k) if k > 0 else []
            balanced.loc[to_flip, 'predicted_label'] = 1
    return balanced


def confusion_matrix_figure(df: pd.DataFrame, group_key: str, group_value: str):
    sub = df[df[group_key] == group_value]
    if sub.empty:
        return go.Figure()
    y_true = sub['actual_label']
    y_pred = sub['predicted_label']
    cm = confusion_matrix(y_true, y_pred, labels=[0,1])
    z = cm.tolist()
    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=['Pred 0','Pred 1'],
        y=['Actual 0','Actual 1'],
        colorscale='Blues',
        showscale=True
    ))
    fig.update_layout(title=f'Confusion Matrix: {group_key} = {group_value}', xaxis_title='Predicted', yaxis_title='Actual')
    # Annotate counts
    annotations = []
    for i in range(len(z)):
        for j in range(len(z[0])):
            annotations.append(dict(showarrow=False, text=str(z[i][j]), x=['Pred 0','Pred 1'][j], y=['Actual 0','Actual 1'][i]))
    fig.update_layout(annotations=annotations)
    return fig


def recommendation_insights(metrics_gender: pd.DataFrame, metrics_region: pd.DataFrame) -> list:
    recs = []
    # Identify biggest recall gap
    if not metrics_gender.empty:
        rgap = metrics_gender['recall'].max() - metrics_gender['recall'].min()
        if rgap > BIAS_THRESHOLD:
            recs.append(f'Recall gap across gender = {rgap:.2f}. Consider threshold tuning or targeted feature review.')
    if not metrics_region.empty:
        rgap_r = metrics_region['recall'].max() - metrics_region['recall'].min()
        if rgap_r > BIAS_THRESHOLD:
            recs.append(f'Recall gap across regions = {rgap_r:.2f}. Investigate regional data quality or sampling.')
    if not recs:
        recs.append('No major gaps detected. Continue monitoring and periodic auditing.')
    # Generic suggestions
    recs.append('Implement periodic fairness evaluation pipeline (daily/weekly).')
    recs.append('Consider threshold calibration per demographic only if policy allows.')
    recs.append('Validate upstream data collection for underrepresented segments.')
    return recs

def render_bias_monitoring_page():
    """Render the full Bias Monitoring Dashboard (callable for tab or standalone use)."""
    # Session State Initialization
    if 'original_df' not in st.session_state:
        st.session_state.original_df = try_load_dataset()
    if 'mitigated_df' not in st.session_state:
        st.session_state.mitigated_df = mitigate_bias(st.session_state.original_df)
    if 'use_after' not in st.session_state:
        st.session_state.use_after = False
    # Controls Panel (formerly sidebar)
    with st.expander('Controls', expanded=True):
        st.checkbox('Use After Mitigation Dataset', value=st.session_state.use_after, key='use_after')
        active_df = st.session_state.mitigated_df if st.session_state.use_after else st.session_state.original_df
        metric_choice = st.selectbox('Bias Gap Metric', ['precision','recall','f1'], key='bm_metric_choice')
        comparison_dimension = st.selectbox('Comparison Dimension', GROUP_KEYS, key='bm_comparison_dim')
        unique_groups = sorted(active_df[comparison_dimension].unique())
        if len(unique_groups) >= 2:
            group_a = st.selectbox('Group A', unique_groups, index=0, key='bm_group_a')
            group_b = st.selectbox('Group B', unique_groups, index=1, key='bm_group_b')
        else:
            group_a = group_b = unique_groups[0]
        cm_dimension = st.selectbox('Confusion Matrix Dimension', GROUP_KEYS, key='bm_cm_dim')
        cm_group_value = st.selectbox('Group for Confusion Matrix', sorted(active_df[cm_dimension].unique()), key='bm_cm_group')
        trend_dimension = st.selectbox('Trend Gap Dimension', GROUP_KEYS, index=0, key='bm_trend_dim')
        trend_groups = sorted(active_df[trend_dimension].unique())
        if len(trend_groups) >= 2:
            trend_group_a = st.selectbox('Trend Group A', trend_groups, index=0, key='bm_trend_a')
            trend_group_b = st.selectbox('Trend Group B', trend_groups, index=1, key='bm_trend_b')
        else:
            trend_group_a = trend_group_b = trend_groups[0]

    # Title & Overview
    st.title('Bias Monitoring Dashboard')
    st.caption('Monitoring model performance across demographic groups for fairness and stability.')

    st.header('Overview')
    st.write('''This dashboard surfaces performance metrics across demographic segments (gender, region) to help detect and monitor potential bias in fraud detection outcomes. It supports before/after mitigation comparison, provides gap analytics, and offers recommendations for ongoing fairness governance.''')

    with st.expander('Fairness Concepts Explained'):
        st.markdown('**Demographic Parity**: A condition where the model predicts positive outcomes at similar rates across demographic groups (e.g., genders). It focuses on equal selection rates regardless of actual outcomes.\n\n' \
                    '**Equalized Odds**: A stricter condition requiring that error rates (false positive and false negative rates) are similar across groups. It emphasizes equitable performance conditioned on the true label.\n\n' \
                    'This dashboard shows comparative metrics, prediction rates, and recall gap trends to approximate signals relevant to these fairness notions.')

    with st.expander('Real-Time Alerting Explained'):
        st.markdown("""**Real-Time Bias Alerts**\n\nIn a production setting the monitoring service continuously ingests model predictions and recent ground-truth confirmations, updating rolling fairness aggregates (prediction rate, false positive rate, false negative rate, recall, precision) for each protected group. These aggregates are compared against governance thresholds stored alongside the dataset or in a configuration repository. When abnormal or biased patterns emerge an alert object is emitted and surfaced here.\n\n**Example Trigger Conditions**\n- Prediction imbalance: one group receives a disproportionately high positive flag rate versus baseline.\n- Demographic parity violation: absolute difference in positive prediction rates exceeds the allowed gap (e.g., > 0.10).\n- Equalized odds deviation: divergence in false negative or false positive rates beyond tolerance.\n- Sudden drift: sharp change in recall/precision or score distribution for a group.\n- Stability breach: bias score (normalized metric gap) crosses a critical threshold.\n\n**Alert Payload Fields**\n| Field | Description |\n|-------|-------------|\n| `timestamp` | UTC time alert generated |\n| `group_type` | Dimension (gender, region, etc.) |\n| `group_value` | Specific group impacted |\n| `bias_score` | Scalar severity measure (e.g., normalized gap) |\n| `violation_type` | Category (`prediction_imbalance`, `demographic_parity`, `drift`) |\n| `metric_snapshot` | Key metrics at alert time (rates, counts) |\n| `threshold` | Configured fairness limit exceeded |\n| `recommended_actions` | Automated remediation suggestions |\n\n**Lifecycle**\n1. Stream predictions & outcomes into short rolling window.\n2. Recompute fairness metrics per group (rates, gaps, drift tests).\n3. Compare gaps / drift statistics to stored thresholds.\n4. Generate and persist alert payload if violation detected.\n5. Surface alert in dashboard & log for audit.\n6. Provide recommended mitigation (e.g., threshold recalibration, data quality review, targeted reweighting).\n\nThe current demo focuses on static metric views; real-time alert objects would be appended as they are produced by the live monitoring backend."""
        )

    # Metrics by Group
    st.header('Metrics by Group')
    metrics_gender = compute_group_metrics(active_df, 'gender')
    metrics_region = compute_group_metrics(active_df, 'region')

    st.subheader('By Gender')
    st.dataframe(metrics_gender, width='stretch')

    st.subheader('By Region')
    st.dataframe(metrics_region, width='stretch')

    # Visual Insights
    st.header('Visual Insights')

    # Prediction Rate Bar Chart
    st.subheader('Prediction Rate (Predicted Positive %)')
    rate_dimension = st.selectbox('Prediction Rate Grouping', GROUP_KEYS, key='rate_dim')
    rate_table = build_prediction_rate_table(active_df, rate_dimension)
    fig_rate = px.bar(rate_table, x=rate_dimension, y='prediction_rate_%', color=rate_dimension, title='Prediction Rate % by Group', text='prediction_rate_%')
    fig_rate.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    fig_rate.update_layout(yaxis_title='Prediction Rate (%)', xaxis_title=rate_dimension)
    st.plotly_chart(fig_rate, use_container_width=True)

    # Confusion Matrix
    st.subheader('Confusion Matrix Heatmap')
    fig_cm = confusion_matrix_figure(active_df, cm_dimension, cm_group_value)
    st.plotly_chart(fig_cm, use_container_width=True)

    # Recall Gap Trend
    st.subheader('Recall Gap Trend Over Time')
    recall_a = compute_daily_recall(active_df, trend_dimension, trend_group_a)
    recall_b = compute_daily_recall(active_df, trend_dimension, trend_group_b)
    recall_a.rename(columns={'recall': f'recall_{trend_group_a}'}, inplace=True)
    recall_b.rename(columns={'recall': f'recall_{trend_group_b}'}, inplace=True)
    trend_df = pd.merge(recall_a, recall_b, on='date', how='outer').sort_values('date')
    if not trend_df.empty:
        trend_df['recall_gap'] = trend_df[f'recall_{trend_group_a}'] - trend_df[f'recall_{trend_group_b}']
        fig_trend = px.line(trend_df, x='date', y=['recall_gap'], title=f'Recall Gap ({trend_group_a} - {trend_group_b}) Over Time')
        fig_trend.update_layout(yaxis_title='Recall Gap', xaxis_title='Date')
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info('Insufficient data to compute recall trend gap.')

    # Bias Gap Analysis
    st.header('Bias Gap Analysis')
    metrics_for_dimension = compute_group_metrics(active_df, comparison_dimension)
    metric_map = metrics_for_dimension.set_index(comparison_dimension)
    if group_a in metric_map.index and group_b in metric_map.index:
        gap_value = metric_map.loc[group_a, metric_choice] - metric_map.loc[group_b, metric_choice]
        st.metric(label=f'{metric_choice.title()} Gap ({group_a} - {group_b})', value=f'{gap_value:.3f}')
        if abs(gap_value) > BIAS_THRESHOLD:
            st.error(f'Gap {gap_value:.3f} exceeds threshold {BIAS_THRESHOLD:.2f}. Potential bias risk.')
        else:
            st.success(f'Gap {gap_value:.3f} within acceptable threshold.')
    else:
        st.warning('Selected groups not found in current dataset.')

    # Underlying table
    st.dataframe(metrics_for_dimension, width='stretch')

    # Recommendations
    st.header('Recommendations')
    recommendations = recommendation_insights(metrics_gender, metrics_region)
    for r in recommendations:
        st.markdown(f'- {r}')

    # Footer
    st.caption('Data synthetic or derived. Mitigation simulated via balancing + selective FN corrections. Use with caution for production fairness audits.')

if __name__ == '__main__':
    render_bias_monitoring_page()

