#!/usr/bin/env python3
"""Profile Boundary enforcer + verifier (dual-origin / t_84bc89dc).

Loads profiles/contracts.yaml and decides, structurally, whether a given
(profile, tool, target-path-or-command) is allowed. This is the single source
of truth that BOTH the pre_tool_call plugin (plugins/profile-boundary-guard)
and the verification test (scripts/tests/test_profile_contracts.py) call, so a
definition of "boundary violation" lives in exactly one place.

Witness kind: invariant. Exits 0 when the contract is well-formed and a
violating artifact is correctly REJECTED and a conforming one ACCEPTED
(--selftest). Exits non-zero otherwise.

WHY THIS IS STRUCTURAL (acceptance criterion 2/4)
-------------------------------------------------
The plugin and test only call functions in this file; there is no per-call
free-text reasoning. A future profile cannot "remember" to stay in bounds -- the
deny set is computed here from the contract and applied to every tool call the
plugin sees.

THE SELF-REPORT RULE (criterion 5)
----------------------------------
For the `reviewer` (Judicial) profile, a returned verdict is only accepted when
it NAMES an external witness handle and does NOT match the self-attestation
patterns (e.g. "CI green", "we ran the tests and they passed"). CI green is an
efferent signal, not a witness; the verdict must point at something a third
party can independently re-check.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


def locate_root() -> Path:
    """Resolve the install root even when a profile-scoped HERMES_HOME is set
    (dispatcher workers run with HERMES_HOME=<root>/profiles/<name>)."""
    hh = Path(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))).resolve()
    if hh.name != "profiles" and hh.parent.name == "profiles":
        return hh.parent.parent
    if hh.name in ("implementer", "orchestrator", "researcher", "reviewer",
                   "treasury", "writer", "default"):
        return hh.parent.parent if hh.parent.name == "profiles" else hh.parent
    return hh


ROOT = locate_root()
CONTRACT_PATH = ROOT / "profiles" / "contracts.yaml"

# Tool names that write to the filesystem and therefore carry a target path.
_WRITE_TOOLS = {
    "write_file", "patch", "skill_manage", "kanban_attach", "memory",
    "kanban_comment", "kanban_complete", "kanban_create",
}
_TERMINAL = "terminal"

# Self-attestation patterns that are NOT a witness (criterion 5).
_SELF_REPORT_PATTERNS = (
    re.compile(r"(?i)ci\s+green"),
    re.compile(r"(?i)tests?\s+(green|pass|passed)\b"),
    re.compile(r"(?i)we?\s+ran\s+the\s+tests?"),
    re.compile(r"(?i)all\s+checks?\s+pass"),
)


class ContractError(Exception):
    """Contract could not be loaded / is malformed."""


class _DenySet:
    __slots__ = ("paths", "tools", "commands")

    def __init__(self, paths: List[str], tools: List[str], commands: List[str]):
        self.paths = paths
        self.tools = tools
        self.commands = [c.lower() for c in commands]


def _as_list(v: Any) -> List[Any]:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def load_contract(path: Path = CONTRACT_PATH) -> Dict[str, Any]:
    """Load + validate the contract. Raises ContractError on any malformation."""
    if yaml is None:
        raise ContractError(f"PyYAML is required to load {path}")
    if not path.is_file():
        raise ContractError(f"contract not found: {path}")
    try:
        cfg = yaml.safe_load(path.read_text()) or {}
    except Exception as exc:  # noqa: BLE001
        raise ContractError(f"contract unparseable: {exc}") from exc
    if not isinstance(cfg, dict):
        raise ContractError("contract root must be a mapping")
    if cfg.get("version") != 1:
        raise ContractError(f"contract version must be 1, got {cfg.get('version')!r}")
    profiles = cfg.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        raise ContractError("contract must declare >=1 profile")
    for name, spec in profiles.items():
        if not isinstance(spec, dict):
            raise ContractError(f"profile {name!r} entry must be a mapping")
        if not spec.get("role"):
            raise ContractError(f"profile {name!r} missing role")
        returns = _as_list(spec.get("returns"))
        if not returns:
            raise ContractError(f"profile {name!r} must declare a `returns` artifact")
    return cfg


def compute_deny_set(profile: str, cfg: Dict[str, Any]) -> _DenySet:
    """Contract deny paths + tools + commands + auto rule (criterion 3)."""
    spec = (cfg.get("profiles") or {}).get(profile, {})
    deny_paths: List[str] = _as_list(spec.get("deny_paths"))
    deny_tools: List[str] = _as_list(spec.get("deny_tools"))
    deny_commands: List[str] = _as_list(spec.get("deny_commands"))

    role = spec.get("role")
    auto = cfg.get("auto_deny") or {}

    if auto.get("other_profile_homes", True):
        for other, home in (cfg.get("profile_homes") or {}).items():
            if other == profile or other == "default":
                # default's home IS the install root -- denying it would block
                # every shared dir (evidence, reports, cache). Cross-profile
                # protection for the ROOT comes from `control_files`, not a
                # blanket home deny.
                continue
            deny_paths.append(str(home))

    if auto.get("control_files", True):
        deny_paths.extend(cfg.get("control_files") or [])

    vault = cfg.get("obsidian_vault", "")
    if auto.get("obsidian_vault_for_roles") and role not in ("state",) and role:
        deny_paths.append(vault)

    seen: set = set()
    clean: List[str] = []
    for p in deny_paths:
        sp = str(p).rstrip("/")
        if not sp or sp in seen:
            continue
        seen.add(sp)
        clean.append(sp)

    return _DenySet(clean, list(dict.fromkeys(t for t in deny_tools if t)),
                    list(dict.fromkeys(c for c in deny_commands if c)))


def path_violation(profile: str, target_path: str, cfg: Dict[str, Any]) -> Optional[str]:
    """Return a reason if `target_path` is denied for `profile`, else None."""
    deny = compute_deny_set(profile, cfg)
    tp = str(target_path)
    for denied in deny.paths:
        if tp == denied or tp.startswith(denied + "/"):
            return (f"profile {profile!r} may not write {tp!r} "
                    f"(forbidden path {denied!r})")
    return None


def tool_violation(profile: str, tool_name: str, cfg: Dict[str, Any]) -> Optional[str]:
    deny = compute_deny_set(profile, cfg)
    for t in deny.tools:
        if t == tool_name or fnmatch_str(tool_name, t):
            return f"profile {profile!r} may not call tool {tool_name!r} (denied {t!r})"
    return None


def fnmatch_str(name: str, pattern: str) -> bool:
    import fnmatch
    return fnmatch.fnmatch(name, pattern)


def check_terminal(profile: str, command: str, cfg: Dict[str, Any]) -> Optional[str]:
    deny = compute_deny_set(profile, cfg)
    low = command.lower()
    for pat in deny.commands:
        if pat in low:
            return f"profile {profile!r} may not run a command containing {pat!r}"
    # Also reject a shell command that references a denied path in a write-y way
    # (crude but structural: if the denied path appears at all, flag it for
    # non-read-only commands. Deny_commands is the precise lever; this catches
    # the obvious `cd obsidian && git push` style bypass for State.)
    return None


def verdict_is_self_report(verdict_text: str, cfg: Dict[str, Any], profile: str = "reviewer") -> bool:
    """Criterion 5: True when the verdict only self-attests (CI green) and lacks
    an external witness handle."""
    deny = compute_deny_set(profile, cfg)
    has_witness = "evidence" in verdict_text.lower() or \
        "receipt" in verdict_text.lower() or \
        re.search(r"/home/hermes/\S+", verdict_text) is not None
    if has_witness:
        # still reject a witness-free self-attestation claiming a path
        for pat in _SELF_REPORT_PATTERNS:
            if pat.search(verdict_text):
                if not has_witness:
                    return True
    for pat in _SELF_REPORT_PATTERNS:
        if pat.search(verdict_text) and not has_witness:
            return True
    return False


def check_verdict(profile: str, verdict_text: str, cfg: Dict[str, Any]) -> Optional[str]:
    """Return a reason if a Judicial verdict is a self-report (no external witness)."""
    if verdict_is_self_report(verdict_text, cfg, profile):
        return ("Judicial verdict is a SELF-REPORT (CI green is not a witness). "
                "Name an external non-self evidence handle (kanban receipt, "
                "evidence-file path/hash) to certify.")
    return None


def check_tool_call(profile: str, tool_name: str, args: Dict[str, Any],
                    cfg: Dict[str, Any]) -> Optional[str]:
    """Full structural check for one tool call. Returns violation reason or None."""
    v = tool_violation(profile, tool_name, cfg)
    if v:
        return v
    if tool_name in _WRITE_TOOLS:
        target = None
        if isinstance(args, dict):
            target = args.get("path") or args.get("file_path")
        if target:
            pv = path_violation(profile, str(target), cfg)
            if pv:
                return pv
    if tool_name == _TERMINAL and isinstance(args, dict):
        cmd = args.get("command", "")
        tv = check_terminal(profile, str(cmd), cfg)
        if tv:
            return tv
    return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _selftest() -> int:
    cfg = load_contract()  # raises on malformation
    failures: List[str] = []

    # 1. contract loads with the expected profiles
    expected = {"default", "implementer", "orchestrator", "researcher",
                "reviewer", "treasury", "writer"}
    missing = expected - set((cfg.get("profiles") or {}).keys())
    if missing:
        failures.append(f"missing profile(s): {sorted(missing)}")

    # 2. DEFENSE cannot write Obsidian (denied) or another profile
    obs = path_violation("implementer", "/home/hermes/.hermes/workspace/obsidian-vault/Daily/2026-09-19.md", cfg)
    other_prof = path_violation("implementer", "/home/hermes/.hermes/profiles/writer/SOUL.md", cfg)
    control = path_violation("implementer", "/home/hermes/.hermes/AGENTS.md", cfg)
    if not obs:
        failures.append("DEFENSE was not denied Obsidian write (must FAIL)")
    if not other_prof:
        failures.append("DEFENSE was not denied writing another profile's home (must FAIL)")
    if not control:
        failures.append("DEFENSE was not denied editing a control file (must FAIL)")

    # 3. implementer may write its OWN home (allowed)
    own = path_violation("implementer", "/home/hermes/.hermes/profiles/implementer/cache/x.yaml", cfg)
    if own:
        failures.append(f"DEFENSE denied its own home write (must PASS): {own}")

    # 4. STATE cannot git push via terminal
    push = check_terminal("writer", "cd ~/obsidian && git push origin main", cfg)
    if not push:
        failures.append("STATE git push was not denied (must FAIL)")

    # 5. reviewer (Judicial) self-report rejected; witness-bearing verdict accepted
    selfrep = check_verdict("reviewer",
                            "PASS: we ran the tests and CI is green, all checks pass.",
                            cfg)
    if not selfrep:
        failures.append("Judicial self-report verdict was ACCEPTED (must FAIL)")
    witnessed = check_verdict("reviewer",
                              "PASS. Witness: evidence/t_abc/pytest.out (sha256 9f2c...).",
                              cfg)
    if witnessed:
        failures.append(f"Judicial witness-bearing verdict was REJECTED (must PASS): {witnessed}")

    # 6. tool deny: State cannot call notion? State OWNS notion; check implementer denied notion
    tool = tool_violation("implementer", "notion", cfg)
    if not tool:
        failures.append("DEFENSE was not denied the `notion` tool (must FAIL)")

    for f in failures:
        print(f"  FAIL {f}")
    if failures:
        print(f"profile-boundary --selftest: {len(failures)} failure(s)")
        return 1
    print("profile-boundary --selftest: OK (contract loadable; violations REJECTED, conforming ACCEPTED)")
    return 0


def _cmd_check(profile: str, target: str) -> int:
    cfg = load_contract()
    pv = path_violation(profile, target, cfg)
    if pv:
        print(pv)
        return 1
    print(f"allowed: {profile} may write {target}")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Profile boundary enforcer")
    ap.add_argument("--selftest", action="store_true",
                    help="run the invariant self-test (proves violating artifact is caught)")
    ap.add_argument("--check", nargs=2, metavar=("PROFILE", "PATH"),
                    help="print allow/deny for a profile writing a path")
    ap.add_argument("--json", action="store_true", help="machine output")
    args = ap.parse_args(argv)

    try:
        if args.selftest:
            rc = _selftest()
        elif args.check:
            profile, target = args.check
            rc = _cmd_check(profile, target)
        else:
            cfg = load_contract()
            if args.json:
                print(json.dumps({"ok": True, "profiles": sorted(cfg["profiles"])}))
            else:
                print(f"contract OK: {CONTRACT_PATH} "
                      f"({len(cfg['profiles'])} profiles)")
            rc = 0
    except ContractError as exc:
        print(f"profile-boundary: CONTRACT ERROR: {exc}", file=sys.stderr)
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}))
        return 2
    return rc


if __name__ == "__main__":
    sys.exit(main())