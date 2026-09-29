# AGENTS.md — AI Team Collaboration Charter
# KGI AI Trading Agent Project

> **Last updated:** 2026-09-29
> **Status:** Active — TASK-001 in review

---

## 1. Team Roles & Scope

### Codex (Master / Project Owner)
- **Role:** Defines tasks, sets acceptance criteria, and is the sole authority to mark a task `done`.
- **Scope:**
  - Assigns tasks and owners via `docs/progress/task_board.md`
  - Reviews evidence in `TASK-XXX-result.md` before approving
  - Sets project direction and priorities
- **Does NOT:** Write code or run tools directly
- **Tool access:** Human-facing — communicates via task files and chat

---

### Antigravity (Developer / Primary AI)
- **Role:** Implements tasks end-to-end, runs tools, writes code, and reports results.
- **Scope:**
  - Reads task definitions from `docs/tasks/TASK-XXX.md`
  - Executes work, writes files, runs Terminal commands
  - Writes results to `docs/progress/TASK-XXX-result.md`
  - Sets task status to `review` when work is complete
  - May delegate sub-tasks to Ollama via the API
- **Does NOT:** Mark tasks `done` (that is Master's role), change project scope
- **Tool access:** Full — file system, terminal, browser, image generation

---

### Ollama (`qwen3.5:4b`, Local Worker)
- **Role:** Local LLM for inference sub-tasks within the software (e.g., stock analysis prompts).
- **Scope:**
  - Responds to structured prompts from `src/agents/analyst_agent.py`
  - Used for: BUY/HOLD/SELL analysis, text summarization, prompt-based reasoning
- **Does NOT:** Access the internet, manage files, or receive tasks directly
- **Tool access:** HTTP API only via `http://localhost:11434` — called programmatically
- **CLI access:** `ollama run <model> "<prompt>"` works non-interactively ✅ (confirmed)

---

### Gemini (Reviewer)
- **Role:** Independent code/logic reviewer to validate Antigravity's outputs.
- **Scope:** Review code quality, flag logic errors, provide second opinion on prompts
- **Current status:** ✅ **ACTIVE** — Authentication resolved.
  - Can be invoked in headless mode using `gemini --prompt "..." --skip-trust`.
- **Tool access:** `gemini --prompt` headless mode is functional.

---

## 2. Communication Protocol

### Task Handoff Chain
```
Codex (Master)
  │  defines task → docs/tasks/TASK-XXX.md
  ▼
Antigravity (Developer)
  │  executes → writes code/files
  │  reports  → docs/progress/TASK-XXX-result.md
  │  sets status → review
  ▼
Codex (Master)
     reviews evidence → sets status → done
```

### File-Based Coordination (Manual Hand-off Mode)
Since no automated inter-agent messaging bus exists today, coordination uses shared files:

| File | Purpose |
|---|---|
| `docs/progress/task_board.md` | Single source of truth for all task statuses |
| `docs/tasks/TASK-XXX.md` | Task definition (objective, inputs, outputs, criteria) |
| `docs/progress/TASK-XXX-result.md` | Evidence of completion |
| `docs/project_context.md` | Shared project state — read before starting any task |
| `AGENTS.md` | This file — team charter and rules |

> **Human-mediated handoff:** All handoffs between Codex and Antigravity currently go through the human (chat interface). Full automation is not yet implemented.

---

## 3. Team Rules

1. **No guessing tools.** Only use commands that have been confirmed to exist and respond correctly. Document version and behavior.
2. **No installing or changing system config** without explicit Master approval.
3. **No secrets in files.** API keys, tokens, and passwords must use `.env` (gitignored). Never commit secrets.
4. **Unverified = unconfirmed.** If a feature has not been tested end-to-end, mark it `[UNVERIFIED]` in docs.
5. **Status discipline.** Tasks move: `ready → in_progress → review → done`. Only Master moves to `done`. Developer moves to `review`.
6. **Evidence required.** Every `review`-status task must link to a result file with concrete evidence (command output, file paths, test results).
7. **Scope lock.** No trading features, no real-money connections, no Dashboard in current phase. SET50 + Paper Trading only — not yet started.
8. **Separate concerns.** The AI team building the *software* (Codex, Antigravity, Ollama-as-worker) is separate from the Ollama *agent inside the software* (analyst_agent.py) that analyzes stocks.

---

## 4. Glossary

| Term | Meaning |
|---|---|
| Master | Codex — the human-side project owner giving instructions |
| Developer | Antigravity IDE — the AI that writes code and runs tools |
| Local Worker | Ollama qwen3.5:4b — the LLM used for inference inside the app |
| Reviewer | Gemini CLI — currently BLOCKED |
| Task Board | `docs/progress/task_board.md` |
| Hand-off | Passing work between agents via shared files + human relay |
