# TASK-002 — Baseline QA: Verify and Harden Core Components

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

Audit and harden core components before adding new features. Fix confirmed gaps; investigate potential gaps by reading actual code first — do not assume something is missing.

---

## Inputs

- `src/tools/market_data.py` — data pipeline and technical indicators
- `src/agents/analyst_agent.py` — AI analyst and prompt logic
- `main.py` — CLI entry point (has existing `try/except` per ticker)
- `docs/project_context.md` — known issues list

---

## Outputs (to be produced when task starts)

| Output | Description |
|---|---|
| Updated `market_data.py` | RSI guarded for all edge cases; data date validation added |
| Updated `analyst_agent.py` | Structured, machine-verifiable output format; handle malformed response |
| Updated `main.py` | Suppress stderr noise from yfinance HTTP errors (if not already handled) |
| `tests/test_market_data.py` | Unit tests covering all RSI and data edge cases |
| `docs/progress/TASK-002-result.md` | Evidence of all fixes with test output |

---

## Acceptance Criteria

### A. RSI Edge Cases
Test all four data conditions for RSI calculation:

| Condition | Expected Behaviour |
|---|---|
| Price continuously rising (< 14 bars) | RSI returns `None` — not NaN, not crash |
| Price continuously falling (< 14 bars) | RSI returns `None` — not NaN, not crash |
| Price constant / no change | RSI does not divide-by-zero; returns `None` or defined constant |
| Fewer than 14 bars total | RSI returns `None` — guarded at source, not patched downstream |

- [ ] `latest_snapshot()` never raises `ZeroDivisionError` or propagates `NaN` to the LLM prompt
- [ ] Unit tests cover all four conditions above

### B. Data Date Validation
Two separate checks — do not conflate:

| Check | Condition | Action |
|---|---|---|
| **Cache age** | File mtime > 1 hour | Re-download from yfinance (already implemented) |
| **Market data currency** | Latest row date is older than expected given market hours and known holidays | Emit a **warning** (not an error) — do not refuse to run |

- [ ] Market data currency check accounts for weekends and Thai/US market holidays
- [ ] Warning is emitted to stderr or log, not silently swallowed
- [ ] Test demonstrates warning fires correctly for stale market data

### C. AI Output Format
- [ ] Define a required output schema with these four sections: `TREND`, `SIGNALS`, `RECOMMENDATION` (must be one of: BUY / HOLD / SELL), `RISKS`
- [ ] The prompt explicitly requires this schema
- [ ] A parser function validates the response contains all four sections
- [ ] If response is malformed or missing a section, return a structured error object — do not pass raw malformed text downstream
- [ ] If input data is insufficient (e.g., RSI is `None`), the prompt must note the gap and the LLM must not hallucinate an RSI value

### D. Error Handling Review
> **Note:** `main.py` already contains a `try/except Exception` block around each ticker (lines 74–79). Investigate before claiming anything is missing.

- [ ] Read and document what the current `try/except` in `main.py` catches and what it misses
- [ ] Verify whether HTTP 404 stderr noise from yfinance leaks past the handler (observed in testing: it does)
- [ ] If stderr leaks, fix by redirecting yfinance's output or filtering stderr at the CLI level
- [ ] All error messages shown to the user are clean and user-facing — no raw Python tracebacks

### E. SET50 Thai Ticker Validation
- [ ] Test at least one `.BK` ticker (e.g., `PTT.BK`) end-to-end via yfinance
- [ ] Confirm OHLCV, technicals, and LLM analysis all work for Thai market data
- [ ] Document whether `.BK` suffix format is reliably supported

---

## Scope Exclusions

- Do NOT add trading features or Dashboard
- Do NOT add new AI models or change Ollama configuration
- Do NOT change team charter, AGENTS.md, or task board structure
- KGI API integration is a **possible future direction** — not an approved goal for this task

---

## Notes on KGI API

KGI broker API integration has been mentioned as a potential future direction but has **not been agreed upon or approved**. It must not appear as a confirmed roadmap item until the Project Owner explicitly approves it.
