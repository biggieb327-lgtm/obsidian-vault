# Workspace Orientation Map (Hermes Agent)

> **Purpose:** 0-token immediate spatial orientation for Hermes agents and subagents.
> Read this file first to avoid exploratory directory scanning (`ls`, `find`, `search_files`).

---

## 1. Primary Filesystem Layout

| Path | Purpose & Contents |
|---|---|
| `/home/hermes/.hermes/` | Root configuration, runtime cache, scripts, memories, and skills. |
| `/home/hermes/.hermes/config.yaml` | Main agent config (provider, default model, toolsets, basic auth). |
| `/home/hermes/.hermes/.env` | Global environment variables & API tokens (`NANOGPT_API_KEY`, `MATRIX_*`, etc.). |
| `/home/hermes/.hermes/AGENTS.md` | Constitutional framework, department charters, approval tiers, and recurring cron blueprints. |
| `/home/hermes/.hermes/SOUL.md` | Core persona, operating principles, priority order, and workflow rules. |
| `/home/hermes/.hermes/profiles/` | Department profiles (`orchestrator`, `implementer`, `researcher`, `writer`, `treasury`, `reviewer`). |
| `/home/hermes/.hermes/skills/` | Installed agent skills organized by topic directory. |
| `/home/hermes/.hermes/scripts/` | Executable maintenance scripts and deterministic tools. |
| `/home/hermes/.hermes/cron/` | Cron job definitions (`jobs.json`) and run logs. |
| `/home/hermes/.hermes/logs/` | System logs (`gateway.log`, `agent.log`, `errors.log`, process outputs). |
| `/home/hermes/.hermes/cache/` | Ephemeral scratch, image downloads, digests (`subreddit_daily.json`, `dreaming_output.md`). |
| `/home/hermes/.hermes/workspace/` | Working projects and repositories. |
| `/home/hermes/.hermes/workspace/obsidian-vault/` | Git-backed markdown knowledge base & Human Archives. |
| `/home/hermes/.hermes/workspace/micro-apps/` | Generated micro-applications from 2am cron sessions. |
| `/home/hermes/.hermes/workspace/kanban_runs/` | Isolated task workspaces for kanban ticket execution. |

---

## 2. Key Deterministic Scripts (`~/.hermes/scripts/`)

| Script | Purpose |
|---|---|
| `pre_change_backup.sh` | Full backup before any system, config, or code change. |
| `rollback.sh` | Restores previous backup manifest. |
| `auto_pin_cron.sh` | Pins all cron jobs to current provider/model after model switch. |
| `rca.py` | Structured 5-Whys root cause analysis following failures. |
| `dod_threat_audit.py` | Local system security, ports, failed logins, and disk health audit. |
| `subreddit_monitor.py` | Reddit RSS fetcher with 65s rate-limit spacing across 7 subreddits. |
| `dreaming_job.py` | Extracts action items, decisions, and project context from daily logs. |
| `vault_hygiene.py` | Detects broken wikilinks, unfiled root notes, and orphans in Obsidian vault. |
| `ynab_reconcile.py` | 0-token financial reconciliation comparing bank balances against YNAB API. |
| `watchdog.py` | Change detection on URLs or command outputs; silent unless diff detected. |
| `kanban_evidence.py` | Enforces isolated workspaces and evidence verification for kanban tasks. |
| `friction_miner.py` | Deterministic log analyzer identifying repetitive commands, tool errors, and corrections. |
| `decision_ledger.py` | Tracks system improvements, tools added, and verifies 7-day utility/health. |

---

## 3. Services & Endpoints

| Service | Port / Socket | Scope / Bind | Auth Method |
|---|---|---|---|
| **Hindsight API** | `127.0.0.1:8888` | Localhost only | Hermes auth via container volume |
| **Hindsight UI** | `127.0.0.1:9999` | Localhost only | Local / public behind loopback |
| **Hermes Gateway** | `100.81.134.67:9119` | Tailscale internal | Basic auth / token |
| **Matrix Homeserver** | `matrix.org` | HTTPS | `@brianault:matrix.org` (verified) |
| **Obsidian Git** | Remote GitHub | SSH / HTTPS PAT | `biggieb327-lgtm/obsidian-vault` |

---

## 4. Quick Working Rules

1. **Before making code/config changes:** Run `~/.hermes/scripts/pre_change_backup.sh`.
2. **Upon completing work:** Spawn a subagent to do a full and thorough quality pass through it for any remaining bugs, issues or QoL improvements (via `delegate_task`).
3. **When a task has multiple steps:** Write status, plan, and diffs to `task_ledger.json` in the task workspace.
4. **Never guess paths:** Use this orientation map.
