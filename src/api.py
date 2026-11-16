from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np
from src.generator import generate_transactions
from src.features import extract_aml_features
from src.scorer import AMLRiskScorer

app = FastAPI(title="Real-Time AML Anomaly Scoring Engine", version="1.0.0")

# Bootstrap model on startup using synthetic baseline
_df = extract_aml_features(generate_transactions(n_normal=2000, n_suspicious=60))
scorer = AMLRiskScorer()
scorer.fit(_df)


class TransactionEvent(BaseModel):
    tx_id: str
    sender_id: str
    amount: float
    channel: str
    mins_since_last_tx: float
    tx_count_24h: int
    tx_sum_24h: float


@app.post("/score")
def score_event(event: TransactionEvent):
    features = {
        "log_amount": float(np.log1p(event.amount)),
        "mins_since_last_tx": event.mins_since_last_tx,
        "tx_count_24h": event.tx_count_24h,
        "tx_sum_24h": event.tx_sum_24h,
        "near_threshold_flag": int(8800 <= event.amount < 10000),
        "is_high_risk_channel": int(event.channel.upper() == "WIRE"),
    }
    result = scorer.score_transaction(features)
    return {"tx_id": event.tx_id, "sender_id": event.sender_id, **result}
