"""Strategi sinyal XAUUSD M5.

Logika:
  - Filter tren : harga > EMA200 dan EMA50 > EMA200  -> hanya cari BUY
                  harga < EMA200 dan EMA50 < EMA200  -> hanya cari SELL
  - Trigger     : EMA9 cross EMA21 searah tren pada candle yang baru close
  - Konfirmasi  : RSI(14) 50-70 untuk BUY, 30-50 untuk SELL
                  (momentum searah, belum overbought/oversold)
  - SL/TP       : SL = 1.5 x ATR(14), TP1 = 1.5 x ATR (RR 1:1), TP2 = 3 x ATR (RR 1:2)
"""

from dataclasses import dataclass

import pandas as pd

SL_ATR = 1.5
TP1_ATR = 1.5
TP2_ATR = 3.0


@dataclass
class Signal:
    side: str          # "BUY" / "SELL"
    time: pd.Timestamp  # waktu open candle sinyal (UTC)
    entry: float
    sl: float
    tp1: float
    tp2: float
    rsi: float
    atr: float
    trend: str


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def evaluate(df: pd.DataFrame) -> Signal | None:
    """Evaluasi candle terakhir (harus sudah close). Return Signal atau None."""
    if len(df) < 210:  # butuh cukup data untuk EMA200
        return None

    close = df["close"]
    ema9, ema21 = ema(close, 9), ema(close, 21)
    ema50, ema200 = ema(close, 50), ema(close, 200)
    rsi14 = rsi(close)
    atr14 = atr(df)

    c = close.iloc[-1]
    r = rsi14.iloc[-1]
    a = atr14.iloc[-1]

    bull = c > ema200.iloc[-1] and ema50.iloc[-1] > ema200.iloc[-1]
    bear = c < ema200.iloc[-1] and ema50.iloc[-1] < ema200.iloc[-1]

    cross_up = ema9.iloc[-2] <= ema21.iloc[-2] and ema9.iloc[-1] > ema21.iloc[-1]
    cross_dn = ema9.iloc[-2] >= ema21.iloc[-2] and ema9.iloc[-1] < ema21.iloc[-1]

    t = df["datetime"].iloc[-1]

    if bull and cross_up and 50 <= r <= 70:
        return Signal("BUY", t, c, c - SL_ATR * a, c + TP1_ATR * a, c + TP2_ATR * a,
                      r, a, "Bullish (harga > EMA200, EMA50 > EMA200)")
    if bear and cross_dn and 30 <= r <= 50:
        return Signal("SELL", t, c, c + SL_ATR * a, c - TP1_ATR * a, c - TP2_ATR * a,
                      r, a, "Bearish (harga < EMA200, EMA50 < EMA200)")
    return None
