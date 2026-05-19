import time
import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from src.loader import load_tickets
from src.recurrence import flag_recurrences
from src.classifier import triage_ticket
from src.dashboard import render_dashboard

st.set_page_config(
    page_title="TICKET — Support Triage",
    page_icon="🎫",
    layout="wide",
)

st.title("🎫 TICKET — AI Support Triage Assistant")
st.caption(
    "Upload a CSV of support tickets and get AI-powered triage in seconds."
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Setup")

    api_key = st.text_input(
        "Gemini API Key",
        value=os.getenv("GEMINI_API_KEY", ""),
        type="password",
        help="Or set GEMINI_API_KEY in your .env file",
    )
    if api_key:
        os.environ["GEMINI_API_KEY"] = api_key

    st.divider()

    st.header("📁 Upload")
    uploaded_file = st.file_uploader("Choose your CSV", type=["csv"])

    st.divider()

    st.markdown("""
**How it works**
1. Add your Gemini API key
2. Upload `support_tickets.csv`
3. Click **Run Triage**
4. View dashboard + results
5. Download enriched CSV
""")

# ── Guard rails ───────────────────────────────────────────────────────────────
if uploaded_file is None:
    st.info("👈 Upload a CSV file in the sidebar to get started.")
    st.stop()

if not os.getenv("GEMINI_API_KEY"):
    st.error(
        "No API key found. Add it in the sidebar or in your .env file."
    )
    st.stop()

# ── Run triage ────────────────────────────────────────────────────────────────
if st.button("🚀 Run Triage", type="primary"):

    with st.spinner("Loading and cleaning tickets..."):
        df = load_tickets(uploaded_file)
        df = flag_recurrences(df)

    st.success(f"Loaded {len(df)} tickets. Running AI triage now...")

    progress = st.progress(0, text="Starting...")
    results = []

    for i, row in df.iterrows():
        triage = triage_ticket(row.to_dict())
        results.append(triage)
        progress.progress(
            (i + 1) / len(df),
            text=f"Triaging ticket {i + 1} of {len(df)}..."
        )
        time.sleep(4)  # Stay comfortably under the free tier rate limit

    progress.empty()

    # Merge AI results back onto the dataframe
    df = pd.concat(
        [df.reset_index(drop=True), pd.DataFrame(results)],
        axis=1,
    )

    st.success("✅ Triage complete!")

    # Dashboard
    render_dashboard(df)

    st.divider()

    # Per-ticket results
    st.header("🎫 Per-Ticket Results")
    show_cols = [
        "ticket_id", "customer_id", "date_submitted",
        "suggested_priority", "suggested_category", "suggested_subcategory",
        "is_recurrence", "prior_ticket_ids", "explanation",
        "status", "ticket_description",
    ]
    st.dataframe(
        df[[c for c in show_cols if c in df.columns]],
        use_container_width=True,
        hide_index=True,
    )

    # Download
    st.download_button(
        label="⬇️ Download enriched CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="triage_results.csv",
        mime="text/csv",
    )