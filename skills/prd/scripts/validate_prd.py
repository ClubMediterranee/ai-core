#!/usr/bin/env python3
"""Validate PRDs produced by the `prd` skill.

Deterministic, dependency-free (stdlib only) structural check. It answers one question: **is the
PRD well-formed and fully filled in?** — not whether its content is at the right altitude, which
only a reader can judge (QG-1, QG-2, QG-3, QG-5, QG-7 stay with the model).

This exists because the other twelve checks would otherwise be self-graded by the same model that
just wrote the PRD. A gate where the author is also the judge drifts, quietly, and the PRD looks
compliant while no longer being so.

Checks, per PRD:
  QG-9  Frontmatter : the 8 required fields present and non-empty; `id` shaped `PRD<NN>` and
                      matching the number in the filename; `status` and `complexity` in their
                      enumerations; `date` in ISO form.
  QG-10 Title       : the first content line after the frontmatter is an H1 equal to `title`.
  QG-11 Brief       : the referenced brief resolves on disk (ERROR if not) and carries
                      `status: validated` (WARN otherwise — an unvalidated brief is a logged
                      tension, not a wall; see refs/REF-brief-contract.md).
  QG-4  Scenarios   : every `### FUNC-xxx` block carries a WHEN and a THEN.
  QG-6  FUNC→Journey: every FUNC defined in §4 appears in at least one §3 *Capabilities revealed:*
                      list.
  QG-8  Metrics     : §7 carries its three subsections; each is populated or explicitly marked
                      "None identified." / "None defined."; every DC row has a numeric threshold.
  QG-12 AC coverage : every BR/ST/PERM/ERR id referenced in §4 is defined in §5.
  Structure         : the 9 sections present, in order, not duplicated.
  Leftovers         : the template's instantiation comment removed (ERROR); no `[ASSUMPTION: ...]`
                      marker surviving the step gate (ERROR); no `[placeholder]` or `XXX` token
                      left behind (WARN).

Headings are detected outside fenced code blocks only, so a PRD may quote a template or a payload
without shadowing its own sections.

Exit codes: 0 = clean · 1 = at least one ERROR · 2 = nothing to validate (empty or bad directory).
A file the caller named explicitly is always validated: if it does not exist that is an ERROR, not
a silent skip. WARN never fails the run.

Usage:
    python3 validate_prd.py <DOCS_ROOT>/prd/prd01-short-name.md
    python3 validate_prd.py <DOCS_ROOT>/prd                      # every PRD in the folder
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REQUIRED_FM = ["id", "title", "version", "status", "complexity", "date", "author", "brief"]
STATUS = {"in-progress", "review", "accepted"}
COMPLEXITY = {"S", "M", "L", "XL"}

SECTIONS = [
    "Executive Summary", "Personas", "User Journeys", "Functional Specifications",
    "Acceptance Criteria", "Out of Scope", "Metrics", "Glossary", "Open Questions",
]
METRIC_SUBSECTIONS = ["Lagging Metrics", "Damage Control", "Leading Metrics"]
EMPTY_MARKERS = ("None identified.", "None defined.")

ID_RE = re.compile(r"\b(BR|ST|PERM|ERR)-\d+[a-z]?\b")
FUNC_RE = re.compile(r"\bFUNC-\d+[a-z]?\b")
FUNC_HEADING_RE = re.compile(r"^###\s+(FUNC-\d+[a-z]?)\b")
SECTION_RE = re.compile(r"^##\s+(\d+)\.\s+(.+?)\s*$")
SUBSECTION_RE = re.compile(r"^###\s+(.+?)\s*$")
CAPABILITIES_RE = re.compile(r"^\s*\*Capabilit(?:y|ies) revealed:\*(.*)$", re.I)
FILENAME_NUM_RE = re.compile(r"^[Pp][Rr][Dd]\s*-?\s*(\d+)")
ID_FIELD_RE = re.compile(r"^PRD-?(\d+)$", re.I)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# a bracketed span that is not a markdown link — i.e. a leftover template placeholder
PLACEHOLDER_RE = re.compile(r"\[[^\]\n]{2,}\](?!\()")
# a speculative-derivation marker from Step 2 — none may survive into a validated PRD
ASSUMPTION_RE = re.compile(r"\[ASSUMPTION:")


@dataclass
class Finding:
    level: str      # ERROR | WARN
    prd: str
    msg: str


def unquote(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def parse_frontmatter(lines: list[str]) -> tuple[dict[str, str], int]:
    """Return (fields, index of the first body line). Empty dict when there is no frontmatter."""
    if not lines or lines[0].strip() != "---":
        return {}, 0
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            fm: dict[str, str] = {}
            for raw in lines[1:i]:
                if ":" in raw and not raw.lstrip().startswith("#"):
                    k, _, v = raw.partition(":")
                    fm[k.strip()] = unquote(v)
            return fm, i + 1
    return {}, 0


def fence_mask(lines: list[str]) -> list[bool]:
    """True for lines that sit inside a fenced code block (the fence lines themselves included)."""
    mask, inside = [], False
    for line in lines:
        if line.lstrip().startswith("```"):
            inside = not inside
            mask.append(True)
            continue
        mask.append(inside)
    return mask


def split_sections(lines: list[str], masked: list[bool]) -> dict[int, tuple[str, int, int]]:
    """Map section number → (title, first line, last line). Later duplicates overwrite; the
    duplicate itself is reported separately by check_structure."""
    marks: list[tuple[int, str, int]] = []
    for i, line in enumerate(lines):
        if masked[i]:
            continue
        m = SECTION_RE.match(line)
        if m:
            marks.append((int(m.group(1)), m.group(2), i))
    out: dict[int, tuple[str, int, int]] = {}
    for idx, (num, title, start) in enumerate(marks):
        end = marks[idx + 1][2] if idx + 1 < len(marks) else len(lines)
        out[num] = (title, start, end)
    return out


def body(lines: list[str], span: tuple[str, int, int] | None) -> list[str]:
    return [] if span is None else lines[span[1] + 1:span[2]]


# --------------------------------------------------------------------------- checks


def check_frontmatter(path: Path, fm: dict[str, str], f: list[Finding]) -> None:
    name = path.name
    for key in REQUIRED_FM:
        if not fm.get(key, "").strip() or fm.get(key, "").strip().startswith("["):
            f.append(Finding("ERROR", name, f"QG-9: frontmatter field `{key}` missing or empty"))

    fid = fm.get("id", "").strip()
    if fid:
        m = ID_FIELD_RE.match(fid)
        if not m:
            f.append(Finding("ERROR", name, f"QG-9: `id` must look like PRD01, found {fid!r}"))
        else:
            fname = FILENAME_NUM_RE.match(name)
            if fname and int(fname.group(1)) != int(m.group(1)):
                f.append(Finding("ERROR", name,
                                 f"QG-9: `id` {fid} does not match the number in the filename"))
            elif not fname:
                f.append(Finding("WARN", name,
                                 "QG-9: filename carries no PRD number — expected prd<NN>-<short-name>.md"))

    status = fm.get("status", "").strip()
    if status and status not in STATUS:
        f.append(Finding("ERROR", name,
                         f"QG-9: `status` must be one of {sorted(STATUS)}, found {status!r}"))

    cx = fm.get("complexity", "").strip()
    if cx and cx not in COMPLEXITY:
        f.append(Finding("ERROR", name,
                         f"QG-9: `complexity` must be one of {sorted(COMPLEXITY)}, found {cx!r}"))

    date = fm.get("date", "").strip()
    if date and not DATE_RE.match(date):
        f.append(Finding("ERROR", name, f"QG-9: `date` must be YYYY-MM-DD, found {date!r}"))


def check_title(path: Path, lines: list[str], start: int, fm: dict[str, str],
                f: list[Finding]) -> None:
    name = path.name
    first = next((ln.strip() for ln in lines[start:] if ln.strip()), "")
    if not first.startswith("# ") or first.startswith("## "):
        f.append(Finding("ERROR", name, "QG-10: first content line after the frontmatter is not an H1"))
        return
    h1 = first[2:].strip()
    title = fm.get("title", "").strip()
    if title and h1 != title:
        f.append(Finding("ERROR", name, f"QG-10: H1 {h1!r} differs from the `title` field {title!r}"))


def resolve_brief(path: Path, ref: str) -> Path | None:
    """A `brief` value is either a path or an id such as `brief-004`. Look for a real file."""
    ref = ref.strip()
    if not ref:
        return None
    cand = (path.parent / ref) if not ref.startswith("/") else Path(ref)
    for p in (cand, cand.with_suffix(".md")):
        if p.is_file():
            return p
    stem = re.escape(Path(ref).stem)
    pattern = re.compile(stem, re.I)
    for folder in (path.parent.parent / "brief", path.parent.parent / "briefs", path.parent, path.parent.parent):
        if folder.is_dir():
            for p in sorted(folder.glob("*.md")):
                if pattern.search(p.stem):
                    return p
    return None


def check_brief(path: Path, fm: dict[str, str], f: list[Finding]) -> None:
    name, ref = path.name, fm.get("brief", "").strip()
    if not ref:
        return                                        # already reported by check_frontmatter
    brief = resolve_brief(path, ref)
    if brief is None:
        f.append(Finding("ERROR", name, f"QG-11: brief {ref!r} does not resolve to a file on disk"))
        return
    bfm, _ = parse_frontmatter(brief.read_text(encoding="utf-8").splitlines())
    status = bfm.get("status", "").strip()
    if status != "validated":
        shown = status or "no `status` field"
        f.append(Finding("WARN", name,
                         f"QG-11: brief {brief.name} is not validated ({shown}) — "
                         "the tension must be logged in canonical-memory.md"))


def check_structure(path: Path, sections: dict[int, tuple[str, int, int]], lines: list[str],
                    masked: list[bool], f: list[Finding]) -> None:
    name = path.name
    seen: list[int] = []
    for i, line in enumerate(lines):
        if masked[i]:
            continue
        m = SECTION_RE.match(line)
        if m:
            seen.append(int(m.group(1)))
    for num, expected in enumerate(SECTIONS, start=1):
        if num not in sections:
            f.append(Finding("ERROR", name, f"structure: section {num}. {expected} is missing"))
        elif sections[num][0].strip().lower() != expected.lower():
            f.append(Finding("WARN", name,
                             f"structure: section {num} is titled {sections[num][0]!r}, "
                             f"expected {expected!r} (headings are machine tokens — do not translate)"))
    for num in sorted(set(n for n in seen if seen.count(n) > 1)):
        f.append(Finding("ERROR", name, f"structure: section {num} appears {seen.count(num)} times"))
    ordered = [n for n in seen if seen.count(n) == 1]
    if ordered != sorted(ordered):
        f.append(Finding("ERROR", name, f"structure: sections are out of order — found {seen}"))


def check_funcs(path: Path, lines: list[str], sections: dict, f: list[Finding]) -> set[str]:
    """QG-4 (each FUNC has a WHEN/THEN scenario) and QG-6 (each FUNC is revealed by a journey)."""
    name = path.name
    s4 = body(lines, sections.get(4))
    if not s4:
        return set()

    blocks: list[tuple[str, list[str]]] = []
    current: str | None = None
    buf: list[str] = []
    for line in s4:
        m = FUNC_HEADING_RE.match(line)
        if m:
            if current:
                blocks.append((current, buf))
            current, buf = m.group(1), []
        elif current:
            buf.append(line)
    if current:
        blocks.append((current, buf))

    if not blocks:
        f.append(Finding("ERROR", name, "QG-4: section 4 defines no FUNC (`### FUNC-001 — …`)"))
        return set()

    for func, block in blocks:
        text = "\n".join(block)
        if not (re.search(r"\bWHEN\b", text) and re.search(r"\bTHEN\b", text)):
            f.append(Finding("ERROR", name, f"QG-4: {func} has no WHEN/THEN nominal scenario"))

    defined = {func for func, _ in blocks}
    revealed: set[str] = set()
    for line in body(lines, sections.get(3)):
        m = CAPABILITIES_RE.match(line)
        if m:
            revealed |= set(FUNC_RE.findall(m.group(1)))
    for func in sorted(defined - revealed):
        f.append(Finding("ERROR", name,
                         f"QG-6: {func} appears in no journey's *Capabilities revealed:* list"))
    for func in sorted(revealed - defined):
        f.append(Finding("ERROR", name,
                         f"QG-6: {func} is revealed by a journey but not defined in section 4"))
    return defined


def check_acceptance_criteria(path: Path, lines: list[str], sections: dict,
                              f: list[Finding]) -> None:
    """QG-12 — every id a FUNC leans on must be defined in section 5."""
    name = path.name
    referenced = {m.group(0) for m in ID_RE.finditer("\n".join(body(lines, sections.get(4))))}
    defined = {m.group(0) for m in ID_RE.finditer("\n".join(body(lines, sections.get(5))))}
    for missing in sorted(referenced - defined):
        f.append(Finding("ERROR", name,
                         f"QG-12: {missing} is referenced in section 4 but not defined in section 5"))


def check_metrics(path: Path, lines: list[str], sections: dict, f: list[Finding]) -> None:
    """QG-8 — the three subsections exist, are populated or explicitly empty, DC rows carry a number."""
    name = path.name
    s7 = sections.get(7)
    if s7 is None:
        return                                        # already reported by check_structure
    block = body(lines, s7)

    subs: dict[str, list[str]] = {}
    current: str | None = None
    for line in block:
        m = SUBSECTION_RE.match(line)
        if m:
            current = m.group(1).strip()
            subs[current] = []
        elif current:
            subs[current].append(line)

    for expected in METRIC_SUBSECTIONS:
        match = next((k for k in subs if k.lower() == expected.lower()), None)
        if match is None:
            f.append(Finding("ERROR", name, f"QG-8: section 7 has no `### {expected}` subsection"))
            continue
        content = subs[match]
        text = "\n".join(content)
        rows = [ln for ln in content if ln.strip().startswith("|")
                and re.search(r"\|\s*(LGM|DC|LDM)-\d+", ln)]
        if not rows and not any(marker in text for marker in EMPTY_MARKERS):
            f.append(Finding("ERROR", name,
                             f"QG-8: `{expected}` is empty and carries neither "
                             f'"None identified." nor "None defined."'))
        if expected == "Damage Control":
            for row in rows:
                cells = [c.strip() for c in row.strip().strip("|").split("|")]
                if not cells or not re.search(r"\d", cells[-1]):
                    rid = re.search(r"DC-\d+", row)
                    f.append(Finding("ERROR", name,
                                     f"QG-8: {rid.group(0) if rid else 'a DC row'} has no numeric "
                                     "threshold in its last column"))


def check_leftovers(path: Path, text: str, lines: list[str], start: int,
                    f: list[Finding]) -> None:
    name = path.name
    if "INSTANTIATION NOTES" in text:
        f.append(Finding("ERROR", name,
                         "the template's instantiation comment block was not deleted"))

    masked = fence_mask(lines)
    assumption_lines = [i + 1 for i in range(start, len(lines))
                        if not masked[i] and ASSUMPTION_RE.search(lines[i])]
    if assumption_lines:
        f.append(Finding("ERROR", name,
                         f"{len(assumption_lines)} `[ASSUMPTION: ...]` marker(s) survived the step "
                         f"gate — confirm or convert each to an OQ-XXX "
                         f"(first at line {assumption_lines[0]})"))

    placeholders: list[str] = []
    for i in range(start, len(lines)):
        if masked[i] or lines[i].lstrip().startswith(("<!--", "|--", "> ")):
            continue
        placeholders += PLACEHOLDER_RE.findall(lines[i])
    placeholders = [p for p in placeholders
                    if not re.fullmatch(r"\[[ x]\]", p) and not p.startswith("[ASSUMPTION:")]
    if placeholders:
        sample = ", ".join(dict.fromkeys(placeholders[:3]))
        f.append(Finding("WARN", name,
                         f"{len(placeholders)} unreplaced placeholder(s) left — e.g. {sample}"))
    if re.search(r"\b(?:brief|OPP|PRD)-?XXX\b", text):
        f.append(Finding("WARN", name, "template token `XXX` still present"))


# --------------------------------------------------------------------------- driver


def check_prd(path: Path, findings: list[Finding]) -> None:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    fm, start = parse_frontmatter(lines)

    if not fm:
        findings.append(Finding("ERROR", path.name, "QG-9: no YAML frontmatter delimited by `---`"))
        return

    masked = fence_mask(lines)
    sections = split_sections(lines, masked)

    check_frontmatter(path, fm, findings)
    check_title(path, lines, start, fm, findings)
    check_brief(path, fm, findings)
    check_structure(path, sections, lines, masked, findings)
    check_funcs(path, lines, sections, findings)
    check_acceptance_criteria(path, lines, sections, findings)
    check_metrics(path, lines, sections, findings)
    check_leftovers(path, text, lines, start, findings)


def discover(paths: list[str]) -> list[Path]:
    out: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            out += [q for q in sorted(p.glob("*.md")) if q.name != "canonical-memory.md"]
        else:
            out.append(p)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate PRDs generated by the prd skill.")
    ap.add_argument("prds", nargs="+", help="PRD .md files, or a directory containing them")
    args = ap.parse_args()

    prds = discover(args.prds)
    if not prds:
        print("No PRD file found — check the path (exit 2).", file=sys.stderr)
        return 2

    findings: list[Finding] = []
    for p in prds:
        if not p.exists():
            findings.append(Finding("ERROR", p.name, "file not found"))
            continue
        try:
            check_prd(p, findings)
        except Exception as e:                        # never let one bad file hide the others
            findings.append(Finding("ERROR", p.name,
                                    f"validator crashed on this file: {type(e).__name__}: {e}"))

    errors = [f for f in findings if f.level == "ERROR"]
    warns = [f for f in findings if f.level == "WARN"]
    print(f"Validated {len(prds)} PRD(s): {len(errors)} error(s), {len(warns)} warning(s)\n")
    for f in errors:
        print(f"  ✗ ERROR [{f.prd}] {f.msg}")
    for f in warns:
        print(f"  ⚠ WARN  [{f.prd}] {f.msg}")
    if not errors and not warns:
        print("  ✓ all structural checks passed")
    print()
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
