# TASK-002 — Baseline QA: Verify and Fix Core Components

| Field | Value |
|---|---|
| **Task ID** | TASK-002 |
| **Title** | Baseline QA — RSI edge cases, data quality, AI output format, error handling |
| **Owner** | Antigravity (Developer) |
| **Reviewer** | Codex (Master) |
| **Status** | `ready` |
| **Created** | 2026-09-29 |
| **Depends on** | TASK-001 `done` |

---

## Objective

Audit and harden the baseline components implemented in session 1. Identify and fix known gaps before adding new features.

---

## Inputs

- `src/tools/market_data.py` — data pipeline
- `src/agents/analyst_agent.py` — AI analyst
- `main.py` — CLI
- `docs/project_context.md` — known issues list

---

## Outputs (to be produced when task starts)

| Output | Description |
|---|---|
| Updated `market_data.py` | RSI guarded for < 14 bars; data freshness validated |
| Updated `analyst_agent.py` | Consistent structured output format |
| Updated `main.py` | Graceful error handling for bad tickers |
| `tests/test_market_data.py` | Unit tests for RSI edge cases |
| `docs/progress/TASK-002-result.md` | Evidence of fixes |

---

## Acceptance Criteria

- [ ] RSI returns `None` (not NaN or crash) when fewer than 14 price bars are available
- [ ] Data cache age is validated; stale data (> 24h) triggers a warning
- [ ] AI response always includes `TREND`, `SIGNALS`, `RECOMMENDATION`, `RISKS` sections
- [ ] Running `python main.py INVALID_TICKER` shows a clean user-facing error, not a Python traceback
- [ ] At least one SET50 Thai ticker (`.BK` format) tested end-to-end via yfinance
- [ ] All changes committed with tests passing

---

## Known Issues to Address (from `docs/project_context.md`)

| Item | File | Fix Needed |
|---|---|---|
| RSI edge cases (< 14 bars) | `market_data.py` | Guard with `if len(df) < 14: return None` |
| Data freshness validation | `market_data.py` | Warn if cache age > 24h |
| SET50 Thai tickers (`.BK`) | `settings.py` + test | Add Thai tickers, verify yfinance compatibility |
| AI response format inconsistency | `analyst_agent.py` | Define structured output schema |
| Error handling (bad ticker) | `main.py` | Catch ValueError, print clean message |

---

## Scope Exclusions

- Do NOT add trading features
- Do NOT add Dashboard
- Do NOT change team charter or task board structure
