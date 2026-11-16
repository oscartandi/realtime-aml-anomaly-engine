import pandas as pd
import numpy as np


def extract_aml_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(["sender_id", "timestamp"]).reset_index(drop=True)

    # Time delta since sender's previous transaction (in minutes)
    df["mins_since_last_tx"] = (
        df.groupby("sender_id")["timestamp"].diff().dt.total_seconds().div(60).fillna(9999.0)
    )

    # Rolling 24-hour transaction count and cumulative volume per sender
    df = df.set_index("timestamp")
    rolling_24h = df.groupby("sender_id")["amount"].rolling("24h")
    df["tx_count_24h"] = rolling_24h.count().values
    df["tx_sum_24h"] = rolling_24h.sum().values
    df = df.reset_index()

    # Proximity to $10,000 regulatory reporting threshold (structuring indicator)
    df["near_threshold_flag"] = ((df["amount"] >= 8800) & (df["amount"] < 10000)).astype(int)
    df["is_high_risk_channel"] = (df["channel"] == "WIRE").astype(int)
    df["log_amount"] = np.log1p(df["amount"])

    return df
