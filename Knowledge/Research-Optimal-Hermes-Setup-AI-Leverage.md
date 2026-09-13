---
title: Research: Optimal Hermes Setup & AI Leverage
tags:
  - research
  - hermes
  - publishing
date: "2026-09-13"
---

# Research: Optimal Hermes Setup & AI Leverage

> **Status:** Published
> **Date:** 2026-09-13
> **Published to:** Notion / Hermes Research Log (page `3da6feaa-0e46-81f4-9aef-dbea554cc36a`)
> **Notion link:** https://app.notion.com/p/Research-Optimal-Hermes-Setup-AI-Leverage-3da6feaa0e4681f49aefdbea554cc36a

## Summary
Use **profile-based role separation**, **context files**, **reusable skills**, **cron jobs**, and **Kanban** to turn Hermes from chat into an operating system for your work. Start with a small proven loop, then expand.

## Recommended Profile Layout
- `default` — your main interactive agent.
- `researcher` — reads docs, web, code; writes findings.
- `implementer` — executes changes against code/projects.
- `orchestrator` — splits work, assigns children, verifies handoffs.

Create from an existing profile to inherit keys/config:

```bash
hermes profile create researcher --clone --description "Reads source and external docs, writes findings."
```

## Setup Quick Path
1. Run `hermes setup --portal` for 300+ models under one subscription.
2. Set a model tier by task: Frontier for architecture/reasoning; fast model for formatting/boilerplate.
3. Set `terminal.cwd` per profile to the project folder you work in most.
4. Create `SOUL.md` for durable personality and `AGENTS.md` for project rules.
5. Run `hermes doctor --fix` to migrate config and fix npm advisories.

## Context Files
- `SOUL.md` — who the agent is; stable across sessions.
- `AGENTS.md` — project conventions; auto-loaded each session.
- `.cursorrules` / `.cursor/rules/*.mdc` — also auto-loaded; no duplication needed.

Keep them concise. Every character counts against token budget.

## Memory vs Skills
- **Memory** = facts: environment, preferences, project locations.
- **Skills** = procedures: multi-step workflows, tool-specific recipes.
- If a task takes 5+ steps and you will repeat it, save it as a skill.

## Cost & Performance
- Don't switch models mid-session frequently; each switch resets prompt cache.
- Run `/compress` before hitting limits; `/usage` and `/insights` to track spend.
- Use `hermes prompt-size` to know fixed per-message cost.

## Daily Automation Blueprints
Proactive jobs: morning briefing, nightly backlog triage, PR code review, uptime monitor, weekly AI digest, docs drift detection. Use `[SILENT]` to suppress empty notifications.

## Multi-Agent Workflow
- Orchestrator splits work into research, implementation, review, QA.
- Each worker returns a verifiable artifact: file, test result, URL, Kanban handoff.
- Use Kanban for durable handoffs, not ephemeral chat.

## Messaging & Gateways
- Set a home channel with `/sethome`.
- Each profile gets its own gateway/bot token; no cross-contamination.
- Use DM pairing instead of `GATEWAY_ALLOW_ALL_USERS=true`.

## Security
- Store secrets in `.env`; settings in `config.yaml`.
- Use `docker` or `daytona` terminal backend for untrusted repos.
- Start dangerous approvals with `session`, not `always`.

## Immediate Next Steps
1. Create missing `.env` for `researcher`.
2. Migrate config with `hermes doctor --fix`.
3. Create one `AGENTS.md` in your most-used project.
4. Schedule one cron job to prove the loop.
5. Create one skill from your most common repeated workflow.

---
[[Content-Calendar]] | [[WORKSPACE_MAP]] | [[Projects-Hub]]