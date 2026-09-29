# TASK-002 — Baseline QA: Verify and Harden Core Components

| Field | Value |
|---|---|
| **Task ID** | TASK-002 |
| **Title** | Baseline QA — RSI correctness, data freshness, structured output, error handling |
| **Owner** | Antigravity (Developer) |
| **Reviewer** | Codex (Master) |
| **Status** | `ready` |
| **Created** | 2026-09-29 |
| **Spec revision** | v2 — updated per Codex review (2026-09-29) |
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
| Updated `src/agents/analyst_agent.py` | Structured output parser, insufficient-data handling |
| Updated `main.py` | Targeted stderr fix (if required after inspection) |
| `tests/test_market_data.py` | Offline unit tests — RSI, snapshot serialization, freshness fixtures |
| `tests/test_analyst_agent.py` | Offline unit tests — output parsing, error paths |
| `docs/progress/TASK-002-result.md` | Evidence: test output, live integration record |

---

## Acceptance Criteria

### A. RSI Correctness

#### A1. Implementation Facts (read before testing)

The current implementation in `market_data.py` uses **simple moving average smoothing**:

```python
delta = df["Close"].diff()
gain  = delta.clip(lower=0).rolling(14).mean()
loss  = (-delta.clip(upper=0)).rolling(14).mean()
rs    = gain / loss.replace(0, float("nan"))
df["RSI_14"] = 100 - (100 / (1 + rs))
```

- `diff()` produces N−1 values for N closes; the first row is NaN.
- `rolling(14).mean()` requires 14 non-NaN diffs, which requires **at least 15 closing prices**.
- The smoothing method is **simple rolling mean (Cutler's RSI)**, not Wilder's EMA.
  - This **must not be changed silently**. Document the method; any change requires Codex approval.
- Rows with fewer than 14 diffs produce NaN in `RSI_14`, propagated into `latest_snapshot()` which already converts NaN to `None` (`if pd.notna(...) else None`).

#### A2. Test Cases

All tests must be **offline** (no yfinance calls). Use synthetic DataFrames.

| Test ID | Input | Expected `RSI_14` in last row |
|---|---|---|
| A2-a | 30 strictly rising closes (e.g., 100, 101, …, 129) | 100.0 — all gains, zero losses |
| A2-b | 30 strictly falling closes (e.g., 129, 128, …, 100) | 0.0 — all losses, zero gains |
| A2-c | 30 constant closes (all same value) | Behavior must be **explicitly chosen and documented** before implementation. Options: `None` (preferred for safety) or a defined constant. Do not leave it unspecified. |
| A2-d | 14 closes exactly | `RSI_14` is NaN in the DataFrame (only 13 diffs); `latest_snapshot()` returns `None` |
| A2-e | 15 closes exactly | `RSI_14` is a valid float in the last row; `latest_snapshot()` returns a rounded float |
| A2-f | 1 close | `RSI_14` is NaN; `latest_snapshot()` returns `None` — no crash |

#### A3. Serialization Requirements

- `compute_technicals()` **must continue to return `pd.DataFrame`**. Do not change its return type.
- `latest_snapshot()` returns a plain `dict` for JSON serialization.
  - All indicator values must be either a finite Python `float` or `None`.
  - `None` serializes to JSON `null`. This is correct.
  - `float("nan")` and `float("inf")` must **never appear** in the returned dict.
  - `Infinity` is not valid JSON and will cause downstream failures.
- [ ] Unit test: `json.dumps(latest_snapshot(df))` succeeds without raising `ValueError` for all A2 test cases.

---

### B. Structured AI Output

#### B1. Current State (read before modifying)

`analyst_agent.py` returns a raw string from the LLM. There is no parser.
`latest_snapshot()` passes `None` for missing indicators, but the prompt does not instruct the LLM to acknowledge the gap — it may hallucinate a value.

#### B2. Required Output Schema

Define a Python `dataclass` or `TypedDict` for the parsed result:

```python
# Illustrative — exact implementation decided during TASK-002
@dataclass
class AnalysisResult:
    trend:          str                          # free text, max 200 chars
    signals:        str                          # free text, max 400 chars
    recommendation: Literal["BUY", "HOLD", "SELL"]
    risks:          str                          # free text, max 400 chars
    raw_response:   str                          # unmodified model output

@dataclass
class AnalysisError:
    error_type: Literal["insufficient_data", "malformed_response", "model_unavailable"]
    detail:     str
    raw_response: str | None
```

`analyse()` must return either `AnalysisResult` or `AnalysisError`. It must never return a raw string.

#### B3. Insufficient-Data Handling

- If `latest_snapshot()` returns `None` for any indicator, the prompt must state this explicitly:
  `"RSI_14: null (insufficient price history — do not invent a value)"`
- The parser must detect if the model invents a numeric RSI when the prompt said it was null.
  If detected, return `AnalysisError(error_type="malformed_response", ...)`.
- A warning must be logged; the response must not be silently accepted.

#### B4. Recommendation Validation

- Extract `recommendation` from the response text using a defined pattern (e.g., regex on known section header).
- If the extracted value is not exactly one of `BUY`, `HOLD`, `SELL`, return `AnalysisError(error_type="malformed_response")`.
- **Do not coerce or guess.** A model that says "CAUTIOUS BUY" must be rejected as malformed, not auto-corrected.

#### B5. Streaming vs Batch

Both code paths exist in `analyst_agent.py`:

| Path | Current behavior | Required addition |
|---|---|---|
| Batch (`stream=False`) | Returns full string from `resp.message.content` | Parse and validate before returning |
| Streaming (`stream=True`) | Accumulates chunks, returns `full_response` string | Treat accumulated string as **unvalidated until streaming ends**; then parse and validate the complete text |

- [ ] Both paths return `AnalysisResult` or `AnalysisError`, never a raw string.
- [ ] Streaming path does not attempt to parse mid-stream.

#### B6. Programmatic Checks vs LLM Limitations

Document explicitly in `TASK-002-result.md`:

| Claim | Can be checked programmatically? |
|---|---|
| `recommendation` is BUY/HOLD/SELL | ✅ Yes — regex or enum parse |
| All four sections present | ✅ Yes — section header search |
| RSI not invented when null | ⚠️ Partially — detect if response contains numeric RSI when prompt said null |
| Qualitative accuracy of trend summary | ❌ No — LLM judgment, cannot be tested |

---

### C. Data Freshness

#### C1. Two Separate Checks (do not conflate)

| Check | What it measures | Threshold | Already implemented? |
|---|---|---|---|
| **Cache age** | File modification time vs now | > 1 hour → re-download | ✅ Yes (`market_data.py` lines 39–42) |
| **Market data currency** | Latest row date vs last completed trading session | Later than expected → warning | ❌ Not implemented |

#### C2. Market Data Currency Requirements

Before implementing, specify and document:

| Parameter | Required Decision |
|---|---|
| **Timezone** | All comparisons in UTC+7 (Asia/Bangkok) for Thai tickers; UTC-5 (America/New_York) for US tickers |
| **Market close** | Thai SET: 16:30 Bangkok time; US NYSE/NASDAQ: 16:00 New York time |
| **Calendar source** | Must be specified. Options: `pandas_market_calendars`, static holiday list, or no calendar (see below) |
| **Supported date range** | Set explicitly. Do not claim correctness beyond tested dates. |

> **If a calendar library is not available or not installed:**
> Do not claim holiday-aware validation. Instead, emit the warning:
> `"Market data currency: unverified — no calendar source configured."`
> Document this limitation in `TASK-002-result.md`.

#### C3. Freshness Test Fixtures

All freshness tests must use **deterministic fixtures** — do not call `datetime.now()` in test bodies.
Inject a `reference_time` parameter or monkeypatch `datetime.now`.

| Test ID | Fixture scenario | Expected outcome |
|---|---|---|
| C3-a | Latest row = last weekday; reference = same day after market close | No warning |
| C3-b | Latest row = Friday; reference = Monday before market open | No warning (weekend gap is expected) |
| C3-c | Latest row = 3 business days ago; reference = today | Warning emitted |
| C3-d | Cache file mtime < 1 hour; latest row = yesterday | Warning emitted (data stale despite fresh cache) |
| C3-e | Known holiday scenario | If calendar source is configured: no warning. If not configured: "unverified" warning |

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

- Fix must be **targeted**: suppress or redirect yfinance's urllib3/HTTP stderr noise only.
- Do **not** globally suppress `sys.stderr` or all warnings — preserve useful diagnostics.
- Acceptable approaches: `contextlib.redirect_stderr`, `logging` filter on yfinance logger, or `warnings.filterwarnings`.
- After fix: running `python main.py INVALID_TICKER --no-stream` must produce clean user output with no HTTP stack trace on stderr.

#### D4. Additional Error Paths to Test (offline)

| Test ID | Scenario | Expected behavior |
|---|---|---|
| D4-a | Empty DataFrame passed to `compute_technicals()` | No crash; all indicators NaN or None |
| D4-b | Invalid ticker (no network — mock yfinance) | `ValueError` raised; caught cleanly by caller |
| D4-c | yfinance returns data but Ollama is unavailable | `AnalysisError(error_type="model_unavailable")` returned; no crash |
| D4-d | Ollama returns empty string or `None` content | `AnalysisError(error_type="malformed_response")` returned |
| D4-e | Malformed model output (missing sections) | `AnalysisError(error_type="malformed_response")` returned |

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
| Exit code | (actual) |
| Output summary | (first 200 chars of analysis) |
| Errors or warnings | (any stderr output) |
| Test date and time | (actual UTC+7 timestamp) |

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
`TASK-002-result.md` documents: test output, serialization check, freshness behavior (or explicit "unverified" if no calendar), confirmed stderr fix, and Thai ticker record.
Codex has verified evidence and set status to `done`.
