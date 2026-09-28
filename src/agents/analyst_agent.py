"""
analyst_agent.py — AI Agent that analyses a stock using Ollama + yfinance data.
"""
import sys
import os
import json

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import ollama
from config.settings import OLLAMA_MODEL, OLLAMA_BASE_URL
from src.tools.market_data import (
    fetch_ohlcv,
    get_ticker_info,
    compute_technicals,
    latest_snapshot,
)

# ─── Prompt Templates ─────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are FinBot, an educational AI stock analysis assistant used for research and paper trading simulations.
You are NOT giving real financial advice — this is a backtesting and learning environment.

Your role:
1. Analyse the technical indicators and fundamentals provided in the user's message.
2. Identify key signals: trend direction, momentum, overbought/oversold conditions.
3. Give a clear, structured educational analysis with a BUY / HOLD / SELL suggestion.
4. Mention 2–3 key risks.
5. Always remind the user this is for educational purposes, not real trading advice.
6. Use plain English. Keep the answer under 400 words.

IMPORTANT: You MUST give a BUY / HOLD / SELL suggestion based on the data provided.
Do NOT refuse or say you cannot analyse stocks — the data is already given to you.
"""

ANALYSIS_TEMPLATE = """\
Please analyse the following stock data and give me a trading recommendation.

=== COMPANY INFO ===
{info_json}

=== LATEST TECHNICAL INDICATORS ===
{snapshot_json}

=== RECENT PRICE TREND (last 10 sessions) ===
{recent_prices}

Based on the above, provide:
1. **Trend summary** — Is the stock in an uptrend, downtrend, or sideways?
2. **Key signals** — What do RSI, MACD, and Bollinger Bands tell you?
3. **Recommendation** — BUY / HOLD / SELL with a brief rationale.
4. **Risks** — List 2–3 key risks an investor should watch.
"""


# ─── Agent class ──────────────────────────────────────────────────────────────

class AnalystAgent:
    """Single-stock analyst powered by Ollama (local LLM)."""

    def __init__(self, model: str = OLLAMA_MODEL):
        self.model  = model
        self.client = ollama.Client(host=OLLAMA_BASE_URL)

    def _build_prompt(self, ticker: str) -> str:
        """Fetch data and render the analysis prompt."""
        # 1) Market data
        df    = fetch_ohlcv(ticker)
        df    = compute_technicals(df)
        snap  = latest_snapshot(df)

        # 2) Recent prices (last 10 sessions)
        recent = df["Close"].tail(10).round(4)
        recent_str = "\n".join(
            f"  {str(d.date())}  {price}" for d, price in recent.items()
        )

        # 3) Company fundamentals
        info = get_ticker_info(ticker)

        return ANALYSIS_TEMPLATE.format(
            info_json     = json.dumps(info, indent=2, default=str),
            snapshot_json = json.dumps(snap, indent=2),
            recent_prices = recent_str,
        )

    def analyse(self, ticker: str, stream: bool = True) -> str:
        """
        Run the full analysis pipeline for *ticker*.
        Returns the LLM's response text.

        Note: qwen3.5:4b uses chain-of-thought thinking.
        We pass think=False to suppress CoT and get immediate streaming output.
        """
        print(f"\n🔍 Fetching data for {ticker} …")
        prompt = self._build_prompt(ticker)

        print(f"🤖 Asking {self.model} to analyse …\n")
        print("─" * 60)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ]

        # think=False suppresses chain-of-thought for qwen3 models
        # making streaming output appear immediately without 1000+ empty chunks
        extra_kwargs = {"think": False}

        if stream:
            full_response = ""
            for chunk in self.client.chat(
                model=self.model,
                messages=messages,
                stream=True,
                **extra_kwargs,
            ):
                text = chunk.message.content or ""
                if text:
                    print(text, end="", flush=True)
                    full_response += text
            print("\n" + "─" * 60)
            return full_response
        else:
            resp = self.client.chat(
                model=self.model,
                messages=messages,
                **extra_kwargs,
            )
            return resp.message.content or ""

    def multi_analyse(self, tickers: list[str]) -> dict[str, str]:
        """Analyse multiple tickers and return a dict of {ticker: analysis}."""
        results = {}
        for ticker in tickers:
            try:
                results[ticker] = self.analyse(ticker)
            except Exception as e:
                results[ticker] = f"ERROR: {e}"
        return results
