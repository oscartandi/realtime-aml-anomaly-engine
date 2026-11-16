# Project Agenda & Architecture Walkthrough

## 1. Project Agenda & Business Problem
Traditional Anti-Money Laundering (AML) transaction monitoring relies heavily on static threshold rules (e.g., flagging any single transaction over $10,000). This approach suffers from two major operational bottlenecks:
1. **High False-Positive Rates:** Legitimate high-value business transactions overwhelm compliance queues.
2. **Threshold Evasion (Structuring / Smurfing):** Bad actors deliberately split large sums into multiple smaller transfers just below the $10,000 reporting limit within short time windows.

**Objective:** Build a low-latency behavioral anomaly scoring microservice that detects velocity spikes and structuring patterns unsupervised, translates mathematical anomaly scores into intuitive risk tiers (`HIGH_SAR_REVIEW`, `MEDIUM_UAR`, `LOW`), and outputs human-readable **reason codes** to accelerate analyst triage.

---

## 2. End-to-End Code Walkthrough

```text
[src/generator.py]  -->  [src/features.py]  -->  [src/scorer.py]  -->  [src/api.py]
 (Synthetic Logs)       (Behavioral Signals)    (Isolation Forest)     (FastAPI REST)
```
A. src/generator.py — Typology & Baseline Simulator
Because real banking transaction logs are strictly confidential, this module generates realistic multi-channel banking traffic (CARD, ACH, WIRE) alongside injected laundering typologies:

Baseline Retail Traffic: Simulates standard consumer spending with normal dollar distributions and natural time gaps between transfers.

Structuring / Smurfing Injection: Deliberately injects rapid bursts of wire transfers clustered just below the $10,000 Currency Transaction Report (CTR) threshold ($8,800–$9,900) within tight time windows.

B. src/features.py — Behavioral Feature Engineering (extract_aml_features)
Raw transaction attributes (amount, timestamp, channel) do not capture account velocity on their own. This module computes six behavioral signals per transaction:

log_amount: Applies np.log1p(amount) to compress extreme dollar skew so large legitimate wires do not distort normal variance.

mins_since_last_tx: Measures exact minutes elapsed since the sender_id's previous transaction to catch rapid-fire bursts.

tx_count_24h & tx_sum_24h: Computes rolling 24-hour transaction counts and cumulative dollar volume per sender account.

near_threshold_flag: Binary indicator (1 or 0) triggered when an amount falls inside the $8,800–$9,999 structuring sweet spot.

is_high_risk_channel: Flags higher-risk payment rails (WIRE) relative to standard consumer card transactions.

C. src/scorer.py — Unsupervised Risk Scoring & Explainability (AMLRiskScorer)
Why Isolation Forest? In financial crime operations, confirmed SAR labels are scarce and laundering typologies constantly evolve. IsolationForest learns normal multi-dimensional account behavior and isolates statistical outliers without requiring large labeled fraud datasets (contamination=0.03).

0–100 Score Normalization: Raw decision_function(X) outputs (where negative scores indicate anomalies) are normalized via min(max((0.25 - raw_score) * 200, 0), 100) into an intuitive 0–100 risk scale.

Alert Tiering & Reason Codes: Routes transactions into operational queues (HIGH_SAR_REVIEW >= 70, MEDIUM_UAR >= 45, LOW < 45) and attaches deterministic reason codes so investigators immediately understand why an alert fired.

D. src/api.py — Real-Time Scoring Microservice
Startup Bootstrap: Trains the AMLRiskScorer on startup using a synthetic baseline of 2,000 normal and 60 suspicious events so the model is warm in memory.

Strict Schema Validation: Uses Pydantic (TransactionEvent) to validate incoming JSON event fields before scoring.

POST /score Endpoint: Computes real-time features and returns the risk score, alert tier, and reason codes in milliseconds.

3. Quality Assurance & CI/CD
tests/test_pipeline.py: Automated pytest integration tests verifying that structuring bursts trigger elevated alert tiers with multiple reason codes, while routine retail purchases score LOW.

.github/workflows/ci.yml: GitHub Actions pipeline executing python -m pytest -v automatically on every push and pull request.
