import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np


def generate_transactions(n_normal: int = 5000, n_suspicious: int = 150, seed: int = 42) -> pd.DataFrame:
    random.seed(seed)
    np.random.seed(seed)
    base_time = datetime(2026, 11, 1, 8, 0, 0)
    accounts = [f"ACC_{i:04d}" for i in range(1, 201)]
    records = []

    # 1. Normal baseline traffic
    for i in range(n_normal):
        ts = base_time + timedelta(minutes=random.randint(0, 20000))
        records.append({
            "tx_id": f"TX_{i:06d}",
            "timestamp": ts,
            "sender_id": random.choice(accounts),
            "receiver_id": random.choice(accounts),
            "amount": round(float(np.random.lognormal(mean=4.8, sigma=1.1)), 2),
            "channel": random.choice(["ACH", "WIRE", "CARD", "UPI"]),
            "country": random.choice(["IN", "US", "UK", "SG"]),
            "is_laundering": 0,
            "typology": "normal",
        })

    # 2. Inject Structuring / Smurfing Typology (multiple transfers just below $10,000 threshold)
    idx = n_normal
    for _ in range(n_suspicious // 3):
        bad_actor = f"ACC_{random.randint(1, 20):04d}"
        mule_target = f"ACC_{random.randint(180, 200):04d}"
        burst_start = base_time + timedelta(minutes=random.randint(0, 19000))
        for burst in range(3):
            records.append({
                "tx_id": f"TX_{idx:06d}",
                "timestamp": burst_start + timedelta(minutes=burst * 18),
                "sender_id": bad_actor,
                "receiver_id": mule_target,
                "amount": round(random.uniform(9100.0, 9950.0), 2),
                "channel": "WIRE",
                "country": "US",
                "is_laundering": 1,
                "typology": "structuring",
            })
            idx += 1

    df = pd.DataFrame(records).sort_values("timestamp").reset_index(drop=True)
    return df


if __name__ == "__main__":
    df = generate_transactions()
    df.to_csv("data/transactions.csv", index=False)
    print(f"Generated {len(df)} rows | Positive AML cases: {df['is_laundering'].sum()}")
