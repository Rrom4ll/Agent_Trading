# TASK-002 — Baseline QA: Verify and Harden Core Components

| Field | Value |
|---|---|
| **Task ID** | TASK-002 |
| **Title** | Baseline QA — RSI correctness, data freshness, structured output, error handling |
| **Owner** | Antigravity (Developer) |
| **Reviewer** | Codex (Master) |
| **Status** | `ready` |
| **Created** | 2026-09-29 |
| **Spec revision** | v3 — final corrections per Codex review (2026-09-29) |
| **Depends on** | TASK-001 `done` |

---

## Objective

Audit and harden core components against known and potential defects before adding new features.
Read actual source code before asserting that anything is missing or broken.
Do not implement changes until the specification is accepted.

---

## Source Files Under Review

| File | Relevant Concern |
|---|---|
| `src/tools/market_data.py` | RSI implementation, `latest_snapshot()` serialization, cache logic |
| `src/agents/analyst_agent.py` | Prompt schema, streaming vs batch paths, output validation |
| `main.py` | Existing error handlers (lines 74–79 confirmed), stderr behavior |

---

## Outputs (produced when implementation begins)

| Output | Description |
|---|---|
| Updated `src/tools/market_data.py` | RSI correctness and serialization fixes |
| Updated `src/agents/analyst_agent.py` | Structured JSON output, insufficient-data and invalid-response handling |
| Updated `main.py` | Updated for new result types; targeted stderr fix (if required after inspection) |
| `tests/test_market_data.py` | Offline unit tests — RSI, snapshot serialization, freshness fixtures |
| `tests/test_analyst_agent.py` | Offline unit tests — output parsing, both streaming and batch, error paths |
| `docs/progress/TASK-002-result.md` | Evidence: test output, live integration record |

---

## Acceptance Criteria

### A. RSI Correctness

#### A1. Implementation Facts (read before testing)

The current implementation in `market_data.py` uses **simple rolling-mean smoothing (Cutler's RSI)**:

```python
delta = df["Close"].diff()
gain  = delta.clip(lower=0).rolling(14).mean()
loss  = (-delta.clip(upper=0)).rolling(14).mean()
rs    = gain / loss.replace(0, float("nan"))
df["RSI_14"] = 100 - (100 / (1 + rs))
```

Key facts:
- `diff()` produces N−1 values for N closes; the first row is NaN.
- `rolling(14).mean()` requires 14 non-NaN diffs, which requires **at least 15 closing prices**.
- The smoothing method is **simple rolling mean (Cutler's RSI)**, not Wilder's exponential.
  - This **must not be changed silently**. Document the method; any change requires Codex approval.
- Rows with fewer than 14 diffs produce NaN in `RSI_14`. Internal NaN during warm-up is acceptable in the DataFrame.
- `latest_snapshot()` converts NaN to `None` via `if pd.notna(...) else None`.

#### A2. RSI Decisions (chosen for this implementation)

| Scenario | Internal DataFrame value | `latest_snapshot()` value | Rationale |
|---|---|---|---|
| Strictly rising (sufficient history) | 100.0 | 100.0 | All gains, zero losses |
| Strictly falling (sufficient history) | 0.0 | 0.0 | All losses, zero gains |
| Constant prices (14-change window all zero) | NaN | `None` | Both gain and loss means are zero; RS is undefined. Emit NaN internally, serialize as `None`. |
| Insufficient history (< 15 closes) | NaN | `None` | `rolling(14)` cannot produce a value |

Preserve simple rolling-mean smoothing. Do not switch to Wilder's EMA.

#### A3. Test Cases

All tests must be **offline** (no yfinance calls). Use synthetic DataFrames.

| Test ID | Input | Expected `RSI_14` in last row | Notes |
|---|---|---|---|
| A3-a | 30 strictly rising closes (100, 101, …, 129) | 100.0 | All gains, zero losses → RS = ∞ → RSI = 100 |
| A3-b | 30 strictly falling closes (129, 128, …, 100) | 0.0 | All losses, zero gains → RS = 0 → RSI = 0 |
| A3-c | 30 constant closes (all 100.0) | NaN in DataFrame; `None` in snapshot | Both gain and loss rolling means = 0; RS is `gain/NaN` = NaN. This is the chosen policy. |
| A3-d | 14 closes, strictly rising | NaN (only 13 diffs; `rolling(14)` requires 14) → `None` in snapshot | Boundary: 14 closes = 13 diffs = not enough |
| A3-e | 15 closes, strictly rising | 100.0 | Boundary: 15 closes = 14 diffs = exactly enough. Use rising prices to produce a defined RSI. |
| A3-f | 1 close only | NaN → `None` in snapshot — no crash | Degenerate input |

#### A4. Serialization Requirements

- `compute_technicals()` **must continue to return `pd.DataFrame`**. Do not change its return type.
- Internal NaN in indicator columns during warm-up is acceptable in the DataFrame.
- `latest_snapshot()` returns a plain `dict` for JSON serialization:
  - All indicator values must be either a finite Python `float` or `None`.
  - `None` serializes to JSON `null`. This is correct.
  - `float("nan")` and `float("inf")` must **never appear** in the returned dict.
- [ ] Unit test: `json.dumps(latest_snapshot(df), allow_nan=False)` succeeds without raising `ValueError` for **all A3 test cases**.

> **Why `allow_nan=False`:** Default `json.dumps()` silently accepts `NaN` and `Infinity`, producing non-standard JSON. `allow_nan=False` enforces strict JSON compliance and will raise `ValueError` if any non-finite float leaks through.

---

### B. Structured AI Output

#### B1. Current State (read before modifying)

`analyst_agent.py` returns a raw string from the LLM. There is no parser.
`latest_snapshot()` passes `None` for missing indicators, but the prompt does not instruct the LLM to acknowledge the gap — it may hallucinate a value.

#### B2. Minimum Input Requirements

Before calling Ollama, validate the input data. Return `insufficient_data` without requesting a recommendation if:

| Condition | Check |
|---|---|
| Empty DataFrame (no rows) | `df.empty` |
| OHLCV columns contain NaN or non-finite values in the last row | Any of Open, High, Low, Close, Volume is NaN/Inf |
| All required indicators are `None` | All of RSI_14, MACD, SMA_20 are `None` in snapshot |

Required vs optional indicators for calling Ollama:

| Indicator | Required? | Reason |
|---|---|---|
| Close (last row) | ✅ Required | Cannot analyse without a price |
| Volume (last row) | ✅ Required | Cannot analyse without activity data |
| RSI_14 | ❌ Optional | May be `None` for constant prices or insufficient history |
| SMA_20, SMA_50 | ❌ Optional | `None` during warm-up |
| MACD, MACD_signal | ❌ Optional | `None` during warm-up |
| BB_upper, BB_lower | ❌ Optional | `None` during warm-up |
| ATR_14 | ❌ Optional | `None` during warm-up |

> A `None` RSI does not always mean "insufficient price history" — it can also mean prices were constant. The prompt must describe the actual reason (e.g., "RSI_14: null — prices constant over 14-day window" or "RSI_14: null — fewer than 15 closes available").

#### B3. Required Output Format

Prefer **one JSON object** with runtime validation. Define a schema:

```python
# Illustrative — exact implementation decided during TASK-002
@dataclass
class AnalysisResult:
    trend:          str   # free text, max 200 chars
    signals:        str   # free text, max 400 chars
    recommendation: str   # exactly one of: "BUY", "HOLD", "SELL"
    risks:          str   # free text, max 400 chars
    raw_response:   str   # unmodified model output

@dataclass
class AnalysisError:
    error_type: str       # one of: "insufficient_data", "malformed_response", "model_unavailable"
    detail:     str
    raw_response: str | None
```

Runtime validation on `AnalysisResult`:
- [ ] `recommendation` is exactly one of `"BUY"`, `"HOLD"`, `"SELL"`. No coercion: `"CAUTIOUS BUY"` → `malformed_response`.
- [ ] `trend` length ≤ 200 chars.
- [ ] `signals` and `risks` length ≤ 400 chars each.
- [ ] Field types checked: all `str`, none `None`.

`analyse()` must return either `AnalysisResult` or `AnalysisError`. It must never return a raw string.

#### B4. Insufficient-Data and Invalid-Response Handling

- If pre-call validation fails (per B2): return `AnalysisError(error_type="insufficient_data")` without calling Ollama at all.
- If `latest_snapshot()` returns `None` for any optional indicator, the prompt must state the actual reason:
  - `"RSI_14: null (constant prices — indicator undefined)"` — not "insufficient history" when history exists.
  - `"RSI_14: null (fewer than 15 closing prices available)"`
- The parser must detect if the model invents a numeric RSI when the prompt said it was null. If detected, return `AnalysisError(error_type="malformed_response")`.
- A `malformed_response` warning must be logged; the response must not be silently accepted.
- **Prompt instructions alone do not guarantee** that the LLM will obey. Document which checks are programmatic and which remain best-effort (see B6).

#### B5. Recommendation Extraction

- Extract `recommendation` from the response text using a defined pattern (e.g., regex on known section header or JSON key).
- If the extracted value is not exactly one of `"BUY"`, `"HOLD"`, `"SELL"`, return `AnalysisError(error_type="malformed_response")`.
- **Do not coerce or guess.**

#### B6. Streaming vs Batch

Both code paths exist in `analyst_agent.py`:

| Path | Current behavior | Required change |
|---|---|---|
| Batch (`stream=False`) | Returns full string from `resp.message.content` | Parse and validate before returning `AnalysisResult` or `AnalysisError` |
| Streaming (`stream=True`) | Accumulates chunks, returns `full_response` string | **Streamed content is unvalidated until accumulation completes.** Either: (a) buffer all chunks silently, then parse and validate, or (b) print chunks in real time but clearly mark the output as unvalidated until the final parse. |

- [ ] Both paths return `AnalysisResult` or `AnalysisError`, never a raw string.
- [ ] Streaming path does not attempt to parse mid-stream.
- [ ] Both paths tested offline with mocked Ollama client.

#### B7. Callers

Update all callers for the new return types:

| Caller | File | Required change |
|---|---|---|
| `main()` loop | `main.py` | Handle `AnalysisResult` (display) and `AnalysisError` (display error cleanly) |
| `multi_analyse()` | `analyst_agent.py` | Return `dict[str, AnalysisResult | AnalysisError]` |

#### B8. Programmatic Checks vs LLM Limitations

Document explicitly in `TASK-002-result.md`:

| Claim | Can be checked programmatically? |
|---|---|
| `recommendation` is exactly BUY/HOLD/SELL | ✅ Yes — enum parse |
| All four fields present and within length limits | ✅ Yes — type/length check |
| RSI not invented when prompt said null | ⚠️ Partially — detect numeric RSI in response text when prompt declared null |
| Qualitative accuracy of trend summary | ❌ No — LLM judgment, cannot be tested |
| Model always follows JSON schema instructions | ❌ No — prompt compliance is not guaranteed |

---

### C. Data Freshness

#### C1. Two Separate Checks (do not conflate)

| Check | What it measures | Threshold | Already implemented? |
|---|---|---|---|
| **Cache age** | File modification time vs now | > 1 hour → re-download | ✅ Yes (`market_data.py` lines 39–42) |
| **Market data currency** | Latest row date vs last completed trading session | Earlier than the last completed trading session → warning | ❌ Not implemented |

#### C2. Market Data Currency Requirements

Before implementing, specify and document:

| Parameter | Specification |
|---|---|
| **Timezone** | Use **timezone-aware timestamps**: `Asia/Bangkok` for Thai (`.BK`) tickers; `America/New_York` for US tickers. Do not hardcode numeric offsets (UTC-5 is incorrect during DST — New York observes EDT = UTC-4). |
| **Market close** | Thai SET: 16:30 Asia/Bangkok; US NYSE/NASDAQ: 16:00 America/New_York |
| **Session schedule** | Verify open/close times against the chosen authoritative calendar source. Account for special sessions (half days, early closes). If calendar does not cover special sessions, document that limitation. |
| **Calendar source** | Must be specified. Options: `pandas_market_calendars`, `exchange_calendars`, a static holiday list, or no calendar. |
| **Supported date range** | Set explicitly. Do not claim correctness beyond tested dates. |
| **Stale definition** | Data is stale if and only if a newer completed trading session exists that the data does not include. Yesterday's data is stale on Tuesday (a newer Monday session exists) but **not stale** on Monday morning before market open (no newer completed session yet). |

> **If a calendar library is not available or not installed:**
> Do not claim holiday-aware validation. Return:
> `"Market data currency: unverified — no calendar source configured."`
> Document this limitation in `TASK-002-result.md`.

> **If a calendar is available but does not cover special sessions:**
> Document the gap. Do not claim full accuracy.

#### C3. Freshness Test Fixtures

All freshness tests must use **deterministic fixtures** — do not call `datetime.now()` in test bodies.
Inject a `reference_time` parameter or monkeypatch. Specify exact reference timestamps.

| Test ID | Latest row date | Reference time | Calendar available? | Expected outcome |
|---|---|---|---|---|
| C3-a | Friday 2026-09-25 | Friday 2026-09-25 17:00 America/New_York | Yes | No warning (same-session data) |
| C3-b | Friday 2026-09-25 | Monday 2026-09-28 08:00 America/New_York | Yes | No warning (no completed session since Friday close) |
| C3-c | Tuesday 2026-09-23 | Friday 2026-09-26 17:00 America/New_York | Yes | Warning (Wed/Thu/Fri sessions completed since last data) |
| C3-d | Thursday 2026-09-25 | Friday 2026-09-26 10:00 Asia/Bangkok | Yes | Warning (Friday session completed; Thursday data is stale) |
| C3-e | Any date | Any date | No | Warning: "Market data currency: unverified — no calendar source configured" |

> Fixtures C3-a through C3-d must use specific dates whose session schedules can be verified against the chosen calendar source. If using a public holiday in a test, verify that the calendar marks it correctly.

---

### D. Error Handling

#### D1. Inspect Existing Handlers First

Confirmed from source review (do not re-assert as missing):

- `main.py` lines 74–79: `try/except Exception` around `agent.analyse(ticker, stream=stream)` — catches all exceptions per ticker, prints `[red]ERROR analysing {ticker}: {exc}[/red]`, continues to next ticker.
- `fetch_ohlcv()` line 48: raises `ValueError` for empty yfinance response — caught by the above.

#### D2. Confirmed Gap (from live test 2026-09-29)

```
Command: python main.py INVALID_TICKER_XYZ123 --no-stream
Observed: HTTP 404 error text and yfinance warning printed to stderr
          BEFORE the ValueError is raised and caught by try/except.
```

The `try/except` block is functioning correctly. The stderr leak is from yfinance's internal logging/urllib, which fires before Python control returns to the `except` clause.

#### D3. Fix Requirements

- **Identify the actual source** of the unwanted messages before selecting a filter. Determine whether they come from the `logging` module (and which logger), `warnings.warn()`, or direct `sys.stderr.write()`.
- Fix must be **targeted**: suppress only the identified source during the yfinance call.
- Do **not** use `contextlib.redirect_stderr` — it redirects all process-wide stderr and would suppress unrelated diagnostics.
- Do **not** globally suppress `sys.stderr` or all warnings.
- Acceptable approaches after source identification: `logging.getLogger("<identified>").setLevel(...)`, `warnings.filterwarnings(...)` scoped to yfinance, or a context manager that adjusts the specific logger level.
- Preserve diagnostic logs from other sources.
- After fix: running `python main.py INVALID_TICKER --no-stream` must produce clean user output with no HTTP stack trace on stderr.

#### D4. Additional Error Paths to Test (offline)

| Test ID | Scenario | Expected behavior |
|---|---|---|
| D4-a | Empty DataFrame passed to `compute_technicals()` | No crash; returns DataFrame with NaN indicator columns; `latest_snapshot()` returns all `None` indicators |
| D4-b | Invalid ticker (mocked yfinance returns empty) | `ValueError` raised by `fetch_ohlcv()`; caught cleanly by `main.py` try/except |
| D4-c | yfinance returns data but Ollama is unavailable (mocked connection error) | `AnalysisError(error_type="model_unavailable")` returned; no crash |
| D4-d | Ollama returns empty string or `None` content (mocked) | `AnalysisError(error_type="malformed_response")` returned |
| D4-e | Malformed model output: missing sections (mocked) | `AnalysisError(error_type="malformed_response")` returned |

---

### E. Thai Ticker Live Integration

#### E1. Offline vs Live Separation

- All tests in sections A–D must pass **without network access and without Ollama running**.
- Use `unittest.mock` or `pytest` fixtures to mock yfinance and the Ollama client.
- Live tests are recorded separately and do not gate the offline test suite.

#### E2. Live Thai Ticker Record

One live integration check must be run and recorded. Record all fields below:

| Field | Value (fill in during task) |
|---|---|
| Ticker tested | e.g., `PTT.BK` |
| Data source | yfinance |
| Latest row date in response | (actual date returned) |
| Ollama model | qwen3.5:4b |
| Command used | `python main.py PTT.BK --no-stream` |
| Python process exit code | (actual — record from `echo $LASTEXITCODE` or equivalent) |
| Output summary | (first 200 chars of analysis) |
| Errors or warnings on stderr | (any stderr output, verbatim) |
| Test date and time | (actual, timezone-aware) |

> **Scope limitation:** One successful `.BK` test confirms that `PTT.BK` works at that moment.
> It does **not** establish that all SET50 tickers are supported, that yfinance reliably
> provides Thai data, or that data quality meets trading requirements.
> State this limitation explicitly in `TASK-002-result.md`.

---

## Scope Exclusions

- Do NOT add trading features or Dashboard
- Do NOT add new AI models or change Ollama configuration
- Do NOT change the RSI smoothing method without explicit Codex approval and documentation
- Do NOT modify `AGENTS.md`, task board, or other coordination files
- KGI API integration is a **possible future direction** — not an approved goal for this or any current task

---

## Definition of Done

All offline tests pass with `pytest tests/ -v` (no network, no Ollama).
Live integration record is complete with all fields filled.
`TASK-002-result.md` documents: test output, serialization check (with `allow_nan=False`), freshness behavior (or explicit "unverified" if no calendar), stderr fix with identified source, programmatic-vs-LLM limitations table, and Thai ticker record with scope limitation.
Codex has verified evidence and set status to `done`.
