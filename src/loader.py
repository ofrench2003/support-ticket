import pandas as pd


def load_tickets(path_or_buffer) -> pd.DataFrame:
    df = pd.read_csv(path_or_buffer, on_bad_lines='warn', engine='python')

    # Normalise column names — lowercase, strip spaces
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Strip whitespace from all string columns
    str_cols = df.select_dtypes(include="object").columns
    df[str_cols] = df[str_cols].apply(lambda c: c.str.strip())

    # Parse dates — anything malformed becomes NaT
    if "date_submitted" in df.columns:
        df["date_submitted"] = pd.to_datetime(
            df["date_submitted"], errors="coerce"
        )

    # Coerce numeric fields
    for col in ["resolution_time_hours", "satisfaction_score"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Ensure key columns always exist even if missing from CSV
    for col in [
        "priority", "category", "subcategory", "status",
        "ticket_description", "resolution_notes",
        "customer_id", "ticket_id",
    ]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("")

    return df