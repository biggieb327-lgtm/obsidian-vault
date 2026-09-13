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
| **Autonomous PR Reviewer** | 12:00 ...[truncated]
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

## 7. Constraints System — Learning from Mistakes

### 7.1 The Constraints File

Agent mistakes are logged in `~/.hermes/memories/constraints.md`. Each entry follows this format:

```
## C<N> — <title>

**What happened:** <one sentence describing the mistake>

**Constraint:** <imperative rule for future behavior>

```bash
# Quick check: <optional verification command>
```

**Seen:** <count>  
**Graduated:** <mechanism path or "Not graduated — <reason>">
```

### 7.2 The Minor Log

Self-corrected errors that don't yet have a pattern go to the `## Minor` section:
- One line each, newest first
- Format: `- YYYY-DD-MM -- <what happened> -> <imperative>`
- Two Minor entries sharing a cause get promoted to a numbered constraint
- After 30 days, unpaired entries move to `## Minor -- archived`

### 7.3 Graduation Rules

| Seen Count | Status | Action |
|---|---|---|
| 1 | First occurrence | Logging is sufficient |
| 2 | Pattern confirmed | Build a mechanism (hook, check, or scanner) |
| 3+ | Ungraduated violation | Escalate to user — the system is failing |

A constraint is "graduated" when it has a mechanical guard — a hook, an eval, a scanner, or a script — that prevents the mistake from recurring. Prose-only constraints (where no mechanism is possible) stay at "Not graduated" indefinitely, and reading them at session startup is the only defence.

### 7.4 Drift Scanning

The constraints file itself can drift. The drift scanner (`~/.hermes/scripts/constraints_drift.py`) checks:

1. **Constraints at seen: 2+ without graduation** — violating the graduation rule
2. **Minor backlog over 8 entries** — signals under-promotion
3. **Promotion candidates** — Minor entries sharing vocabulary that indicate a pattern

### 7.5 Session Startup Audit

At the start of every session, run:
```bash
bash ~/.hermes/scripts/session_audit.sh
```

This reports:
- Total active constraints
- Prose-only constraints (reading is the only defence)
- Overdue mechanisms (seen: 2+ without graduation)
- Minor backlog count

### 7.6 Confidence Tracking

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

### 7.7 Debrief Integration

The weekly review asks "mistakes made?" — this question is now formalized:
- If the answer references a constraint, increment its `seen` count
- If the answer is "none," check the Minor log — an empty section means under-reporting, not a clean run
