"""Pengambilan data candle XAU/USD dari Twelve Data (free tier)."""

import logging

import pandas as pd
import requests

log = logging.getLogger(__name__)

BASE_URL = "https://api.twelvedata.com/time_series"


class DataError(Exception):
    pass


def fetch_candles(api_key: str, symbol: str = "XAU/USD",
                  interval: str = "5min", outputsize: int = 250) -> pd.DataFrame:
    """Ambil candle terbaru, urut dari lama ke baru.

    Kolom: datetime (UTC, tz-aware), open, high, low, close.
    """
    resp = requests.get(BASE_URL, params={
        "symbol": symbol,
        "interval": interval,
        "outputsize": outputsize,
        "timezone": "UTC",
        "apikey": api_key,
    }, timeout=30)
    resp.raise_for_status()
    payload = resp.json()

    if payload.get("status") == "error" or "values" not in payload:
        raise DataError(f"Twelve Data error: {payload.get('message', payload)}")

    df = pd.DataFrame(payload["values"])
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    for col in ("open", "high", "low", "close"):
        df[col] = pd.to_numeric(df[col])
    df = df.sort_values("datetime").reset_index(drop=True)
    return df[["datetime", "open", "high", "low", "close"]]


def drop_forming_candle(df: pd.DataFrame, now_utc: pd.Timestamp,
                        interval_minutes: int = 5) -> pd.DataFrame:
    """Buang candle yang masih berjalan agar sinyal hanya dari candle yang sudah close."""
    boundary = now_utc.floor(f"{interval_minutes}min")
    return df[df["datetime"] < boundary].reset_index(drop=True)
