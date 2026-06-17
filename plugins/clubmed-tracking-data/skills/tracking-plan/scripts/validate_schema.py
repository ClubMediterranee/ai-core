#!/usr/bin/env python3
"""
Tracking Plan Validator
JSON Schema + 4 business rules. Exit 0 = pass. Exit 1 = errors present.
"""

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema not installed — run: pip install jsonschema")
    sys.exit(1)

SKILL_DIR   = Path(__file__).resolve().parent.parent
SCHEMA_FILE = SKILL_DIR / "data" / "plan.schema.json"

_RE_ACCENTED    = re.compile(r"[éèêàâôûùîïç]")
_RE_SLUG        = re.compile(r"^[a-z][a-z0-9_]*$")
_RE_PLACEHOLDER = re.compile(r"%")

WIDTH = 60


# ── Finding / Report ─────────────────────────────────────────────────────────


@dataclass
class Finding:
    level:   Literal["error", "warning"]
    code:    str
    message: str

    def __str__(self) -> str:
        icon = "❌" if self.level == "error" else "⚠️ "
        return f"{icon} [{self.code}] {self.message}"


@dataclass
class Report:
    plan_name: str
    findings:  list[Finding] = field(default_factory=list)

    def error(self, code: str, msg: str) -> None:
        self.findings.append(Finding("error", code, msg))

    def warn(self, code: str, msg: str) -> None:
        self.findings.append(Finding("warning", code, msg))

    @property
    def errors(self)   -> list[Finding]: return [f for f in self.findings if f.level == "error"]
    @property
    def warnings(self) -> list[Finding]: return [f for f in self.findings if f.level == "warning"]
    @property
    def ok(self) -> bool: return not self.errors

    def print_report(self) -> None:
        print(f"\n{'=' * WIDTH}")
        print(f"Tracking Plan Validation — {self.plan_name}")
        print(f"{'=' * WIDTH}")

        if not self.findings:
            print("✅ All checks passed")
        else:
            for label, items in (
                (f"🔴 {len(self.errors)} error(s)",    self.errors),
                (f"🟡 {len(self.warnings)} warning(s)", self.warnings),
            ):
                if items:
                    print(f"\n{label}:\n")
                    for f in items:
                        print(f"  {f}")
            result = "FAIL" if self.errors else "WARN"
            print(f"\n{'─' * WIDTH}")
            print(f"Result: {result} — {len(self.errors)} error(s), {len(self.warnings)} warning(s)")

        print(f"{'=' * WIDTH}\n")


# ── Rules ────────────────────────────────────────────────────────────────────


def _check_schema(plan: dict, schema: dict, report: Report) -> bool:
    """JSON Schema structural validation. Returns False if errors found (skip business rules)."""
    v = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    for error in sorted(v.iter_errors(plan), key=lambda e: list(e.path)):
        path = " → ".join(str(p) for p in error.path) or "root"
        report.error("SCHEMA", f"{path}: {error.message}")
    return report.ok


def _check_b1_pending(plan: dict, report: Report) -> None:
    """B1 — pending_approval gated by meta.status."""
    status  = plan.get("meta", {}).get("status", "inprogress")
    pending = [e["id"] for e in plan.get("entries", []) if e.get("_status") == "pending_approval"]
    if not pending:
        return
    n    = len(pending)
    noun = "entry" if n == 1 else "entries"
    ids  = ", ".join(pending[:5]) + ("…" if n > 5 else "")
    if status == "ready":
        report.error("B1", f"{n} {noun} still pending_approval but meta.status=ready — run confirm-agent: {ids}")
    else:
        report.warn("B1", f"{n} {noun} pending approval (meta.status={status}, confirmation in progress): {ids}")


def _check_b2_payload_slugs(plan: dict, report: Report) -> None:
    """B2 — payload string slugs must be language-neutral snake_case with no unresolved placeholders.
    Payload structure is enforced by JSON Schema; this checks slug quality only."""
    for entry in plan.get("entries", []):
        payload = entry.get("payload") or {}
        slugs: list[tuple[str, str]] = []  # (field_path, value)

        # event_click.detail_click
        ec = payload.get("event_click")
        if isinstance(ec, dict) and ec.get("detail_click"):
            slugs.append(("event_click.detail_click", ec["detail_click"]))

        # page_name
        if payload.get("page_name"):
            slugs.append(("page_name", payload["page_name"]))

        eid = entry["id"]
        for field_path, slug in slugs:
            if _RE_PLACEHOLDER.search(slug):
                report.error("B2", f"{eid}: {field_path} \"{slug}\" has unresolved placeholder — replace %var with a real value")
            elif _RE_ACCENTED.search(slug):
                report.error("B2", f"{eid}: {field_path} \"{slug}\" has accented characters — use language-neutral slugs")
            elif not _RE_SLUG.match(slug):
                report.error("B2", f"{eid}: {field_path} \"{slug}\" must be snake_case")


def _check_b3_inferred(plan: dict, report: Report) -> None:
    """B3 — inferred entries must carry rationale; confidence > 0.95 is suspicious."""
    for entry in plan.get("entries", []):
        if entry.get("origin") != "inferred":
            continue
        eid = entry["id"]
        if not entry.get("rationale"):
            report.error("B3", f"{eid}: inferred entry missing rationale")
        conf = entry.get("confidence")
        if conf is not None and float(conf) > 0.95:
            report.warn("B3", f"{eid}: inferred confidence {conf} > 0.95 — only confirmed events reach 1.0")


def _check_b5_params_enriched(plan: dict, report: Report) -> None:
    """B5 — params should be objects with name/type/description, not bare strings."""
    for entry in plan.get("entries", []):
        if entry.get("_status") in ("rejected", "pending_approval"):
            continue
        for i, p in enumerate(entry.get("params") or []):
            eid = entry["id"]
            if isinstance(p, str):
                report.warn("B5", f"{eid}: params[{i}] is a bare string '{p}' — use object {{name, type, description, example}}")
            elif isinstance(p, dict):
                if not p.get("type"):
                    report.warn("B5", f"{eid}: params[{i}] '{p.get('name','')}' missing type")
                if not p.get("description"):
                    report.warn("B5", f"{eid}: params[{i}] '{p.get('name','')}' missing description")


def _check_b4_target(plan: dict, report: Report) -> None:
    """B4 — approved entries should carry a target anchor."""
    skip = {"rejected", "pending_approval"}
    for entry in plan.get("entries", []):
        if entry.get("_status") in skip:
            continue
        if not entry.get("target"):
            report.warn("B4", f"{entry['id']}: no target anchor — harder to implement")


# ── Entry point ───────────────────────────────────────────────────────────────


def validate(plan_path: Path) -> int:
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"❌ [JSON] Invalid JSON: {e}")
        return 1

    schema = json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
    report = Report(plan_name=plan_path.name)

    if _check_schema(plan, schema, report):
        _check_b1_pending(plan, report)
        _check_b2_payload_slugs(plan, report)
        _check_b3_inferred(plan, report)
        _check_b5_params_enriched(plan, report)
        _check_b4_target(plan, report)

    report.print_report()
    return 0 if report.ok else 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: validate_schema.py <path/to/plan.json>")
        sys.exit(1)
    target = Path(sys.argv[1])
    if not target.exists():
        print(f"File not found: {target}")
        sys.exit(1)
    sys.exit(validate(target))
