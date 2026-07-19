"""Webhook endpoint tests."""

from src.config import SETTINGS


class TestReceiveAlert:
    def test_buy_signal_returns_ok(self, client):
        payload = {
            "ticker": "MPL",
            "action": "buy",
            "price": 950.50,
            "qty": 1,
            "signal_id": "sig_test_001",
        }
        resp = client.post("/webhook/tradingview", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["order_id"] is not None
        assert "BUY" in data["message"].upper()

    def test_sell_signal_returns_ok(self, client):
        # First go long
        client.post("/webhook/tradingview", json={"action": "buy", "price": 950.0, "signal_id": "sig_in"})
        # Then sell (reverses to short per plan design)
        resp = client.post("/webhook/tradingview", json={"action": "sell", "price": 960.0, "signal_id": "sig_out"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_missing_action_returns_422(self, client):
        resp = client.post("/webhook/tradingview", json={"ticker": "MPL"})
        assert resp.status_code == 422

    def test_webhook_secret_auth(self, client):
        SETTINGS.webhook_secret = "test-secret"
        payload = {"action": "buy", "price": 950.0}
        # No secret header -> 403
        resp = client.post("/webhook/tradingview", json=payload)
        assert resp.status_code == 403
        # Wrong secret -> 403
        resp = client.post("/webhook/tradingview", json=payload, headers={"x-webhook-secret": "wrong"})
        assert resp.status_code == 403
        # Correct secret -> 200
        resp = client.post("/webhook/tradingview", json=payload, headers={"x-webhook-secret": "test-secret"})
        assert resp.status_code == 200
        SETTINGS.webhook_secret = None  # reset
