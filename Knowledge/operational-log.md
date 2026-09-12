# Operational Log — System Failures

> Records system failures: bot crashes, deploy issues, fleet misbehavior.
> Agent mistakes go to `constraints.md`.
>
> **Sorting test:** Did a *system* fail, or did *we* (the agent) fail?
> System failures go here. Agent mistakes go to constraints.

---

## 2026-09-12 — Hindsight slim image crashed on startup

**What happened:** The `ghcr.io/vectorize-io/hindsight:latest-slim` container
crashed immediately on startup with:
```
ImportError: sentence-transformers is required for LocalSTEmbeddings.
Install it with: pip install sentence-transformers
```

**Root cause:** The slim image omits `sentence-transformes` to reduce size.
The Hindsight documentation states slim is for "API only" deployments, but
doesn't clearly warn that the retain path requires the full image.

**Resolution:** Removed the slim container and volume, redeployed with
`ghcr.io/vectorize-io/hindsight:latest` (full image). Container started
successfully.

**Prevention:** Always use the full image unless the slim variant's
contents are explicitly verified. See constraint C1.
