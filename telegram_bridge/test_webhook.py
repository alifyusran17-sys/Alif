"""Quick self-test — run without env vars and hit endpoints with the test client.

Usage:  python test_webhook.py
"""

import os

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("TELEGRAM_CHAT_ID", "1")
os.environ.setdefault("WEBHOOK_SECRET", "test-secret")

from unittest.mock import patch  # noqa: E402

import webhook_server  # noqa: E402


def run() -> None:
    client = webhook_server.app.test_client()

    r = client.get("/health")
    assert r.status_code == 200 and r.get_json()["ok"] is True, r.get_json()

    r = client.post("/webhook?secret=wrong", json={"side": "LONG"})
    assert r.status_code == 403, r.status_code

    with patch.object(webhook_server, "_send_telegram", return_value=(True, "ok")) as m:
        payload = {"symbol": "XAUUSD", "side": "LONG", "price": 2345.6, "sl": 2340.1, "tp": 2356.6}
        r = client.post("/webhook?secret=test-secret", json=payload)
        assert r.status_code == 200 and r.get_json()["ok"] is True, r.get_json()
        assert m.called
        sent_text = m.call_args.args[0]
        assert "XAUUSD" in sent_text and "LONG" in sent_text and "2345.6" in sent_text

        r = client.post("/webhook?secret=test-secret", json=payload)
        assert r.get_json().get("deduped") is True, r.get_json()

    with patch.object(webhook_server, "_send_telegram", return_value=(True, "ok")) as m:
        r = client.post("/webhook?secret=test-secret", data="raw text alert", content_type="text/plain")
        assert r.status_code == 200, r.status_code
        assert "raw text alert" in m.call_args.args[0]

    print("all tests passed")


if __name__ == "__main__":
    run()
