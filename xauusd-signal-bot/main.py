"""Bot pemantau XAUUSD M5 -> alert entry ke Telegram.

Jalan sebagai web service kecil (endpoint / untuk keep-alive) dengan
loop pemantauan di background thread. Setiap candle M5 close, bot
mengambil data, mengevaluasi strategi, dan mengirim sinyal ke Telegram.

Env vars wajib : TWELVEDATA_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
Env vars opsi  : SYMBOL (default XAU/USD), COOLDOWN_CANDLES (default 6), PORT
"""

import logging
import os
import threading
import time
from datetime import datetime, timezone

import pandas as pd
from flask import Flask

import data
import notify
import strategy

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("bot")

INTERVAL_MIN = 5

API_KEY = os.environ.get("TWELVEDATA_API_KEY", "")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
SYMBOL = os.environ.get("SYMBOL", "XAU/USD")
COOLDOWN_CANDLES = int(os.environ.get("COOLDOWN_CANDLES", "6"))

app = Flask(__name__)
state = {"last_check": None, "last_signal": None, "candles_since_signal": 999}


@app.route("/")
def health():
    return {
        "status": "running",
        "symbol": SYMBOL,
        "last_check_utc": str(state["last_check"]),
        "last_signal": state["last_signal"],
    }


def market_open(now: datetime) -> bool:
    """Jam pasar XAUUSD (kira-kira): Minggu 22:00 UTC s.d. Jumat 21:00 UTC,
    dengan jeda harian 21:00-22:00 UTC."""
    wd, hr = now.weekday(), now.hour
    if wd == 5:                      # Sabtu
        return False
    if wd == 6 and hr < 22:          # Minggu sebelum buka
        return False
    if wd == 4 and hr >= 21:         # Jumat setelah tutup
        return False
    if hr == 21:                     # jeda harian
        return False
    return True


def sleep_until_next_candle():
    """Tidur sampai ~20 detik setelah candle M5 berikutnya close."""
    now = time.time()
    period = INTERVAL_MIN * 60
    next_boundary = (now // period + 1) * period
    time.sleep(max(1, next_boundary - now + 20))


def check_once():
    now_utc = pd.Timestamp.now(tz=timezone.utc)
    df = data.fetch_candles(API_KEY, symbol=SYMBOL, interval=f"{INTERVAL_MIN}min")
    df = data.drop_forming_candle(df, now_utc, INTERVAL_MIN)
    state["last_check"] = df["datetime"].iloc[-1] if len(df) else None

    sig = strategy.evaluate(df)
    state["candles_since_signal"] += 1

    if sig is None:
        log.info("Tidak ada sinyal. Close terakhir: %s @ %s",
                 df["close"].iloc[-1] if len(df) else "-", state["last_check"])
        return

    if state["candles_since_signal"] < COOLDOWN_CANDLES:
        log.info("Sinyal %s ditahan (cooldown %d candle).",
                 sig.side, COOLDOWN_CANDLES)
        return

    log.info("SINYAL %s @ %.2f", sig.side, sig.entry)
    if notify.send_telegram(BOT_TOKEN, CHAT_ID, notify.format_signal(sig)):
        state["last_signal"] = f"{sig.side} @ {sig.entry:.2f} ({sig.time})"
        state["candles_since_signal"] = 0


def monitor_loop():
    notify.send_telegram(
        BOT_TOKEN, CHAT_ID,
        f"🤖 Bot sinyal {SYMBOL} M5 aktif.\n"
        f"Strategi: EMA200/50 trend filter + EMA9/21 cross + RSI(14), SL/TP via ATR(14).\n"
        f"⚠️ Sinyal bersifat informasi, bukan saran keuangan.")
    while True:
        sleep_until_next_candle()
        now = datetime.now(timezone.utc)
        if not market_open(now):
            log.info("Pasar tutup (%s UTC), skip.", now.strftime("%a %H:%M"))
            continue
        try:
            check_once()
        except Exception:
            log.exception("Gagal memproses candle, coba lagi candle berikutnya.")


def main():
    missing = [k for k, v in {"TWELVEDATA_API_KEY": API_KEY,
                              "TELEGRAM_BOT_TOKEN": BOT_TOKEN,
                              "TELEGRAM_CHAT_ID": CHAT_ID}.items() if not v]
    if missing:
        raise SystemExit(f"Env var belum di-set: {', '.join(missing)}")

    threading.Thread(target=monitor_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "10000")))


if __name__ == "__main__":
    main()
