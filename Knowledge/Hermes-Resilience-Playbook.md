# Hermes Agent — Resilience Playbook

> **Purpose:** Complement the Matrix Recovery Handoff with proactive resilience measures. This playbook prevents outages rather than just responding to them.  
> **Version:** 1.0.0  
> **Last updated:** 2026-09-11

---

## 1. Proactive Model Quota Monitoring

### Problem
The NanoGPT weekly quota ran dry without warning, causing complete inference failure across all profiles.

### Solution: Quota Monitoring Cron

Create a cron that checks NanoGPT usage mid-week and alerts before exhaustion:

```bash
hermes cron create "0 10 * * 3" "Check NanoGPT weekly quota status:
1. Query the Nous Portal API or check recent error logs for 429 rate limit responses.
2. If quota utilization is >70%, notify the Sovereign with recommended actions:
   - Switch to Nous Portal free-tier model (google/gemini-3.8-flash) before Sunday reset.
   - Or enable 'Use balance after limits' at nano-gpt.com/subscription.
3. Log the quota status to memory." \
  --name "NanoGPT Quota Mid-Week Check" \
  --skill "grounded-citations" \
  --deliver "origin"
```

### Current Model Fallback Chain

When the primary model fails, the fallback order should be:

1. **Primary:** `google/gemini-3.8-flash` via Nous Portal (free tier)
2. **Secondary:** `nex-agi/nex-n2.5-mini:free` via OpenRouter (free)
3. **Tertiary:** `llama3.2:3b` via local phone router (Tailscale, zero cost)
4. **Emergency:** Paid OpenRouter model (requires valid API key)

### Configure Fallback in config.yaml

Verify if Hermes v0.21.0 supports `model.fallback`:

```bash
hermes config show model.fallback
```

If supported, configure:

```yaml
model:
  default: google/gemini-3.8-flash
  provider: nous
  fallback:
    model: nex-agi/nex-n2.5-mini:free
    provider: openrouter
```

If not supported, use the `model_aliases` system and a custom dispatch script.

---

## 2. Restore Phone Local-Router Fallback

### Problem
The original `t_e8a1896d` task (Route simple commands to phone router) was never completed. This would have provided zero-cost inference during the NanoGPT outage.

### Solution: Complete the Phone Router Setup

**Step 1:** Verify phone connectivity:

```bash
curl -s http://100.113.100.67:11434/api/tags
```

**Step 2:** Configure the local-router alias in `~/.hermes/config.yaml`:

```yaml
model_aliases:
  local-router:
    provider: custom
    base_url: http://100.113.100.67:11434/v1
    model: llama3.2:3b
    key_env: OLLAMA_API_KEY
```

**Step 3:** Test routing:

```bash
hermes -m local-router chat "Say hello in 3 words"
```

**Step 4:** For true intent-based routing (cheap to phone, heavy to cloud), create a simple classifier script or use the built-in `smart_model_routing` if available.

**Use case:** When NanoGPT/Nous quota is exhausted, switch profiles to `local-router` for free inference.

---

## 3. Fix OpenRouter API Key

### Problem
The root instance has an invalid OpenRouter key (`401 "User not found"`). This eliminates a fallback option.

### Solution

1. Generate a new key at https://openrouter.ai/keys
2. Update `/root/.hermes/.env`:
   ```bash
   OPENROUTER_API_KEY=sk-or-v1-...
   ```
3. Test:
   ```bash
   curl -s https://openrouter.ai/api/v1/chat/completions \
     -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"nex-agi/nex-n2.5-mini:free","messages":[{"role":"user","content":"Hello"}]}'
   ```

---

## 4. Crypto Store Corruption — Clarified

### Problem
The handoff doc implies the model change caused the crypto store corruption. This is misleading.

### Actual Cause
The corruption occurred because the gateway was restarted **during active troubleshooting** while the crypto store was in an inconsistent state. The restart interrupted a write operation or the olm session was already degraded from repeated auth failures.

### Prevention

Before any gateway restart or config change:

```bash
# 1. Back up crypto store
cp -a /home/hermes/.hermes/platforms/matrix/store/ \
      /home/hermes/.hermes/platforms/matrix/store.bak.$(date +%Y%m%d)/

# 2. Check store integrity (if tooling exists)
sqlite3 /home/hermes/.hermes/platforms/matrix/store/crypto.db "PRAGMA integrity_check;"

# 3. Gracefully stop the gateway
hermes gateway stop

# 4. Make config changes

# 5. Restart
hermes gateway start
```

### Recovery Procedure (Refined)

```bash
# 1. Back up current (even if corrupted)
cp -a ~/.hermes/platforms/matrix/store/ ~/.hermes/platforms/matrix/store.bak.$(date +%Y%m%d)/

# 2. Delete corrupted store
rm ~/.hermes/platforms/matrix/store/crypto.db*

# 3. Restart gateway
hermes gateway restart

# 4. Send a new message from Matrix client to establish fresh encryption session
# NOTE: Messages from before the reset will NOT be decryptable
```

---

## 5. Config Drift SOP (Safe Model Changes)

### Problem
Changing `model.default` triggers `drift_skip` on all unpinned cron jobs, causing them to fail silently.

### Procedure for Safe Model Changes

```bash
# 1. List all cron jobs and note their current model/provider
hermes cron list

# 2. Change the default model
hermes config set model.default <new-model>
hermes config set model.provider <new-provider>

# 3. Pin ALL existing cron jobs to the new config
# (Copy the job IDs from step 1)
hermes cron edit <job-id-1> --provider <new-provider> --model <new-model>
hermes cron edit <job-id-2> --provider <new-provider> --model <new-model>
# ... repeat for every job

# 4. Verify no jobs are showing drift_skip
hermes cron list

# 5. Trigger a test run on one job to confirm
hermes cron run <job-id>
```

### One-Liner to Pin All Jobs

```bash
hermes cron list --json 2>/dev/null | python3 -c "
import sys, json, subprocess
data = json.load(sys.stdin)
for job in data:
    if job.get('enabled'):
        jid = job['id']
        name = job.get('name', '')[:40]
        print(f'Pinning {jid} ({name})...')
        subprocess.run(['hermes', 'cron', 'edit', jid, '--provider', 'nous', '--model', 'google/gemini-3.8-flash'])
"
```

---

## 6. Lessons Learned (From This Incident)

| What Happened | What We Did Wrong | What We'll Do Differently |
|---|---|---|
| NanoGPT quota ran dry | No quota monitoring until failure | Add mid-week quota check cron |
| Drift_skip stopped all cron jobs | Jobs were unpinned | Pin all jobs after any model change |
| Crypto store corrupted | Restarted during active troubleshooting | Back up store before any restart; use graceful stop |
| OpenRouter fallback invalid | Key was never tested after creation | Test fallback keys monthly |
| Phone router not restored | t_e8a1896d blocked and abandoned | Complete phone router setup for zero-cost fallback |
| No fallback model configured | Assumed primary would always work | Configure fallback chain explicitly |

---

## 7. Resilience Testing Schedule

Run these tests monthly to verify fallback systems work:

### Monthly Fallback Test (First Sunday of Month)

```bash
#!/bin/bash
# File: ~/.hermes/scripts/monthly_fallback_test.sh

echo "=== Hermes Fallback Test $(date) ==="

echo "--- Test 1: Primary Model (Nous) ---"
hermes -m google/gemini-3.8-flash chat "Reply with: primary ok" 2>&1 | tail -1

echo "--- Test 2: OpenRouter Fallback ---"
hermes -m nex-agi/nex-n2.5-mini:free chat "Reply with: openrouter ok" 2>&1 | tail -1

echo "--- Test 3: Phone Local-Router ---"
hermes -m local-router chat "Reply with: phone ok" 2>&1 | tail -1

echo "--- Test 4: YNAB Connection ---"
hermes -p treasury chat "What is my Chase Checking balance?" 2>&1 | tail -1

echo "--- Test 5: Matrix Crypto Store ---"
sqlite3 /home/hermes/.hermes/platforms/matrix/store/crypto.db "PRAGMA integrity_check;" 2>&1

echo "--- Test 6: Obsidian Git Sync ---"
cd /home/hermes/.hermes/workspace/obsidian-vault && git status -sb

echo "=== Test Complete ==="
```

Schedule:

```bash
hermes cron create "0 11 1-7 * 0" "Run monthly fallback resilience test" \
  --script monthly_fallback_test.sh \
  --deliver local \
  --name "Monthly Resilience Test"
```

---

## 8. Key Paths Quick Reference

| Component | Path |
|---|---|
| Config | `/home/hermes/.hermes/config.yaml` |
| Env (API keys) | `/home/hermes/.hermes/.env` |
| Crypto store | `/home/hermes/.hermes/platforms/matrix/store/` |
| Cron jobs | `/home/hermes/.hermes/cron/jobs.json` |
| Executions DB | `/home/hermes/.hermes/cron/executions.db` |
| Logs | `/home/hermes/.hermes/logs/` |
| Gateway service | `systemctl --user status hermes-gateway.service` |
| Obsidian vault | `/home/hermes/.hermes/workspace/obsidian-vault/` |
| Scripts | `/home/hermes/.hermes/scripts/` |
| Qdrant storage | `/home/hermes/.hermes/qdrant_storage/` |
