import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import uuid

STATUS_OPTIONS = ["Pending", "Resolved", "Escalated"]
QUERY_TYPES = ["Chargeback", "Login Issue", "Payment Failure", "Account Lock", "Suspicious Activity"]
ASSIGNEES = ["Analyst A", "Analyst B", "Team Lead", "Queue"]

def _init_sample_tickets(n: int = 18) -> pd.DataFrame:
    now = datetime.utcnow()
    rows = []
    for i in range(n):
        submitted = now - timedelta(hours=i * 4)
        status = STATUS_OPTIONS[0] if i % 5 != 0 else "Resolved"
        resolved_on = submitted + timedelta(hours=2) if status == "Resolved" else None
        sla_hours = 24  # static SLA window for demo
        due = submitted + timedelta(hours=sla_hours)
        rows.append({
            "Ticket ID": f"TKT-{uuid.uuid4().hex[:8]}",
            "User ID": f"U{1000+i}",
            "Query Type": QUERY_TYPES[i % len(QUERY_TYPES)],
            "Submitted On": submitted,
            "Status": status,
            "Assigned To": ASSIGNEES[i % len(ASSIGNEES)],
            "SLA Time": (due - datetime.utcnow()).total_seconds() / 3600.0,  # hours remaining
            "Resolved On": resolved_on,
        })
    df = pd.DataFrame(rows)
    return df

def _format_sla(hours_remaining: float) -> str:
    if hours_remaining < 0:
        return "Expired"
    return f"{hours_remaining:.1f}h" if hours_remaining < 48 else f"{hours_remaining/24:.1f}d"

def render_reply_tracker_page():
    st.header("Reply Tracker")
    st.caption("Track user support / fraud review replies, adjust status, and export history.")

    # Initialize tickets in session state
    if "tickets_df" not in st.session_state:
        st.session_state.tickets_df = _init_sample_tickets()
    if "tickets_prev" not in st.session_state:
        st.session_state.tickets_prev = st.session_state.tickets_df.copy()

    tickets_df: pd.DataFrame = st.session_state.tickets_df.copy()

    # Recompute SLA remaining each render
    tickets_df["SLA Time"] = tickets_df["Submitted On"].apply(lambda ts: (ts + timedelta(hours=24) - datetime.utcnow()).total_seconds()/3600.0)

    # Filters
    with st.expander("Filters", expanded=True):
        search = st.text_input("Search Ticket/User ID")
        status_filter = st.multiselect("Status", STATUS_OPTIONS, default=STATUS_OPTIONS)
        type_filter = st.multiselect("Query Type", QUERY_TYPES, default=QUERY_TYPES)
        assignee_filter = st.multiselect("Assigned To", ASSIGNEES, default=ASSIGNEES)
        date_from = st.date_input("From Date", value=datetime.utcnow().date())
        date_to = st.date_input("To Date", value=datetime.utcnow().date())

    # Apply filters
    filtered = tickets_df[
        tickets_df["Status"].isin(status_filter) &
        tickets_df["Query Type"].isin(type_filter) &
        tickets_df["Assigned To"].isin(assignee_filter)
    ]
    if search:
        s = search.lower().strip()
        filtered = filtered[filtered.apply(lambda r: s in r["Ticket ID"].lower() or s in r["User ID"].lower(), axis=1)]
    filtered = filtered[(filtered["Submitted On"].dt.date >= date_from) & (filtered["Submitted On"].dt.date <= date_to)]

    # Display summary metrics
    pending_count = (tickets_df["Status"] == "Pending").sum()
    resolved_count = (tickets_df["Status"] == "Resolved").sum()
    escalated_count = (tickets_df["Status"] == "Escalated").sum()
    m1, m2, m3 = st.columns(3)
    m1.metric("Pending", pending_count)
    m2.metric("Resolved", resolved_count)
    m3.metric("Escalated", escalated_count)

    # Prepare view DataFrame (format SLA)
    view_df = filtered.copy()
    view_df["SLA Time"] = view_df["SLA Time"].apply(_format_sla)

    # Data Editor for status updates
    st.subheader("Tickets")
    edited = st.data_editor(
        view_df,
        key="tickets_editor",
        column_config={
            "Status": st.column_config.SelectboxColumn(
                "Status",
                options=STATUS_OPTIONS,
                help="Update ticket status"
            ),
            "Submitted On": st.column_config.DatetimeColumn("Submitted On", format="YYYY-MM-DD HH:mm"),
            "Resolved On": st.column_config.DatetimeColumn("Resolved On", format="YYYY-MM-DD HH:mm", disabled=True),
        },
        hide_index=True,
        disabled=["Ticket ID", "User ID", "Query Type", "Submitted On", "Assigned To", "SLA Time"],
    )

    # Detect status changes and apply to master dataframe
    master = st.session_state.tickets_df
    changes = []
    # Map edited rows back by Ticket ID
    for _, row in edited.iterrows():
        tid = row["Ticket ID"]
        original_row = master[master["Ticket ID"] == tid].iloc[0]
        if row["Status"] != original_row["Status"]:
            # Update master
            master.loc[master["Ticket ID"] == tid, "Status"] = row["Status"]
            if row["Status"] == "Resolved" and pd.isna(original_row["Resolved On"]):
                master.loc[master["Ticket ID"] == tid, "Resolved On"] = datetime.utcnow()
            elif row["Status"] != "Resolved":
                # Clear resolved timestamp if moved out of resolved state
                master.loc[master["Ticket ID"] == tid, "Resolved On"] = pd.NaT
            changes.append((tid, original_row["Status"], row["Status"]))
    if changes:
        st.session_state.tickets_df = master
        for tid, old, new in changes:
            st.toast(f"Ticket {tid} status: {old} → {new}", icon="✅")

    # Line chart of resolution time by date
    st.subheader("Resolution Time Trend")
    resolved = master.dropna(subset=["Resolved On"]).copy()
    if not resolved.empty:
        resolved["Resolution Hours"] = (resolved["Resolved On"] - resolved["Submitted On"]).dt.total_seconds()/3600.0
        resolved["Resolved Date"] = resolved["Resolved On"].dt.date
        trend = resolved.groupby("Resolved Date")["Resolution Hours"].mean().reset_index()
        trend = trend.sort_values("Resolved Date")
        st.line_chart(trend.set_index("Resolved Date"))
    else:
        st.info("No resolved tickets yet to plot resolution time trend.")

    # Download button (historical master dataset)
    csv_data = master.drop(columns=["Resolved On"]).copy()
    st.download_button(
        label="Download Ticket History CSV",
        data=csv_data.to_csv(index=False),
        file_name="ticket_history.csv",
        mime="text/csv"
    )

    st.caption("SLA Time is hours remaining until a 24h window expires. Resolution trend averages hours to resolve per day.")

if __name__ == "__main__":
    render_reply_tracker_page()
