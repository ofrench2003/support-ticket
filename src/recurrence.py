import pandas as pd


def flag_recurrences(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("date_submitted").reset_index(drop=True)

    is_recurrence = []
    prior_ids = []

    for i, row in df.iterrows():
        earlier = df[
            (df["customer_id"] == row["customer_id"]) &
            (df.index < i)
        ]

        if len(earlier) > 0:
            is_recurrence.append(True)
            prior_ids.append(
                ", ".join(earlier["ticket_id"].astype(str).tolist())
            )
        else:
            # First time we've seen this customer
            is_recurrence.append(False)
            prior_ids.append("")

    df["is_recurrence"] = is_recurrence
    df["prior_ticket_ids"] = prior_ids
    return df