from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)


def test_structuring_alert_triggered():
    payload = {
        "tx_id": "TX_TEST_999",
        "sender_id": "ACC_0007",
        "amount": 9650.00,
        "channel": "WIRE",
        "mins_since_last_tx": 12.0,
        "tx_count_24h": 4,
        "tx_sum_24h": 38200.00,
    }
    res = client.post("/score", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["alert_tier"] in {"HIGH_SAR_REVIEW", "MEDIUM_UAR"}
    assert len(body["reason_codes"]) >= 2


def test_normal_transaction_low_risk():
    payload = {
        "tx_id": "TX_TEST_100",
        "sender_id": "ACC_0042",
        "amount": 85.50,
        "channel": "CARD",
        "mins_since_last_tx": 1440.0,
        "tx_count_24h": 1,
        "tx_sum_24h": 85.50,
    }
    res = client.post("/score", json=payload)
    assert res.status_code == 200
    assert res.json()["alert_tier"] == "LOW"
