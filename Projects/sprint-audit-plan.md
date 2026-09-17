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
- **Result (2026-09-17): GAPS (CC-audited from a neutral dir + verified against ground truth).**
  - **F1 [CRITICAL] — `sovereign-guard` (declared Tier 1 veto) is NOT loaded.** AGENTS.md §2
    names it as the `pre_tool_call` interceptor; `plugins.enabled` lists only
    `control-file-sentinel`; `hermes plugins list` → "not enabled"; `plugins_discovery.py:213-217`
    `gate_manifest` skips any user plugin absent from `plugins.enabled`, so `register()` never
    runs. **Zero Tier 1 enforcement** (rm -rf /, force-push main, DROP, mkfs/dd). The guard's own
    docstring (`guard_control_files.py:98-101`) names this plugin as the honest out-of-process
    boundary. Secondary: the plugin's docstring claims `systemctl/ufw/iptables` coverage but
    `_BLOCKED_PATTERNS` has no such rule.
  - **F2 [HIGH] — Tier 2 "mandatory" judicial review has no mechanical gate.** §2 says completion
    "CANNOT" be declared without an IG PASS, but §12 admits review is optional ("Every
    completed-but-unreviewed task is normal by default"). Prose convention, not enforced.
  - **F3 [HIGH] — pre-change backup: no enforcement + built-in affordance off.** No
    `.py/.yaml/.sh` invokes `pre_change_backup.sh`; `updates.pre_update_backup: false`
    (config.yaml:196) and `approvals.destructive_slash_confirm: false` (:137) are both disabled.
    Only manual agent discipline remains.
  - **F4 [MED] — `command_allowlist` auto-approves dangerous patterns** (:139-142:
    overwrite-via-redirection, `-e/-c` exec, heredoc exec, `execute_code`) — none covered by
    sovereign-guard's regexes, so with F1 these are open paths.
  - **F5 [MED] — Mechanism Registry blind spot: plugin enablement is unwitnessed.** The registry
    catches dead scripts but not a disabled plugin — exactly why F1 went undetected.
  - **F6 [INFO] — `control-file-sentinel` is detection/evidence, not an approval gate**
    (self-documented); the "guard/approval" framing oversells it.
  - **Verified SAFE:** `.env` mode 600 + untracked (CC's uncertainty was a bundle-scope artifact);
    redacted bundle leak-scan clean.
- **Status:** Pending remediation decision (F1/F4 are posture changes — Sovereign sign-off).
- **Remediated (2026-09-17, Sovereign-approved):** F1 — `hermes plugins enable sovereign-guard`
  (enabled; interceptor unit-verified 9/9; live on next plugin load / gateway restart);
  F3 — `approvals.destructive_slash_confirm: true`; F4 — `command_allowlist: []`; F5 — new
  mechanism `guard-plugins-enabled` (`scripts/check_guards_enabled.py`, invariant: both guards
  in `plugins.enabled`; registry now 28 mechs / 0 failures); F7 — sovereign-guard docstring
  corrected (systemctl/ufw/iptables are NOT matched → hostops allowlist); F2 — AGENTS.md
  §2/§12 wording aligned. F6 accepted as documented (detection ≠ gate). Backup
  `pre-change-20260917-075213`. **IG:** round 1 `deleg_ca8d10d2` FAIL (LOW: plugin.yaml:3
  manifest still claimed systemd interception — fixed) → round 2 `deleg_722b07b8` PASS.
  **Sprint 1 CLOSED.**

## Sprint 2 — Cabinet Profiles
- **Scope:** `profiles/{default,orchestrator,implementer,researcher,writer,treasury,reviewer}/`
  (`config.yaml`, skills, scripts, memories).
- **Audit focus:** Per-profile config sane and role-tool aligned? Any **drift** between
  canonical (`skills/`, `scripts/`) and per-profile copies? Dead/mis-pathed scripts?
- **Acceptance (PASS):** no unexplained copy drift; every profile's role maps to its tools.
- **Result (2026-09-17): GAPS (CC-audited + verified).** 16 CC findings → 7 real, 2 false, rest minor.
  - **F1/F2/F10 [CRITICAL] Treasury = wholesale root-config copy** (32/33 keys shared): carried
    `dashboard.basic_auth` (real creds), the 4 dangerous `command_allowlist` entries, full
    `custom_providers`, and the default profile's Matrix home_channel + a webhook secret. Stripped
    to minimal finance-scoped config (dashboard/command_allowlist/platforms/custom_providers
    removed); removed 16 infra/devops skill packs (kept note-taking/productivity/research).
  - **F8 [CRITICAL] Writer missing mandated skills** — added obsidian-markdown/obsidian-bases/
    json-canvas (grounded-citations + notion were already present under research/productivity).
  - **F9 [HIGH] Researcher memory non-functional** — added hindsight + note-taking/obsidian;
    initialized memories/.
  - **F3 [MED] stale reasoning_overrides stepfun** in implementer/reviewer — removed.
  - **F4 [LOW] mirror-sync unwitnessed** — added `skill-mirror-sync` mechanism (file_fresh on
    cron/output/05ba9f1d1951/*); registry now 29/0.
  - **F16 [LOW] writer/memories empty** — initialized.
  - **FALSE (not remediated):** F5 (vps_security_audit.py is a referenced self-checking mirror in
    reviewer's vps-security-controls skill — IG security audit is in-scope); F14 (no webhook key in
    implementer); F15 (_config_version = redaction artifact); F11's "grounded-citations absent from
    canonical" (it's at skills/research/grounded-citations).
  - Backup `pre-change-20260917-084658`. **IG round 1 `deleg_99555617` PASS. Sprint 2 CLOSED.**
    - Follow-up (IG-flagged, deferred): writer/researcher still hold autonomous-ai-agents/devops/media/
      social-media/software-development packs — trim if strict role-scoping wanted.

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
- **Result (2026-09-17): GAPS (CC-audited + verified).** 3 CC findings → 2 real, 1 by-design.
  - **F1 [MED] `check_script_drift` dead-coded** — defined at mechanism_audit.py:251 but never
    called from main(). Wired in (line 471); added `_strip_mirror_header` so the designed
    DEPLOYED-MIRROR pattern (implementer healthcheck_cron.py) compares equal by body. Proven
    failing-able (it fired on the mirror before the strip).
  - **F2 [MED] security-reaudit on-change + ban-drill legs unwitnessed** — the mechanism
    documented three legs but only the monthly leg had a witness. Added `security-reaudit-on-change`
    (cron 41e27f5fc53d, invariant = the scanner itself) and `f2b-ban-drill` (file_fresh on
    /run/hermes-ops/f2b-ban-drill.json). Registry now 31.
  - **F3 [LOW] task-producer self-test framing** — by-design: a non-empty candidate list is the
    producer's normal job, so a self-test is the honest liveness witness. Not remediated.
  - mechanism_audit 31/0/0; health ALL 11 PASSED. **IG pending.**

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
- Tier-2 IG round 1 (`deleg_106e7ef1`): **FAIL** — found `max_chars()` read the cap from a **top-level** config key while the real cap is **nested** (`memory.memory_char_limit`); the hardcoded fallback (2200) coincided with the live value and hid it, and the witness couldn't detect it. Dedup archive under-recorded. **Fixed**: `max_chars()` reads the nested key; witness rewritten to prove the read with a *distinct* injected value and to fail on the regression; dedup archive corrected; 3 copies re-synced (`a6324eef`). Re-audit `deleg_60b7807e`.
- **Lesson (recorded in `regression-witnesses`):** a fallback default equal to the live value masks a broken config read — prove a config read by injecting a *distinct* value, never by asserting the current one.
- Tier-2 IG round 2 (`deleg_60b7807e`): **PASS** — all 7 criteria verified by execution (nested-cap inject, negative mutation, dedup archive, 3-copy hash, audit+health), no remaining defects. **Sprint 6 closed.**

## Sprint 3 — Cron & Delivery (CC verdict: **GAPS**; verified)

**Scope:** 48 jobs / 4 stores (default, orchestrator, implementer, writer), 38 enabled; the delivery-resolution code (`scheduler_delivery.py`, `scheduler_preflight.py`) + the digest/witness scripts.

**Ground truth (established independently):**
- Delivery: 36 `local`, 10 `origin` (all in the **default** profile → resolves to the Matrix home), 1 `matrix`, 1 `matrix:<room>`. **No `all` in use** → the zero-target trap is latent, not firing.
- Aggregate witness `cron-output` (mechanism, `invariant: check_cron_output.py`, 360m) → **48 jobs scanned, 0 failures, 0 unwitnessed**; executed by the 6-hourly health check (`mechanism_audit.py:382-394` runs invariant commands).
- Scripts: 0 active broken. **1 disabled landmine** — orchestrator `7fd64b8a6209`, `scripts/self_improvement_loop.py` → resolves to `.../scripts/scripts/…` (not found); inert, duplicate of working `e56b431cf11e`.

**CC findings — VERIFIED:**
- **F1 real:** staleness rule compares the run against the whole `jobs.json` mtime (`check_cron_output.py:88`), so editing ANY job can mask ANOTHER job's still-broken failure as "stale". Moot today (all 36 recorded `last_status` = ok).
- **F2 real:** `daily_digest.py:100` maps an unparseable/crashed artifact to the same gray "silent" badge as genuine silence — a failed agent run can render as "nothing to report".
- **F3 real (housekeeping):** 5 jobs bulk-paused 2026-09-08T01:48:49–54; `d77a845c7e13` superseded digest; `c08ce685de9a`; `c8a2af9a96b6` (disabled) duplicates the active `ba6623dfa30c` (same `0 8 * * *`).
- **F4 latent:** `41e27f5fc53d` has `origin: null` + `deliver: origin` — relies on the home-channel fallback; if the home channel is ever removed it logs `ok` and delivers nowhere.
- **F5 latent:** `5222499063c3` / `b1af5452cf5b` (monthly) never ran; first fire 2026-10-01 — script/delivery path unvalidated.

**CC false alarm — DISMISSED:**
- Q3 “`check_cron_output` is not wired into any schedule → not an active witness”: **FALSE**. It is mechanism `cron-output` (`config/mechanisms.yaml`), and its `invariant` command is executed by `mechanism_audit.py:382-394` inside the 6-hourly health check. The derived “8 local jobs have no witness” is overstated — the aggregate covers all 48.
- CC’s bundle covered only the **default** profile, so it could not see the orchestrator landmine.

## Sprint Status Board
| Sprint | Scope | CC Verdict | Top Findings | Actions |
|---|---|---|---|---|
| 1 Governance & Config | **GAPS (verified)** | Tier 1 guard not loaded; backup/confirm disabled; registry plugin blind spot | ✅ Remediated (F1,F3,F4,F5,F7); IG PASS (`deleg_722b07b8`) |
| 2 Cabinet Profiles | **GAPS (verified)** | Treasury=root-config copy w/ secrets; writer/researcher missing mandated skills; stale reasoning_overrides; mirror-sync unwitnessed | ✅ Remediated (F1-F4,F8,F9,F16); IG PASS (`deleg_99555617`) |
| 3 Cron & Delivery | **GAPS (verified)** | Staleness=whole-file mtime; digest masks failures as "silent"; disabled landmine; origin-null job | ✅ Remediated (F1+F2+F3); IG PASS (`deleg_7bf66103`) |
| 4 Mechanisms & Witnesses | **GAPS (verified)** | check_script_drift dead-coded; security-reaudit on-change+ban-drill unwitnessed | ✅ Remediated (F1,F2); IG pending |
| 5 Security Posture | **GAPS (verified)** | Drill `before=1` degenerate-pass; uid:0 manual runs | Drill fix staged pending; audit flags root runs (opt.) |
| 6 Memory & Knowledge | **GAPS (verified)** | Curator silent no-op; MEMORY.md over cap; no Hindsight witness | ✅ Remediated; IG PASS (`deleg_60b7807e`) |
| 7 Kanban & Dispatch | | | | |
| 8 Token Economy | | | | |
