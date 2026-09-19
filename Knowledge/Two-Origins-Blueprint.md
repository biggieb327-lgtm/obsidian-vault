---
title: Two-Origins Blueprint — Multi-Agent Architecture Application
date: 2026-09-19
type: architecture-review
status: active
tags: [multi-agent, architecture, governance, reasoning-replay, blueprint]
source: https://www.samsung-news.com/articles/uU_fbJMUIVZ0HuW8JErQ_w-en-US
source_pub: ScienceAlert / Nature Neuroscience (Stanford, Jokhai/Dundes/Loh)
---

# Two-Origins Blueprint — Multi-Agent Architecture Application

## The Finding
The human brain develops as **two parallel neural systems** already anatomically
separate at gastrulation (embryonic week 2–3), not one system that later
subdivides. `Otx2`-marked progenitors build fore/midbrain; `Gbx2`-marked build
hindbrain. The two populations originate, are regulated, and hold identity
**independently** — a composite blueprint preserved across ~550 Myr of
vertebrate evolution. In the mature brain the pieces must interoperate to
function, yet are built by different maker lines and are **not interchangeable**.

> Architectural insight: a functioning whole can be, and must be, assembled from
> independently-originated, non-interchangeable subsystems that cooperate
> without merging.

## Three Model Takes (2026-09-19)
Three independent models (GLM-5.3-flash, Qwen-3.8-27B, Gemini-3.8-flash) given an
identical applied brief against our 7-profile governance architecture. Full text
preserved at `~/tmp/brain_origins_takes/` and in this archive's daily note.

### GLM (z-ai/glm-5.3-flash) — "Current contracts are implicit; make them structural"
- Over-integration: shared FS, shared memory, one dispatch daemon; boundary enforced by
  convention, not structure. Fix: explicit per-profile I/O contracts + tool/path allowlists.
- Dispatch as **fixed developmental lineage** (born in Legislative → Defense → witnessed by
  Judicial); maker line never swaps mid-task; delegated children carry `{originating_profile, criteria_id}`.
- Padding is fine but **asymmetric**: keep boundary signals (vetoes, direction changes, decisions);
  compress deliberative chains behind executed actions. Promote user corrections to memory/skills IMMEDIATELY.

### Qwen (qwen/qwen3.8-27b) — "We let the forebrain build hindbrain tissue"
- Per-profile skill/cron/memory **drift is identity leakage**. Fix: freeze per-profile artifact schemas.
- Dispatch to exactly one profile matching the artifact type; "whoever's free" is a malformation.
- "Keep newest N" has the **wrong unit**: the ancient state that must survive is boundary-crossing
  lines (criteria, approvals, witness handles, assumptions), not raw reasoning. Latent-commitment loss is the risk.

### Gemini (google/gemini-3.8-flash) — "exit 0 is efferent signal, not proof of state"
- Bifurcate profiles into two lineages:
  - **Telic/Cognitive** (Otx2): Executive, Legislative, Intelligence, State — intent/policy/synthesis.
  - **Somatic/Invariant** (Gbx2): Defense, Treasury, Judicial — exit codes, ledgers, FS, test assertions.
- Witness queries **external state** (sockets, hashes, DB rows) from isolated env; never self-attestation loops.
- Keep structural morphology (state deltas, witness receipts); drop transient gradients (deliberative scratchpads).

## Shared Conclusions (independent convergence — high signal)
1. **Separation must become mechanical, not conventional.** Typed contracts + tool/path allowlists,
   not a politeness rule in SOUL.md.
2. **Lineage-locked dispatch.** Propagate profile-of-record through delegation
   (`{originating_profile, criteria_id}`); maker + inspector fixed from a task's birth.
3. **Reasoning-replay has a specific risk, same mitigation from all three:** drop deliberative noise
   but protect durable marks — user corrections, assumptions, witness/decision records. Promote
   boundary-crossing facts to memory/skills at write time; tag lines beyond the newest-N window.

## Optional / noted (weaker signal)
- Gemini's two-lineage categorization useful as a mental model, not a hard rule (Treasury is
  hybrid: cognitive + numeric).
- Typed bill-spec (JSON Schema) at the delegation seam — machine-checkable contract, maps to
  existing reviewer-must-verdict tradition.

## Next Actions
- Kanban cards drafted under codename `dual-origin` (see board).
- Constraint logged: reasoning-replay durability risk (seen 1x, t3 hidden-word class).