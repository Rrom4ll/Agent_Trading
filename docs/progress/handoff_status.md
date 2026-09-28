# KGI AI Trading Agent - Project Status & Handoff

**Last Updated:** 2026-09-28
**Environment:** Python 3.14+, Node.js v24+, Git, Ollama (`qwen3.5:4b`)

---

## 1. Project Overview
This project is an AI-powered stock analysis agent designed for educational and paper trading purposes. It uses `yfinance` to fetch market data, computes technical indicators, and leverages a local LLM via **Ollama** to analyze the data and provide **BUY / HOLD / SELL** recommendations.

## 2. Current Progress & Implemented Features

### ✅ Core Infrastructure
- **Project Structure**: Established a modular structure (`config/`, `src/agents/`, `src/tools/`).
- **Dependencies Management**: Created `requirements.txt` and `.env.example`. Installed `yfinance`, `pandas`, `ollama`, `rich`, `pyarrow`, etc.

### ✅ Market Data Pipeline (`src/tools/market_data.py`)
- **Data Fetching**: Pulls OHLCV and fundamental data from Yahoo Finance (`yfinance`).
- **Technical Analysis**: Automatically computes key indicators:
  - SMA (20, 50)
  - RSI (14)
  - MACD & MACD Signal
  - Bollinger Bands
  - ATR (14)
- **Caching Mechanism**: Implemented `.parquet` caching to store data locally and reduce redundant API calls (1-hour cache lifetime).

### ✅ AI Analyst Agent (`src/agents/analyst_agent.py`)
- **Ollama Integration**: Fully integrated with a local Ollama instance (default model: `qwen3.5:4b`).
- **Prompt Engineering**: The agent is explicitly prompted as "FinBot" (an educational research bot) to bypass standard LLM financial advice refusals. It enforces structured outputs including Trend, Key Signals, Recommendations, and Risks.
- **Streaming & Performance**: Handled `qwen3.5:4b`'s Chain-of-Thought (CoT) behavior by utilizing `think=False` in the Ollama SDK, ensuring immediate and clean streaming outputs without thousands of empty `<think>` chunks.

### ✅ CLI Interface (`main.py`)
- Built a rich, formatted command-line interface.
- Supports single or multiple ticker arguments (e.g., `python main.py AAPL MSFT`).
- Supports both streaming (default) and batch (`--no-stream`) output modes.

---

## 3. Directory Structure

```text
Agent_Trading/
├── config/
│   ├── __init__.py
│   └── settings.py          # Centralized configuration (Ollama URL, default tickers)
├── docs/
│   └── progress/
│       └── handoff_status.md # Current file (Project status & history)
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   └── analyst_agent.py # AI LLM Agent handling logic
│   ├── tools/
│   │   ├── __init__.py
│   │   └── market_data.py   # yfinance integration & Technical Analysis
│   └── data/
│       └── cache/           # Parquet cache files for market data
├── .env.example
├── .gitignore
├── debug_stream.py          # Dev script for testing LLM streaming responses
├── main.py                  # Main CLI entry point
└── requirements.txt
```

---

## 4. Antigravity AI Implementation Notes (Resolved Issues)

- **Execution Policy**: Resolved initial PowerShell execution policy blocks preventing `npm` and other tools from running.
- **Qwen 3.5 Streaming Issue**: Qwen 3.5 models separate their output into `thinking` and `content`. During streaming, the AI originally printed empty lines for thousands of chunks while "thinking". **Fix applied:** Added `**{"think": False}` to the Ollama SDK call to bypass the `<think>` process, resulting in instantaneous, readable streaming responses.
- **LLM Safety Refusal**: The AI initially refused to give recommendations ("I cannot provide financial advice"). **Fix applied:** Refined the `SYSTEM_PROMPT` to enforce an educational/paper-trading context, compelling the AI to analyze the data without ethical blockages.

---

## 5. Next Steps / Roadmap for Continued Development

If you are picking up this code, here are the logical next steps:

1. **Dashboard / UI Development**:
   - Create a web dashboard (e.g., using Streamlit, Gradio, or Next.js) to visualize the OHLCV charts, overlay the technical indicators, and display the LLM's analysis side-by-side.
2. **Paper Trading Engine**:
   - Implement a simulated portfolio tracker.
   - Allow the agent (or user) to execute simulated trades based on the BUY/SELL signals, tracking P&L (Profit & Loss).
3. **Multi-Agent Architecture**:
   - **Screener Agent**: Scans thousands of tickers to find setups.
   - **Analyst Agent**: Deep-dives into specific tickers (Current implementation).
   - **Risk Manager Agent**: Calculates position sizing and stop-loss levels based on ATR.
4. **KGI Broker Integration**:
   - Once the strategies are proven in paper trading via `yfinance`, swap out the data ingestion and order execution modules to use the actual **KGI API**.
