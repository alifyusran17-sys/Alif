"""TradingView -> Telegram webhook bridge.

TradingView alert (Pro+ tier) POSTs JSON to /webhook?secret=<WEBHOOK_SECRET>.
This server validates the secret, formats the payload, and forwards it to a
Telegram chat via the Bot API.

Env vars (see .env.example):
  TELEGRAM_BOT_TOKEN  - from @BotFather
  TELEGRAM_CHAT_ID    - your chat id (get from @userinfobot) or channel id
  WEBHOOK_SECRET      - shared string TradingView must pass in ?secret=
  PORT                - default 8080
"""

from __future__ import annotations

import hmac
import json
import logging
import os
import time
from typing import Any

import requests
from flask import Flask, jsonify, request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("tv-bridge")

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
SECRET = os.environ.get("WEBHOOK_SECRET", "")
PORT = int(os.environ.get("PORT", "8080"))

if not BOT_TOKEN or not CHAT_ID or not SECRET:
    log.warning(
        "Missing env: TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID / WEBHOOK_SECRET. "
        "The server will start but /webhook will return 500 until they are set."
    )

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

app = Flask(__name__)

_recent: dict[str, float] = {}
_DEDUPE_WINDOW_S = 30.0


def _dedupe_key(payload: dict[str, Any]) -> str:
    return f"{payload.get('symbol','')}|{payload.get('side','')}|{payload.get('price','')}"


def _is_duplicate(payload: dict[str, Any]) -> bool:
    key = _dedupe_key(payload)
    now = time.time()
    for k, ts in list(_recent.items()):
        if now - ts > _DEDUPE_WINDOW_S:
            _recent.pop(k, None)
    if key in _recent:
        return True
    _recent[key] = now
    return False


def _format_message(payload: dict[str, Any]) -> str:
    side = str(payload.get("side", "")).upper()
    arrow = "🟢 LONG" if side == "LONG" else "🔴 SHORT" if side == "SHORT" else f"⚪ {side}"
    lines = [
        f"<b>{arrow}  {payload.get('symbol','?')}</b>",
        f"Price : <code>{payload.get('price','?')}</code>",
    ]
    if "sl" in payload:
        lines.append(f"SL    : <code>{payload['sl']}</code>")
    if "tp" in payload:
        lines.append(f"TP    : <code>{payload['tp']}</code>")
    if "tf" in payload:
        lines.append(f"TF    : {payload['tf']}")
    if "time" in payload:
        lines.append(f"Time  : {payload['time']}")
    return "\n".join(lines)


def _send_telegram(text: str) -> tuple[bool, str]:
    try:
        r = requests.post(
            TELEGRAM_URL,
            json={
                "chat_id": CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=10,
        )
        if r.status_code == 200:
            return True, "ok"
        return False, f"tg {r.status_code}: {r.text[:200]}"
    except requests.RequestException as e:
        return False, f"tg exception: {e}"


@app.get("/health")
def health() -> Any:
    return jsonify({"ok": True, "configured": bool(BOT_TOKEN and CHAT_ID and SECRET)})


@app.post("/webhook")
def webhook() -> Any:
    if not (BOT_TOKEN and CHAT_ID and SECRET):
        return jsonify({"error": "server not configured"}), 500

    supplied = request.args.get("secret") or request.headers.get("X-Webhook-Secret", "")
    if not hmac.compare_digest(supplied, SECRET):
        log.warning("rejected webhook (bad secret) from %s", request.remote_addr)
        return jsonify({"error": "forbidden"}), 403

    raw = request.get_data(as_text=True) or ""
    payload: dict[str, Any]
    try:
        payload = json.loads(raw) if raw.strip().startswith("{") else {"text": raw}
    except json.JSONDecodeError:
        payload = {"text": raw}

    if isinstance(payload, dict) and "side" in payload and _is_duplicate(payload):
        log.info("dedup skip: %s", _dedupe_key(payload))
        return jsonify({"ok": True, "deduped": True})

    text = _format_message(payload) if "side" in payload else f"<pre>{payload.get('text', raw)[:3500]}</pre>"
    ok, info = _send_telegram(text)
    if not ok:
        log.error("telegram send failed: %s", info)
        return jsonify({"error": info}), 502

    log.info("forwarded: %s", _dedupe_key(payload) if "side" in payload else "raw")
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
