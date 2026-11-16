# Real-Time AML Transaction Anomaly Scoring Engine

An end-to-end financial crime detection microservice that ingests high-velocity transaction streams, engineers rolling behavioral and structuring features, and scores Anti-Money Laundering (AML) risk in real time with explainable reason codes for SAR/UAR triage.

## System Architecture

```mermaid
flowchart LR
    A[Synthetic Event Stream] --> B[Feature Engineering<br/>24h Velocity & Threshold Proximity]
    B --> C[Isolation Forest<br/>Anomaly Scoring Engine]
    C --> D{Risk Tiering}
    D -->|Score >= 70| E[HIGH_SAR_REVIEW + Reason Codes]
    D -->|45 <= Score < 70| F[MEDIUM_UAR + Reason Codes]
    D -->|Score < 45| G[LOW / Baseline Log]`\
```

Key Capabilities
Typology Simulation (src/generator.py): Generates baseline multi-channel banking traffic alongside injected structuring/smurfing bursts just under the $10,000 regulatory reporting threshold.

Behavioral Feature Pipeline (src/features.py): Computes time-since-last-transaction, rolling 24-hour transaction counts/volumes, and threshold proximity flags.

Explainable Scoring API (src/scorer.py & src/api.py): Exposes a low-latency FastAPI /score endpoint returning normalized risk scores (0–100), alert tiers, and human-readable reason codes.

Automated CI (tests/test_pipeline.py): Verified via pytest and GitHub Actions on every push.

Quickstart

# 1. Install dependencies
pip install -r requirements.txt

# 2. Run automated tests
pytest -v

# 3. Start the real-time scoring API
uvicorn src.api:app --reload

Example API Request (POST /score)

{
  "tx_id": "TX_TEST_999",
  "sender_id": "ACC_0007",
  "amount": 9650.00,
  "channel": "WIRE",
  "mins_since_last_tx": 12.0,
  "tx_count_24h": 4,
  "tx_sum_24h": 38200.00
}
