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
4. Supports **paper trading simulation** (no real money, no broker connection yet)
5. Eventually integrates with KGI broker API — **not in current phase**

---

## 2. Agreed Constraints (Current Phase)

| Constraint | Detail |
|---|---|
| **No real trading** | Paper trading only. No real-money orders. |
| **No KGI API** | Broker integration is future work |
| **No Dashboard yet** | UI development is next phase |
| **Local LLM only** | Ollama (`qwen3.5:4b`) — no external AI API calls |
| **SET50 focus** | Primary market. US tickers used for testing only. |
| **yfinance as data source** | Real broker data feed is future work |

---

## 3. Current Technical State (as of 2026-09-29)

### Repository
- **GitHub:** `https://github.com/Rrom4ll/Agent_Trading.git`
- **Branch:** `main` — 3 commits
- **Working tree:** Clean

### Implemented & Verified
| Component | File | Status |
|---|---|---|
| Market data pipeline | `src/tools/market_data.py` | ✅ Working |
| Technical indicators | `src/tools/market_data.py` | ✅ SMA/RSI/MACD/BB/ATR |
| Parquet cache | `src/data/cache/` | ✅ Working (1hr TTL) |
| AI Analyst Agent | `src/agents/analyst_agent.py` | ✅ Working |
| Ollama integration | `src/agents/analyst_agent.py` | ✅ think=False applied |
| CLI entry point | `main.py` | ✅ Streaming + batch |
| Config system | `config/settings.py` | ✅ dotenv-based |

### Known Issues / Unverified Items
| Item | Status | Note |
|---|---|---|
| RSI edge cases (< 14 bars) | `[UNVERIFIED]` | No test for short history |
| Data freshness validation | `[UNVERIFIED]` | Cache may serve stale data |
| SET50 tickers | `[UNVERIFIED]` | Only US tickers tested so far |
| Thai stock format `.BK` | `[UNVERIFIED]` | e.g., `PTT.BK` — yfinance format unconfirmed |
| AI response format consistency | `[UNVERIFIED]` | No structured output parsing yet |
| Error handling (bad ticker) | `[PARTIAL]` | ValueError raised but not caught gracefully in CLI |

---

## 4. Tool Readiness (confirmed 2026-09-29)

| Tool | Version | Headless/Non-interactive | Status |
|---|---|---|---|
| Python | 3.14.7 | ✅ Yes | Ready |
| Git | 2.55.0 | ✅ Yes | Ready |
| Ollama CLI | 0.34.4 | ✅ Yes (`ollama run model "prompt"`) | Ready |
| `qwen3.5:4b` model | 3a145e630c7b | ✅ Loaded (3.4 GB) | Ready |
| `agy` CLI (Antigravity) | 1.0.3 | ✅ Yes (`agy --print "..."`) | Ready |
| Gemini CLI | 0.61.0 | ⛔ Auth broken | BLOCKED |
| yfinance | 1.7.0 | ✅ (Python lib) | Ready |
| pandas | 3.0.6 | ✅ (Python lib) | Ready |
| ollama SDK | 0.6.2 | ✅ (Python lib) | Ready |

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
│   └── progress/
│       ├── handoff_status.md       # Historical handoff from session 1
│       ├── task_board.md           # All tasks and their statuses
│       ├── TASK-001-result.md      # Evidence for TASK-001
│       └── TASK-002-result.md      # (future)
├── docs/
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
│   │   └── analyst_agent.py        # AnalystAgent — Ollama integration
│   ├── tools/
│   │   ├── __init__.py
│   │   └── market_data.py          # yfinance + technical indicators
│   └── data/
│       └── cache/                  # Parquet files (gitignored)
└── tests/                          # Empty — planned for TASK-002
```

---

## 6. Upcoming Work

| Task | Priority | Phase |
|---|---|---|
| TASK-002: Baseline QA (RSI edge cases, data quality, error handling) | High | Current |
| TASK-003: SET50 ticker validation | High | Current |
| TASK-004: Structured AI output (JSON schema) | Medium | Next |
| TASK-005: Paper trading engine | Medium | Next |
| TASK-006: Dashboard / UI | Low | Future |
| TASK-007: KGI API integration | Low | Future |
