#!/usr/bin/env python3
"""Resolve the rule set for one subagent and print it (push model).

The orchestrator runs this before spawning a subagent and injects the output into
the subagent's prompt. Each rule file declares its own scope in YAML frontmatter:

    ---
    applies-to: [write, review, harden]
    enforcement: grep | judgment | runtime
    ---
    # Rule: ...

so this resolver is a pure, deterministic function of the rule files — there is no
per-agent list to keep in sync. It reads the frontmatter with PyYAML when available
and falls back to a tiny built-in parser otherwise (no third-party dependency
required to run the bundle).

Usage:
    build_rule_bundle.py <agent>           # write | review | harden | plan | ground
    build_rule_bundle.py <agent> --list    # print matching rule filenames only

Exit codes: 0 ok · 2 bad usage · 3 no rules matched
"""
from __future__ import annotations

import sys
from pathlib import Path

AGENTS = {"write", "review", "harden", "plan", "ground"}
RULES_DIR = Path(__file__).resolve().parent.parent / "references" / "rules"


def split_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter_block, body). Empty frontmatter if none present."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return "", text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i]), "\n".join(lines[i + 1 :])
    return "", text  # unterminated frontmatter → treat as no frontmatter


def parse_frontmatter(block: str) -> dict:
    """Parse the frontmatter block. Prefer PyYAML; fall back to a minimal parser."""
    if not block.strip():
        return {}
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(block)
        return data if isinstance(data, dict) else {}
    except Exception:
        return _minimal_parse(block)


def _minimal_parse(block: str) -> dict:
    """Dependency-free parser for the two keys we use: applies-to, enforcement."""
    out: dict = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip(), val.strip()
        if val.startswith("[") and val.endswith("]"):
            items = [x.strip().strip("'\"") for x in val[1:-1].split(",")]
            out[key] = [x for x in items if x]
        else:
            out[key] = val.strip("'\"")
    return out


def load_rules() -> list[tuple[Path, dict]]:
    if not RULES_DIR.is_dir():
        sys.exit(f"error: rules dir not found at {RULES_DIR}")
    rules = []
    for path in sorted(RULES_DIR.glob("*.md")):
        if path.name == "README.md":
            continue
        fm = parse_frontmatter(split_frontmatter(path.read_text(encoding="utf-8"))[0])
        rules.append((path, fm))
    return rules


def rules_for(agent: str) -> list[Path]:
    matched = []
    for path, fm in load_rules():
        applies = fm.get("applies-to", [])
        if isinstance(applies, str):  # tolerate "a, b" written as a scalar
            applies = [x.strip() for x in applies.strip("[]").split(",")]
        if agent in applies:
            matched.append(path)
    return matched


HEADER = """\
## RULES — you MUST obey every rule below

These are hard constraints for this project, injected into your prompt. They are
not optional and not "read if relevant" — they are already in your context. A
violation of any rule is a blocking defect.
"""


def main(argv: list[str]) -> int:
    if not argv or argv[0] in {"-h", "--help"}:
        print(__doc__)
        return 0 if argv else 2
    agent = argv[0]
    list_only = len(argv) > 1 and argv[1] == "--list"

    if agent not in AGENTS:
        sys.stderr.write(f"error: unknown agent '{agent}' (expected one of {sorted(AGENTS)})\n")
        return 2

    matched = rules_for(agent)
    if not matched:
        sys.stderr.write(f"error: no rules match agent '{agent}'\n")
        return 3

    if list_only:
        print("\n".join(p.name for p in matched))
        return 0

    parts = [HEADER]
    for path in matched:
        parts.append(path.read_text(encoding="utf-8").rstrip())
        parts.append("\n---\n")
    print("\n".join(parts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
