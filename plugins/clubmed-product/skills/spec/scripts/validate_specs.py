#!/usr/bin/env python3
"""Validate specs produced by the `spec` skill.

Deterministic, dependency-free (stdlib only) format & completeness check. It answers one
question: **is the spec well-formed and fully filled in?** — not whether its content is
semantically correct (that is the reviewer subagent's job in Step 7.2).

Design rule: **fail loudly, never silently.** A file the caller named explicitly is always
validated — a spec so broken that it no longer looks like a spec must ERROR, not be skipped.

Checks, per spec:
  - Frontmatter : required keys present and non-empty; `confidence` / `data_contract_confidence`
                  valid buckets; `status` a known value; `data_contract_sources` ⊆ {api, directus};
                  `related_specs` entries resolve on disk (WARN).
  - Structure   : the 9 sections present, in order, not duplicated, and not empty; §5 carries at
                  least one PRD id.
  - §8          : sub-sections found by anchors ON A HEADING (`dc:clarify`, `dc:index`,
                  `dc:handoff`); the endpoint index has at least one row; when `api` is a declared
                  source, at least one curl/bash block, one TypeScript block, one 🟢/🟡/🔴 tier.
  - §9          : anchor `at:tests`; Gherkin parsed INSIDE the fence only; every scenario carries
                  exactly one category tag and at least one trace tag; every trace id is declared
                  in §5; at least one passing scenario; every ERR-xxx declared in §5 has a
                  non-passing scenario tagged with it.
  - §6 assets   : every local image path resolves on disk, relative to the spec file.
  - index.md    : per-PRD manifest — listed specs exist, sibling specs are listed (WARN).
  - sizing      : WARN when §5 > 15 rules or §8 > 5 endpoint detail blocks (likely >2h).

Headings and anchors inside fenced code blocks are ignored, so a spec may quote the canonical
template without shadowing its own sections.

Exit codes: 0 = clean · 1 = at least one ERROR · 2 = nothing to validate (bad path).
WARN never fails the run.

Usage:
    python3 validate_specs.py <DOCS_ROOT>/specs/<prd-slug>/childcare-slots.md
    python3 validate_specs.py <DOCS_ROOT>/specs/<prd-slug>   # one PRD's folder
    python3 validate_specs.py <DOCS_ROOT>/specs              # every PRD folder (recursive)
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.parse
from pathlib import Path

CONF = {"high", "medium", "low"}
STATUS = {"draft", "review", "approved", "done"}
ALLOWED_SOURCES = {"api", "directus"}
REQUIRED_FM = [
    "title", "author", "date", "status", "confidence",
    "data_contract_confidence", "data_contract_sources", "prd_source",
]
CATEGORY_TAGS = {
    "@nominal-passing", "@nominal-non-passing",
    "@alternative-passing", "@alternative-non-passing", "@edge",
}
PASSING_TAGS = {"@nominal-passing", "@alternative-passing"}
# id shapes: PRD-native (BR-012, FUNC-006a) and generated for unstructured sources (BR-G1)
TRACE_RE = re.compile(r"@(?:FUNC|BR|ERR|ACC|PERM|ST)-(?:G\d+|\d+[a-z]?)", re.I)
ID_RE = re.compile(r"\b(?:FUNC|BR|ERR|ACC|PERM|ST)-(?:G\d+|\d+[a-z]?)", re.I)

# Gherkin scenario keywords across the languages a spec may realistically use (Gherkin i18n).
SCENARIO_WORDS = [
    "scenario outline", "scenario template", "abstract scenario", "scenario",
    "example", "scénario", "plan du scénario", "plan du scenario", "exemple",
    "szenario", "szenariogrundriss", "beispiel",
    "escenario", "esquema del escenario", "ejemplo",
    "cenário", "cenario", "esquema do cenário", "exemplo",
    "voorbeeld", "abstract scenario",
]
_SCENARIO = re.compile(
    r"^\s*(?:" + "|".join(sorted((re.escape(w) for w in SCENARIO_WORDS), key=len, reverse=True)) + r")\s*:\s*(.*)$",
    re.I,
)
_TAG_LINE = re.compile(r"^\s*@\S")
_HEADING = re.compile(r"(?m)^####[ \t]*(\d+)\.[ \t]*(.*?)[ \t]*$")
_FENCE = re.compile(r"(?m)^\s*(`{3,}|~{3,})")


class Finding:
    __slots__ = ("level", "spec", "msg")

    def __init__(self, level: str, spec: str, msg: str) -> None:
        self.level, self.spec, self.msg = level, spec, msg


# --------------------------------------------------------------------------- parsing

def mask_fences(text: str) -> str:
    """Blank out fenced-code content, preserving length and newlines.

    Lets heading/anchor detection ignore anything quoted inside a ``` block while the original
    text (with its fences intact) is still used for the content checks.
    """
    out = list(text)
    in_fence = False
    marker = ""
    for m in re.finditer(r"(?m)^.*$", text):
        line = m.group(0)
        f = _FENCE.match(line)
        if not in_fence and f:
            in_fence, marker = True, f.group(1)[0]
            continue
        if in_fence:
            if f and f.group(1)[0] == marker:
                in_fence = False
                continue
            for i in range(m.start(), m.end()):
                if out[i] != "\n":
                    out[i] = " "
    return "".join(out)


def parse_frontmatter(text: str):
    """Minimal YAML frontmatter parser: `key: value`, `[a, b]` inline lists, `-` block lists.

    Avoids a PyYAML dependency. Tolerates a BOM and leading blank lines. An inline comment is
    only stripped when preceded by two or more spaces, so a value like `Créneau #2` survives.
    """
    text = text.lstrip("﻿ \t\r\n")
    if not text.startswith("---"):
        return None, text, text
    end = text.find("\n---", 3)
    if end == -1:
        return None, text, text
    fm_raw = text[3:end].strip("\n")
    body = text[end + 4:]
    fm: dict = {}
    cur_list_key = None
    for line in fm_raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if cur_list_key is not None and re.match(r"\s*-\s+", line) and not re.match(r"\s*[A-Za-z0-9_]+:", line):
            fm[cur_list_key].append(line.strip()[1:].strip().strip("'\""))
            continue
        m = re.match(r"([A-Za-z0-9_]+):\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val and not val.startswith(("'", '"')):
            val = re.sub(r"\s{2,}#.*$", "", val).strip()
        if val == "":
            fm[key] = []
            cur_list_key = key
        elif val.startswith("[") and val.endswith("]"):
            fm[key] = [x.strip().strip("'\"") for x in val[1:-1].split(",") if x.strip()]
            cur_list_key = None
        else:
            fm[key] = val.strip("'\"")
            cur_list_key = None
    return fm, body, text


def sections(body: str):
    """Return ({num: (title, text)}, [ordered nums], [duplicated nums]).

    Headings are located on a fence-masked copy so a `#### 8.` quoted inside a code block does
    not shadow the real section; bodies are sliced from the original text.
    """
    masked = mask_fences(body)
    heads = list(_HEADING.finditer(masked))
    out: dict = {}
    order, dupes = [], []
    for i, h in enumerate(heads):
        num = int(h.group(1))
        order.append(num)
        start = h.end()
        end = heads[i + 1].start() if i + 1 < len(heads) else len(body)
        if num in out:
            dupes.append(num)
            out[num] = (out[num][0], out[num][1] + "\n" + body[start:end])
        else:
            out[num] = (h.group(2).strip(), body[start:end])
    return out, order, sorted(set(dupes))


def gherkin_scenarios(section_text: str):
    """Parse the ```gherkin fences of §9 into [{'label', 'tags'}] — fence content only."""
    scenarios: list = []
    for block in re.findall(r"(?ms)^\s*(?:`{3,}|~{3,})gherkin[ \t]*\n(.*?)^\s*(?:`{3,}|~{3,})", section_text):
        pending: list = []
        for raw in block.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue                      # blank lines and `# language: xx` keep pending tags
            if _TAG_LINE.match(line):
                pending.extend(t for t in line.split() if t.startswith("@"))
                continue
            m = _SCENARIO.match(line)
            if m:
                scenarios.append({"label": m.group(1).strip(), "tags": pending})
                pending = []
                continue
            pending = []
    return scenarios


def image_paths(section_text: str):
    """Local image targets of `![alt](target)`, handling <>, %20, titles and balanced parens."""
    out = []
    for m in re.finditer(r"!\[[^\]]*\]\(", section_text):
        i, depth, buf = m.end(), 1, []
        while i < len(section_text) and depth:
            c = section_text[i]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if not depth:
                    break
            buf.append(c)
            i += 1
        target = "".join(buf).strip()
        target = re.sub(r'\s+"[^"]*"$', "", target)          # drop optional "title"
        target = re.sub(r"\s+'[^']*'$", "", target)
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1]
        if not target or target.startswith(("http://", "https://", "data:", "#")):
            continue
        out.append(urllib.parse.unquote(target.split("#")[0]).strip())
    return out


def looks_like_spec(fm, body: str) -> bool:
    """Structural signature only — never keyed on a required field, so a spec missing its
    required frontmatter still gets validated (and fails) instead of being skipped."""
    return bool(fm) and _HEADING.search(mask_fences(body)) is not None


# --------------------------------------------------------------------------- checks

def check_spec(path: Path, findings: list, explicit: bool) -> None:
    spec = path.name
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        findings.append(Finding("ERROR", spec, f"cannot read file: {e}"))
        return
    fm, body, _ = parse_frontmatter(text)
    if not looks_like_spec(fm, body):
        # Explicitly named by the caller → it was meant to be a spec; refusing to check it
        # silently is the one failure mode this validator must not have.
        level = "ERROR" if explicit else "SKIP"
        findings.append(Finding(level, spec, "not a spec: missing frontmatter or numbered sections"))
        return

    # ---- frontmatter
    for k in REQUIRED_FM:
        v = fm.get(k)
        if k not in fm or v in ("", []) or (isinstance(v, str) and not v.strip()):
            findings.append(Finding("ERROR", spec, f"frontmatter missing/empty: {k}"))
    for k in ("confidence", "data_contract_confidence"):
        v = fm.get(k)
        if v and not isinstance(v, str):
            findings.append(Finding("ERROR", spec, f"{k} must be a single value, got {v!r}"))
        elif isinstance(v, str) and v.strip() and v not in CONF:
            findings.append(Finding("ERROR", spec, f"{k}='{v}' not in {sorted(CONF)}"))
    st = fm.get("status")
    if isinstance(st, str) and st.strip() and st not in STATUS:
        findings.append(Finding("WARN", spec, f"status='{st}' not in {sorted(STATUS)}"))
    srcs = fm.get("data_contract_sources", [])
    if isinstance(srcs, str):
        srcs = [srcs]
    bad = [s for s in srcs if s not in ALLOWED_SOURCES]
    if bad:
        findings.append(Finding("ERROR", spec,
            f"data_contract_sources has unknown source(s) {bad} — only {sorted(ALLOWED_SOURCES)}"))
    if fm.get("date") and not re.match(r"\d{4}-\d{2}-\d{2}$", str(fm["date"])):
        findings.append(Finding("WARN", spec, f"date '{fm['date']}' is not YYYY-MM-DD"))
    rel = fm.get("related_specs", [])
    if isinstance(rel, str):
        rel = [rel]
    for r in rel:
        if r and not (path.parent / r).is_file():
            findings.append(Finding("WARN", spec, f"related_specs entry does not resolve: {r}"))

    # ---- structure
    secs, order, dupes = sections(body)
    for n in dupes:
        findings.append(Finding("ERROR", spec,
            f"section #{n} appears more than once — merge it (a split section silently disables its checks)"))
    for n in range(1, 10):
        if n not in secs:
            findings.append(Finding("ERROR", spec, f"missing section #{n}"))
    present = [n for n in order if 1 <= n <= 9]
    if present != sorted(present):
        findings.append(Finding("ERROR", spec, f"sections out of order: {present}"))
    for n, (_title, txt) in sorted(secs.items()):
        if 1 <= n <= 9 and len(re.sub(r"\s+", "", txt)) < 20:
            findings.append(Finding("ERROR", spec, f"section #{n} is empty or too short to be meaningful"))
    if 5 in secs and not ID_RE.search(secs[5][1]):
        findings.append(Finding("ERROR", spec, "§5 carries no PRD id (BR-/FUNC-/ERR-…) — rules must keep their ids"))
    # sizing heuristics — a spec should stay implementable by an AI in under ~2h
    if 5 in secs:
        rules = len(re.findall(r"(?m)^\s*\d+[.)]\s", secs[5][1]))
        if rules > 15:
            findings.append(Finding("WARN", spec, f"§5 has {rules} rules — likely >2h for an AI, consider a split"))
    if 8 in secs:
        detail_blocks = len(re.findall(r"(?m)^######\s", mask_fences(secs[8][1])))
        if detail_blocks > 5:
            findings.append(Finding("WARN", spec, f"§8 details {detail_blocks} endpoints — likely >2h for an AI, consider a split"))

    has_api = "api" in srcs

    # ---- §8 Data Contract
    if 8 in secs:
        dc = secs[8][1]
        dc_masked_headings = "\n".join(
            l for l in dc.splitlines() if l.lstrip().startswith("#")
        )
        for anchor, label, level in (
            ("dc:clarify", "'Points to clarify'", "ERROR"),
            ("dc:index", "the endpoint index", "ERROR"),
            ("dc:handoff", "'Developer Handoff'", "WARN"),
        ):
            if anchor not in dc_masked_headings:
                findings.append(Finding(level, spec,
                    f"§8 missing {label} sub-section (anchor <!-- {anchor} --> on its heading)"))
        idx = dc.split("dc:index", 1)[1] if "dc:index" in dc else ""
        rows = [l for l in idx.splitlines() if l.strip().startswith("|") and not re.match(r"^\s*\|[\s|:-]+\|\s*$", l)]
        if "dc:index" in dc_masked_headings and len(rows) < 2:
            findings.append(Finding("ERROR", spec, "§8 endpoint index has no data row"))
        if has_api:
            if not re.search(r"(?m)^\s*(?:`{3,}|~{3,})(bash|sh|shell|console|curl)\b", dc):
                findings.append(Finding("WARN", spec, "§8 has no curl/bash code block — endpoint call not shown"))
            if not re.search(r"(?m)^\s*(?:`{3,}|~{3,})(typescript|ts|tsx)\b", dc):
                findings.append(Finding("WARN", spec, "§8 has no TypeScript code block"))
            if not any(g in dc for g in ("🟢", "🟡", "🔴")):
                findings.append(Finding("WARN", spec, "§8 has no confidence tier marker (🟢/🟡/🔴)"))

    # ---- §6 assets
    if 6 in secs:
        for img in image_paths(secs[6][1]):
            if not (path.parent / img).is_file():
                findings.append(Finding("ERROR", spec, f"§6 image not found on disk: {img}"))

    # ---- §7 feature flag
    if 7 in secs:
        t7 = secs[7][1]
        declined = re.search(r"(?i)\b(no feature flag|not feature[- ]flagged|aucun (?:feature )?flag|pas de (?:feature )?flag|sans flag)\b", t7)
        if "`" not in t7 and not declined:
            findings.append(Finding("WARN", spec, "§7 Feature Flag has no flag name in backticks"))

    # ---- §9 Acceptance Tests
    if 9 in secs:
        at_title, at = secs[9]
        if "at:tests" not in (at_title + "\n" + "\n".join(
            l for l in at.splitlines() if l.lstrip().startswith("#")
        )):
            findings.append(Finding("ERROR", spec, "§9 missing the acceptance-tests anchor (<!-- at:tests --> on its heading)"))
        if not re.search(r"(?m)^\s*(?:`{3,}|~{3,})gherkin\b", at):
            findings.append(Finding("ERROR", spec, "§9 has no ```gherkin block"))
        scen = gherkin_scenarios(at)
        if not scen:
            findings.append(Finding("ERROR", spec, "§9 has no Gherkin Scenario inside the gherkin block"))
        else:
            # An id is "declared" if the spec actually covers it anywhere in §1–§7 (FUNC ids
            # naturally live in §1/§4, BR/ERR in §5). Catches fabricated ids without punishing
            # a legitimate capability reference.
            declared = {
                i.upper()
                for n in range(1, 8) if n in secs
                for i in ID_RE.findall(secs[n][1])
            }
            for s in scen:
                cats = [t for t in s["tags"] if t.lower() in CATEGORY_TAGS]
                traces = [t for t in s["tags"] if TRACE_RE.fullmatch(t)]
                label = s["label"][:50]
                if len(cats) != 1:
                    findings.append(Finding("ERROR", spec,
                        f"§9 scenario needs exactly one category tag ({len(cats)} found): {label}"))
                if not traces:
                    findings.append(Finding("ERROR", spec,
                        f"§9 scenario has no trace tag (@FUNC/@BR/@ERR…): {label}"))
                unknown = [t for t in traces if t[1:].upper() not in declared]
                if unknown and declared:
                    findings.append(Finding("ERROR", spec,
                        f"§9 scenario traces ids the spec never covers (§1–§7) {unknown}: {label}"))
            if not any(t.lower() in PASSING_TAGS for s in scen for t in s["tags"]):
                findings.append(Finding("ERROR", spec,
                    "§9 has no passing scenario (@nominal-passing / @alternative-passing)"))
            # ERR coverage — an ERR declared as a rule in §5 (start of a list item), not merely cited
            errs = set()
            if 5 in secs:
                for line in secs[5][1].splitlines():
                    m = re.match(r"\s*(?:[-*+]|\d+[.)])\s*\**\s*(ERR-(?:G\d+|\d+[a-z]?))", line)
                    if m:
                        errs.add(m.group(1).upper())
            for err in sorted(errs):
                tag = "@" + err
                covered = any(
                    any(t.upper() == tag for t in s["tags"])
                    and any(t.lower() in CATEGORY_TAGS and "non-passing" in t.lower() for t in s["tags"])
                    for s in scen
                )
                if not covered:
                    findings.append(Finding("ERROR", spec,
                        f"§9 {err} (a rule in §5) has no non-passing scenario tagged {tag}"))
            if len(scen) < 3:
                findings.append(Finding("WARN", spec,
                    f"§9 has only {len(scen)} scenario(s) — target is the five types where they apply"))


# --------------------------------------------------------------------------- driver

def discover(paths: list):
    """Return [(path, explicit)] — explicit files are always validated, directories are swept
    recursively (specs/ is output-only, so every .md under it is a spec or an index.md)."""
    specs = []
    for p in paths:
        pp = Path(p)
        if pp.is_dir():
            specs.extend((f, False) for f in sorted(pp.rglob("*.md")))
        else:
            specs.append((pp, True))
    return specs


def check_manifest(path: Path, findings: list) -> None:
    """index.md — the per-PRD manifest: every spec it lists exists, every sibling spec is listed."""
    name = f"{path.parent.name}/index.md"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        findings.append(Finding("ERROR", name, f"cannot read manifest: {e}"))
        return
    listed = set(re.findall(r"([A-Za-z0-9._-]+\.md)\b", text)) - {"index.md"}
    listed = {f for f in listed if not f.endswith((".index.md",))}
    siblings = {f.name for f in path.parent.glob("*.md")} - {"index.md"}
    for f in sorted(listed - siblings):
        if "/" not in f and not f.startswith("PRD"):    # ignore prd_source-style references
            findings.append(Finding("WARN", name, f"manifest lists a spec that does not exist: {f}"))
    for f in sorted(siblings - listed):
        findings.append(Finding("WARN", name, f"spec present in the folder but absent from the manifest: {f}"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate specs generated by the spec skill.")
    ap.add_argument("specs", nargs="+", help="spec .md files or a directory containing them")
    args = ap.parse_args()

    specs = discover(args.specs)
    if not specs:
        print("No spec files found — check the path (exit 2).", file=sys.stderr)
        return 2

    findings: list = []
    for s, explicit in specs:
        if not s.exists():
            findings.append(Finding("ERROR", s.name, "file not found"))
            continue
        try:
            if s.name == "index.md":
                check_manifest(s, findings)
                continue
            check_spec(s, findings, explicit)
        except Exception as e:                      # never let one bad file hide the others
            findings.append(Finding("ERROR", s.name, f"validator crashed on this file: {type(e).__name__}: {e}"))

    errors = [f for f in findings if f.level == "ERROR"]
    warns = [f for f in findings if f.level == "WARN"]
    skips = [f for f in findings if f.level == "SKIP"]
    validated = len(specs) - len(skips)
    print(f"Validated {validated} spec(s): {len(errors)} error(s), {len(warns)} warning(s)"
          + (f", {len(skips)} skipped" if skips else "") + "\n")
    for f in errors:
        print(f"  ✗ ERROR [{f.spec}] {f.msg}")
    for f in warns:
        print(f"  ⚠ WARN  [{f.spec}] {f.msg}")
    for f in skips:
        print(f"  · skip  [{f.spec}] {f.msg}")
    if not errors and not warns:
        print("  ✓ all checks passed" if validated else "  · nothing to validate")
    print()
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
