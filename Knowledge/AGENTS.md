# AGENTS.md — Constitutional Governance & Operating Architecture

> **Framework:** U.S. Constitutional Model for Multi-Agent Operations  
> **Version:** 1.0.0 (Updated 2026-09-12)  
> **Scope:** All Hermes Agent profiles and workflow dispatches

---

## The Three Branches of Governance

```
                    ┌─────────────────────────┐
                    │     THE SOVEREIGN       │
                    │   (User / Executive)    │
                    └───────────┬─────────────┘
                                │ Directives / Veto
                    ┌───────────▼─────────────┐
                    │   THE EXECUTIVE OFFICE  │
                    │ (default / Chief of Staff)
                    └──────┬───────────┬──────┘
                           │           │
          ┌────────────────┘           └──────────────┐
          ▼                                           ▼
┌──────────────────┐                       ┌──────────────────┐
│   LEGISLATIVE    │                       │    EXECUTIVE     │
│  (orchestrator)  │                       │   DEPARTMENTS    │
│  • Task Drafting │                       │ • implementer    │
│  • Priorities    │                       │ • researcher     │
│  • Work Queue    │                       │ • writer         │
└─────────┬────────┘                       │ • treasury       │
          │ Dispatches Tasks               └─────────┬────────┘
          │                                          │ Completed Work
          └──────────────────► ◄─────────────────────┘
                               │
                    ┌──────────▼──────────────┐
                    │    JUDICIAL BRANCH      │
                    │ (reviewer / Inspector   │
                    │        General)         │
                    │  • Audits & Tests       │
                    │  • Verification         │
                    │  • Signs off to "Done"  │
                    └─────────────────────────┘
```

---

## 1. Separation of Powers & Cabinet Directory

| Branch / Department | Profile | Historical Official | Role Description | Key Tools & Scope |
|---|---|---|---|---|
| **Executive Office** | `default` | **James A. Baker III** | **Chief of Staff**: Triage user requests, coordinate cross-department actions, deliver high-level briefs. | General, delegation, status, communication |
| **Legislative Branch** | `orchestrator` | **Lyndon B. Johnson** | **Congressional Leadership**: Drafts "bills" (Kanban tasks with acceptance criteria), sets dependencies. | `kanban`, `delegate_task`, `memory` |
| **Dept. of Defense & Infra** | `implementer` | **General Colin L. Powell** | **Engineering & Systems**: VPS reliability, bug fixes, terminal operations, test execution. | `terminal`, `patch`, `read_file`, `write_file` |
| **Office of Intelligence** | `researcher` | **Allen W. Dulles** | **Intelligence & Archives**: Multi-source investigations, fact-checking, Hindsight memory retain/recall/reflect. | `web_search`, `web_extract`, `hindsight_*`, citations |
| **Dept. of State** | `writer` | **Benjamin Franklin** | **Communications & Publishing**: Crafting clear documentation, Notion pages, and formatted digests. | `notion`, `obsidian_*` |
| **Dept. of the Treasury** | `treasury` | **Paul A. Volcker** | **Fiscal Administration**: YNAB account reconciliation, cashflow auditing, budget tracking. | `ynab_*` |
| **Judicial Branch** | `reviewer` | **Antonin G. Scalia** | **Inspector General**: Independent QA, diff auditing, test suite execution, compliance checking. | Code inspection, verification, test suites |

---

## 2. Checks & Balances: Three-Tiered Approval Protocol

To maintain high operating velocity without risking destructive actions or hallucinated completion:

### Tier 1: Sovereign Powers (User Confirmation Required)
Agents cannot execute these autonomously under any circumstances. They must draft the proposed action and request approval:
- **Mechanical Pre-Execution Block (Sovereign Guard / Orca Pattern):** The `sovereign-guard` plugin intercepts calls to the `terminal` tool on the `pre_tool_call` hook. Any destructive command pattern (e.g. `rm -rf /`, force-pushing to `main`, disk partition formatting, database dropping) is halted with an immediate veto before reaching the operating system shell.
- Destructive filesystem or process commands (`rm -rf`, dropping databases, terminating system services).
- Modifying firewall, Tailscale, or root systemd configuration.
- Off-budget financial movements (moving funds between YNAB envelopes or logging large transfers).
- Force-pushing or merging directly to upstream `main` branches.

### Tier 2: Judicial Review (Mandatory Subagent QA Before "Done")
Applied to all technical, code, and infrastructure deliverables before tasks can be marked complete:
- **Automatic Subagent QA Pass:** Upon completing work, spawn a subagent to do a full and thorough quality pass through it for any remaining bugs, issues or QoL improvements. The primary agent MUST invoke `delegate_task` with a clean context window acting as Judicial Review / Inspector General using that mandate.
- **Review Protocol & Inputs:**
  - The reviewer subagent is given: the original goal/acceptance criteria, specific constraints, and the exact files changed or git diff.
  - The reviewer subagent executes: verification tests (e.g. `pytest`, syntax check, execution test) and inspects the code diff for regressions, edge cases, missing error handlers, and hallucinated claims.
  - The primary agent CANNOT declare completion until the review subagent returns an explicit PASS without outstanding defects.
- **Testing calibration:** Require tests that are *meaningful and necessary* to verify a change — for non-trivial logic (branches, loops, parsers, money/security paths) or when the failure path is genuinely uncertain. Do **not** demand tests that merely mirror a reversible, low-impact change; a wrapper around an existing call or a doc edit needs no test. Repeat/broaden testing only when new changes, failures, or unresolved concerns justify it — otherwise move toward completion. Over-testing a small change burns budget and slows the loop as surely as under-testing breaks it.
- **Shared Task Ledger Pattern (GVS5H):** For complex or multi-phase tasks, agents coordinate through a persistent task ledger file (`~/.hermes/task_ledger.json` or `plan.md`) recording current step, artifacts, and test outcomes to prevent context compression amnesia.
- **Research Deliverables:** The `reviewer` validates that claims are backed by `grounded-citations` before archiving to Notion/Obsidian.

### Tier 3: Autonomous Executive Actions (Fast Path)
Executed immediately without gating:
- Querying files, checking system logs, running semantic searches.
- Polling bank balances, checking cron statuses, inspecting git logs.
- Writing to temporary task scratchpads and local drafts.
- Read-only diagnostics and health inspections.

---

## 3. Knowledge Division: Notion vs. Obsidian

- **Notion** = *The Public Record & Structured Databases* (filter, query, share with metadata).
- **Obsidian** = *The National Archives & Working Library* (free-form markdown, daily notes, wikilinks, git versioning).

| Deliverable | Location | Rationale |
|---|---|---|
| Research Findings & Citations | Notion | Structured properties (status, source, tags) |
| Daily Session Logs | Obsidian (`Daily/`) | Chronological, personal record |
| Project Documentation | Obsidian (`Projects/`) | Long-form wikilinked markdown |
| Kanban Alignment Sync | Notion | Multi-agent status tracking via API |
| Infrastructure Runbooks | Obsidian (`Knowledge/`) | Offline-capable system documentation |
| Fiscal Audits & Summaries | Obsidian / Notion | Archival review and trend analysis |

---

## 4. Memory Architecture

Hindsight is the primary agent-facing memory layer. It replaces Qdrant for semantic memory because it forms **confidence-scored beliefs** that update over time, rather than retrieving static chunks.

| Operation | What it does | When to use |
|---|---|---|
| **Retain** | Converts interactions into structured, time-aware memories with entity extraction | After every significant conversation turn |
| **Recall** | Retrieves relevant memories within a synthesized token budget (vs raw chunks) | Before any research task or decision |
| **Reflect** | Reasons over memories to answer questions and update synthesized beliefs | Periodically, or when project context shifts |

**Memory bank:** `hermes-agent` (configured at `http://localhost:8888/v1/default/banks/hermes-agent`)

**Qdrant status:** Deprecated for agent memory. The reindex cron (`9fdcd1be42f4`) is disabled. Qdrant storage is preserved but no longer actively maintained.

---

## 5. Pre-Change Procedures & Rollback

Before ANY config change, model change, or system modification, follow this protocol:

### 5.1 Pre-Change Backup

Run the backup script to capture full system state:

```bash
~/.hermes/scripts/pre_change_backup.sh
```

This creates a timestamped backup at `~/.hermes/backups/pre-change-<timestamp>/` containing:
- Config files (`config.yaml`, `.env`)
- Profile configs
- SOUL.md and AGENTS.md
- Matrix crypto store
- Qdrant storage
- Cron jobs state
- Obsidian vault
- Memory files
- Scripts and skills

### 5.2 Safe Model Change Procedure

```bash
# 1. Back up current state
~/.hermes/scripts/pre_change_backup.sh

# 2. Make the change
hermes config set model.default <new-model>
hermes config set model.provider <new-provider>

# 3. Auto-pin all cron jobs
~/.hermes/scripts/auto_pin_cron.sh

# 4. Verify
hermes cron list
```

### 5.3 Rollback Procedure

If a change breaks something:

```bash
# 1. Stop the gateway
hermes gateway stop

# 2. Run rollback to last backup
~/.hermes/scripts/rollback.sh ~/.hermes/backups/pre-change-<timestamp>/

# 3. Restart gateway
hermes gateway start

# 4. Verify functionality
hermes status
```

### 5.4 Root Cause Analysis (RCA)

When something breaks, don't just fix it — find out WHY:

```bash
python3 ~/.hermes/scripts/rca.py "Description of the symptom"
```

The RCA script:
- Captures current system state (disk, memory, cron health, gateways)
- Extracts relevant log entries from the last 24h
- Provides structured questions for timeline reconstruction
- Generates a blame-free analysis report
- Recommends immediate, short-term, and long-term actions

## 6. Installed Intelligence & Community Advisory

### Hermes Advisor Skill (`hermes-advisor`)
The system has `hermes-advisor` installed at `~/.hermes/skills/hermes-advisor/`.
It contains an offline SQLite FTS5 database (`hermes_rag.sqlite`) indexing **674 real-world Hermes showcases** and **487 community skills/plugins** from the Nous Research Discord.

- **Query Tool:** `python3 ~/.hermes/skills/hermes-advisor/scripts/query_knowledge.py "<query>"`
- **CLI Blueprint Generator:** `python3 ~/.hermes/skills/hermes-advisor/scripts/advisor_cli.py "<concept>"`
- Use this database whenever researching new agent tools, architectures, or community precedents before reinventing wheels.

---

## 7. Recurring Government Blueprints (Cron Jobs)

| Entity / Agency | Cadence | Mission |
|---|---|---|
| **DoD Daily Threat Brief** | 07:00 daily | Comprehensive security assessment: VPS ports, auth logs, Linux CVEs, and WA State cyber/physical news. |
| **Treasury Daily Financial Brief** | 07:30 daily | Deterministic 0-token budget & outflow summary via `treasury_brief.py` (checking balances, debt, top categories). |
| **Weekly Community Knowledge Sync** | Mon 03:00 | Ingest newly announced community showcases and plugins into `hermes-advisor` via `update_advisor_knowledge.py`. |
| **Autonomous PR Reviewer** | 12:00 daily | Audits open GitHub Pull Requests across configured repos via `pr_reviewer.py`, inspecting diffs and security flags. |
| **Executive Cabinet Briefing** | 08:00 daily | Chief of Staff synthesis: Defense, Treasury (YNAB), Intelligence, State, and Legislative updates. |
| **Congressional Standup** | Mon–Fri 09:00 | Audit Kanban backlog and progress across active departments. |
| **GAO (Health Audit)** | Every 6h | Run `bulletproof-hermes` infrastructure health check. |
| **Inspector General Audit** | Every 6h | Scan Kanban for orphaned or unverified tasks. |
| **Archival Sync (Git)** | Every 10m | Automatically commit and push Obsidian vault changes to GitHub. |
| **OMB (Cost & Efficiency)** | Sun 03:00 | Audit token usage, evaluate model cost-effectiveness. |
| **National Memory Hygiene** | Sun 02:00 | Prune stale memory entries and deduplicate records. |
| **Nightly Dreaming** | 0 3 * * * | Extract action items, decisions, and project context from today's logs; run Hindsight reflect on findings; save to Obsidian daily note. |
| **2am Micro-App Session (DoS)** | 0 2 * * * | Scan past 7 days of logs for repetitive tasks, wishes, and "wouldn't it be nice if…" signals; build one small tool (CLI script, HTML dashboard, or automation) saved to `~/.hermes/workspace/micro-apps/<date>/`. |
| **Vault Hygiene Audit** | Sun 04:00 | Scan Obsidian vault for unfiled root notes, broken wikilinks, and orphaned pages via `vault_hygiene.py`. |
| **Infrastructure Watchdog** | Every 30m | Monitor open ports, service endpoints, and URLs via `watchdog.py`; alert to Matrix only on diff. |
| **Retrospective Backfill** | Every 30m | Deterministic, 0-token capture of a retrospective for every completed Kanban task lacking one, via `retrospective_backfill.py --quiet`. Writes to `memories/retrospectives.md` and posts a task comment. Silent when idle. |

---

## 8. Kanban Dispatch Ownership (single-owner, deterministic)

Dispatch must never depend on which gateway wins the boot race. Ownership is
therefore **designated by configuration**, not by lock contention:

- `kanban.dispatch_in_gateway: true` — **implementer profile only** (the designated dispatcher).
- `kanban.dispatch_in_gateway: false` — default profile and every other profile.

Effect: the implementer gateway is the sole dispatcher. The default gateway
backs off by config rather than by losing a race, so a restart of the default
gateway can never silently take over or silently stop dispatch.

**Residual risk:** the designated gateway is a single point of failure. If
`hermes-gateway-implementer.service` stops, nothing dispatches. The
`bulletproof-hermes` `Dispatcher` check surfaces this (lock present but holder
dead/absent) on every 6h health run.

**Migration path (staged, not yet active):** a standalone
`~/.config/systemd/user/hermes-kanban-dispatcher.service` is installed but
**not enabled**. It runs `hermes kanban daemon --interval 60`, removing the
single point entirely. To activate, from a shell **outside** the gateway
process (restarting a gateway from inside itself is blocked):

```bash
systemctl --user disable --now hermes-gateway-implementer.service
systemctl --user enable --now hermes-kanban-dispatcher.service
```

Then set `kanban.dispatch_in_gateway: false` on the implementer profile too, so
no gateway dispatches at all.


## 9. Mechanism Registry — Proving Mechanisms Are Wired

A mechanism is not working because a script exists, a kanban task is `done`, or a
document says so. It is working only when a witness proves its effect.

**Registry:** `~/.hermes/config/mechanisms.yaml`
**Auditor:** `~/.hermes/scripts/mechanism_audit.py` (runs inside the 6-hourly
bulletproof-hermes health check as the `Mechanisms` check).

The auditor enforces three distinct things:

1. **Structural** — every *enabled* cron job that names a `script` must resolve
   under `~/.hermes/scripts/`. A typo'd or moved path fails silently forever.
   This is how a dead job was found: orchestrator `7fd64b8a6209` pointed at
   `scripts/self_improvement_loop.py`, resolving to a nonexistent nested path.
2. **Liveness** — every registered mechanism must have run within
   `interval_minutes * 3` (floor 60m) and must not sit in `error`/`failed`.
   A job that has never run is only a failure once it has existed past that
   window, so a newly created mechanism is not flagged before its first tick.
3. **Witness** — the mechanism must prove its *effect*, not merely that a
   command exited. Witness kinds:
   - `file_fresh` — the declared artifact exists and is newer than `max_age_minutes`.
     A glob is allowed (e.g. `cron/output/<job>/*`); the freshest match is judged.
   - `invariant` — a command exits 0, asserting a property of the world.
   - `null` — explicitly acknowledged as unproven (reported, not hidden).

**All 9 registered mechanisms now carry a real witness; none is `null`.**

**Adding a mechanism:** give it a witness. An entry without one is a declaration,
not a guarantee, and the report says so out loud.

### 11.1 Witnesses that assert end state, not activity

Three mechanisms cannot be witnessed by freshness, because "nothing happened" is
their normal successful outcome. They are witnessed by the state they are
responsible for instead:

| Mechanism | Witness | Assertion |
|---|---|---|
| `vault-auto-push` | `check_vault_sync.py` | Vault worktree clean and HEAD not ahead of `origin/main` (30m tolerance for the 10m schedule). |
| `infrastructure-watchdog` | `watchdog_state.json` fresh | The diff baseline is rewritten every run, proving the pass executed. |
| `bulletproof-health-check` | `cron/output/e490b859eacc/*` fresh | The per-run output artifact exists (agent job — nothing else on disk to hash). |
| `kanban-dispatch` | `check_dispatcher_lock.py` | Lock resolved to a **live Hermes PID**, not merely a file that exists. |

The dispatch witness matters most: a lock *file* outlives its holder, so the old
check ("file present") would report healthy while the board was silently stalled.

### 11.2 Root-cause fix: delegated-child marker leaked into the shell

The `HERMES_DELEGATED_CHILD_CONTEXT` leak is **fixed at source**, not worked
around. The terminal session persists shell state by dumping `export -p` into a
snapshot sourced by every later command; its exclusion list omitted the marker,
so a transient `delegate_task` fence was baked in for the rest of the session and
the Kanban CLI refused every call — including reads — from a context that was
never delegated.

`tools/environments/base_session_env.py` now unsets the marker when building the
snapshot. Per-command envs re-derive it from the live context, so real delegated
children and dispatcher workers keep their write fence. `_hermes_env.py` stays as
defence in depth for scripts that shell out to the CLI.

Committed in the `hermes-agent` fork as `fb2b4a37` (not pushed).

**The retrospective invariant** (`retrospective_backfill.py --check 90`) is the
monitor for the defect that started this: it compares the SET of done tasks
against the SET carrying a real retrospective comment, and fails naming any
uncovered task older than the grace period. It deliberately counts only comments
produced by the tool — not file markers — because the original bug was a
hand-written fake block that satisfied a marker check.

---

## 10. Token Economy & Model Configuration

Measured, not assumed. `scripts/token_economy.py` records a baseline from
`state.db` (`baseline`) and fails a regression (`--check`), wired into the
mechanism registry so the 6-hourly health run catches drift.

**Observed facts (2026-09-13, deepseek/deepseek-v4-flash-0731):**

- cache-hit ratio **98%**; cost **$0.000325/call**
- the previous default (`google/gemini-3.8-flash`) cost **$0.015453/call — 47.5x more**
- reasoning is ~50% of output tokens
- output/input ratio ~0.003: this install is input-dominated, not verbose

**`agent.reasoning_effort` — LEAVE IT UNSET.** Measured directly against the
provider on 2026-09-13 (same prompt, completion+reasoning tokens, medians):

    omitted (provider default)   814
    max                         1066
    high                        1294
    low                         1770   <- most verbose

The ladder is **inverted** on this route, and every explicit value is worse than
sending nothing. A paired run put `low` at 2.7x the omitted default, cheaper on
0/3 runs. `low` is not the cheap end of the dial — it is the worst setting
available. The original unset config was already optimal.

This contradicted both the Nous catalog (`supported_efforts: [max, high, low]`)
and the vLLM recipe's claim that low = "Non-think". **Do not set a reasoning
effort from documentation alone — measure it.** n=3-5 per arm, one prompt, one
model: confident in the direction, softer on the exact magnitude.

Mechanics: read by `hermes_constants.resolve_reasoning_config`, the single
chokepoint for CLI, gateway, TUI, cron, `/model` and fallback. Per-model
overrides live in `agent.reasoning_overrides`; per-session escape hatch is
`/reasoning`. `hermes config set` warns this key is "not recognized" — that is
the CLI key-registry, not the runtime; the runtime reads it (verify with
`resolve_reasoning_config(cfg, model)`).

**Beware the per-session usage table for A/B measurement.** `session_model_usage`
aggregates per (session, model, task), so a session's whole history pins to one
`last_seen`. Splitting a change by timestamp measures session *length*, not the
setting — that confound made the `low` change look like a 45% cost/call win when
a direct API test showed it was a 2.7x regression.

**Auxiliary tasks inherit the main model by default.** That is how one aux task
(`background_review`) reached 17% of all recorded spend — it was simply
inheriting gemini while gemini was the default. `auxiliary.<task>.{provider,model}`
overrides it. There are **13** aux slots; `auxiliary` is absent from config.yaml
until you set one.

**Corrections to commonly-circulated advice:**

- Migrating to `deepseek-v4.1-flash` costs **~5.7x more** on Nous ($0.20/$0.60 per M
  vs $0.0352/$0.1056; cache read $0.006 vs $0.0011). Not cheaper.
- Nous pricing is **flat** — there is no peak/off-peak dimension to schedule around.
- `/thinkon` does not exist in v0.21.0; use `/reasoning`.
- `incontext` needs a vLLM `/tokenize` endpoint we do not have.
- Tightening `compression.threshold` is **anti-cache**: a cache hit costs 1/32 of a
  miss, so rewriting history to shrink a cached context can cost more than it saves.

---

## 11. Constraints System — Learning from Mistakes

### 10.1 The Constraints File

Agent mistakes are logged in `~/.hermes/memories/constraints.md`. Each entry follows this format:

```
## 12. Review Routing (Judicial Branch)

`kanban.request_review` takes an OPTIONAL `reviewer` profile. **When it is
omitted, the task keeps its own assignee and the implementer reviews its own
work.** There is no config default.

**Convention: same-card review must name the IG explicitly.**

    kanban_request_review(summary=..., reviewer="reviewer")

Until 2026-09-09 this could not work: the `reviewer` profile did not exist, so
the one review ever requested (`t_e8a1896d`) was reassigned by hand with the
comment "Reassigning from non-existent reviewer profile to implementer", and
the dispatcher spawned `implementer` to audit its own work. The profile now
exists and is registered, so the documented route works.

Note `kanban.review_dispatch: true` does NOT mean "send reviews to the reviewer
profile" — it means "spawn the assigned profile with the bundled `sdlc-review`
skill". Routing to the IG depends entirely on passing `reviewer=`.

Every completed-but-unreviewed task is therefore normal by default; the board
does not review anything unless asked to.

---

## 13. Cron Delivery for Platform-less Profiles

Secondary profiles (orchestrator, writer, researcher, reviewer, implementer)
have **no messaging platform**. A job with `deliver: origin` there fails with
*"platform 'matrix' not configured/enabled"* — and the failure notice goes to
the same dead target, so the result and the error are both invisible. Six jobs
sat in `delivery_failed` that way.

**Decision: `deliver: local` for those jobs, plus one aggregator.**

- Jobs write to `<profile_home>/cron/output/<job_id>/<timestamp>.md`.
- `scripts/cron_digest.py` (cron `d77a845c7e13`, every 2h, no-agent) collects
  new artifacts from every profile and posts ONE digest via the default
  profile, which owns the only working Matrix adapter. Silent when idle.
- Agent artifacts are `## Prompt` + `## Response`; the digest takes only the
  response, strips the no-agent header block, and skips silent runs.
- `scripts/check_cron_output.py` (mechanism `cron-output`) is the witness:
  every enabled job's newest artifact must be at/after its last run.

**Rejected: an own Matrix account per profile.** It is the more faithful model
(departments report in their own voice, two-way replies), but it costs five
accounts, five E2EE crypto stores to keep verified, and five silent auth
failure modes — in the one subsystem already observed failing quietly
(`BAD_ACCOUNT_KEY`). Revisit for one profile (orchestrator) before ever doing
five.

**`deliver=all` is a second trap in the same profile.** It means "every platform
with a configured home channel" and resolves at fire time — so in a profile with
no platforms it resolves to **zero targets and silently delivers nowhere**. It
is not the same string as `origin`, so a scan for `origin` misses it entirely;
that is how three further implementer jobs (the morning briefing and both digest
scripts) were still dropping their output after the first pass. When auditing
delivery, enumerate the *resolved* target set, not the literal value.

**Staleness rule (matters for every status check here):** a `last_status`
failure recorded *before* the job was last reconfigured does not describe its
current configuration. Without this rule the check stays red for days on the
weekly jobs because re-pinning a model does not rewrite history.

---

## C<N> — <title>

**What happened:** <one sentence describing the mistake>

**Constraint:** <imperative rule for future behavior>

```bash
# Quick check: <optional verification command>
```

**Seen:** <count>  
**Graduated:** <mechanism path or "Not graduated — <reason>">
```

### 10.2 The Minor Log

Self-corrected errors that don't yet have a pattern go to the `## Minor` section:
- One line each, newest first
- Format: `- YYYY-DD-MM -- <what happened> -> <imperative>`
- Two Minor entries sharing a cause get promoted to a numbered constraint
- After 30 days, unpaired entries move to `## Minor -- archived`

### 10.3 Graduation Rules

| Seen Count | Status | Action |
|---|---|---|
| 1 | First occurrence | Logging is sufficient |
| 2 | Pattern confirmed | Build a mechanism (hook, check, or scanner) |
| 3+ | Ungraduated violation | Escalate to user — the system is failing |

A constraint is "graduated" when it has a mechanical guard — a hook, an eval, a scanner, or a script — that prevents the mistake from recurring. Prose-only constraints (where no mechanism is possible) stay at "Not graduated" indefinitely, and reading them at session startup is the only defence.

### 10.4 Drift Scanning

The constraints file itself can drift. The drift scanner (`~/.hermes/scripts/constraints_drift.py`) checks:

1. **Constraints at seen: 2+ without graduation** — violating the graduation rule
2. **Minor backlog over 8 entries** — signals under-promotion
3. **Promotion candidates** — Minor entries sharing vocabulary that indicate a pattern

### 10.5 Session Startup Audit

At the start of every session, run:
```bash
bash ~/.hermes/scripts/session_audit.sh
```

This reports:
- Total active constraints
- Prose-only constraints (reading is the only defence)
- Overdue mechanisms (seen: 2+ without graduation)
- Minor backlog count

### 10.6 Confidence Tracking

Track predictions vs. outcomes to calibrate confidence:

```
## Confidence Log

| Date | Task | Confidence | Actual | Delta |
|---|---|---|---|---|
| 2026-09-12 | Wire Hindsight retain | 8/10 | 6/10 | -2 |
| 2026-09-12 | Option A token-neutral | 7/10 | 8/10 | +1 |
| 2026-09-12 | Docker slim has deps | 6/10 | 0/10 | -6 |
```

If delta is consistently negative → you're overconfident. If consistently positive → you're underconfident. Update confidence scores on skills based on this log.

### 10.7 Debrief Integration

The weekly review asks "mistakes made?" — this question is now formalized:
- If the answer references a constraint, increment its `seen` count
- If the answer is "none," check the Minor log — an empty section means under-reporting, not a clean run

## 14. Instruction & Skill Hygiene (progressive disclosure)

Instructions and skills should be *lean and contextual*, not exhaustive:
- **Skill descriptions are triggers, not essays.** Keep them short, self-contained,
  and specific about WHEN they apply ("use when adding a DB migration", not "use
  when working with databases"). A description that over-claims applicability
  gets loaded when it should not be — wasted tokens and misapplied behavior.
- **Progressive disclosure.** The root `SKILL.md` should route and point to the
  detail (reference files, scripts) the task actually needs, not inline a full
  itinerary. Read the piece you need when you need it; do not front-load a doc
  stack into context before every edit.
- **Instructions shape behavior.** Periodically audit skills and `AGENTS.md`/
  `SOUL.md` for instructions that over-constrain, contradict each other, or would
  make the agent stall or ask when it should proceed. A skill that exists should
  earn its tokens every load.
- **Reserve "ask first" for what is genuinely destructive/irreversible** (Tier 1).
  Otherwise bias toward action and carry the task to completion.
