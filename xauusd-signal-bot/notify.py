"""Kirim notifikasi sinyal ke Telegram."""

import logging
from datetime import timedelta, timezone

import requests

from strategy import Signal

log = logging.getLogger(__name__)

WIB = timezone(timedelta(hours=7))


def send_telegram(token: str, chat_id: str, text: str) -> bool:
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=15,
        )
        ok = resp.ok and resp.json().get("ok", False)
        if not ok:
            log.error("Telegram gagal: %s", resp.text)
        return ok
    except requests.RequestException as e:
        log.error("Telegram error: %s", e)
        return False


def format_signal(sig: Signal) -> str:
    emoji = "🟢" if sig.side == "BUY" else "🔴"
    wib = sig.time.astimezone(WIB).strftime("%d %b %Y %H:%M WIB")
    risk = abs(sig.entry - sig.sl)
    return (
        f"{emoji} SINYAL {sig.side} XAUUSD (M5)\n"
        f"🕐 Candle: {wib}\n"
        f"\n"
        f"💰 Entry : {sig.entry:.2f}\n"
        f"🛑 SL    : {sig.sl:.2f}  ({risk:.2f} poin)\n"
        f"🎯 TP1   : {sig.tp1:.2f}  (RR 1:1)\n"
        f"🎯 TP2   : {sig.tp2:.2f}  (RR 1:2)\n"
        f"\n"
        f"📊 RSI(14): {sig.rsi:.1f} | ATR(14): {sig.atr:.2f}\n"
        f"📈 Tren: {sig.trend}\n"
        f"⚡ Trigger: EMA9 cross {'↑' if sig.side == 'BUY' else '↓'} EMA21\n"
        f"\n"
        f"⚠️ Bukan saran keuangan. Selalu kelola risiko (maks 1-2% per posisi)."
    )
