# SSH Hardening Runbook — vmi3420780

> **Purpose:** Record how the public SSH surface of this VPS was closed, as a runbook that can be re-executed on a rebuild.
> **Host:** `vmi3420780` (Contabo) — public `94.72.123.175`, tailnet `100.81.134.67`
> **Executed:** 2026-09-15 (two phases — see below)
> **Status:** COMPLETE AND VERIFIED for the port/password/key hardening. **ONE
> ITEM STAGED, NOT APPLIED:** owner-scoping of the tailnet rule (I8) — see §5.2
> and §7.1. The live tailnet rule still trusts the whole tailnet (owner-only in
> practice: the tailnet holds just the owner's two nodes).
> **Related:** [[Hermes-Resilience-Playbook]] · [[constraints]] · [[Decisions-Log]]

---

## 1. Summary

The VPS ran `sshd` on a world-open `22/tcp`, with `PermitRootLogin yes` and
password authentication enabled by a root-only cloud-init drop-in. Over roughly
three days `auth.log.1` recorded **18,474 failed password attempts** and **zero
successful intrusions**.

**Phase 1 (04:39–05:11): ufw tailnet-only.** Port 22 was removed from the public
internet and left reachable only over the Tailscale interface. This phase used
UFW and is documented in §4.1–4.4.

**Phase 2 (same day ~08:00–09:00): firewall re-architecture.** UFW was found to
be **silently non-enforcing** (Docker 29 wipes the entire nftables ruleset on any
container create/remove/daemon restart — see §9). Enforcement moved to a
Docker-immune custom nftables table and UFW was disabled. **This phase also
turned password auth fully off and installed an SSH key.**

**Outcome (current, enforced):**
- Host firewall: `table inet hostfw` (nftables), policy **drop**, loaded by
  `host-firewall.service` + self-healing `firewall-drift-guard.timer` (20 s)
- `22/tcp` — **tailnet-only** (no eth0 rule; the internet cannot reach it)
- Password auth — **OFF** (`PasswordAuthentication no`, `PermitRootLogin
  prohibit-password`); root SSH is **key-only** (`/root/.ssh/authorized_keys`)
- `fail2ban` — `active` + `enabled`, `sshd` jail; single-IP bans **verified**
  landing in `inet f2b-table addr-set-sshd`
- `8644` (Hermes webhook API) — **closed entirely** (2026-09-15: the webhook
  platform is disabled and has no subscriptions; `8644`/`8642` listen nowhere —
  `platforms.webhook.enabled: false` in config beats the env override)
- `8642` (gateway/admin API) — loopback-only, `API_SERVER_KEY`-gated
- Access path — Termux → `100.81.134.67` with Tailscale (works), plus home
  public IPs over key auth
- Fallback — Contabo web console (provider-side, independent of port 22)

---

## 2. The Problem, With Evidence

| Reading | Value |
|---|---|
| `Failed password` in `auth.log.1` | 18,474 |
| `Accepted password` (genuine) | 6 |
| Successful intrusions | **0** |
| `PermitRootLogin` | `yes` |
| `PasswordAuthentication` | `yes` — via `50-cloud-init.conf` |
| `fail2ban` | not installed |

**Why password auth was on despite `60-cloudimg-settings.conf` saying `no`:**
sshd config is **first-set-wins**. `Include /etc/ssh/sshd_config.d/*.conf` sits at
the top of the main file, so the *lowest*-numbered drop-in wins. The root-only
`50-cloud-init.conf` (27 bytes, exactly `PasswordAuthentication yes`) beats the
readable `60-cloudimg-settings.conf`. Reading only the latter gives the wrong
answer.

**Intrusion triage — how we concluded no breach:** every accepted login traced to
the user's own devices — Comcast (Oak Harbor WA) and AT&T (Sacramento, AS7018).
The AT&T set carried low source ports (1449–3163), i.e. carrier-grade NAT, i.e. a
mobile handset, not a datacenter VPN. `authorized_keys` was 0 bytes, there were no
key-based or non-root logins, and nothing under `/home/hermes` had been modified.
The user confirmed: *"My phone has a at&t VPN because that's my provider."*

---

## 3. Preconditions (do not skip)

Both must be true **before** deleting the public rule. Skipping either risks a
lockout recoverable only through the provider console.

1. **A working login over the tailnet, from the client that actually matters.**
   Here the client is **Termux on the phone** — not a laptop. Proven by connecting
   to `100.81.134.67` from Termux and getting a root shell.
2. **A verified provider-side fallback.** Contabo web console → VPS → Console.
   Confirm it reaches a login prompt while the public route is still open.

Tailscale must be connected on the phone whenever shell access is needed.

---

## 4. Phase 1 — UFW (historical: superseded by Phase 2)

### 4.1 ufw — rules before

```
[1] 22/tcp                      ALLOW IN    Anywhere          ← public
[2] Anywhere on tailscale0      ALLOW IN    Anywhere
[3] 22/tcp on tailscale0        ALLOW IN    Anywhere
[4] 22/tcp (v6)                 ALLOW IN    Anywhere (v6)     ← public
[5] Anywhere (v6) on tailscale0 ALLOW IN    Anywhere (v6)
[6] 22/tcp (v6) on tailscale0   ALLOW IN    Anywhere (v6)
```

### 4.2 ufw — rules after

```
[1] Anywhere on tailscale0      ALLOW IN    Anywhere
[2] 22/tcp on tailscale0        ALLOW IN    Anywhere
[3] Anywhere (v6) on tailscale0 ALLOW IN    Anywhere (v6)
[4] 22/tcp (v6) on tailscale0   ALLOW IN    Anywhere (v6)
```

No rule bound port 22 to the internet. The remaining four are redundant with each
other (`Anywhere on tailscale0` already covers every port) — leave them alone.

### 4.3 fail2ban (phase 1)

```bash
sudo apt-get install -y fail2ban
systemctl is-active fail2ban     # -> active
systemctl is-enabled fail2ban    # -> enabled
```
Debian/Ubuntu ship `jail.d/defaults-debian.conf` with the `sshd` jail enabled
(`banaction = nftables`, `backend = systemd`).

### 4.4 Why Phase 1 did not hold (the Lesson that drove Phase 2)

`ufw status` reported `ENABLED=yes`, but **no rules were ever live in the
kernel** (`nft list ruleset` empty, `iptables -S INPUT` → `-P INPUT ACCEPT`).
Despite `ufw --force enable` "succeeding", the box had **no firewall at all**, so
`0.0.0.0:22` and `0.0.0.0:8644` were publicly reachable. UFW cannot survive on a
Docker host because Docker 29 resets the whole nftables ruleset (see §9).

---

## 5. Phase 2 — Docker-immune host firewall (current)

Ran ~08:00–09:00 the same day after Phase 1's silent failure was proven.

### 5.1 Files / services

| Component | Path / unit | Role |
|---|---|---|
| Ruleset (source of truth) | `/etc/nftables.d/hostfw.nft` | `table inet hostfw` — policy drop + allows |
| Loader | `/usr/local/sbin/host-firewall.sh` | flushes *only* `inet hostfw`, then `nft -f` |
| Load at boot | `host-firewall.service` | oneshot, `Before=docker` (firewall early) |
| Rapid heal | `docker-fw-watcher.service` | `After=docker`, re-applies on every container event (double-tap) |
| Safety net | `firewall-drift-guard.timer` (5 s) | re-loads hostfw + DOCKER-USER if anything wipes them |
| Forward bypass close | `docker-ufw-guard.service` | drops new inbound on eth0 in `DOCKER-USER` |
| Disabled | `ufw.service`, `nftables.service` | `nftables.service` would `flush ruleset` (nukes Docker) |

### 5.2 The ruleset (`inet hostfw`, policy DROP, loaded atomically via `nft --check`)

```
iifname "lo" accept
ct state established,related accept
ct state invalid drop
icmp + icmpv6 echo / errors accept
iifname "tailscale0" accept            # entire tailnet (covers SSH + webhook/API)
log prefix "hostfw-drop: " limit rate 3/second burst 10 packets drop      # logged drop
```
`host-firewall.sh` runs `nft --check -f hostfw.nft` BEFORE flushing, so a bad
config can never leave the table empty (open) — it refuses to apply.
**Public-internet exposure is ZERO:** SSH, the 8642 API, and the 8644 webhook are
all tailnet/loopback-only (2026-09-15: `eth0 8644` removed — the webhook platform
has no subscriptions, so a public unauth listener was dead risk).

**Owner-scoping of the tailnet rule is STAGED, NOT APPLIED (t_20321384).** The
live rule is still the whole-tailnet `iifname "tailscale0" accept`: safe only
because the tailnet happens to contain just the owner's two nodes (see §7.5).
Scoping it to the owner's device addresses needs a **three-file lockstep** root
change — `hostfw.nft` plus the hardcoded predicate in
`firewall-drift-guard.sh` and `hostops` `fw_state()` (otherwise the *more
restrictive* firewall reports `MISSING-or-drifted` forever and `hostops fw-apply`
aborts). Staged, reviewed and rehearsed at
`~/.hermes/evidence/t_20321384/` (`owner-scope-README.md`, `install-i8-owner-scope.sh`).

### 5.3 Password auth OFF + SSH key installed

- `PasswordAuthentication no`, `PermitRootLogin prohibit-password` (key-only root).
- User's `ed25519` key installed at `/root/.ssh/authorized_keys` (0600). Verified:
  the fingerprint `SHA256:y/bfXOQ…` authenticated from the phone.
- **2026-09-15:** a second, distinct **offline recovery key** (`recovery-offline-20260915`,
  fingerprint `SHA256:OaoQkI9CGdbP/DZt4WBlbv2saxwqxKPbS8LXEWEAxSs`) was added to
  `authorized_keys` so losing the primary key is not total loss (see §11 Recovery).
- Log-proof the old path died: every successful root login (Aug–Sep) was
  `Accepted password`; after this change, the only new success is
  `Accepted publickey`. The old `termux` public key was an orphan (no matching
  private key) and was replaced.

---

## 6. Verification

**Verification gotcha on a Docker host: never read the firewall with
`docker run … nft list ruleset`.** Spinning that ephemeral container *itself*
triggers Docker to reset nftables, wiping the table you are about to read — it
always looks broken. Read the live ruleset from a **pure-host** vantage:

```bash
# as root, host-side, no docker-run:
systemd-run --no-block --collect /bin/sh -c 'nft list table inet hostfw > /tmp/fw.txt; nft list table inet f2b-table >> /tmp/fw.txt'
cat /tmp/fw.txt
```

**External probe — the only honest reachability check.** `ufw`/nft saying
`ENABLED` says nothing about which ports actually pass. `check-host.net`
(check-tcp over several independent nodes). Probe a control port that is
loopback-bound (`8888`, `53`) as a self-validator — if two nodes report it
reachable it is loopback-only and the probe is broken, not the firewall.

**fail2ban actually banning** (config ≠ rules landing) — TEST an action, don't
just read `enabled = true`:

```bash
sudo fail2ban-client set sshd banip 203.0.113.77; sleep 2
nft list set inet f2b-table addr-set-sshd    # expect the IP present
sudo fail2ban-client set sshd unbanip 203.0.113.77
```

---

## 7. Current Soft Spots

### 7.1 SSH port 22 — closed to the internet (tailnet-only) ✅ / owner-scoping staged ⏳
`hostfw.nft` has **no** `eth0 … 22` rule — shell access is tailnet-only via
`tailscale0`, and the internet cannot reach 22 (verified externally:
check-host.net 2026-09-16, 11/12 nodes *Connection timed out*, 0 reachable).
**Caveat, previously mis-stated here:** the live rule is the *whole-tailnet*
`iifname "tailscale0" accept`, so today every tailnet node can reach 22, not only
the owner's phone. That is owner-only **in practice** (the tailnet holds only the
owner's two nodes) but not **enforced**. Owner-scoping to
`100.113.100.67` + `fd7a:115c:a1e0::dd32:6444` is staged, not applied — see §5.2
and §11. Reopen to the internet if ever needed: add
`iifname "eth0" tcp dport 22 accept` to `/etc/nftables.d/hostfw.nft` and run
`sudo host-firewall.sh`.

### 7.2 `0.0.0.0` binds
**Fixed 2026-09-15:** `8644` (webhook) is no longer public or listening at all —
the platform is disabled with zero subscriptions, so the public unauth-capable
listener was pure attack surface and was closed. `8642` (gateway/admin API) is
loopback-only and key-gated. If a real HMAC-secret webhook subscription is ever
added, re-open `eth0` 8644 deliberately (with a *correct* rate limit — the old
`limit rate 20/second accept` was followed by an unconditional `accept`, so it
never actually limited). Rebind anything else you do not want exposed to
`127.0.0.1` or the tailnet IP.

### 7.3 Docker churn transiently lifts the firewall (~≤20 s)
Any ephemeral `docker run`/`docker rm` resets all nft tables; the
`firewall-drift-guard.timer` re-applies within 20 s. Persistent containers
(Hindsight, Hermes gateways) do not churn, so steady-state is enforced.

### 7.4 fail2ban CIDR bans fail
The `addr-set-sshd` set lacks `flags interval`, so brute subnet bans error out.
Single-IP bans (the real attacker case) work and are verified.

### 7.5 Tailscale is load-bearing for shell access; IPv6 external surface = untested
Only the owner's phone + box are on the tailnet. hostfw does **not yet** scope
tailnet access — the live rule is `iifname "tailscale0" accept`, i.e. any tailnet
node, which is owner-only in practice today but not enforced. Owner-scoping to
the phone's v4+v6 tailnet addresses is staged (t_20321384), not applied. v6
outbound quantity unverified from outside; hostfw allows v6 ICMP/ND and applies
the same drop policy.

---

## 8. Rollback

- **Reopen a port in the new firewall:** edit `/etc/nftables.d/hostfw.nft`, then
  `sudo /usr/local/sbin/host-firewall.sh` (or `systemctl restart host-firewall`).
- **Restore the whole pre-hardening state:** `~/.hermes/scripts/rollback.sh
  ~/.hermes/backups/pre-change-20260915-082211/` (taken before this phase), then
  restart the gateway.
- **If Tailscale is the problem:** re-run `sudo tailscale up` on the box and
  reopen the app on the phone.
- **If locked out entirely:** Contabo web console (this is why precondition 2
  exists).

---

## 9. Root-cause lesson — Docker 29 wipes ALL of nftables

On every container **create/remove** and daemon **start/restart**, Docker 29
resets the **entire nftables ruleset** — not just `ip/ip6 filter`. It silently
wipes UFW's rules, any custom iptables table, AND fail2ban's `f2b-table`. This is
why the box had no firewall despite `ufw ENABLED=yes`, and why a statically-loaded
ruleset cannot persist. Enforcement therefore uses a **custom `table inet hostfw`
plus a self-heal timer** (the drift-guard), and verification must be **pure-host**
(never `docker run`). Full treatment in the `docker-ufw-firewall-pitfall` skill.

## 10. Lessons (full text in the `hermes-infrastructure` skill)

- **A firewall that reports "enabled" is not proof it is enforcing.** Verify the
  live kernel ruleset (`nft list ruleset`), not the config file.
- **`ufw delete <number>` renumbers on every delete, and its confirmation prompt
  does not distinguish v4 from v6.** Re-read the list after each delete; veto by
  interface scope, not number.
- **Prove the replacement path before deleting the original.** Never remove the
  last working route to a box you cannot physically reach.
- **Testing a ban action requires actually firing it and reading the set back.**
  `enabled=true` until the ban lands and is gone again proves nothing.
- **Find out what the user actually types in before prescribing client-side
  changes.** Provider console vs. Termux are different sides of the socket.
- **Identify every listener, not just the one you were asked about.** This
  review surfaced a write-capable HTTP bridge (`hermes_bridge.py` — SOUL, memory
  and skill writes) bound to `0.0.0.0`, a larger risk than the port under
  discussion. It was removed (quarantined to
  `~/.hermes/backups/console-removed-20260915-052626/`).

---

## 11. Recovery — root SSH keys (2026-09-15)

Two distinct root SSH keys are now in `/root/.ssh/authorized_keys` so losing one
is not total loss:

| Key | Comment | Fingerprint (SHA256) | Private half |
|---|---|---|---|
| Primary | `brian-termux` (phone / Termux) | `y/bfXOQ3JP6lM5PGbTp0yBvaXIyvruD4Nb0t0CJMzl8` | on the phone |
| **Recovery** | `recovery-offline-20260915` | `OaoQkI9CGdbP/DZt4WBlbv2saxwqxKPbS8LXEWEAxSs` | **kept OFFLINE** by the Sovereign (delivered to their chat, not stored on this VPS) |

### Key-loss recovery procedure (primary key lost)

1. **If the recovery private key is available (offline):** use it to log in —
   `ssh -i <recovery_key> root@100.81.134.67` (Tailscale on the phone) or from
   any client. Then install a fresh key: append the new public key to
   `/root/.ssh/authorized_keys` (`chown root:root`, `chmod 0600`), verify it
   authenticates, and remove the lost key's line.
2. **If BOTH keys are lost:** the only path is the **Contabo web console** →
   VPS → Console (provider-side, independent of port 22/Tailscale). From the
   console root shell, install a new public key into `/root/.ssh/authorized_keys`
   (0600) and reconnect over the tailnet. This is why the console fallback is a
   documented precondition — see §3.
3. **If Tailscale itself is down:** re-run `sudo tailscale up` on the box and
   reopen the app on the phone (see §8 Rollback).

### Tailscale ACL (control-plane) — defense in depth — NOT APPLIED

**Status 2026-09-16: not applied, and it cannot be applied from this VPS.** There
is no Tailscale API key on the box, the CLI cannot write ACLs, and the tailnet is
not managed by an agent-accessible surface — so this is a sovereign step in the
admin console. Do not believe §7.1's old claim that the firewall already scopes
by owner: it does not (see §5.2, §7.5). What is true today:

* the **host** firewall blocks all public-internet access to 22 and every admin
  port (verified externally — §7.1);
* the tailnet rule is **whole-tailnet**, so any node that joins the tailnet can
  reach 22 unless the ACL below (or the staged host-side scoping) is in place.

The ACL is the **identity-based** control and is strictly better than the staged
IP scoping because it survives a node re-registration changing its `100.x`
address. Apply this in the Tailscale admin console → Access Controls to gate SSH
by tailnet policy rather than by the host firewall alone:

```json
{
  "tagOwners": { "tag:server": ["autogroup:admin"] },
  "acls": [
    { "action": "accept", "src": ["brianault327@gmail.com"], "dst": ["100.81.134.67:22"] }
  ]
}
```

Replace the e-mail with the owner account and `100.81.134.67` with this box's
tailnet IP. The tailnet currently holds only the owner's two devices, so today
the firewall scoping already equals "owner only"; the ACL adds a control-plane
guarantee that holds even if a non-owner node joins later.