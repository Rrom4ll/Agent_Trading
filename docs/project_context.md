# Project Context
# KGI AI Trading Agent

> **Read this file before starting any task.**
> Last updated: 2026-09-29 | Maintained by: Antigravity

---

## 1. Project Goal

Build an AI-powered stock analysis and paper trading system that:
1. Fetches market data for **SET50** Thai stocks (and US stocks for validation)
2. Computes technical indicators automatically
3. Uses a **local LLM (Ollama)** to generate structured BUY / HOLD / SELL analysis
4. Supports **paper trading simulation** (no real money, no broker connection)

> **Note:** KGI broker API integration has been mentioned as a possible future direction but has **not been agreed upon or approved**. It must not be treated as a confirmed roadmap item.

---

## 2. Agreed Constraints (Current Phase)

| Constraint | Detail |
|---|---|
| **No real trading** | Paper trading only. No real-money orders. |
| **No broker API** | No live order routing. KGI API is unapproved future direction. |
| **No Dashboard yet** | UI development is next phase |
| **Local LLM only** | Ollama (`qwen3.5:4b`) — no external AI API calls in application |
| **SET50 focus** | Primary market. US tickers used for testing only. |
| **yfinance as data source** | Live broker data feed is future work |

---

## 3. Current Technical State (as of 2026-09-29)

### Repository
- **GitHub:** `https://github.com/Rrom4ll/Agent_Trading.git`
- **Branch:** `main` — 7 commits (5 pushed, 2 local-only)
- **Working tree:** Clean

### Implemented & Verified
| Component | File | Status |
|---|---|---|
| Market data pipeline | `src/tools/market_data.py` | ✅ Verified — AAPL tested end-to-end |
| Technical indicators | `src/tools/market_data.py` | ✅ SMA/RSI/MACD/BB/ATR computed |
| Parquet cache | `src/data/cache/` | ✅ 1hr TTL implemented |
| AI Analyst Agent | `src/agents/analyst_agent.py` | ✅ Verified — AAPL produced HOLD output |
| Ollama integration | `src/agents/analyst_agent.py` | ✅ `think=False` applied; streaming works |
| CLI entry point | `main.py` | ✅ `try/except` per ticker; streaming + batch |
| Config system | `config/settings.py` | ✅ dotenv-based |

### Known Issues / Unverified Items
| Item | Status | Detail |
|---|---|---|
| RSI: < 14 bars (rising) | `[UNVERIFIED]` | No test; may raise ZeroDivisionError or return NaN |
| RSI: < 14 bars (falling) | `[UNVERIFIED]` | Same as above |
| RSI: constant price | `[UNVERIFIED]` | Division by zero risk in gain/loss calculation |
| Market data currency check | `[UNVERIFIED]` | Cache TTL exists; market-day awareness does not |
| AI response format validation | `[UNVERIFIED]` | No parser; malformed output passed through raw |
| stderr noise from yfinance | `[PARTIAL]` | `try/except` catches exception; HTTP 404 stack trace leaks to stderr |
| SET50 Thai tickers (`.BK`) | `[UNVERIFIED]` | Only US tickers tested. `PTT.BK` format not confirmed. |

---

## 4. Tool Readiness (confirmed 2026-09-29)

| Tool | Version | Non-interactive | Status | Evidence |
|---|---|---|---|---|
| Python | 3.14.7 | ✅ Yes | Ready | `python --version` |
| Git | 2.55.0 | ✅ Yes | Ready | `git --version` |
| Ollama CLI | 0.34.4 | ✅ Yes | Installed; headless test unverified | `ollama --version` |
| `qwen3.5:4b` model | 3a145e630c7b | ✅ Loaded | Ready | `ollama list` |
| `agy` CLI (Antigravity) | 1.0.3 | ✅ `--print` flag | Installed; headless test unverified | `agy --version`; `--print` confirmed in help text |
| Gemini CLI | 0.61.0 | ✅ `--prompt --skip-trust` | Partially verified | Responds to prompt. Code review NOT yet tested. |
| yfinance | 1.7.0 | ✅ Python lib | Ready | AAPL analysis succeeded |
| pandas | 3.0.6 | ✅ Python lib | Ready | Used in market_data.py |
| ollama SDK | 0.6.2 | ✅ Python lib | Ready | AAPL analysis succeeded |

> **Gemini note:** "Responds to prompt" ≠ "can perform read-only code review". The latter has not been tested. Do not claim it works for code review until a structured code review task has been completed successfully.

> **`agy --print` note:** Background headless test produced no output; cause unverified. Cannot determine suitability for automation from this single observation. Human relay is the current coordination mode.

---

## 5. Directory Structure

```text
Agent_Trading/
├── AGENTS.md                       # Team charter and rules
├── .env.example                    # Template for local secrets
├── .gitignore                      # Python + secrets excluded
├── config/
│   ├── __init__.py
│   └── settings.py                 # Central config (Ollama URL, tickers, paths)
├── docs/
│   ├── project_context.md          # This file
│   ├── progress/
│   │   ├── handoff_status.md       # Session 1 summary
│   │   ├── task_board.md           # Task status tracker
│   │   └── TASK-001-result.md      # Evidence for TASK-001
│   └── tasks/
│       ├── TASK-001.md             # Task definition: Setup coordination
│       └── TASK-002.md             # Task definition: Baseline QA (ready)
├── main.py                         # CLI entry point
├── debug_stream.py                 # Dev utility: stream chunk inspector
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   └── analyst_agent.py        # AnalystAgent — application component using Ollama
│   ├── tools/
│   │   ├── __init__.py
│   │   └── market_data.py          # yfinance + technical indicators
│   └── data/
│       └── cache/                  # Parquet files (gitignored)
└── tests/                          # Empty — planned for TASK-002
```

---

## 6. Upcoming Work

| Task | Priority | Status |
|---|---|---|
| TASK-001: Setup coordination system | High | `review` |
| TASK-002: Baseline QA | High | `ready` |
| TASK-003: SET50 ticker validation | Medium | Not yet defined |
| TASK-004: Structured AI output (JSON schema) | Medium | Folded into TASK-002 |
| TASK-005: Paper trading engine | Low | Not yet defined |
| TASK-006: Dashboard / UI | Low | Not yet defined |
