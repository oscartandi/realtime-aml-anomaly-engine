import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest

FEATURE_COLS = [
    "log_amount",
    "mins_since_last_tx",
    "tx_count_24h",
    "tx_sum_24h",
    "near_threshold_flag",
    "is_high_risk_channel",
]


class AMLRiskScorer:
    def __init__(self, contamination: float = 0.03):
        self.model = IsolationForest(
            n_estimators=150, contamination=contamination, random_state=42
        )

    def fit(self, df_features: pd.DataFrame) -> None:
        self.model.fit(df_features[FEATURE_COLS])

    def score_transaction(self, row: dict) -> dict:
        X = pd.DataFrame([row])[FEATURE_COLS]
        raw_score = float(self.model.decision_function(X)[0])
        # Normalize to 0–100 risk score (higher = riskier)
        risk_score = round(min(max((0.25 - raw_score) * 200, 0), 100), 2)

        reasons = []
        if row.get("near_threshold_flag") == 1:
            reasons.append("Amount just below $10k reporting threshold (Structuring risk)")
        if row.get("tx_count_24h", 0) >= 3:
            reasons.append(f"High 24h velocity ({int(row['tx_count_24h'])} transfers)")
        if row.get("mins_since_last_tx", 999) < 30:
            reasons.append("Rapid burst transfer (<30 mins since prior tx)")

        return {
            "risk_score": risk_score,
            "alert_tier": "HIGH_SAR_REVIEW" if risk_score >= 70 else ("MEDIUM_UAR" if risk_score >= 45 else "LOW"),
            "reason_codes": reasons or ["Normal behavioral baseline"],
        }

    def save(self, path: str = "model.joblib") -> None:
        joblib.dump(self.model, path)
