# SSH Hardening Runbook — vmi3420780

> **Purpose:** Record how the public SSH surface of this VPS was closed, as a runbook that can be re-executed on a rebuild.
> **Host:** `vmi3420780` (Contabo) — public `94.72.123.175`, tailnet `100.81.134.67`
> **Executed:** 2026-09-15
> **Status:** COMPLETE AND VERIFIED
> **Related:** [[Hermes-Resilience-Playbook]] · [[constraints]] · [[Decisions-Log]]

---

## 1. Summary

The VPS ran `sshd` on a world-open `22/tcp`, with `PermitRootLogin yes` and
password authentication enabled by a root-only cloud-init drop-in. Over roughly
three days `auth.log.1` recorded **18,474 failed password attempts** and **zero
successful intrusions**.

The fix taken was **not** to fight the guessing — it was to remove the exposure.
Port 22 is now reachable only over the Tailscale interface. The internet can no
longer see the service at all.

**Outcome:**

- `22/tcp` — closed to the internet, verified from 8 external nodes (all time out)
- `fail2ban` — installed, `active` + `enabled`, `sshd` jail on
- Access path — Termux → `100.81.134.67` with Tailscale connected
- Fallback — Contabo web console (provider-side, independent of port 22)
- Every other listener — unchanged, still blocked by ufw

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

## 4. The Change

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

No rule binds port 22 to the internet any more. The remaining four are redundant
with each other (`Anywhere on tailscale0` already covers every port) — **leave
them alone**, tidying is pure risk.

### 4.3 Commands, in order

```bash
# 1. Read the CURRENT numbering. Never act on a remembered number.
sudo ufw status numbered

# 2. Delete the public rules, HIGHEST number first so renumbering cannot bite.
sudo ufw delete <v6 public rule number>     # prompt must NOT mention tailscale0
sudo ufw delete <v4 public rule number>     # prompt must NOT mention tailscale0

# 3. Confirm only tailnet-scoped rules remain.
sudo ufw status numbered
```

### 4.4 fail2ban

```bash
sudo apt-get install -y fail2ban
systemctl is-active fail2ban     # -> active
systemctl is-enabled fail2ban    # -> enabled
```

Debian/Ubuntu ship `jail.d/defaults-debian.conf` with the `sshd` jail already
enabled (`enabled = true`, `banaction = nftables`, `backend = systemd`). No jail
config was needed.

---

## 5. Verification

**External probe — the only honest check.** `ufw` saying `ENABLED=yes` says
nothing about which ports actually pass.

Method: `check-host.net/check-tcp?host=IP:PORT`, then poll `/check-result/<id>`.
Requires a browser `User-Agent` or it returns **403**.

```
:22    -> closed/filtered   8/8 nodes (timeouts)
:8642  -> filtered
:8644  -> filtered
:9119  -> filtered
:9131  -> filtered
:45682 -> filtered
```

**Use a control port.** Probe a loopback-bound service alongside the real targets
and the verdict proves itself: two nodes reported `8888` and `53` reachable, but
both are bound to `127.0.0.x` and *cannot* be publicly reachable. The probe was
broken, not the firewall. Confirm binds first:

```bash
ss -tln | awk '{print $4}' | sort -u
```

**Full listener inventory (post-change):**

- **Public-bound, all ufw-blocked:** `22` (sshd, now tailnet-only), `8642`/`8644`
  (Hermes API), `9119` (Hermes dashboard), `9131` (`hermes_bridge.py`)
- **Loopback only:** `8888`, `9999` (Hindsight), `53` (systemd-resolved)
- **Tailnet only:** `100.81.134.67:45682` (Tailscale's own listener)

**fail2ban actually banning** (config ≠ rules landing):

```bash
sudo fail2ban-client status sshd      # expect Currently banned / Total banned
```

---

## 6. Rollback

**If the tailnet path fails and you need the public port back** — run in the
Contabo web console:

```bash
sudo ufw allow 22/tcp
```

That reopens 22 to the internet. Accept it as a temporary measure only.

**If Tailscale itself is the problem:** re-running `sudo tailscale up` on the box
and reopening the app on the phone restores the tailnet route. `tailscaled` is a
system service and survives reboots.

**If locked out entirely:** Contabo web console. This is why precondition 2
exists.

---

## 7. Known Remaining Soft Spots

1. **`0.0.0.0` binds.** The dashboard (9119), the bridge (9131), and the Hermes
   API (8642/8644) are each one ufw misconfiguration away from being public.
   Rebinding them to `127.0.0.1` — or the tailnet IP — would make them
   unreachable regardless of the firewall. **Not yet done; needs a decision on
   how the dashboard is reached.**
2. **Password auth over the tailnet remains enabled.** Acceptable: only devices on
   the tailnet can reach the port, and the tailnet is this box plus the phone. An
   SSH key in Termux would let it be turned off entirely.
3. **`PermitRootLogin yes`** is unchanged. With 22 off the internet it is no longer
   the exposure it was.
4. **Tailscale is now load-bearing for shell access.** It was *not* before — Hermes
   itself does not depend on it (Matrix runs over the public internet). The
   dependency introduced here is inbound reachability only.
5. **IPv6 external surface untested.** `check-host` rejects the bracketed v6
   target format and `/etc/ufw/user6.rules` is root-only. The v6 rules in
   `ufw status` are tailnet-scoped, so the intent is correct, but it is unproven
   from outside.

---

## 8. Lessons (full text in the `hermes-infrastructure` skill)

- **`ufw delete <number>` renumbers on every delete, and its confirmation prompt
  does not distinguish v4 from v6** — both print as `allow 22/tcp`. Re-read the
  list after each delete.
- **The safe veto is interface scope, not the number.** If the prompt names a rule
  containing `on tailscale0`, answer `n`. This check caught a would-be lockout: an
  `allow in on tailscale0 to any port 22` had been appended since the last
  listing, shifting the numbers so the presumed "public v6" slot was actually the
  lifeline.
- **Prove the replacement path before deleting the original.** Never remove the
  last working route to a box you cannot physically reach.
- **Find out what the user actually types in before prescribing client-side
  changes.** "My SSH app is my VPS provider" is a category error — the provider is
  the server side, the client is Termux.
- **Prove the incident is over by removing the exposure, not by fighting the
  guessing.** `fail2ban` defends; closing the port makes the question moot.
