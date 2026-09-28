"""
Project-wide settings and configuration.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ─── Ollama ───────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL",    "qwen3.5:4b")

# ─── Default tickers to watch ─────────────────────────────────────────────────
DEFAULT_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",   # US Tech
    "PTT.BK", "AOT.BK", "DELTA.BK",             # Thai SET (example)
]

# ─── Data window ──────────────────────────────────────────────────────────────
DEFAULT_PERIOD   = "6mo"   # yfinance period string
DEFAULT_INTERVAL = "1d"    # yfinance interval string

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = os.path.join(BASE_DIR, "src", "data", "cache")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
