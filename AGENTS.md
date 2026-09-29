# AGENTS.md — AI Team Collaboration Charter
# KGI AI Trading Agent Project

> **Last updated:** 2026-09-29
> **Status:** TASK-001 in review (pending Master approval)

---

## 1. Team Roles & Scope

### Project Owner (Human / User)
- **Role:** Ultimate decision-maker and project sponsor.
- **Scope:**
  - Sets project vision, constraints, and strategic direction
  - Reviews and approves or rejects deliverables via Codex
  - Has final say on scope changes, budget, and go/no-go decisions
- **Does NOT:** Run tools or write code directly

---

### Codex (Master / AI Project Manager)
- **Role:** Manages tasks, defines acceptance criteria, reads files, runs verification commands, and is the sole authority to mark a task `done`.
- **Scope:**
  - Reads task definitions and result files to verify evidence
  - Runs inspection commands (e.g., `git log`, `python -m pytest`) to validate claims
  - Manages control files: `task_board.md`, `TASK-XXX.md`
  - Sets task status to `done` only after verifying evidence
- **Does NOT:** Write application code or install packages
- **Tool access:** File reads, terminal (verification/inspection only), control file updates

---

### Antigravity (Developer / Primary AI)
- **Role:** Implements tasks end-to-end — writes code, runs tools, tests, and reports evidence.
- **Scope:**
  - Reads task definitions from `docs/tasks/TASK-XXX.md`
  - Writes application code, tests, and configuration
  - Runs build, test, and analysis commands
  - Writes results to `docs/progress/TASK-XXX-result.md`
  - Sets task status to `review` when work is complete — never to `done`
- **Does NOT:** Mark tasks `done`, change project scope unilaterally
- **Tool access:** Full — file system, terminal, browser, image generation

---

### Ollama — Development Use (qwen3.5:4b, Local Worker)
> **Important:** This role describes Ollama as a *team development tool*, not the analyst agent inside the application.

- **Role:** Local LLM for development sub-tasks: generating code drafts, summarising diffs, or answering quick questions during development.
- **Current status:** ✅ Available via HTTP API and CLI.
  - CLI: `ollama run qwen3.5:4b "<prompt>"` — headless, non-interactive.
  - Python SDK: `ollama.Client(host=...).chat(...)` — used in application code.
- **Does NOT:** Receive structured tasks, manage files, or access the internet.

> **Separate from:** The `AnalystAgent` in `src/agents/analyst_agent.py`, which is an *application component* that uses `qwen3.5:4b` to analyse stocks. That is part of the product being built, not the development team.

---

### Gemini (Reviewer)
- **Role:** Independent reviewer to cross-check Antigravity's code and reasoning.
- **Scope (defined, not yet fully tested):**
  - Can be invoked with `gemini --prompt "..." --skip-trust`
  - Intended for: code review, logic checks, second opinion on prompts
- **Current status:** ⚠️ **PARTIALLY VERIFIED**
  - ✅ Responds to prompt: confirmed (`gemini --prompt "Hello..." --skip-trust` returned a valid response)
  - ❌ Read-only code review (reading files and giving structured feedback): **NOT YET TESTED**
  - Auth issue (`IneligibleTierError`) resolved as of 2026-09-29
- **Does NOT:** Write code, commit files, or manage tasks
- **Tool access:** `gemini --prompt` headless mode functional; `--skip-trust` required

---

## 2. Communication Protocol

### Task Handoff Chain
```
Project Owner (Human)
  │  provides direction
  ▼
Codex (Master)
  │  defines task → docs/tasks/TASK-XXX.md
  │  verifies evidence → sets status to done
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
All coordination uses shared files. No automated inter-agent messaging bus exists today.

| File | Purpose |
|---|---|
| `docs/progress/task_board.md` | Single source of truth for all task statuses |
| `docs/tasks/TASK-XXX.md` | Task definition (objective, inputs, outputs, criteria) |
| `docs/progress/TASK-XXX-result.md` | Evidence of completion |
| `docs/project_context.md` | Shared project state — read before starting any task |
| `AGENTS.md` | This file — team charter and rules |

> **Human-mediated handoff:** All handoffs between Codex and Antigravity currently go through the Project Owner (chat interface). Full automation is not yet implemented.

---

## 3. Team Rules

1. **No guessing tools.** Only use commands confirmed to exist and respond correctly. Document version and actual output.
2. **No installing or changing system config** without explicit Project Owner approval.
3. **No secrets in files.** API keys must use `.env` (gitignored). Never commit secrets.
4. **Unverified = unconfirmed.** Mark anything not tested end-to-end as `[UNVERIFIED]`.
5. **Status discipline.** Tasks move: `ready → in_progress → review → done`. Only Master moves to `done`. Developer moves to `review`.
6. **Evidence required.** Every `review`-status task must link to a result file with concrete evidence (actual command output, file paths, test results).
7. **Scope lock (current phase).** No real-money trading, no KGI API connection, no Dashboard. SET50 + Paper Trading only — not yet started.
8. **Separate concerns.** The AI development team (Codex, Antigravity, Ollama-as-dev-tool) is entirely separate from `AnalystAgent` inside the application (which uses Ollama to analyse stocks).
9. **Distinguish capability from verification.** "Tool is installed" ≠ "Tool works for our use case". Test each intended use explicitly.

---

## 4. Glossary

| Term | Meaning |
|---|---|
| Project Owner | The human — ultimate authority and vision holder |
| Master | Codex — AI project manager; verifies and approves tasks |
| Developer | Antigravity — AI that writes code and runs tools |
| Ollama (dev) | qwen3.5:4b used as a dev-side LLM tool |
| AnalystAgent | The stock-analysis component *inside the application* (uses Ollama) |
| Reviewer | Gemini CLI — partially verified, code review not yet tested |
| Task Board | `docs/progress/task_board.md` |
| Hand-off | Passing work between agents via shared files + human relay |
