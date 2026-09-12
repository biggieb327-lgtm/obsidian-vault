# Constraints — Agent Mistake Record

> This file records mistakes the *agent* made — wrong commands, premature "done",
> theories asserted as fact, checks that could not fail. It is the system's memory
> of its own failure modes.
>
> **Not** the operational log. Bot failures go to `operational-log.md`.
> Agent mistakes go here.
>
> Format: one line for what happened, one imperative line for the constraint.
> Graduation at `seen: 2` earns a mechanism (hook, eval, or scanner).

---

## C1 — Verify the image variant before deployment

**What happened:** Deployed `ghcr.io/vectorize-io/hindsight:latest-slim` without
verifying the slim variant contained `sentence-transformers`. The container
crashed on startup with `ImportError: sentence-transformers is required for
LocalSTEmbeddings`. Recovery required deleting the container, volume, and
redeploying with the full image. ~15 minutes lost.

**Constraint:** When deploying a Docker image with variant tags (`-slim`,
`-alpine`, `-distroless`), verify the variant contains the required
dependencies *before* deployment. Check the image's Dockerfile or
documentation, or test in a throwaway container first.

```bash
# Quick check: does the slim image have the dep?
docker run --rm <image>:latest-slim pip list 2>/dev/null | grep sentence-transformers
```

**Seen:** 1  
**Graduated:** Not graduated — needs a mechanism if it recurs.

---

## C2 — Verify the provider name matches the service

**What happened:** Set `HINDSIGHT_API_LLM_PROVIDER=openai` while using a Nous API
key and base URL. Hindsight's fact extraction path sent the key to OpenAI's
servers, not Nous. The retain operation failed with `Incorrect API key provided
***. You can find your API key at https://platform.openai.com/account/api-keys.`
The Nous provider uses `NousAuthManager` (reads `~/.hermes/auth.json`), not env
vars. Recovery required re-reading the source code and restarting with
`HINDSIGHT_API_LLM_PROVIDER=nous`. ~20 minutes lost.

**Constraint:** When configuring an LLM provider, verify the provider name
matches the actual service. Don't assume `openai` works for all
OpenAI-compatible APIs — check if the service has its own provider
implementation (e.g., `nous`, `anthropic`, `gemini`).

```bash
# Quick check: what providers does this service support?
docker exec <container> grep -r "provider" /app/api/hindsight_api/engine/providers/ --include="*.py" | head
```

**Seen:** 1  
**Graduated:** Not graduated — needs a mechanism if it recurs.

---

## C3 — Check tool permissions before attempting commands

**What happened:** Repeatedly ran `docker exec hindsight ...` commands knowing I
didn't have docker permissions (the `hermes` user isn't in the `docker` group).
Every command failed with `permission denied while trying to connect to the
docker API at unix:///var/run/docker.sock`. I wasted ~5 turns asking the user
to run commands I couldn't, instead of recognizing the permission boundary and
adapting my workflow.

**Constraint:** Before attempting commands that require specific permissions,
check if the current user has those permissions. If not, either:
1. Ask the user to run the command directly, or
2. Find an alternative that doesn't require the missing permission.

```bash
# Quick check: can I run docker?
docker ps 2>/dev/null || echo "No docker access"
```

**Seen:** 1  
**Graduated:** Not graduated — needs a mechanism if it recurs.

---

## C4 — Don't restart or repeat work after compaction

**What happened:** After context compaction, I lost track of what I had already
done. I re-ran diagnostic commands, re-checked status, and repeated exploration
paths I had already completed. This wasted tokens and user time.

**Constraint:** After compaction, check the conversation summary for completed
actions before repeating work. If the summary says "Created X" or "Tested Y",
don't re-create or re-test it. Use `session_search` to recover specific details
if needed.

**Seen:** 1  
**Graduated:** Not graduated — prose only, because a hook cannot see "the agent
forgot what it already did."

---

## C5 — Log mistakes immediately, not at end of session

**What happened:** Mistakes C1-C3 were all made during this session but weren't
logged in any structured way. They only became visible when the user provided
the constraints framework. If the framework hadn't been introduced, these
mistakes would have been forgotten and likely repeated.

**Constraint:** The moment a mistake is recognized — not at the end of the
session, not in a summary, not softened after the fact — add an entry to this
file. The rule is immediate: before continuing the task, write down what
happened.

**Seen:** 1  
**Graduated:** Not graduated — prose only, because the damaging action is "the
agent doesn't write anything down," which no hook can detect.

---

## C6 — Don't explore when you should execute

**What happened:** While executing Option A, I got lost in exploration. I ran
diagnostic commands, dumped massive output, and didn't actually complete the
task. The user had to restart me. This is a pattern: I explore when I should
execute, and I execute when I should explore.

**Constraint:** Before running a diagnostic command, ask: "What will I do with
this output?" If the answer is "I don't know" or "look at it," stop. Either
commit to an action or ask the user for direction. Exploration without a
hypothesis is just noise.

**Seen:** 1  
**Graduated:** Not graduated — prose only, because the shape is "ran a command
without a hypothesis," which is indistinguishable from legitimate data
gathering.

---

## C7 — Read the whole file before patching it

**What happened:** While patching `AGENTS.md`, I used partial reads and made
two broken edits that had to be undone. One edit removed a heading instead of
updating it. Another failed because I didn't have full context for the
`old_string`. I had to re-read the entire file before making correct changes.

**Constraint:** Before patching a file, read the whole file (or at least 50
lines of context around the edit). Partial reads lead to broken edits and
wasted turns.

```bash
# Quick check: how many lines is this file?
wc -l <file>
```

**Seen:** 1  
**Graduated:** Not graduated — prose only, because a hook cannot see "the agent
didn't read enough context."

---

---

## Minor — Self-Corrected Errors

> Self-corrected errors go here. One line each, newest first.
> Two Minor entries sharing a cause get promoted to a numbered constraint.
> After 30 days, unpaired entries move to `## Minor -- archived`.

- 2026-09-12 -- Ran `docker exec` knowing permissions would fail -> Check `docker ps` before attempting docker commands
- 2026-09-12 -- Used `openai` provider for Nous instead of `nous` -> Check available provider names before configuring
- 2026-09-12 -- Deployed slim image without checking dependencies -> Verify image variant contains required packages
- 2026-09-12 -- Lost track of completed work after compaction -> Check conversation summary before repeating actions
- 2026-09-12 -- Explored instead of executing Option A -> Ask "what will I do with this output?" before running diagnostics

---

## Minor -- Archived

> Entries older than 30 days that never paired with anything.
> Kept verbatim and searchable.

*(Empty — archive starts populating after 30 days)*
