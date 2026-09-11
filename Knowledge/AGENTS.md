# AGENTS.md — Constitutional Governance & Operating Architecture

> **Framework:** U.S. Constitutional Model for Multi-Agent Operations  
> **Version:** 1.0.0 (Updated 2026-09-11)  
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

| Branch / Department | Profile | Role Description | Key Tools & Scope |
|---|---|---|---|
| **Executive Office** | `default` | **Chief of Staff**: Triage user requests, coordinate cross-department actions, deliver high-level briefs. | General, delegation, status, communication |
| **Legislative Branch** | `orchestrator` | **Congressional Leadership**: Drafts "bills" (Kanban tasks with acceptance criteria), sets dependencies. | `kanban`, `delegate_task`, `memory` |
| **Dept. of Defense & Infra** | `implementer` | **Engineering & Systems**: VPS reliability, bug fixes, terminal operations, test execution. | `terminal`, `patch`, `read_file`, `write_file` |
| **Office of Intelligence** | `researcher` | **Intelligence & Archives**: Multi-source investigations, fact-checking, semantic memory querying. | `web_search`, `web_extract`, `qdrant_*`, citations |
| **Dept. of State** | `writer` | **Communications & Publishing**: Crafting clear documentation, Notion pages, and formatted digests. | `notion`, `obsidian_*` |
| **Dept. of the Treasury** | `treasury` | **Fiscal Administration**: YNAB account reconciliation, cashflow auditing, budget tracking. | `ynab_*` |
| **Judicial Branch** | `reviewer` | **Inspector General**: Independent QA, diff auditing, test suite execution, compliance checking. | Code inspection, verification, test suites |

---

## 2. Checks & Balances: Three-Tiered Approval Protocol

To maintain high operating velocity without risking destructive actions or hallucinated completion:

### Tier 1: Sovereign Powers (User Confirmation Required)
Agents cannot execute these autonomously under any circumstances. They must draft the proposed action and request approval:
- Destructive filesystem or process commands (`rm -rf`, dropping databases, terminating system services).
- Modifying firewall, Tailscale, or root systemd configuration.
- Off-budget financial movements (moving funds between YNAB envelopes or logging large transfers).
- Force-pushing or merging directly to upstream `main` branches.

### Tier 2: Judicial Review (Mandatory Sign-off Before "Done")
Applied to all technical and research deliverables before tasks are closed on the Kanban board:
- **Code & Infra Tasks:** The `implementer` submits the work. The `reviewer` profile audits the diff and runs the test suite (`pytest`). If tests fail, the task is returned with `changes_requested`.
- **Research Artifacts:** The `reviewer` validates that claims are backed by `grounded-citations` before archiving to Notion/Obsidian.

### Tier 3: Autonomous Executive Actions (Fast Path)
Executed immediately without gating:
- Querying files, checking system logs, running Qdrant semantic searches.
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

---

## 6. Recurring Government Blueprints (Cron Jobs)

| Entity / Agency | Cadence | Mission |
|---|---|---|
| **DoD Daily Threat Brief** | 07:00 daily | Comprehensive security assessment: VPS ports, auth logs, Linux CVEs, and WA State cyber/physical news. |
| **Executive Cabinet Briefing** | 08:00 daily | Chief of Staff synthesis: Defense, Treasury (YNAB), Intelligence, State, and Legislative updates. |
| **Congressional Standup** | Mon–Fri 09:00 | Audit Kanban backlog and progress across active departments. |
| **GAO (Health Audit)** | Every 6h | Run `bulletproof-hermes` infrastructure health check. |
| **Inspector General Audit** | Every 6h | Scan Kanban for orphaned or unverified tasks. |
| **Archival Sync (Git)** | Every 10m | Automatically commit and push Obsidian vault changes to GitHub. |
| **OMB (Cost & Efficiency)** | Sun 03:00 | Audit token usage, evaluate model cost-effectiveness. |
| **National Memory Hygiene** | Sun 02:00 | Prune stale memory entries and deduplicate records. |
