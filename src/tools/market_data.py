"""
market_data.py — Tool for fetching & caching stock data via yfinance.
"""
import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import yfinance as yf

# Add project root to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config.settings import DATA_DIR, DEFAULT_PERIOD, DEFAULT_INTERVAL


def _cache_path(ticker: str, period: str, interval: str) -> str:
    key = f"{ticker}_{period}_{interval}"
    return os.path.join(DATA_DIR, f"{key}.parquet")


def fetch_ohlcv(
    ticker: str,
    period: str  = DEFAULT_PERIOD,
    interval: str = DEFAULT_INTERVAL,
    force_refresh: bool = False,
) -> pd.DataFrame:
    """
    Download OHLCV data for *ticker* using yfinance.
    Results are cached as Parquet files (refreshed if > 1 hour old).

    Returns a DataFrame with columns: Open, High, Low, Close, Volume.
    """
    cache_file = _cache_path(ticker, period, interval)

    # Use cache if fresh
    if not force_refresh and os.path.exists(cache_file):
        mtime = datetime.fromtimestamp(os.path.getmtime(cache_file))
        if datetime.now() - mtime < timedelta(hours=1):
            return pd.read_parquet(cache_file)

    # Download fresh data
    tk   = yf.Ticker(ticker)
    df   = tk.history(period=period, interval=interval, auto_adjust=True)
    if df.empty:
        raise ValueError(f"No data returned for ticker '{ticker}'. Check symbol.")

    df.index = pd.to_datetime(df.index)
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    df.to_parquet(cache_file)
    return df


def get_ticker_info(ticker: str) -> dict:
    """Return basic company info as a plain dict (safe for LLM prompt injection)."""
    tk   = yf.Ticker(ticker)
    info = tk.info or {}
    keys = [
        "shortName", "sector", "industry", "country",
        "marketCap", "trailingPE", "forwardPE",
        "dividendYield", "fiftyTwoWeekHigh", "fiftyTwoWeekLow",
        "currentPrice", "currency", "exchange",
        "recommendationKey", "numberOfAnalystOpinions",
    ]
    return {k: info.get(k) for k in keys}


def compute_technicals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Append basic technical indicators to OHLCV DataFrame:
    - SMA_20, SMA_50
    - RSI_14
    - MACD, MACD_signal, MACD_hist
    - Bollinger Bands (BB_upper, BB_lower)
    - ATR_14
    """
    df = df.copy()

    # Simple Moving Averages
    df["SMA_20"] = df["Close"].rolling(20).mean()
    df["SMA_50"] = df["Close"].rolling(50).mean()

    # RSI
    delta = df["Close"].diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rs    = gain / loss.replace(0, float("nan"))
    df["RSI_14"] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"]        = ema12 - ema26
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_hist"]   = df["MACD"] - df["MACD_signal"]

    # Bollinger Bands
    std20         = df["Close"].rolling(20).std()
    df["BB_upper"] = df["SMA_20"] + 2 * std20
    df["BB_lower"] = df["SMA_20"] - 2 * std20

    # ATR
    tr = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - df["Close"].shift()).abs(),
        (df["Low"]  - df["Close"].shift()).abs(),
    ], axis=1).max(axis=1)
    df["ATR_14"] = tr.rolling(14).mean()

    return df


def latest_snapshot(df: pd.DataFrame) -> dict:
    """Return the latest row of technical indicators as a human-readable dict."""
    latest = df.tail(1).iloc[0]
    return {
        "date":        str(latest.name.date()),
        "close":       round(float(latest["Close"]), 4),
        "volume":      int(latest["Volume"]),
        "SMA_20":      round(float(latest["SMA_20"]),  4) if pd.notna(latest["SMA_20"])  else None,
        "SMA_50":      round(float(latest["SMA_50"]),  4) if pd.notna(latest["SMA_50"])  else None,
        "RSI_14":      round(float(latest["RSI_14"]),  2) if pd.notna(latest["RSI_14"])  else None,
        "MACD":        round(float(latest["MACD"]),    4) if pd.notna(latest["MACD"])    else None,
        "MACD_signal": round(float(latest["MACD_signal"]), 4) if pd.notna(latest["MACD_signal"]) else None,
        "BB_upper":    round(float(latest["BB_upper"]), 4) if pd.notna(latest["BB_upper"]) else None,
        "BB_lower":    round(float(latest["BB_lower"]), 4) if pd.notna(latest["BB_lower"]) else None,
        "ATR_14":      round(float(latest["ATR_14"]),  4) if pd.notna(latest["ATR_14"])  else None,
    }
