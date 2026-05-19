# TICKET — AI Support Triage Assistant

A Streamlit app that triages support tickets using Google Gemini AI.

## Setup

```bash
git clone <your-repo>
cd ticket

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Add your Gemini API key to `.env`:
```
GEMINI_API_KEY=your_key_here
```

## Run

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Usage

1. Upload `support_tickets.csv` in the sidebar
2. Click **Run Triage**
3. View the dashboard and per-ticket results
4. Download the enriched CSV

## Output format

**Per ticket:** suggested priority, category, subcategory,
recurrence flag, prior ticket IDs, and a plain-English explanation.

**Dashboard:** KPI tiles, volume by category, priority breakdown,
recurring customer hotspots, open/escalated backlog, satisfaction by priority.

## Why Streamlit?

File upload, interactive tables, and charts with no frontend code.
The right shape for a tool a support manager opens in a browser
first thing each morning.