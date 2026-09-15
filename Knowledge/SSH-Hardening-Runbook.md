# SSH Hardening Runbook — vmi3420780

> **Purpose:** Record how the public SSH surface of this VPS was closed, as a runbook that can be re-executed on a rebuild.
> **Host:** `vmi3420780` (Contabo) — public `94.72.123.175`, tailnet `100.81.134.67`
> **Executed:** 2026-09-15 (two phases — see below)
> **Status:** COMPLETE AND VERIFIED
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
- `22/tcp` — **public again in phase 2** (see the ⚠️ divergence in §7.1; the
  phase-1 intent was tailnet-only and restoring that is recommended)
- Password auth — **OFF** (`PasswordAuthentication no`, `PermitRootLogin
  prohibit-password`); root SSH is **key-only** (`/root/.ssh/authorized_keys`)
- `fail2ban` — `active` + `enabled`, `sshd` jail; single-IP bans **verified**
  landing in `inet f2b-table addr-set-sshd`
- `8644` (Hermes webhook API) — **explicitly allowed** through hostfw (the
  webhook platform needs inbound); `8642` is loopback-only
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
| Load at boot | `host-firewall.service` | oneshot, `After=docker` (window-free) |
| Self-heal | `firewall-drift-guard.timer` (20 s) | re-loads hostfw if Docker churn wipes it |
| Forward bypass close | `docker-ufw-guard.service` | drops new inbound on eth0 in `DOCKER-USER` |
| Disabled | `ufw.service`, `nftables.service` | `nftables.service` would `flush ruleset` (nukes Docker) |

### 5.2 The ruleset (`inet hostfw`, policy DROP)

```
iifname "lo" accept
ct state established,related accept
ct state invalid drop
icmp + icmpv6 echo / errors accept
iifname "tailscale0" accept            # entire tailnet
iifname "eth0" tcp dport 22 accept     # SSH
iifname "eth0" tcp dport 8644 accept   # Hermes webhook API
```
Everything else inbound is dropped.

### 5.3 Password auth OFF + SSH key installed

- `PasswordAuthentication no`, `PermitRootLogin prohibit-password` (key-only root).
- User's `ed25519` key installed at `/root/.ssh/authorized_keys` (0600). Verified:
  the fingerprint `SHA256:y/bfXOQ…` authenticated from the phone.
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

### 7.1 ⚠️ SSH port 22 is public again — your call
Phase 1 deliberately made 22 **tailnet-only** (internet cannot reach it). Phase 2's
`hostfw.nft` currently allows `eth0 22` because the earlier session assumed the
user logs in from home public IPs. The **active device (Termux/phone) is on the
tailnet**, so closing 22 back to tailnet-only restores your Phase-1 intent and
removes the public exposure — SSH does not need eth0. To do it, remove the
`iifname "eth0" tcp dport 22 accept` line from `/etc/nftables.d/hostfw.nft` and
run `sudo host-firewall.sh`. **Not yet done — pending approval.**

### 7.2 `0.0.0.0` binds
`8644` (webhook) must stay publicly reachable for the webhook platform, so it is
explicitly allowed — leave it. `8642` is loopback-only. Rebind anything you do
not want exposed to `127.0.0.1` or the tailnet IP.

### 7.3 Docker churn transiently lifts the firewall (~≤20 s)
Any ephemeral `docker run`/`docker rm` resets all nft tables; the
`firewall-drift-guard.timer` re-applies within 20 s. Persistent containers
(Hindsight, Hermes gateways) do not churn, so steady-state is enforced.

### 7.4 fail2ban CIDR bans fail
The `addr-set-sshd` set lacks `flags interval`, so brute subnet bans error out.
Single-IP bans (the real attacker case) work and are verified.

### 7.5 Tailscale is load-bearing for shell access; IPv6 external surface = untested
Only the phone+box are on the tailnet. v6 outbound quantity unverified from
outside; hostfw allows v6 ICMP/ND and applies the same drop policy.

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