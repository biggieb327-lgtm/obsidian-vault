# Sprint Audit Plan — Hermes Deployment Setup & Workflow

> Purpose: chunk the Hermes Agent deployment (vmi3420780) into bounded, independently
> auditable "sprints" so Claude Code (external strong-reasoning auditor) can review each
> increment without blowing a context window. Each sprint is a self-contained unit:
> scope (paths), audit focus (what to verify), and acceptance (what PASS means).
>
> Created 2026-09-17. Engine: Claude Code print mode (audit role).
> Invocation pattern: `cat <scope> | claude -p "Audit…" --max-turns 2` (300s+ timeout).

---

## How to run an audit sprint

```
cat /home/hermes/.hermes/<sprint-scope-files> | \
  claude -p "Audit this Hermes deployment subsystem. <sprint audit focus>.
  Report: (1) findings by severity, (2) concrete file:line, (3) whether it matches
  the documented intent. Max 25 bullets." --max-turns 2
```
- Give the terminal call **300s+** (CC audit mode on a large scope can exceed 180s).
- Keep each sprint's scope bounded so the pipe stays under CC's effective context.
- After CC returns, Hermes verifies any claim before acting; CC output is a **finding, not a fact**.
- Log the result per sprint below (verdict, top findings, actions taken).

---

## Sprint 1 — Governance & Core Config
- **Scope:** `config.yaml`, `.env` (presence/redaction only), `AGENTS.md`, `SOUL.md`,
  `plugins/sovereign-guard/`, `plugins/control-file-sentinel/`,
  `scripts/pre_change_backup.sh`, `scripts/guard_control_files.py`, `hooks:` block.
- **Audit focus:** Does the *declared* governance (three tiers, judicial review, pre-change
  backup, guard) match the *enforced* reality (plugins, hooks, guard baselines)? Is any
  documented rule dead/contradictory? Secrets safe? Guard coverage complete?
- **Acceptance (PASS):** every declared guard has a real enforcement path; no secret leaks
  in scope; no doc-vs-config contradiction.

## Sprint 2 — Cabinet Profiles
- **Scope:** `profiles/{default,orchestrator,implementer,researcher,writer,treasury,reviewer}/`
  (`config.yaml`, skills, scripts, memories).
- **Audit focus:** Per-profile config sane and role-tool aligned? Any **drift** between
  canonical (`skills/`, `scripts/`) and per-profile copies? Dead/mis-pathed scripts?
- **Acceptance (PASS):** no unexplained copy drift; every profile's role maps to its tools.

## Sprint 3 — Cron Schedule & Delivery
- **Scope:** `cron/jobs.json` (39 jobs), `scripts/cron_digest.py`, `scripts/daily_digest.py`,
  `scripts/check_cron_output.py`.
- **Audit focus:** Every job has a script path that **resolves**, a real delivery target
  (the `deliver: local` vs `origin` vs `all` trap), and a fresh artifact. Any job delivering
  nowhere or pointing at a missing/moved path?
- **Acceptance (PASS):** no job silently dead; delivery targets resolve to a working channel.

## Sprint 4 — Mechanism Registry & Witnesses
- **Scope:** `config/mechanisms.yaml` (25), `scripts/mechanism_audit.py`.
- **Audit focus:** Every mechanism carries a **real, failing-able** witness (file_fresh /
  invariant / null); none is `null`; auditors self-consistent; intervals match cadence.
- **Acceptance (PASS):** audit reports all green with real witnesses; no "witness" that
  cannot actually fail.

## Sprint 5 — Security Posture
- **Scope:** firewall (hostfw via `hostops fw-status`), fail2ban + fire-drill,
  SSH/Tailscale listener + config, sudo `hostops` allowlist, `scripts/security_reaudit.py`
  + `evidence/`, secrets hygiene in scripts/config.
- **Audit focus:** Are the controls **real, enforced, and witnessed**? Is the firewall
  default-drop with tailnet-only accept actually in effect? Do P1/P2 stay at 0? Any
  credential in scope?
- **Acceptance (PASS):** P1:0 P2:0; every control has an enforcement + witness path.

## Sprint 6 — Memory & Knowledge Architecture
- **Scope:** `memories/` (MEMORY.md, USER.md, constraints.md, retrospectives.md),
  Hindsight (Docker bank `hermes-agent`), Obsidian vault (`workspace/obsidian-vault/`),
  Notion sync scripts, `scripts/memory_curator.py`, `scripts/constraints_drift.py`.
- **Audit focus:** Hygiene, drift, and architecture-vs-intent (4-layer memory). Any stale
  copies (e.g. vault `Knowledge/AGENTS.md` vs live)? Constraints drift scanner healthy?
- **Acceptance (PASS):** memory within budget; no stale authoritative copy; drift scanner 0.

## Sprint 7 — Kanban & Dispatch
- **Scope:** `kanban.db`, `CODENAMES.md`, dispatcher (single-owner, `kanban.dispatch_in_gateway`),
  boards, `scripts/kanban_audit*.py`, `scripts/check_dispatcher_lock.py`, the `hooks:` block.
- **Audit focus:** Single-owner dispatch held (lock resolves to a live PID)? No orphaned or
  unverified tasks? Boards vs codename convention honored? Judicial-review routing works?
- **Acceptance (PASS):** dispatch lock live; no orphaned tasks; reviewer routing explicit.

## Sprint 8 — Token Economy & Model Routing
- **Scope:** model/provider config, `agent.reasoning_effort` (left unset), `reasoning_overrides`,
  `scripts/token_economy.py` + baseline, `state.db` usage, aux task routing, Claude Code
  plan/build/audit division of labor.
- **Audit focus:** Config matches **measured** facts (cache-hit, cost/call, the inverted
  reasoning-effort ladder)? No regression vs baseline? Aux tasks not silently inheriting a
  costly default?
- **Acceptance (PASS):** config matches measurement; token_economy check green; no costly drift.

---

## Sprint 5 result (2026-09-17)
**CC verdict: GAPS.** Verified disposition (CC output is a finding, not a fact):
- **Drill `before=1` degenerate-pass — CONFIRMED (highest-value finding).** `f2b-ban-drill.sh` lines 113-129: if the test address is already in the set before the drill, `ok_after_ban` is trivially true and `ok_after_unban` is satisfied by the element *still being present* after `unbanip` — i.e. a completely broken unban also yields pass. A stale residue (prior failed unban) makes every later run report `pass` without testing ban or unban. **Fix pending (root-owned file → staged root action).**
- **`uid:0` self-audit — REAL but not systemic.** 35/37 evidence files are `uid=1000` (hermes, per design docstring); the two `uid=0` runs are manual Sovereign checks from SSH. Standing hardening: the audit should *flag* a root run (can't claim unprivileged independence). Optional.
- **`sshd-kbd` — DISMISSED (audit-bundle gap).** `KbdInteractiveAuthentication no` IS set (sshd_config:71); CC couldn't see it because the scope bundle's grep filtered out the `kbd` keyword. P2:0 was legitimate.
- **`firewall-drift-guard` "stuck activating" — DISMISSED.** Normal oneshot-timer pattern (unit `inactive`, timer `active`).
- **Lower-priority limitations (not yet acted):** `check_secrets()` scans only 2 hardcoded paths; `check_deamplification()` docker-group check can silently no-op for system/stopped units; `jail.local` `ignoreip` hardcodes a home/office public IPv4 (PII if bundle shared); `hostops unit-*` wildcards unbounded; `docker-ufw-guard.service` absent from `FINGERPRINT_FILES`; `check_fail2ban()` log window resets on config mtime touch.

## Sprint audit protocol — lessons
- **Verify CC findings against ground truth before acting.** CC inferred a false `sshd-kbd` P2 from a scope bundle whose grep had *filtered out* the `kbd` keyword. A filtered/incomplete bundle manufactures false alarms. Include the full config or state the exact filter.
- **Check whether a "green" CC is over-claiming** (drill `before=1`) *and* whether a "red" CC is under-claiming (bundle gap) — both directions.

## Sprint 6 result (2026-09-17)
**CC verdict: GAPS.** Verified disposition (CC output is a finding, not a fact):
- **`memory_curator.py` silent no-op on MEMORY.md — CONFIRMED.** `curate()` splits on `\n## ` (line 108); MEMORY.md has 0 `## ` headers and 11 `§` separators, so the split yields one section and the dedup/consolidate loop iterates nothing. The auto-curator never curates.
- **Curator thresholds miscalibrated — CONFIRMED.** `MAX_CHARS=4000`/`MAX_ENTRIES=15` (lines 8-9,27-28) vs the real enforced cap `memory_char_limit: 2200`; MEMORY.md is already 2208 bytes — over cap, under the curator's trigger.
- **Layer 2 (Hindsight) has no witness — CONFIRMED.** The 6h health check (`skills/bulletproof-hermes/scripts/health_check.py`) never probes Hindsight/`:8888`. MEMORY.md itself notes Hindsight writes still 500.
- **`vault_hygiene.py` + `session_audit.sh` cannot fail on findings — CONFIRMED.** `main()` returns 0 even with broken links/orphans (line 300; only a missing vault returns 1); `session_audit.sh` ends `exit 0` (line 33). Both are reporters, not gates.
- **`save_memory()` plain `open("w")` overwrite, no lock/backup — CONFIRMED** (line 150); the `.lock` files present are not read by this writer.
- **Layer 3 doc/impl drift — CONFIRMED (CC inverted it).** CC said "no code path"; `scripts/search_memory.py` exists but implements **Qdrant + fastembed**, while USER.md describes **Ollama+NumPy+JSONL+FTS5** — and AGENTS.md §4 deprecates Qdrant. Doc and code contradict each other.
- **Unowned cruft:** `MEMORY.md.bak.*`, `*.lock`, stale `Knowledge/AGENTS.md` duplicate (30KB, Sep 14) — no mechanism owns them.
- **Dismissed:** CC's "layer 3 not wired" as an *absence* claim — a bundle-scope artifact (2nd occurrence; always verify CC against ground truth).

### Sprint 6 remediation (2026-09-17)
**Phase A — quick hygiene (done):** MEMORY.md trimmed to 2170/2200 and the false "Hindsight: Docker" fact corrected (native process); stale `.bak` archived + stale 0-byte `.lock` removed; vault `Knowledge/AGENTS.md` refreshed from canonical (was materially stale; 9 wikilinks preserved); guard baseline re-accepted.

**Phase B — mechanism fixes (done, IG pending):**
- `memory_curator.py` rewritten: splits on the real `§` delimiter, reads `memory_char_limit` from config (was hardcoded 4000), preserves the `§` format on consolidation, backs up before overwrite. Synced to all 3 copies (`scripts/`, `skills/memory-curator/`, `profiles/treasury/skills/memory-curator/`), byte-identical `fdac198c`.
- New `scripts/check_hindsight.py` — the missing layer-2 witness (verified it fails on a dead port).
- New `scripts/test_memory_curator.py` — regression witness (fails if the split/cap regress).
- `config/mechanisms.yaml` +2 mechanisms → 27 verified, 0 failures; full health check ALL PASSED.
- Tier-2 IG audit: `deleg_106e7ef1`.

## Sprint Status Board
| Sprint | Scope | CC Verdict | Top Findings | Actions |
|---|---|---|---|---|
| 1 Governance & Config | | | | |
| 2 Cabinet Profiles | | | | |
| 3 Cron & Delivery | | | | |
| 4 Mechanisms & Witnesses | | | | |
| 5 Security Posture | **GAPS (verified)** | Drill `before=1` degenerate-pass; uid:0 manual runs | Drill fix staged pending; audit flags root runs (opt.) |
| 6 Memory & Knowledge | **GAPS (verified)** | Curator silent no-op; MEMORY.md over cap; no Hindsight witness | Hygiene + mechanism fixes applied; IG `deleg_106e7ef1` |
| 7 Kanban & Dispatch | | | | |
| 8 Token Economy | | | | |
