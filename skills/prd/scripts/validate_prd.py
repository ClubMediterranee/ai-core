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
                      enumerations; `date` in ISO form; `author` a human name — neither an email
                      nor the AI that drafted the PRD.
  QG-10 Title       : the first content line after the frontmatter is an H1 equal to `title`.
  QG-11 Brief       : the referenced brief resolves on disk (ERROR if not) and carries
                      `status: validated` (WARN otherwise — an unvalidated brief is a logged
                      tension, not a wall; see references/REF-brief-contract.md).
  QG-4  Scenarios   : every `### FUNC-xxx` block carries a WHEN and a THEN.
  QG-6  FUNC<->Journey: every FUNC defined in §4 appears in at least one §3
                      *Capabilities revealed:* list, every id revealed by a journey is defined, and
                      every journey reveals at least one FUNC — a journey still carrying the Step 2
                      `TBD` placeholder reveals nothing and is reported.
  QG-8  Metrics     : §7 carries its three subsections; each is populated or explicitly marked
                      "None identified." / "None defined."; every DC row has a numeric threshold.
  QG-12 AC integrity: referential integrity between §4 and §5. Every id referenced in §4 is
                      defined; every id is defined exactly once; every FUNC carries criteria; the
                      `Applies to` column points at capabilities that exist and mirrors what each
                      FUNC declares; each `- **ID** — text` bullet matches its §5 definition
                      (verbatim for BR and ERR, by containment for the deliberately reduced ST and
                      PERM forms); business rules open with a recap and do not reference one
                      another; ids owned by other sections resolve there.
  Structure         : the 9 sections present, in order, not duplicated; the optional §10
                      Constraints checked only when present; no stray `## ` sub-heading.
  Leftovers         : the template's instantiation comment removed (ERROR); no `[ASSUMPTION: ...]`
                      marker surviving the step gate (ERROR); no `[placeholder]` or `XXX` token
                      left behind (WARN) — short all-caps codes such as `[FR]` are content, not
                      slots, and do not count.

Deliberately NOT checked: gaps in the numbering. An id is an identifier, not a rank — a merged
FUNC retires its id and the gap is the expected trace of that merge. Flagging gaps would push
authors back into renumbering, and the renumbering cascade through §3, §5, the scenario clauses and
the PERM conditions is precisely what retiring ids exists to avoid. Do not add that check.

A check that cannot see its evidence does not accuse: where a section is absent, or carries a title
that says the document is misnumbered, the checks that depend on it stay silent rather than emit one
warning per id and bury the structural finding that explains them all.

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
# section 10 is optional: a PRD that inherits no constraint simply does not carry it. Present, it
# is checked like the other nine; absent, it is not an error.
OPTIONAL_SECTIONS = {10: "Constraints"}
# which level-3 heading each criterion type belongs under, for the type/table coherence check
KIND_HEADING = {"BR": "business rules", "ST": "states & transitions",
                "PERM": "permissions", "ERR": "error scenarios"}
# ids that live outside section 5, keyed by the section that defines them
FOREIGN_PREFIX_HOME = {"NG": 6, "OQ": 9, "LGM": 7, "DC": 7, "LDM": 7}
FOREIGN_ID_RE = re.compile(r"\b(NG|OQ|LGM|DC|LDM)-\d+[a-z]?\b")
EMPTY_MARKERS = ("None identified.", "None defined.")

ID_RE = re.compile(r"\b(BR|ST|PERM|ERR|CB|CL)-\d+[a-z]?\b")
# a criterion is *defined* by sitting in the first cell of a table row (or, for CB/CL, by being
# the leading bold id of a Constraints bullet) — never merely by being mentioned somewhere in §5
TABLE_ROW_ID_RE = re.compile(r"^\s*\|\s*\*{0,2}((?:BR|ST|PERM|ERR)-\d+[a-z]?)\*{0,2}\s*\|")
BULLET_ID_RE = re.compile(r"^\s*[-*]\s+\*\*((?:BR|ST|PERM|ERR|CB|CL)-\d+[a-z]?)\*\*\s*(.*)$")
AC_BLOCK_RE = re.compile(r"^\s*\*\*Acceptance criteria:?\*\*\s*(.*)$", re.I)
# split a markdown table row on unescaped pipes only: a `States` cell legitimately holds `\|`,
# and a naive split truncates it silently — the file stays valid and the check goes blind
PIPE_SPLIT_RE = re.compile(r"(?<!\\)\|")
SUBHEAD_RE = re.compile(r"^(#{3,4})\s+(.+?)\s*$")
LOOSE_CAPABILITIES_RE = re.compile(r"^\s*\*?Capabilit(?:y|ies) revealed:", re.I)
# the AI listing itself as author means the PM never took ownership; the convention also forbids
# an email in this field (SKILL.md Step 1: "The name alone")
AI_AUTHOR_RE = re.compile(r"anthropic|noreply|copilot", re.I)
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
# …except a short all-caps code, which is content: `[FR]`, `[DE]`, `[B2C]` annotate a country variant
# or a segment. `[XXX]` stays excluded — that one really is a template token.
LOCALE_TAG_RE = re.compile(r"\[(?!XXX\])[A-Z][A-Z0-9]{1,3}\]")
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



def split_cells(line: str) -> list[str]:
    """Cells of a markdown table row, split on unescaped pipes and unescaped afterwards."""
    parts = PIPE_SPLIT_RE.split(line.strip())
    if parts and not parts[0].strip():
        parts = parts[1:]
    if parts and not parts[-1].strip():
        parts = parts[:-1]
    return [c.strip().replace("\\|", "|") for c in parts]


def norm(s: str) -> str:
    """Comparison form: collapsed whitespace, no surrounding dash or space."""
    return re.sub(r"\s+", " ", s).strip().strip("—–-").strip()


@dataclass
class ACDef:
    cid: str
    kind: str
    line: int
    heading: str                 # the level-3 heading this row sits under
    text: str | None             # exact expected description (BR, ERR, CB, CL)
    parts: list[str]             # substrings that must all appear (ST, PERM)
    applies: set[str]            # FUNC ids read from the `Applies to` column


@dataclass
class FuncBlock:
    fid: str
    line: int
    body: list[str]


def index_criteria(lines: list[str], sections: dict,
                   f: list[Finding], name: str) -> dict[str, ACDef]:
    """Column-aware index of §5 (plus §10 Constraints).

    A criterion is recognised by the **id prefix in its first cell**, never by which table it sits
    in: §5 groups business rules into `####` thematic sub-tables, so table membership says nothing.
    Duplicate definitions are reported here — two rows sharing an id is the failure that retiring
    ids (rather than renumbering them) makes possible.
    """
    defs: dict[str, ACDef] = {}
    for sec in (5, 10):
        span = sections.get(sec)
        if span is None:
            continue
        heading = ""
        for i in range(span[1] + 1, span[2]):
            line = lines[i]
            m = SUBHEAD_RE.match(line)
            if m:
                if len(m.group(1)) == 3:
                    heading = m.group(2).strip()
                continue

            row = TABLE_ROW_ID_RE.match(line)
            bullet = BULLET_ID_RE.match(line)
            if row:
                cells = split_cells(line)
                cid = row.group(1)
                kind = cid.split("-")[0]
                text, parts, applies = None, [], set()
                if kind in ("BR", "ERR"):
                    text = cells[1] if len(cells) > 1 else ""
                elif kind == "ST":
                    parts = [cells[1]] if len(cells) > 1 else []
                    if len(cells) > 2:
                        parts += [s for s in re.split(r"[|/]", cells[2]) if s.strip()]
                elif kind == "PERM":
                    parts = [c for c in cells[1:3] if c]
                if kind == "BR" and len(cells) > 2:
                    applies = set(FUNC_RE.findall(cells[-1]))
            elif bullet and sec == 10:
                cid = bullet.group(1)
                kind = cid.split("-")[0]
                text, parts, applies = norm(bullet.group(2)), [], set()
            else:
                continue

            if cid in defs:
                f.append(Finding("ERROR", name,
                                 f"QG-12: {cid} is defined twice (lines {defs[cid].line} and "
                                 f"{i + 1}) — an id identifies one criterion and is never reused"))
                continue
            defs[cid] = ACDef(cid, kind, i + 1, heading, text, [x.strip() for x in parts], applies)
    return defs


def collect_funcs(lines: list[str], sections: dict,
                  f: list[Finding], name: str) -> list[FuncBlock]:
    """FUNC blocks of §4, in document order. Duplicate headings are reported, not silently merged."""
    blocks: list[FuncBlock] = []
    span = sections.get(4)
    if span is None:
        return blocks
    current: FuncBlock | None = None
    for i in range(span[1] + 1, span[2]):
        m = FUNC_HEADING_RE.match(lines[i])
        if m:
            current = FuncBlock(m.group(1), i + 1, [])
            blocks.append(current)
        elif current:
            current.body.append(lines[i])
    seen: dict[str, int] = {}
    for b in blocks:
        if b.fid in seen:
            f.append(Finding("ERROR", name,
                             f"QG-12: {b.fid} is defined twice (lines {seen[b.fid]} and {b.line}) "
                             "— a retired id is never re-used for another capability"))
        else:
            seen[b.fid] = b.line
    return blocks


def func_criteria(block: FuncBlock) -> tuple[list[tuple[str, str]], str | None]:
    """The `- **ID** — text` bullets of a FUNC, and the inline remainder of its header line.

    The inline remainder is non-empty only when the block still lists bare identifiers on the
    `**Acceptance criteria:**` line itself, which the readability convention replaced with bullets.
    """
    bullets: list[tuple[str, str]] = []
    inline: str | None = None
    inside = False
    for line in block.body:
        head = AC_BLOCK_RE.match(line)
        if head:
            inside = True
            inline = head.group(1).strip()
            continue
        if not inside:
            continue
        m = BULLET_ID_RE.match(line)
        if m:
            bullets.append((m.group(1), norm(m.group(2))))
        elif line.strip() and not line.lstrip().startswith(("-", "*")):
            inside = False
    return bullets, inline


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

    author = fm.get("author", "").strip()
    if "@" in author:
        f.append(Finding("ERROR", name,
                         "QG-9: `author` carries an email — the field takes the name alone"))
    if AI_AUTHOR_RE.search(author):
        f.append(Finding("ERROR", name,
                         "QG-9: `author` names the AI that drafted the PRD — put the "
                         "human owner's name here"))


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
    for num, expected in OPTIONAL_SECTIONS.items():
        if num in sections and sections[num][0].strip().lower() != expected.lower():
            f.append(Finding("WARN", name,
                             f"structure: section {num} is titled {sections[num][0]!r}, "
                             f"expected {expected!r} (headings are machine tokens)"))
    for num in sorted(set(n for n in seen if seen.count(n) > 1)):
        f.append(Finding("ERROR", name, f"structure: section {num} appears {seen.count(num)} times"))
    # only worth saying on a document whose sections parse: where they do not, the missing-section
    # findings above already explain every stray heading, and repeating them buries that signal
    structure_parses = all(n in sections for n in range(1, len(SECTIONS) + 1))
    # everything above section 1 is front matter — the table of contents lives there, under whatever
    # name the PRD's language gives it. Sub-heading misuse only means something inside a section.
    first_section = min((s[1] for s in sections.values()), default=len(lines))
    for i, line in enumerate(lines):
        if not structure_parses or masked[i] or i < first_section:
            continue
        if not line.startswith("## ") or SECTION_RE.match(line):
            continue
        f.append(Finding("WARN", name,
                         f"structure: {line.strip()!r} (line {i + 1}) uses the document's own"
                         " heading level for a sub-heading — thematic groups inside a section"
                         " belong at `####`"))
    ordered = [n for n in seen if seen.count(n) == 1]
    if ordered != sorted(ordered):
        f.append(Finding("ERROR", name, f"structure: sections are out of order — found {seen}"))


def check_funcs(path: Path, lines: list[str], sections: dict, blocks: list[FuncBlock],
                f: list[Finding]) -> set[str]:
    """QG-4 (each FUNC has a WHEN/THEN scenario) and QG-6 (FUNC <-> journey, both directions)."""
    name = path.name
    if not blocks:
        if sections.get(4) is not None:
            f.append(Finding("ERROR", name, "QG-4: section 4 defines no FUNC (`### FUNC-001 — …`)"))
        return set()

    for b in blocks:
        text = "\n".join(b.body)
        if not (re.search(r"\bWHEN\b", text) and re.search(r"\bTHEN\b", text)):
            f.append(Finding("ERROR", name, f"QG-4: {b.fid} has no WHEN/THEN nominal scenario"))
        bullets, inline = func_criteria(b)
        if not bullets and not (inline and ID_RE.search(inline)):
            f.append(Finding("WARN", name,
                             f"QG-12: {b.fid} lists no acceptance criteria — a capability with no "
                             "criterion is unspecified, not simple"))

    defined = {b.fid for b in blocks}

    # journeys: every one reveals at least one capability, and none is left at its Step 2 placeholder
    revealed: set[str] = set()
    s3 = sections.get(3)
    if s3 is not None:
        journeys: list[tuple[str, int, int]] = []
        for i in range(s3[1] + 1, s3[2]):
            m = SUBSECTION_RE.match(lines[i])
            if m and not lines[i].startswith("####"):
                journeys.append((m.group(1), i, s3[2]))
                if len(journeys) > 1:
                    journeys[-2] = (journeys[-2][0], journeys[-2][1], i)
        for title, jstart, jend in journeys:
            found: set[str] = set()
            declared = False
            for i in range(jstart, jend):
                if LOOSE_CAPABILITIES_RE.match(lines[i]):
                    declared = True
                m = CAPABILITIES_RE.match(lines[i])
                if m:
                    found |= set(FUNC_RE.findall(m.group(1)))
            revealed |= found
            if not found:
                detail = ("its *Capabilities revealed:* line is still a placeholder"
                          if declared else "it carries no *Capabilities revealed:* line")
                f.append(Finding("ERROR", name,
                                 f"QG-6: journey {title!r} reveals no FUNC — {detail} "
                                 f"(line {jstart + 1})"))

    for func in sorted(defined - revealed):
        f.append(Finding("ERROR", name,
                         f"QG-6: {func} appears in no journey's *Capabilities revealed:* list"))
    for func in sorted(revealed - defined):
        f.append(Finding("ERROR", name,
                         f"QG-6: {func} is revealed by a journey but not defined in section 4"))
    return defined


def check_acceptance_criteria(path: Path, lines: list[str], sections: dict,
                              blocks: list[FuncBlock], defs: dict[str, ACDef],
                              funcs: set[str], f: list[Finding]) -> None:
    """QG-12 — referential integrity between §4 and §5, and fidelity of the criteria bullets.

    The two sections describe the same relation from both ends: a FUNC lists the criteria it leans
    on, and a business rule lists the FUNCs it applies to. Nothing forced them to agree until now.

    Deliberately NOT checked: gaps in the numbering. An id is an identifier, not a rank — a merge
    retires its id and the gap is the expected trace of that merge. Flagging gaps would push authors
    back into renumbering, which is the cascade the convention exists to avoid.
    """
    name = path.name
    s4_text = "\n".join(body(lines, sections.get(4)))
    mentioned = {m.group(0) for m in ID_RE.finditer(s4_text)}

    for missing in sorted(mentioned - set(defs)):
        f.append(Finding("ERROR", name,
                         f"QG-12: {missing} is referenced in section 4 but not defined in section 5"))
    for orphan in sorted(set(defs) - mentioned):
        f.append(Finding("WARN", name,
                         f"QG-12: {orphan} is defined but referenced by no FUNC in section 4"))

    # `Applies to` must point at capabilities that exist, and mirror what the FUNC itself declares
    declared: dict[str, set[str]] = {}
    for b in blocks:
        bullets, inline = func_criteria(b)
        declared[b.fid] = {cid for cid, _ in bullets}
        if inline and ID_RE.search(inline):
            f.append(Finding("WARN", name,
                             f"QG-12: {b.fid} still lists bare identifiers on its "
                             "`**Acceptance criteria:**` line — expand them into "
                             "`- **ID** — description` bullets"))
        for cid, text in bullets:
            d = defs.get(cid)
            if d is None:
                continue
            if d.text is not None:
                if norm(text) != norm(d.text):
                    f.append(Finding("ERROR", name,
                                     f"QG-12: {b.fid} describes {cid} differently from its "
                                     f"section 5 definition (line {d.line}) — section 5 is the "
                                     "source of truth, realign the bullet"))
            else:
                absent = [x for x in d.parts if x and norm(x).lower() not in norm(text).lower()]
                if absent:
                    f.append(Finding("ERROR", name,
                                     f"QG-12: {b.fid}'s bullet for {cid} omits {absent[0]!r}, "
                                     f"which its section 5 definition carries (line {d.line})"))

    for cid, d in sorted(defs.items()):
        for func in sorted(d.applies):
            if func not in funcs:
                f.append(Finding("ERROR", name,
                                 f"QG-12: {cid} applies to {func}, which section 4 does not define"))
            elif func in declared and declared[func] and cid not in declared[func]:
                f.append(Finding("WARN", name,
                                 f"QG-12: {cid} applies to {func}, but {func} does not list it — "
                                 "the two directions disagree"))
        expected = KIND_HEADING.get(d.kind)
        actual = d.heading.strip().lower()
        if expected and actual and actual != expected and actual in KIND_HEADING.values():
            f.append(Finding("WARN", name,
                             f"QG-12: {cid} is defined under {d.heading!r} (line {d.line}) — "
                             "an id belongs under the heading for its type"))
        if d.kind == "BR" and d.text is not None:
            if not d.text.lstrip().startswith("**"):
                f.append(Finding("WARN", name,
                                 f"QG-12: {cid} opens with no recap (line {d.line}) — start the "
                                 "rule with a short bold label naming the case handled"))
            others = {x for x in re.findall(r"\bBR-\d+[a-z]?\b", d.text) if x != cid}
            if others:
                f.append(Finding("WARN", name,
                                 f"QG-12: {cid} references {sorted(others)[0]} in its own body "
                                 f"(line {d.line}) — a rule must stand alone; cite ST-XXX if a "
                                 "state is involved"))

    # ids owned by other sections: cited somewhere, defined nowhere
    whole = "\n".join(lines)
    for prefix, home in FOREIGN_PREFIX_HOME.items():
        span = sections.get(home)
        # only conclude when the owning section is actually there and actually is what it claims:
        # on a PRD whose sections are misnumbered, check_structure already says so once, and
        # repeating it here as one warning per id would bury the real signal
        if span is None or span[0].strip().lower() != SECTIONS[home - 1].lower():
            continue
        home_text = "\n".join(body(lines, span))
        cited = {m.group(0) for m in FOREIGN_ID_RE.finditer(whole) if m.group(1) == prefix}
        for fid in sorted(cited):
            if fid not in home_text:
                f.append(Finding("WARN", name,
                                 f"QG-12: {fid} is cited but defined nowhere in section {home}"))


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
        # `\*{0,2}` as in TABLE_ROW_ID_RE: an id written `**DC-001**` is the same row. Without it a
        # bold id makes the subsection look empty, and QG-8 fails on a purely cosmetic choice.
        rows = [ln for ln in content if ln.strip().startswith("|")
                and re.search(r"\|\s*\*{0,2}(LGM|DC|LDM)-\d+", ln)]
        if not rows and not any(marker in text for marker in EMPTY_MARKERS):
            f.append(Finding("ERROR", name,
                             f"QG-8: `{expected}` is empty and carries neither "
                             f'"None identified." nor "None defined."'))
        if expected == "Damage Control":
            for row in rows:
                cells = split_cells(row)
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
                    if not re.fullmatch(r"\[[ x]\]", p)
                    and not LOCALE_TAG_RE.fullmatch(p)
                    and not p.startswith("[ASSUMPTION:")]
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
    blocks = collect_funcs(lines, sections, findings, path.name)
    defs = index_criteria(lines, sections, findings, path.name)
    funcs = check_funcs(path, lines, sections, blocks, findings)
    check_acceptance_criteria(path, lines, sections, blocks, defs, funcs, findings)
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
