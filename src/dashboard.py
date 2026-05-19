import pandas as pd
import plotly.express as px
import streamlit as st

PRIORITY_ORDER = ["Critical", "High", "Medium", "Low"]
PRIORITY_COLOURS = {
    "Critical": "#ef4444",
    "High":     "#f97316",
    "Medium":   "#3b82f6",
    "Low":      "#22c55e",
}


def render_dashboard(df: pd.DataFrame):
    st.header("📊 Dashboard")

    # ── KPI tiles ─────────────────────────────────────────────────────────────
    total     = len(df)
    open_esc  = len(df[df["status"].str.lower().isin(["open", "escalated"])])
    recurring = int(df["is_recurrence"].sum())
    crit_high = len(df[df["suggested_priority"].isin(["Critical", "High"])])

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Tickets",       total)
    k2.metric("Open / Escalated",    open_esc)
    k3.metric("Recurring Customers", recurring)
    k4.metric("Critical / High",     crit_high)

    st.divider()

    # ── Category volume + Priority pie ────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Volume by Category")
        cat_counts = df["suggested_category"].value_counts().reset_index()
        cat_counts.columns = ["Category", "Count"]
        fig = px.bar(
            cat_counts, x="Count", y="Category",
            orientation="h", color="Count",
            color_continuous_scale="Blues",
        )
        fig.update_layout(
            showlegend=False,
            coloraxis_showscale=False,
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Priority Breakdown")
        pri_counts = (
            df["suggested_priority"]
            .value_counts()
            .reindex(PRIORITY_ORDER, fill_value=0)
            .reset_index()
        )
        pri_counts.columns = ["Priority", "Count"]
        fig2 = px.pie(
            pri_counts, names="Priority", values="Count",
            color="Priority",
            color_discrete_map=PRIORITY_COLOURS,
            hole=0.4,
        )
        fig2.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ── Recurring customer hotspots ───────────────────────────────────────────
    st.subheader("🔁 Recurring Customer Hotspots")
    hotspots = (
        df.groupby("customer_id")
        .agg(
            total_tickets=("ticket_id", "count"),
            priorities=("suggested_priority", lambda x: ", ".join(sorted(set(x)))),
            categories=("suggested_category", lambda x: ", ".join(sorted(set(x)))),
        )
        .query("total_tickets > 1")
        .sort_values("total_tickets", ascending=False)
        .reset_index()
    )
    if len(hotspots) > 0:
        st.dataframe(hotspots, use_container_width=True, hide_index=True)
    else:
        st.info("No recurring customers in this dataset.")

    st.divider()

    # ── Open / escalated backlog ──────────────────────────────────────────────
    st.subheader("🚨 Open / Escalated Backlog")
    backlog = df[
        df["status"].str.lower().isin(["open", "escalated"])
    ].copy()

    if len(backlog) > 0:
        backlog["Recurring"] = backlog["is_recurrence"].map(
            {True: "⚠ Yes", False: "No"}
        )
        show_cols = [
            "ticket_id", "customer_id", "suggested_priority",
            "suggested_category", "status", "Recurring", "explanation",
        ]
        st.dataframe(
            backlog[[c for c in show_cols if c in backlog.columns]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.success("Backlog clear — no open or escalated tickets.")

    st.divider()

    # ── Satisfaction by priority ──────────────────────────────────────────────
    if (
        "satisfaction_score" in df.columns
        and df["satisfaction_score"].notna().any()
    ):
        st.subheader("😊 Avg Satisfaction Score by Priority")
        sat = (
            df.groupby("suggested_priority")["satisfaction_score"]
            .mean()
            .reindex(PRIORITY_ORDER)
            .dropna()
            .reset_index()
        )
        sat.columns = ["Priority", "Avg Score"]
        fig3 = px.bar(
            sat, x="Priority", y="Avg Score",
            color="Priority",
            color_discrete_map=PRIORITY_COLOURS,
            range_y=[0, 5],
        )
        fig3.update_layout(
            showlegend=False,
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig3, use_container_width=True)