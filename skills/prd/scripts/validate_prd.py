#!/usr/bin/env python3
"""Validate PRDs produced by the `prd` skill.

Deterministic, stdlib-only. It answers one question — **is the PRD well-formed and fully filled
in?** — and leaves altitude and meaning to a reader: QG-3 and the judged halves of QG-1 and QG-2
are the Challenge Pass tables of `references/REF-challenge-pass.md`; QG-5 and QG-7 are the gate's
third movement, the two crossings no table can see. One check, one home: what
this script decides, no table restates — and a gate whose every check is judged by the model that
just wrote the PRD would drift, quietly.

Checks run in the order the skill writes the document, one group per step. `--up-to N` runs the
groups 1..N and stays silent about what later steps still owe; without it, every group runs.

  Step 1 — frame & scope: the file is a PRD
    QG-9   frontmatter: 8 fields present; `id` = PRD<NN> = the filename's number; `status` and
           `complexity` in their enumerations; ISO date; `author` a human name (no email, not
           the AI that drafted it); `record` present when `brief` is `none`             ERROR
    QG-10  the first content line is an H1 equal to `title`                             ERROR
    QG-11  the brief resolves on disk (ERROR) and carries `status: validated` (WARN);
           `brief: none` is a PRD framed without a brief (WARN)
    —      the 9 sections present, in order, once (ERROR); §10 tolerated absent in
           PRDs written before 1.8.0; a fence left
           open, the template's instantiation comment (ERROR); a `## ` used inside a
           section, a translated section title, a section after `## Parked` (WARN);
           the `## Parked` table keeps its columns, every row targets `Step 2`..`6`
           (ERROR); the project record resolves on disk (WARN)
  Step 2 — personas and journeys
    QG-1   every journey states a `*Goal:*` and numbers its steps flat, no `2a.`         WARN
    QG-12  §2 Personas is not empty                                                     WARN
    QG-12  §8 ↔ the project record's Vocabulary: a term frozen in §8 has a row with the
           same definition (ERROR on a different one, WARN when absent); a row minted
           by this PRD is in §8 (WARN)
    QG-2   a journey step names a UI component (modal, drawer, onglet…) — the lexical
           half; the semantic half (positions, mechanics, container-driven carving)
           stays with the Challenge Pass                                                WARN
  Step 3 — functional blocks
    QG-4   every FUNC carries a WHEN and a THEN                                         ERROR
    QG-6   FUNC ↔ journeys in three directions: every FUNC revealed by a journey, every
           revealed id defined, every journey revealing at least one — a `TBD` left
           from Step 2 reveals nothing                                                  ERROR
    QG-12  FUNC ids defined once                                                        ERROR
    QG-2   a FUNC names a UI component in its title, capability or scenario — same
           lexical half as Step 2's                                                     WARN
  Step 4 — acceptance criteria
    QG-12  §4 ↔ §5: every id referenced in §4 is defined, every id is defined once, each
           bullet equals its §5 row (verbatim for BR/ERR, by containment for ST/PERM),
           `Applies to` names FUNCs that exist and is never empty — §10's constraints
           are read from Step 6 only                                                    ERROR
           every FUNC lists criteria, the mirror agrees both ways, a BR opens with a
           bold recap and cites no other BR, an id sits under the heading of its type  WARN
    QG-12  §5 carries its four subsections (WARN); every table keeps the columns it is
           read by — arity and order (ERROR), translated wording (WARN)
  Step 5 — metrics
    QG-8   §7 carries its three subsections, each populated or explicitly empty        ERROR
           a DC without numeric threshold, an LGM without threshold, an LDM without
           collection method or review cadence                                          WARN
    QG-12  LGM/DC/LDM ids defined once (ERROR); the §7 tables keep their columns
  Step 6 — closing sections
    QG-9   `complexity` coherent with the grid for the number of FUNCs                  WARN
    QG-12  NG and OQ ids defined once (ERROR); a §6 row opens with an NG id, a glossary
           term is defined once (WARN); the §6/§8/§9 tables keep their columns; an
           `accepted` PRD carries no open question; `## Parked` still in a `review` or
           `accepted` PRD (ERROR)
  Every run, over what the steps so far own
    QG-12  an NG/OQ/LGM/DC/LDM id cited anywhere is defined in its home section; a
           FUNC cited outside §3–§5 is defined in §4                                    WARN
    —      no `[ASSUMPTION: ...]` survives a gate (ERROR); no `[placeholder]`, no
           `XXX` token left behind (WARN)
    —      a `## Parked` row still targeting a step whose gate has passed (ERROR); under
           `--up-to N`, a section a later step owns already holding content — written
           before its gate (ERROR; known limits: a persona on one italic line, a
           blockquote, a FUNC body entirely in a fence are not seen); a record decision
           that resolves an OQ still open in §9 (ERROR)
  The project record, `{DOCS_ROOT}/record/<record>.md`, once per run
    —      its four tables present, each with its table and columns (every table of a
           block is checked); its instantiation comment deleted, its title filled; D/T
           ids unique and numbered for the PRD they name (a `brief-NN` row is the
           brief's); a term defined once; a `Status` / `Gate` in its enumeration; a PRD
           column that resolves on disk — the next number is reserved, not missing

Under `--up-to N` the last group reads only the lines Steps 1..N own: §4's acceptance-criteria
bullets belong to Step 4, §6/§8/§9 close at Step 6, a `## Parked` row belongs to the step it is
parked for. A skeleton still holding its later placeholders therefore passes the earlier gates.

Deliberately NOT checked: gaps in the numbering. An id is an identifier, not a rank — a merged
FUNC retires its id and the gap is the expected trace of that merge. Flagging gaps would push
authors back into renumbering, and the renumbering cascade through §3, §5, the scenario clauses
and the PERM conditions is precisely what retiring ids exists to avoid. Do not add that check.

A check that cannot see its evidence does not accuse: where a section is absent, or carries a title
that says the document is misnumbered, the checks that depend on it stay silent rather than emit one
warning per id and bury the structural finding that explains them all. Headings are read outside
fenced code blocks only, and ids inside a fence never count, so a PRD may quote a template or a
payload without shadowing its own sections.

The suite `tests/prd/test_validate_prd.py`, at the repository root, tests the validator itself —
run it after any change. It never runs during a PRD session and is not packaged with the skill.

Exit codes: 0 = clean · 1 = at least one ERROR · 2 = nothing to validate (empty or bad directory).
Python 3.8 or later (the `:=` operator; later syntax is deferred by the `__future__` import).
A file the caller named explicitly is always validated: if it does not exist that is an ERROR, not
a silent skip. WARN never fails the run.

Usage:
    python3 validate_prd.py <DOCS_ROOT>/prd/prd01-short-name.md
    python3 validate_prd.py <DOCS_ROOT>/prd/prd01-short-name.md --up-to 3
    python3 validate_prd.py <DOCS_ROOT>/prd                      # every PRD in the folder
    python3 validate_prd.py <DOCS_ROOT>/record/brief01-name.md   # the project record alone
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------- the format

REQUIRED_FM = ["id", "title", "version", "status", "complexity", "date", "author", "brief"]
# `record` names the project's decision record; it defaults to the brief's stem, so it is required
# only for a PRD framed without a brief
NO_BRIEF = "none"
STATUS = {"in-progress", "review", "accepted"}
COMPLEXITY = {"S", "M", "L", "XL"}
COMPLEXITY_GRID = [("S", 3), ("M", 7), ("L", 14), ("XL", 10**6)]

SECTIONS = [
    "Executive Summary", "Personas", "User Journeys", "Functional Specifications",
    "Acceptance Criteria", "Out of Scope", "Metrics", "Glossary", "Open Questions",
]
# section 10 is in every PRD since 1.8.0 (its legend states the inherited baseline), but a PRD
# written before carries it only when it inherits a constraint — so its absence is not an error
OPTIONAL_SECTIONS = {10: "Constraints"}
AC_SUBSECTIONS = ["Business Rules", "States & Transitions", "Permissions", "Error Scenarios"]
METRIC_SUBSECTIONS = ["Lagging Metrics", "Damage Control", "Leading Metrics"]
# read by its words: the case and the closing period are typography, not the marker
EMPTY_MARKER_RE = re.compile(r"\bNone (?:identified|defined)\b", re.I)

# every cell in this file is read by POSITION — `Applies to` is the last cell, an object's states are
# the third. A column added, removed or permuted makes the reader take the wrong one, silently, and
# nothing downstream can tell. The headers are therefore part of the format, not decoration.
#
# Each entry lists the accepted headers, the first being the current template. A second form is
# listed only where the table carries no positional read that a variation would corrupt — Lagging
# Metrics gained its `Baseline (T0)` column after PRDs had already been written, and its cells are
# read by name-independent rules alone. Refusing the older form there would fail existing documents
# to protect nothing.
TABLE_HEADERS = {
    "Business Rules": [["ID", "Rule", "Applies to"]],
    "States & Transitions": [["ID", "Object", "States", "Allowed transitions", "Blocked transitions"]],
    "Permissions": [["ID", "Actor", "Action", "Allowed condition", "Blocked condition"]],
    "Error Scenarios": [["ID", "Failure mode", "Expected behavior"]],
    "Out of Scope": [["Item", "Reason"]],
    "Lagging Metrics": [["ID", "Metric", "Baseline (T0)", "Threshold"],
                        ["ID", "Metric", "Threshold"]],
    "Damage Control": [["ID", "Metric", "Current baseline", "Max acceptable degradation"]],
    "Leading Metrics": [["ID", "Observable behavior", "Collection method", "Review cadence"]],
    "Glossary": [["Term", "Definition"]],
    "Open Questions": [["ID", "Question", "Impact if unresolved", "Blocks", "Source"]],
    "Parked": [["Item", "Kind", "For", "Origin"]],
}
# the project's decision record — one file per brief under {DOCS_ROOT}/record/, four tables by
# nature, every row naming the PRD it comes from; ids are prefixed by that PRD's number
RECORD_DIR = "record"
RECORD_TABLES = {
    "Decisions": ["ID", "PRD", "Step", "Decision", "Why", "Resolves", "Affects"],
    "Tensions": ["ID", "PRD", "Tension", "Status", "Resolution", "Affects"],
    "Vocabulary": ["Term", "Definition", "PRD"],
    "Sources": ["PRD", "Source", "What it produced", "Gate"],
}
RECORD_ID_RE = re.compile(r"^\*{0,2}([DT])-(\d+)-(\d+)\*{0,2}$")
TENSION_STATUS = {"open", "accepted", "resolved"}
SOURCE_GATE = {"kept", "cut"}
# §6, §8 and §9 carry a single unnamed table: the section title stands in for the sub-heading
SECTION_TABLE_OWNER = {6: "Out of Scope", 8: "Glossary", 9: "Open Questions"}
# which level-3 heading each criterion type belongs under
KIND_HEADING = {"BR": "business rules", "ST": "states & transitions",
                "PERM": "permissions", "ERR": "error scenarios"}
# ids that live outside section 5, keyed by the section that defines them
FOREIGN_PREFIX_HOME = {"NG": 6, "OQ": 9, "LGM": 7, "DC": 7, "LDM": 7}

# the step that writes each section — `--up-to N` reads nothing a later step still owes. §6, §8 and
# §9 grow across the steps and close at Step 6; §4's criteria bullets are back-filled at Step 4.
SECTION_STEP = {1: 1, 2: 2, 3: 2, 4: 3, 5: 4, 6: 6, 7: 5, 8: 6, 9: 6, 10: 6}
LAST_STEP = 6
# §6, §8, §9 and §10 grow across the steps — an item lands there at the `[C]` of the step that
# spotted it — so content in them never means a gate was skipped; the other sections are written
# at their own step's `[C]` and at no other moment
GATED_SECTIONS = {n for n, step in SECTION_STEP.items() if step < LAST_STEP}
STEP_TITLES = {
    0: "the file",
    1: "frontmatter, title, brief, structure",
    2: "personas and journeys",
    3: "functional blocks",
    4: "acceptance criteria",
    5: "metrics",
    6: "closing sections",
}
# the step after a gate, as SKILL.md names it, with the reference it reads and whether `[A]` is
# offered — printed after every `--up-to N` run so the gate discipline re-enters the context at
# the one moment it matters, whatever a compaction kept
NEXT_STEP = {
    0: ("Step 1 — Frame & scope", "references/REF-brief-contract.md", False),
    1: ("Step 2 — User journeys", "references/REF-user-journeys.md", True),
    2: ("Step 3 — Functional blocks", "references/REF-functional-blocks.md", True),
    3: ("Step 4 — Acceptance criteria", "references/REF-acceptance-criteria.md", True),
    4: ("Step 5 — Leading metrics", "references/REF-metrics.md", True),
    5: ("Step 6 — Complexity", "references/REF-complexity-sizing.md", False),
    6: ("the quality gate", None, False),
}

# --------------------------------------------------------------------------- patterns

ID_RE = re.compile(r"\b(BR|ST|PERM|ERR|CB|CL)-\d+[a-z]?\b")
FOREIGN_ID_RE = re.compile(r"\b(NG|OQ|LGM|DC|LDM)-\d+[a-z]?\b")
FUNC_RE = re.compile(r"\bFUNC-\d+[a-z]?\b")
# a criterion is *defined* by sitting in the first cell of a table row (or, for CB/CL, by being the
# leading bold id of a Constraints bullet) — never merely by being mentioned somewhere in §5
TABLE_ROW_ID_RE = re.compile(r"^\s*\|\s*\*{0,2}((?:BR|ST|PERM|ERR)-\d+[a-z]?)\*{0,2}\s*\|")
BULLET_ID_RE = re.compile(r"^\s*[-*+]\s+\*\*((?:BR|ST|PERM|ERR|CB|CL)-\d+[a-z]?)\*\*\s*(.*)$")
OQ_ROW_RE = re.compile(r"^\s*\|\s*\*{0,2}(OQ-\d+[a-z]?)\b")
NG_CELL_RE = re.compile(r"^\*{0,2}(NG-\d+[a-z]?)")
METRIC_ROW_RE = re.compile(r"\|\s*\*{0,2}((?:LGM|DC|LDM)-\d+[a-z]?)")
# the three labels are matched on their words, not on their typography: one or two asterisks, and
# the space French puts before a colon, are the same label
AC_BLOCK_RE = re.compile(r"^\s*\*{1,2}Acceptance criteria\s*:?\s*\*{1,2}\s*(.*)$", re.I)
# a FUNC's criteria list ends at the block's next labelled field (`**Nominal scenario:**`) or at a
# heading of the FUNC's own level or above — never at the first line that merely is not a bullet.
# `####` is deliberately excluded: a long FUNC groups its criteria under one.
AC_BLOCK_END_RE = re.compile(r"^\s*(?:\*{1,2}[^*\n]+:?\s*\*{1,2}\s*$|#{1,3}\s)")
# split a markdown table row on unescaped pipes only: a `States` cell legitimately holds `\|`,
# and a naive split truncates it silently — the file stays valid and the check goes blind
PIPE_SPLIT_RE = re.compile(r"(?<!\\)\|")
# markdown reads a heading indented by up to three spaces as a heading — so does this file
SECTION_RE = re.compile(r"^ {0,3}##\s+(\d+)\.\s+(.+?)\s*$")
SUBSECTION_RE = re.compile(r"^ {0,3}###\s+(.+?)\s*$")            # level 3 only: `####` does not match
SUBHEAD_RE = re.compile(r"^ {0,3}(#{3,4})\s+(.+?)\s*$")
FUNC_HEADING_RE = re.compile(r"^ {0,3}###\s+(FUNC-\d+[a-z]?)\b")
H2_RE = re.compile(r"^ {0,3}## ")
# the PRD's scratch block: unnumbered, last, deleted once the quality gate passes
PARKED_RE = re.compile(r"^ {0,3}##\s+Parked\s*$", re.I)
PARKED_FOR_RE = re.compile(r"^\s*Step\s+(\d)\s*$", re.I)
# a line a section holds before its step writes it: a bare label (`**Acceptance criteria:**`), a
# `*Capabilities revealed:* TBD`, a legend in italics — everything else with a word in it is content
BARE_LABEL_RE = re.compile(r"^\s*\*{1,2}[^*]+:\*{1,2}\s*(?:TBD)?\s*$", re.I)
LEGEND_RE = re.compile(r"^\s*\*[^*].*[^*]\*\s*$")
LEGEND_OPEN_RE = re.compile(r"^\s*\*[^*\s]")
LABELLED_RE = re.compile(r"^\s*\*{1,2}[^*]+:\*{1,2}\s*\S")     # `*Goal:* the user …`
# a fence opens on three backticks or three tildes, and only its own character closes it
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
LEADING_COMMENTS_RE = re.compile(r"\A(?:\s*<!--.*?-->)+", re.S)
CAPABILITIES_RE = re.compile(r"^\s*\*{1,2}Capabilit(?:y|ies) revealed\s*:\s*\*{1,2}(.*)$", re.I)
LOOSE_CAPABILITIES_RE = re.compile(r"^\s*\*{0,2}Capabilit(?:y|ies) revealed\s*:", re.I)
GOAL_RE = re.compile(r"^\s*\*{1,2}Goal\s*:\s*\*{1,2}")
BRANCH_STEP_RE = re.compile(r"^\s*\d+[a-z]\.\s")
FILENAME_NUM_RE = re.compile(r"^[Pp][Rr][Dd]\s*-?\s*(\d+)")
ID_FIELD_RE = re.compile(r"^PRD-?(\d+)$", re.I)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# the AI listing itself as author means the PM never took ownership; the convention also forbids
# an email in this field (SKILL.md Step 1: "The name alone")
AI_AUTHOR_RE = re.compile(r"anthropic|noreply|copilot|gemini|chatgpt|openai|"
                          r"claude\s+(?:code|opus|sonnet|haiku)", re.I)
# QG-2's script half — an unambiguous UI-component noun in a journey step or a FUNC is a design
# leak whatever the intent; the Challenge Pass judges the semantic half (positions, mechanics,
# container-driven carving). WARN: a word list can misfire, a reader arbitrates. The list lives in
# `references/ui-lexicon.txt`, one `lang: word|word` line per language, so it is calibrated
# without touching this script.
UI_LEXICON = Path(__file__).resolve().parent.parent / "references" / "ui-lexicon.txt"


def load_ui_lexicon(path: Path = UI_LEXICON) -> re.Pattern[str]:
    """The lexicon as one pattern. An empty or missing file disables the check rather than
    matching every line (`\\b()\\b` would) or crashing before the first PRD is read."""
    words: list[str] = []
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            _, _, alternatives = line.partition(":")
            words += [w.strip() for w in alternatives.split("|") if w.strip()]
    except OSError:
        words = []
    if not words:
        return re.compile(r"(?!x)x")
    return re.compile(r"\b(" + "|".join(dict.fromkeys(words)) + r")\b", re.I)


UI_COMPONENT_RE = load_ui_lexicon()
# a bracketed span that is not a markdown link — i.e. a leftover template placeholder
PLACEHOLDER_RE = re.compile(r"\[[^\]\n]{2,}\](?!\()")
# a speculative-derivation marker from Step 2 — none may survive into a validated PRD
ASSUMPTION_RE = re.compile(r"\[ASSUMPTION:")
# every prefix the skill mints: the messages tell authors to write `OQ-XXX`, so a leftover may
# carry any of them, not only the template's three
XXX_TOKEN_RE = re.compile(
    r"\b(?:brief|OPP|PRD|FUNC|BR|ST|PERM|ERR|CB|CL|LGM|DC|LDM|NG|OQ|D|T)-?XXX\b")
# every dash a human or an editor may type as a bullet separator. Stripping only three of them made
# `describes X differently` fire on the dash rather than on the text — a wrong diagnosis
DASHES = "—–-‐‑‒―−﹘﹣－"

# --------------------------------------------------------------------------- the document model


@dataclass
class Finding:
    level: str          # ERROR | WARN
    prd: str
    msg: str
    step: int = 0       # the step whose gate owns the finding; 0 = the file itself


@dataclass
class Section:
    number: int
    title: str
    start: int          # heading line, 0-based
    end: int            # first line past the section


@dataclass
class Journey:
    title: str
    start: int                  # heading line, 0-based
    has_goal: bool
    branch_line: int | None     # 1-based line of the first `2a.`-style step
    declared: bool              # a *Capabilities revealed:* line exists, filled or not
    revealed: set[str]


@dataclass
class Func:
    fid: str
    line: int                   # 1-based heading line
    body_start: int             # 0-based index of the first body line
    body: list[str]
    bullets: list[tuple[str, str]] = field(default_factory=list)   # (id, normalised text)
    inline: str | None = None   # what stayed on the `**Acceptance criteria:**` line itself
    block: list[int] = field(default_factory=list)                  # body offsets of that block


@dataclass
class Criterion:
    cid: str
    kind: str
    line: int                   # 1-based
    heading: str                # the level-3 heading this row sits under
    text: str | None            # exact expected description (BR, ERR, CB, CL)
    parts: list[str]            # substrings that must all appear (ST, PERM)
    applies: set[str]           # FUNC ids read from the `Applies to` column
    applies_declared: bool      # False when the cell exists but names nothing


@dataclass
class ParkedRow:
    line: int                   # 1-based
    item: str
    kind: str
    for_step: int | None        # None when the `For` cell is not `Step N`
    origin: str


@dataclass
class Record:
    """The project's decision record, read table by table. Rows are (1-based line, cells)."""
    path: Path
    tables: dict[str, list[tuple[int, list[str]]]]
    headers: dict[str, tuple[list[str], int]]       # table -> (header cells, 1-based line)
    missing: list[str]                              # tables whose heading or table is absent
    text: str = ""

    @property
    def name(self) -> str:
        return self.path.name


@dataclass
class Document:
    path: Path
    text: str
    lines: list[str]
    masked: list[bool]              # inside a fenced block, fences included
    unclosed_fence: int | None      # 1-based line of a fence never closed
    fm: dict[str, str]
    body_start: int                 # first line after the frontmatter
    sections: dict[int, Section]
    marks: list[int]                # every numbered `## N.` heading, in document order
    clean: list[str]                # the lines, fenced blocks blanked out, numbering preserved
    owner: list[int] = field(default_factory=list)      # the step that writes each line
    journeys: list[Journey] = field(default_factory=list)
    funcs: list[Func] = field(default_factory=list)
    criteria: list[Criterion] = field(default_factory=list)   # every row, duplicates included
    parked_span: tuple[int, int] | None = None      # 0-based [heading, end) of `## Parked`
    parked: list[ParkedRow] = field(default_factory=list)
    record: Record | None = None                    # the project record, when it resolves
    up_to: int | None = None                        # the `--up-to N` of this run, once known

    def criteria_in_scope(self) -> list[Criterion]:
        """The criteria the steps so far own — §10's constraints are Step 6's, so a Step 4 check
        does not read them before their step."""
        return [c for c in self.criteria
                if self.up_to is None or self.owner[c.line - 1] <= self.up_to]

    @property
    def name(self) -> str:
        return self.path.name

    def section(self, number: int) -> Section | None:
        return self.sections.get(number)

    def body(self, number: int) -> list[str]:
        sec = self.section(number)
        return [] if sec is None else self.clean[sec.start + 1:sec.end]

    def text_of(self, number: int) -> str:
        return "\n".join(self.body(number))

    def defined(self) -> dict[str, Criterion]:
        """First definition of each criterion id — the one the bullets are compared against."""
        out: dict[str, Criterion] = {}
        for c in self.criteria:
            out.setdefault(c.cid, c)
        return out

    def func_ids(self) -> set[str]:
        return {f.fid for f in self.funcs}

    def owned(self, up_to: int | None) -> list[int]:
        """Indices of the lines Steps 1..up_to have written — every line when up_to is None."""
        return [i for i in range(len(self.lines)) if up_to is None or self.owner[i] <= up_to]

    def number(self) -> str:
        """The PRD's number from its `id`, as written (`07`), or '' when the id is malformed."""
        m = ID_FIELD_RE.match(self.fm.get("id", "").strip())
        return m.group(1) if m else ""


# --------------------------------------------------------------------------- parsing


def unquote(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def parse_frontmatter(lines: list[str]) -> tuple[dict[str, str], int]:
    """(fields, index of the first body line). Empty dict when there is no frontmatter."""
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


def fence_mask(lines: list[str]) -> tuple[list[bool], int | None]:
    """(mask, 1-based line of an unclosed fence). True for lines inside a fenced block.

    An unclosed fence masks everything after it, so the document loses most of its sections at once
    and the run would report eight missing sections without naming the cause. The opening line is
    returned so the structure check can say it in one finding.
    """
    mask, fence, opened_at = [], None, None
    for i, line in enumerate(lines):
        m = FENCE_RE.match(line)
        if m and fence in (None, m.group(1)[0]):
            fence = None if fence else m.group(1)[0]
            opened_at = i + 1 if fence else None
            mask.append(True)
            continue
        mask.append(fence is not None)
    return mask, opened_at


def split_cells(line: str) -> list[str]:
    """Cells of a markdown table row, split on unescaped pipes and unescaped afterwards."""
    parts = PIPE_SPLIT_RE.split(line.strip())
    if parts and not parts[0].strip():
        parts = parts[1:]
    if parts and not parts[-1].strip():
        parts = parts[:-1]
    return [c.strip().replace("\\|", "|") for c in parts]


def norm(s: str) -> str:
    """Comparison form: collapsed whitespace, no surrounding dash or space, and one spelling for
    what editors respell on their own — a curly apostrophe, an escaped pipe, an ASCII arrow."""
    s = s.replace("\u2019", "'").replace("\u2018", "'").replace("\\|", "|").replace("->", "\u2192")
    return re.sub(r"\s+", " ", s).strip().strip(DASHES).strip()


def table_header(lines: list[str], start: int, end: int) -> tuple[list[str], int] | None:
    """The first markdown table header in a span, as (cells, 1-based line). None when there is none."""
    for i in range(start, end):
        line = lines[i]
        if not line.lstrip().startswith("|"):
            continue
        nxt = lines[i + 1] if i + 1 < end else ""
        if set(nxt.strip()) <= set("|- :") and "-" in nxt:      # the separator row
            return split_cells(line), i + 1
    return None


def subsections(doc: Document, number: int) -> list[tuple[str, int, int]]:
    """Level-3 headings of a section as (title, heading line, end line). `####` groups belong to
    their parent."""
    sec = doc.section(number)
    if sec is None:
        return []
    heads = [(m.group(1).strip(), i) for i in range(sec.start + 1, sec.end)
             if (m := SUBSECTION_RE.match(doc.clean[i]))]
    return [(title, start, heads[k + 1][1] if k + 1 < len(heads) else sec.end)
            for k, (title, start) in enumerate(heads)]


def parse_journeys(doc: Document) -> list[Journey]:
    out: list[Journey] = []
    for title, start, end in subsections(doc, 3):
        block = doc.clean[start:end]
        revealed: set[str] = set()
        declared = False
        for line in block:
            if LOOSE_CAPABILITIES_RE.match(line):
                declared = True
            m = CAPABILITIES_RE.match(line)
            if m:
                revealed |= set(FUNC_RE.findall(m.group(1)))
        branch = next((start + k + 1 for k, line in enumerate(block) if BRANCH_STEP_RE.match(line)),
                      None)
        out.append(Journey(title, start, any(GOAL_RE.match(ln) for ln in block), branch,
                           declared, revealed))
    return out


def read_criteria_block(body: list[str]) -> tuple[list[tuple[str, str]], str | None, list[int]]:
    """A FUNC's `- **ID** — text` bullets, the remainder of the label line, and the body offsets
    the block spans — Step 4 owns those lines, whatever Step 3 left in them.

    The remainder is non-empty only when the block still lists bare identifiers on the
    `**Acceptance criteria:**` line itself, which the readability convention replaced with bullets.
    """
    bullets: list[tuple[str, str]] = []
    inline: str | None = None
    span: list[int] = []
    inside = False
    for k, line in enumerate(body):
        head = AC_BLOCK_RE.match(line)
        if head:
            inside, inline = True, head.group(1).strip()
            span.append(k)
            continue
        if not inside:
            continue
        if AC_BLOCK_END_RE.match(line):
            inside = False
            continue
        span.append(k)
        m = BULLET_ID_RE.match(line)
        if m:
            bullets.append((m.group(1), norm(m.group(2))))
    return bullets, inline, span


def parse_funcs(doc: Document) -> list[Func]:
    """FUNC blocks of §4, in document order — duplicates kept, reported by the Step 3 check."""
    sec = doc.section(4)
    if sec is None:
        return []
    funcs: list[Func] = []
    current: Func | None = None
    for i in range(sec.start + 1, sec.end):
        m = FUNC_HEADING_RE.match(doc.clean[i])
        if m:
            current = Func(m.group(1), i + 1, i + 1, [])
            funcs.append(current)
        elif SUBSECTION_RE.match(doc.clean[i]):
            current = None          # a `###` that is no FUNC closes the block: what follows is nobody's
        elif current is not None:
            current.body.append(doc.clean[i])
    for func in funcs:
        func.bullets, func.inline, func.block = read_criteria_block(func.body)
    return funcs


def parse_criteria(doc: Document) -> list[Criterion]:
    """Column-aware read of every §5 row (plus §10 Constraints), duplicates included.

    A criterion is recognised by the **id prefix in its first cell**, never by which table it sits
    in: §5 groups business rules into `####` thematic sub-tables, so table membership says nothing.
    """
    out: list[Criterion] = []
    for number in (5, 10):
        sec = doc.section(number)
        if sec is None:
            continue
        heading = ""
        for i in range(sec.start + 1, sec.end):
            line = doc.clean[i]
            m = SUBHEAD_RE.match(line)
            if m:
                if len(m.group(1)) == 3:
                    heading = m.group(2).strip()
                continue
            row, bullet = TABLE_ROW_ID_RE.match(line), BULLET_ID_RE.match(line)
            if row:
                cells = split_cells(line)
                cid = row.group(1)
                kind = cid.split("-")[0]
                text, parts, applies, declared = None, [], set(), True
                if kind in ("BR", "ERR"):
                    text = cells[1] if len(cells) > 1 else ""
                elif kind == "ST":
                    parts = [cells[1]] if len(cells) > 1 else []
                    if len(cells) > 2:
                        parts += [s for s in re.split(r"[|/]", cells[2]) if s.strip()]
                elif kind == "PERM":
                    parts = [c for c in cells[1:3] if c]
                if kind == "BR":
                    applies = set(FUNC_RE.findall(cells[-1])) if len(cells) > 2 else set()
                    declared = bool(applies)
            elif bullet and number == 10:
                cid = bullet.group(1)
                kind = cid.split("-")[0]
                text, parts, applies, declared = norm(bullet.group(2)), [], set(), True
            else:
                continue
            out.append(Criterion(cid, kind, i + 1, heading, text, [x.strip() for x in parts],
                                 applies, declared))
    return out


def parse_parked(doc: Document) -> list[ParkedRow]:
    """The rows of `## Parked` — header and separator skipped, cells read by position."""
    if doc.parked_span is None:
        return []
    start, end = doc.parked_span
    out: list[ParkedRow] = []
    for i in range(start + 1, end):
        line = doc.clean[i]
        if not line.lstrip().startswith("|"):
            continue
        cells = split_cells(line)
        first = norm(cells[0]) if cells else ""
        if not first or set(first) <= set("-: "):
            continue
        nxt = doc.clean[i + 1].strip() if i + 1 < end else ""
        if set(nxt) <= set("|-: ") and "-" in nxt:     # the header, whatever word it carries
            continue
        cells += [""] * (4 - len(cells))
        m = PARKED_FOR_RE.match(plain(cells[2]))
        out.append(ParkedRow(i + 1, cells[0], cells[1], int(m.group(1)) if m else None, cells[3]))
    return out


def assign_owners(doc: Document) -> list[int]:
    """The step that writes each line. Everything before §1 — frontmatter, title, table of
    contents — is Step 1's; a section belongs to the step that writes it; §4's criteria block is
    Step 4's; a `## Parked` row belongs to the step it is parked for, the block itself to Step 1."""
    owner = [1] * len(doc.lines)
    for sec in doc.sections.values():
        step = SECTION_STEP.get(sec.number, LAST_STEP)
        for i in range(sec.start, sec.end):
            owner[i] = step
    for func in doc.funcs:
        for k in func.block:
            owner[func.body_start + k] = 4
    if doc.parked_span is not None:
        for i in range(*doc.parked_span):
            owner[i] = 1
        for row in doc.parked:
            if row.for_step in range(2, LAST_STEP + 1):
                owner[row.line - 1] = row.for_step
    return owner


def parse_document(path: Path) -> Document:
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    fm, body_start = parse_frontmatter(lines)
    masked, unclosed = fence_mask(lines)
    # the id-level checks read the document with its fenced blocks blanked out — an example quoted
    # in a PRD is an illustration, not a second definition. Blanking rather than dropping keeps
    # every reported line number honest.
    clean = ["" if masked[i] else line for i, line in enumerate(lines)]
    heads = [(int(m.group(1)), m.group(2), i) for i, line in enumerate(lines)
             if not masked[i] and (m := SECTION_RE.match(line))]
    # `## Parked` closes the section before it: an id parked there is not defined in §9, and the
    # §9/§10 table readers must not take its rows for theirs
    parked_at = next((i for i, line in enumerate(lines)
                      if not masked[i] and PARKED_RE.match(line)), None)
    bounds = sorted([i for _, _, i in heads] + ([parked_at] if parked_at is not None else []))
    sections: dict[int, Section] = {}
    for number, title, start in heads:
        end = next((b for b in bounds if b > start), len(lines))
        sections[number] = Section(number, title, start, end)   # a later duplicate overwrites;
    doc = Document(path, text, lines, masked, unclosed, fm, body_start, sections,
                   [number for number, _, _ in heads], clean)   # the structure check reports it
    if parked_at is not None:
        doc.parked_span = (parked_at, next((b for b in bounds if b > parked_at), len(lines)))
    doc.journeys = parse_journeys(doc)
    doc.funcs = parse_funcs(doc)
    doc.criteria = parse_criteria(doc)
    doc.parked = parse_parked(doc)
    doc.owner = assign_owners(doc)
    return doc


def h2_tables(lines: list[str], masked: list[bool]) -> dict[str, tuple[int, int]]:
    """Unnumbered `## Name` blocks of a file as name -> (heading line, end), 0-based."""
    heads = [(line.strip()[3:].strip(), i) for i, line in enumerate(lines)
             if not masked[i] and H2_RE.match(line) and not SECTION_RE.match(line)]
    return {name: (i, heads[k + 1][1] if k + 1 < len(heads) else len(lines))
            for k, (name, i) in enumerate(heads)}


def parse_record(path: Path) -> Record:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    masked, _ = fence_mask(lines)
    clean = ["" if masked[i] else line for i, line in enumerate(lines)]
    blocks = {name.lower(): span for name, span in h2_tables(lines, masked).items()}
    tables: dict[str, list[tuple[int, list[str]]]] = {}
    headers: dict[str, tuple[list[str], int]] = {}
    missing: list[str] = []
    for name in RECORD_TABLES:
        span = blocks.get(name.lower())
        if span is None:
            missing.append(name)
            continue
        start, end = span
        head = table_header(clean, start + 1, end)
        rows: list[tuple[int, list[str]]] = []
        if head is None:
            missing.append(name)
        else:
            headers[name] = head
            for i in range(head[1] + 1, end):          # past the separator row
                line = clean[i]
                if line.lstrip().startswith("|"):
                    cells = split_cells(line)
                    if cells and norm(cells[0]) and not set(norm(cells[0])) <= set("-: "):
                        rows.append((i + 1, cells))
        tables[name] = rows
    return Record(path, tables, headers, missing, "\n".join(lines))


def record_path(doc: Document) -> Path | None:
    """`{DOCS_ROOT}/record/<record>.md`, `record` defaulting to the brief's stem."""
    stem = doc.fm.get("record", "").strip() or doc.fm.get("brief", "").strip()
    if not stem or stem.lower() == NO_BRIEF:
        return None
    return doc.path.parent.parent / RECORD_DIR / f"{Path(stem).stem}.md"


# --------------------------------------------------------------------------- step 1


def say(f: list[Finding], doc: Document, level: str, step: int, msg: str) -> None:
    f.append(Finding(level, doc.name, msg, step))


def check_frontmatter(doc: Document, f: list[Finding]) -> None:
    fm = doc.fm
    for key in REQUIRED_FM:
        value = fm.get(key, "").strip()
        if not value or value.startswith("["):
            say(f, doc, "ERROR", 1, f"QG-9: frontmatter field `{key}` missing or empty")

    fid = fm.get("id", "").strip()
    if fid:
        m = ID_FIELD_RE.match(fid)
        if not m:
            say(f, doc, "ERROR", 1, f"QG-9: `id` must look like PRD01, found {fid!r}")
        else:
            fname = FILENAME_NUM_RE.match(doc.name)
            if fname and int(fname.group(1)) != int(m.group(1)):
                say(f, doc, "ERROR", 1,
                    f"QG-9: `id` {fid} does not match the number in the filename")
            elif not fname:
                say(f, doc, "WARN", 1,
                    "QG-9: filename carries no PRD number — expected prd<NN>-<short-name>.md")

    if fm.get("brief", "").strip().lower() == NO_BRIEF and not fm.get("record", "").strip():
        say(f, doc, "ERROR", 1, "QG-9: `brief` is `none`, so `record` must name the project's "
                                "decision record (its filename stem in record/) — nothing else "
                                "ties this PRD to its project")

    status = fm.get("status", "").strip()
    if status and status not in STATUS:
        say(f, doc, "ERROR", 1,
            f"QG-9: `status` must be one of {sorted(STATUS)}, found {status!r}")
    cx = fm.get("complexity", "").strip()
    if cx and cx not in COMPLEXITY:
        say(f, doc, "ERROR", 1,
            f"QG-9: `complexity` must be one of {sorted(COMPLEXITY)}, found {cx!r}")
    date = fm.get("date", "").strip()
    if date and not DATE_RE.match(date):
        say(f, doc, "ERROR", 1, f"QG-9: `date` must be YYYY-MM-DD, found {date!r}")
    author = fm.get("author", "").strip()
    if "@" in author:
        say(f, doc, "ERROR", 1, "QG-9: `author` carries an email — the field takes the name alone")
    if AI_AUTHOR_RE.search(author):
        say(f, doc, "ERROR", 1, "QG-9: `author` names the AI that drafted the PRD — put the "
                                "human owner's name here")


def check_title(doc: Document, f: list[Finding]) -> None:
    # a comment above the title is not content: the forgotten instantiation block has its own
    # finding in the structure check, and naming the title instead sends the author to the wrong place
    body = LEADING_COMMENTS_RE.sub("", "\n".join(doc.lines[doc.body_start:]))
    first = next((ln.strip() for ln in body.splitlines() if ln.strip()), "")
    if not first.startswith("# "):
        say(f, doc, "ERROR", 1, "QG-10: first content line after the frontmatter is not an H1")
        return
    h1, title = first[2:].strip(), doc.fm.get("title", "").strip()
    if title and h1 != title:
        say(f, doc, "ERROR", 1, f"QG-10: H1 {h1!r} differs from the `title` field {title!r}")


def resolve_brief(path: Path, ref: str) -> Path | None:
    """A `brief` value is either a path or an id such as `brief-004`. Look for a real file."""
    ref = ref.strip()
    if not ref:
        return None
    cand = (path.parent / ref) if not ref.startswith("/") else Path(ref)
    for p in (cand, cand.with_suffix(".md")):
        if p.is_file():
            return p
    # `brief-01` and `brief01-shopping` are the same reference: an id's punctuation varies
    # between a brief's frontmatter and its filename, the letters do not
    wanted = re.sub(r"[^a-z0-9]", "", Path(ref).stem.lower())
    for folder in (path.parent.parent / "brief", path.parent.parent / "briefs",
                   path.parent, path.parent.parent):
        if folder.is_dir():
            for p in sorted(folder.glob("*.md")):
                if p.resolve() == path.resolve() or FILENAME_NUM_RE.match(p.name):
                    continue              # a PRD is never a brief, least of all this one
                # `brief1` must not take `brief10-transfers`: the digits end where the name's do
                if wanted and re.search(re.escape(wanted) + r"(?!\d)",
                                        re.sub(r"[^a-z0-9]", "", p.stem.lower())):
                    return p
    return None


def check_brief(doc: Document, f: list[Finding]) -> None:
    ref = doc.fm.get("brief", "").strip()
    if not ref:
        return                                        # already reported by check_frontmatter
    if ref.lower() == NO_BRIEF:
        say(f, doc, "WARN", 1, "QG-11: no brief — §1 carries the frame confirmed with the PM at "
                               "Step 1 as this PRD's source; a Tensions row (`accepted`) in the "
                               "project record is expected")
        return
    brief = resolve_brief(doc.path, ref)
    if brief is None:
        say(f, doc, "ERROR", 1, f"QG-11: brief {ref!r} does not resolve to a file on disk")
        return
    bfm, _ = parse_frontmatter(brief.read_text(encoding="utf-8-sig").splitlines())
    status = bfm.get("status", "").strip()
    if status != "validated":
        say(f, doc, "WARN", 1, f"QG-11: brief {brief.name} is not validated "
                               f"({status or 'no `status` field'}) — a Tensions row (`accepted`) "
                               "in the project record is expected, written at Step 1's [C]")


def check_structure(doc: Document, f: list[Finding]) -> None:
    if doc.unclosed_fence is not None:
        say(f, doc, "ERROR", 1, f"structure: a code fence opened at line {doc.unclosed_fence} is "
                                "never closed — everything below it is read as code, which is why "
                                "the sections below are reported missing")
    if "INSTANTIATION NOTES" in doc.text:
        say(f, doc, "ERROR", 1, "the template's instantiation comment block was not deleted")

    for number, expected in enumerate(SECTIONS, start=1):
        sec = doc.section(number)
        if sec is None:
            say(f, doc, "ERROR", 1, f"structure: section {number}. {expected} is missing")
        elif sec.title.strip().lower() != expected.lower():
            say(f, doc, "WARN", 1, f"structure: section {number} is titled {sec.title!r}, expected "
                                   f"{expected!r} (headings are machine tokens — do not translate)")
    for number, expected in OPTIONAL_SECTIONS.items():
        sec = doc.section(number)
        if sec is not None and sec.title.strip().lower() != expected.lower():
            say(f, doc, "WARN", 1, f"structure: section {number} is titled {sec.title!r}, expected "
                                   f"{expected!r} (headings are machine tokens)")
    for number in sorted({n for n in doc.marks if doc.marks.count(n) > 1}):
        say(f, doc, "ERROR", 1, f"structure: section {number} appears {doc.marks.count(number)} times")

    # a stray `## ` is only worth naming on a document whose sections parse: where they do not, the
    # missing-section findings above already explain every odd heading. Everything above section 1
    # is front matter — the table of contents lives there, under whatever name the PRD's language
    # gives it — so sub-heading misuse only means something inside a section.
    if all(doc.section(n) is not None for n in range(1, len(SECTIONS) + 1)):
        first = min(sec.start for sec in doc.sections.values())
        for i in range(first, len(doc.lines)):
            line = doc.lines[i]
            if doc.masked[i] or not H2_RE.match(line) or SECTION_RE.match(line) \
                    or PARKED_RE.match(line):
                continue
            say(f, doc, "WARN", 1, f"structure: {line.strip()!r} (line {i + 1}) uses the document's "
                                   "own heading level for a sub-heading — thematic groups inside a "
                                   "section belong at `####`")
    ordered = [n for n in doc.marks if doc.marks.count(n) == 1]
    if ordered != sorted(ordered):
        say(f, doc, "ERROR", 1, f"structure: sections are out of order — found {doc.marks}")

    if doc.parked_span is not None:
        start, end = doc.parked_span
        after = sorted(sec.number for sec in doc.sections.values() if sec.start > start)
        if after:
            say(f, doc, "WARN", 1, f"structure: section {after[0]} sits after `## Parked` (line "
                                   f"{start + 1}) — Parked is the last block of the file, so "
                                   "that it is deleted whole when the quality gate passes")
        check_table_shape(doc, "Parked", start, end, 1, f)
        for row in doc.parked:
            if row.for_step not in range(2, LAST_STEP + 1):
                say(f, doc, "ERROR", 1, f"structure: the parked item {row.item[:40]!r} (line "
                                        f"{row.line}) targets no step — `For` is `Step 2`..`Step "
                                        f"{LAST_STEP}`: every parked item is consumed by a step of "
                                        "this PRD, nothing waits for later")

    rec = record_path(doc)
    if rec is not None and not rec.is_file():
        say(f, doc, "WARN", 1, f"the project record {RECORD_DIR}/{rec.name} does not exist — "
                               "Step 1's [C] creates it from the skill's template; a PRD written "
                               "before 1.8.0 has none, create it once by hand")


# --------------------------------------------------------------------------- step 2


def check_journey_shape(doc: Document, f: list[Finding]) -> None:
    """QG-1, script half — the journey shape the methodology makes mandatory."""
    for j in doc.journeys:
        if not j.has_goal:
            say(f, doc, "WARN", 2, f"QG-1: journey {j.title!r} states no `*Goal:*` (line "
                                   f"{j.start + 1}) — left implicit in a title, a goal cannot be "
                                   "tested and two readers hold two versions of it")
        if j.branch_line is not None:
            say(f, doc, "WARN", 2, f"QG-1: journey {j.title!r} uses branch notation at line "
                                   f"{j.branch_line} — a variation is a flat step carrying "
                                   "the variation prefix, never `2a.`/`2b.`")


def check_personas(doc: Document, f: list[Finding]) -> None:
    if doc.section(2) is None:
        return
    # emphasis is content — a persona written in italics is not an empty section. Non-content is
    # only the quote lines and the bracketed placeholder, which in the template spans several lines
    text = re.sub(r"\[[^\]]*\]", "", doc.text_of(2))
    prose = [ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith(">")]
    if not prose:
        say(f, doc, "WARN", 2, "QG-12: section 2 Personas is empty — a PRD without an actor cannot "
                               "produce acceptance criteria, and Step 6 counts personas to size it")


def ui_components(doc: Document, number: int) -> list[tuple[int, str]]:
    """(1-based line, matched word) for every clean line of a section naming a UI component."""
    sec = doc.section(number)
    if sec is None:
        return []
    out = []
    for i in range(sec.start + 1, sec.end):
        m = UI_COMPONENT_RE.search(doc.clean[i])
        if m:
            out.append((i + 1, m.group(0)))
    return out


def check_journey_ui(doc: Document, f: list[Finding]) -> None:
    """QG-2, script half — see UI_COMPONENT_RE."""
    for line, word in ui_components(doc, 3):
        say(f, doc, "WARN", 2, f"QG-2: a journey step names a UI component ({word!r}, line {line}) "
                               "— a step is written at product altitude; the component stays with "
                               "the mockup")


# --------------------------------------------------------------------------- step 3


def check_func_ui(doc: Document, f: list[Finding]) -> None:
    """QG-2, script half, on §4 — the finding names the FUNC when one encloses the line."""
    for line, word in ui_components(doc, 4):
        fid = None
        for fn in doc.funcs:
            if fn.line <= line:
                fid = fn.fid
            else:
                break
        where = fid or f"section 4 (line {line})"
        say(f, doc, "WARN", doc.owner[line - 1], f"QG-2: {where} names a UI component ({word!r}, line {line}) — a "
                               "capability is written at product altitude; the component stays "
                               "with the mockup")


def check_scenarios(doc: Document, f: list[Finding]) -> None:
    """QG-4 — each FUNC has a WHEN/THEN scenario."""
    if doc.section(4) is None:
        return
    if not doc.funcs:
        say(f, doc, "ERROR", 3, "QG-4: section 4 defines no FUNC (`### FUNC-001 — …`)")
        return
    for func in doc.funcs:
        # read with the fenced blocks: a scenario written as a gherkin block is still a scenario
        text = "\n".join(doc.lines[func.body_start:func.body_start + len(func.body)])
        if not (re.search(r"\bWHEN\b", text) and re.search(r"\bTHEN\b", text)):
            say(f, doc, "ERROR", 3, f"QG-4: {func.fid} has no WHEN/THEN nominal scenario")


def check_func_journeys(doc: Document, f: list[Finding]) -> None:
    """QG-6 — FUNC ↔ journey, three directions. Silent until both sections carry something."""
    if not doc.funcs or doc.section(3) is None:
        return
    defined, revealed = doc.func_ids(), set()
    for j in doc.journeys:
        revealed |= j.revealed
        if not j.revealed:
            detail = ("its *Capabilities revealed:* line is still a placeholder" if j.declared
                      else "it carries no *Capabilities revealed:* line")
            say(f, doc, "ERROR", 3, f"QG-6: journey {j.title!r} reveals no FUNC — {detail} "
                                    f"(line {j.start + 1})")
    for fid in sorted(defined - revealed):
        say(f, doc, "ERROR", 3, f"QG-6: {fid} appears in no journey's *Capabilities revealed:* list")
    for fid in sorted(revealed - defined):
        say(f, doc, "ERROR", 3, f"QG-6: {fid} is revealed by a journey but not defined in section 4")


def check_func_ids(doc: Document, f: list[Finding]) -> None:
    seen: dict[str, int] = {}
    for func in doc.funcs:
        if func.fid in seen:
            say(f, doc, "ERROR", 3, f"QG-12: {func.fid} is defined twice (lines {seen[func.fid]} "
                                    f"and {func.line}) — a retired id is never re-used for another "
                                    "capability")
        else:
            seen[func.fid] = func.line


# --------------------------------------------------------------------------- step 4


def check_criteria(doc: Document, f: list[Finding]) -> None:
    """QG-12 — referential integrity between §4 and §5, and fidelity of the criteria bullets.

    The two sections describe the same relation from both ends: a FUNC lists the criteria it leans
    on, and a business rule lists the FUNCs it applies to. Every row is checked, a duplicate
    included — one defect must not hide the others on its line.
    """
    if doc.section(5) is None:
        return
    defs: dict[str, Criterion] = {}
    for c in doc.criteria_in_scope():
        defs.setdefault(c.cid, c)

    seen: dict[str, int] = {}
    for c in doc.criteria_in_scope():
        if c.cid in seen:
            say(f, doc, "ERROR", 4, f"QG-12: {c.cid} is defined twice (lines {seen[c.cid]} and "
                                    f"{c.line}) — an id identifies one criterion and is never reused")
        else:
            seen[c.cid] = c.line

    mentioned = {m.group(0) for m in ID_RE.finditer(doc.text_of(4))}
    for missing in sorted(mentioned - set(defs)):
        home = 10 if missing.startswith(("CB", "CL")) else 5
        say(f, doc, "ERROR", 4, f"QG-12: {missing} is referenced in section 4 but not defined in "
                                f"section {home}")
    for orphan in sorted(set(defs) - mentioned):
        say(f, doc, "WARN", 4, f"QG-12: {orphan} is defined but referenced by no FUNC in section 4")

    # §4 → §5: what each FUNC declares, and whether it matches the definition word for word
    declared: dict[str, set[str]] = {}
    for func in doc.funcs:
        declared[func.fid] = {cid for cid, _ in func.bullets}
        bare = bool(func.inline and ID_RE.search(func.inline))
        if not func.bullets and not bare:
            say(f, doc, "WARN", 4, f"QG-12: {func.fid} lists no acceptance criteria — a capability "
                                   "with no criterion is unspecified, not simple")
        if bare:
            say(f, doc, "WARN", 4, f"QG-12: {func.fid} still lists bare identifiers on its "
                                   "`**Acceptance criteria:**` line — expand them into "
                                   "`- **ID** — description` bullets")
        for cid, text in func.bullets:
            d = defs.get(cid)
            if d is None:
                continue
            if d.text is not None:
                if norm(text) != norm(d.text):
                    say(f, doc, "ERROR", 4, f"QG-12: {func.fid} describes {cid} differently from its "
                                            f"section 5 definition (line {d.line}) — section 5 is "
                                            "the source of truth, realign the bullet")
            else:
                absent = [x for x in d.parts if x and norm(x).lower() not in norm(text).lower()]
                if absent:
                    say(f, doc, "ERROR", 4, f"QG-12: {func.fid}'s bullet for {cid} omits "
                                            f"{absent[0]!r}, which its section 5 definition carries "
                                            f"(line {d.line})")
    for fid, cids in sorted(declared.items()):
        for cid in sorted(cids):
            d = defs.get(cid)
            if d is not None and d.kind == "BR" and d.applies and fid not in d.applies:
                say(f, doc, "WARN", 4, f"QG-12: {fid} lists {cid}, but {cid}'s `Applies to` does "
                                       f"not name {fid} (line {d.line}) — the two directions disagree")

    # §5 → §4: every row, read on its own
    funcs = doc.func_ids()
    for c in doc.criteria_in_scope():
        if c.kind == "BR" and not c.applies_declared:
            say(f, doc, "ERROR", 4, f"QG-12: {c.cid} has an empty `Applies to` cell (line {c.line}) "
                                    "— a rule bound to no capability reaches no spec, and the "
                                    "§4 ↔ §5 mirror cannot be checked at all")
        for fid in sorted(c.applies):
            if fid not in funcs:
                say(f, doc, "ERROR", 4, f"QG-12: {c.cid} applies to {fid}, which section 4 does "
                                        "not define")
            elif declared.get(fid) and c.cid not in declared[fid]:
                say(f, doc, "WARN", 4, f"QG-12: {c.cid} applies to {fid}, but {fid} does not list "
                                       "it — the two directions disagree")
        expected, actual = KIND_HEADING.get(c.kind), c.heading.strip().lower()
        if expected and actual and actual != expected and actual in KIND_HEADING.values():
            say(f, doc, "WARN", 4, f"QG-12: {c.cid} is defined under {c.heading!r} (line {c.line}) "
                                   "— an id belongs under the heading for its type")
        if c.kind == "BR" and c.text is not None:
            if not c.text.lstrip().startswith("**"):
                say(f, doc, "WARN", 4, f"QG-12: {c.cid} opens with no recap (line {c.line}) — start "
                                       "the rule with a short bold label naming the case handled")
            others = {x for x in re.findall(r"\bBR-\d+[a-z]?\b", c.text) if x != c.cid}
            if others:
                say(f, doc, "WARN", 4, f"QG-12: {c.cid} references {sorted(others)[0]} in its own "
                                       f"body (line {c.line}) — a rule must stand alone; cite "
                                       "ST-XXX if a state is involved")


def check_table_shape(doc: Document, title: str, start: int, end: int, step: int,
                      f: list[Finding]) -> None:
    """Every named table keeps the number and order of the columns it is read by.

    What corrupts a positional read is the shape, not the wording. A French PRD writing
    `| ID | Métrique | T0 | Cible |` parses exactly as well as the English one — the skill lets its
    prose be translated, and failing it here would fail every PRD already written. So: arity and
    order are errors, wording is a warning.
    """
    expected = next((v for k, v in TABLE_HEADERS.items() if k.lower() == title.lower()), None)
    if expected is None:
        return
    accepted = [[c.lower() for c in a] for a in expected]
    # every table of the span, not only the first: §5 groups its rules under `####` sub-tables,
    # and a permuted header there would feed three wrong diagnoses instead of this one
    i = start
    while i < end:
        found = table_header(doc.clean, i, end)
        if found is None:
            return                    # no table (left): the empty marker or the subsection rule speaks
        cells, line_no = found
        i = line_no + 1
        got = [norm(c).lower() for c in cells]
        if got in accepted:
            continue
        same_arity = [a for a in accepted if len(a) == len(got)]
        if not same_arity:
            say(f, doc, "ERROR", step, f"QG-12: the `{title}` table has {len(got)} columns (line "
                                       f"{line_no}), expected {len(accepted[0])} — every cell here is "
                                       "read by position, so a column added or removed shifts all of them")
        elif any(sorted(got) == sorted(a) for a in same_arity):
            say(f, doc, "ERROR", step, f"QG-12: the `{title}` table has its columns in the order {cells} "
                                       f"(line {line_no}), expected {expected[0]} — the cells are read "
                                       "by position, so a permuted header feeds every check the wrong one")
        else:
            say(f, doc, "WARN", step, f"QG-12: the `{title}` table has the columns {cells} (line "
                                      f"{line_no}), expected {expected[0]} — column headers are machine "
                                      "tokens and stay in English, like the section titles; only the "
                                      "cells are translated")


def check_ac_tables(doc: Document, f: list[Finding]) -> None:
    if doc.section(5) is None:
        return
    subs = subsections(doc, 5)
    for expected in AC_SUBSECTIONS:
        if not any(title.lower() == expected.lower() for title, _, _ in subs):
            # WARN, not ERROR: ids are recognised by their prefix, so nothing breaks — but a reader
            # looking for a type needs its heading, and an absent one is indistinguishable from a
            # forgotten one. §7 gets an ERROR for the opposite reason: there, an absent subsection
            # does break the count.
            say(f, doc, "WARN", 4, f"QG-12: section 5 has no `### {expected}` subsection — write it "
                                   'with "None identified." rather than leaving it out')
    for title, start, end in subs:
        check_table_shape(doc, title, start, end, 4, f)


# --------------------------------------------------------------------------- step 5


def check_metrics(doc: Document, f: list[Finding]) -> None:
    """QG-8 — the three subsections exist, are populated or explicitly empty, rows are complete."""
    if doc.section(7) is None:
        return
    subs = subsections(doc, 7)
    seen: dict[str, int] = {}
    for expected in METRIC_SUBSECTIONS:
        match = next((s for s in subs if s[0].lower() == expected.lower()), None)
        if match is None:
            say(f, doc, "ERROR", 5, f"QG-8: section 7 has no `### {expected}` subsection")
            continue
        _, start, end = match
        content = doc.clean[start + 1:end]
        # `\*{0,2}` as in TABLE_ROW_ID_RE: an id written `**DC-001**` is the same row. Without it a
        # bold id makes the subsection look empty, and QG-8 fails on a purely cosmetic choice.
        rows = [(start + 1 + k, line) for k, line in enumerate(content)
                if line.strip().startswith("|") and METRIC_ROW_RE.search(line)]
        if not rows and not EMPTY_MARKER_RE.search("\n".join(content)):
            say(f, doc, "ERROR", 5, f"QG-8: `{expected}` is empty and carries neither "
                                    '"None identified." nor "None defined."')
        for i, row in rows:
            cells = split_cells(row)
            rid = METRIC_ROW_RE.search(row).group(1)
            if rid in seen:
                say(f, doc, "ERROR", 5, f"QG-12: {rid} is defined twice (lines {seen[rid]} and "
                                        f"{i + 1}) — an id identifies one metric and is never reused")
            else:
                seen[rid] = i + 1
            if expected == "Damage Control":
                if not cells or not re.search(r"\d", cells[-1]):
                    say(f, doc, "WARN", 5, f"QG-8: {rid} has no numeric threshold in its last "
                                           "column — a guardrail with no bound protects nothing")
            elif expected == "Lagging Metrics":
                if len(cells) < 3 or not cells[-1]:
                    say(f, doc, "WARN", 5, f"QG-8: {rid} has no threshold — a success criterion "
                                           "nobody can read is not one")
            elif expected == "Leading Metrics":
                missing = [label for label, idx in (("collection method", 2), ("review cadence", 3))
                           if len(cells) <= idx or not cells[idx]]
                if missing:
                    say(f, doc, "WARN", 5, f"QG-8: {rid} has no {' and no '.join(missing)} — an "
                                           "indicator nobody can collect predicts nothing")
    for title, start, end in subs:
        check_table_shape(doc, title, start, end, 5, f)


# --------------------------------------------------------------------------- step 6


def check_complexity(doc: Document, f: list[Finding]) -> None:
    """Step 6's grid, applied. The PM may override it — hence a warning, never an error."""
    declared, funcs = doc.fm.get("complexity", "").strip(), doc.func_ids()
    if declared not in COMPLEXITY or not funcs:
        return
    expected = next(band for band, ceiling in COMPLEXITY_GRID if len(funcs) <= ceiling)
    if expected != declared:
        say(f, doc, "WARN", 6, f"QG-9: complexity is {declared} for {len(funcs)} FUNCs, the grid "
                               f"says {expected} from the FUNC count alone — legitimate if the "
                               "personas or the PM raised it, otherwise a miscount")


def table_rows(doc: Document, number: int) -> list[tuple[int, list[str]]]:
    """(0-based line, cells) of every data row in a section's table — header and separator skipped.

    The header is the row before a separator, whatever word it carries: a translated header is
    the shape check's finding, not a data row without an id."""
    sec = doc.section(number)
    if sec is None:
        return []
    out = []
    for i in range(sec.start + 1, sec.end):
        line = doc.clean[i]
        if not line.lstrip().startswith("|"):
            continue
        cells = split_cells(line)
        first = norm(cells[0]) if cells else ""
        if not first or set(first) <= set("-: "):
            continue
        nxt = doc.clean[i + 1].strip() if i + 1 < sec.end else ""
        if set(nxt) <= set("|-: ") and "-" in nxt:
            continue
        out.append((i, cells))
    return out


def check_closing_sections(doc: Document, f: list[Finding]) -> None:
    """§6, §8, §9 — read at last, once Step 6 has closed them."""
    seen: dict[str, int] = {}
    for i, cells in table_rows(doc, 6):
        first = norm(cells[0])
        if first.lower() == "item":
            continue
        m = NG_CELL_RE.match(first)
        if not m:
            say(f, doc, "WARN", 6, f"QG-12: out-of-scope entry {first[:40]!r} (line {i + 1}) opens "
                                   "with no NG-XXX id — an exclusion nothing can cite is not "
                                   "enforceable")
        elif m.group(1) in seen:
            say(f, doc, "ERROR", 6, f"QG-12: {m.group(1)} is defined twice (lines {seen[m.group(1)]} "
                                    f"and {i + 1}) — an id identifies one exclusion and is never reused")
        else:
            seen[m.group(1)] = i + 1

    terms: dict[str, int] = {}
    for i, cells in table_rows(doc, 8):
        term = norm(cells[0]).lower()
        if term == "term":
            continue
        if term in terms:
            say(f, doc, "WARN", 6, f"QG-12: the glossary defines {cells[0]!r} twice (lines "
                                   f"{terms[term]} and {i + 1}) — one term, one definition")
        else:
            terms[term] = i + 1

    seen = {}
    for i, cells in table_rows(doc, 9):
        m = OQ_ROW_RE.match(doc.clean[i])
        if m is None:
            if norm(cells[0]).lower() != "id":
                say(f, doc, "WARN", 6, f"QG-12: open-question row {norm(cells[0])[:40]!r} (line "
                                       f"{i + 1}) opens with no OQ-XXX id — a question nothing can "
                                       "cite blocks nothing")
            continue
        if m.group(1) in seen:
            say(f, doc, "ERROR", 6, f"QG-12: {m.group(1)} is defined twice (lines {seen[m.group(1)]} "
                                    f"and {i + 1}) — an id identifies one question and is never reused")
        else:
            seen[m.group(1)] = i + 1
    if seen and doc.fm.get("status", "").strip() == "accepted":
        say(f, doc, "ERROR", 6, f"QG-12: the PRD is `accepted` with {len(seen)} open question(s) "
                                "still in §9 — acceptance means every question answered, "
                                "integrated and its row removed, with a Decisions row in the record")

    for number, title in SECTION_TABLE_OWNER.items():
        sec = doc.section(number)
        if sec is not None:
            check_table_shape(doc, title, sec.start, sec.end, 6, f)


# --------------------------------------------------------------------------- every run


def check_references(doc: Document, up_to: int | None, f: list[Finding]) -> None:
    """Ids cited in what the steps so far own are defined in their home section.

    Only concluded when the home section is there and is what it claims: on a PRD whose sections
    are misnumbered, the structure check already says so once, and repeating it as one warning per
    id would bury the real signal.
    """
    owned = doc.owned(up_to)

    # FUNC-XXX outside the sections that define and mirror them — §3 is QG-6's, §5's `Applies to`
    # is checked with the criteria; what remains is §1, §2, §6–§10 and the front matter
    if doc.section(4) is not None and (up_to is None or up_to >= 3):
        skip = set()
        for number in (3, 4, 5):
            sec = doc.section(number)
            if sec is not None:
                skip.update(range(sec.start, sec.end))
        funcs, first_seen = doc.func_ids(), {}
        for i in owned:
            if i in skip:
                continue
            for m in FUNC_RE.finditer(doc.clean[i]):
                if m.group(0) not in funcs:
                    first_seen.setdefault(m.group(0), i)
        for fid, i in sorted(first_seen.items()):
            say(f, doc, "WARN", doc.owner[i], f"QG-12: {fid} is cited (line {i + 1}) but section 4 "
                                              "defines no such FUNC")

    for prefix, home in FOREIGN_PREFIX_HOME.items():
        sec = doc.section(home)
        if sec is None or sec.title.strip().lower() != SECTIONS[home - 1].lower():
            continue
        home_ids = {m.group(0) for m in FOREIGN_ID_RE.finditer(doc.text_of(home))}
        first_seen = {}
        for i in owned:
            for m in FOREIGN_ID_RE.finditer(doc.clean[i]):
                if m.group(1) == prefix and m.group(0) not in home_ids:
                    first_seen.setdefault(m.group(0), i)
        for fid, i in sorted(first_seen.items()):
            say(f, doc, "WARN", doc.owner[i], f"QG-12: {fid} is cited but defined nowhere in "
                                              f"section {home}")


def check_leftovers(doc: Document, up_to: int | None, f: list[Finding]) -> None:
    """Template residue in what the steps so far own. A bracketed token is always a slot: the
    methodology writes country variants unbracketed for exactly this reason."""
    owned = [i for i in doc.owned(up_to) if i >= doc.body_start and not doc.masked[i]]

    assumptions = [i for i in owned if ASSUMPTION_RE.search(doc.lines[i])]
    if assumptions:
        say(f, doc, "ERROR", doc.owner[assumptions[0]],
            f"{len(assumptions)} `[ASSUMPTION: ...]` marker(s) survived the step gate — confirm or "
            f"convert each to an OQ-XXX (first at line {assumptions[0] + 1})")

    placeholders: list[str] = []
    first: int | None = None
    for i in owned:
        if doc.lines[i].lstrip().startswith(("<!--", "|--", "> ")):
            continue
        found = [p for p in PLACEHOLDER_RE.findall(doc.lines[i])
                 if not re.fullmatch(r"\[[ x]\]", p) and not p.startswith("[ASSUMPTION:")]
        if found and first is None:
            first = i
        placeholders += found
    if placeholders:
        sample = ", ".join(dict.fromkeys(placeholders[:3]))
        say(f, doc, "WARN", doc.owner[first], f"{len(placeholders)} unreplaced placeholder(s) left "
                                              f"— e.g. {sample}")

    token = next((i for i in doc.owned(up_to) if not doc.masked[i]
                  and XXX_TOKEN_RE.search(doc.lines[i])), None)
    if token is not None:
        say(f, doc, "WARN", doc.owner[token], "template token `XXX` still present")


def is_content(line: str) -> bool:
    """A line a step has written, as opposed to what the skeleton holds before that step: a
    placeholder, a heading, a legend, a bare label, an empty marker, a table frame."""
    s = line.strip()
    if not s or s.startswith(("#", "<!--", "---", ">")):
        return False
    if set(s) <= set("|-: ") or BARE_LABEL_RE.match(s) or LEGEND_RE.match(s):
        return False
    if EMPTY_MARKER_RE.search(s) or s.strip("*").strip().upper() == "TBD":
        return False
    return bool(re.search(r"\w", s))


def check_ahead_of_gate(doc: Document, up_to: int | None, f: list[Finding]) -> None:
    """Under `--up-to N`, a section a later step owns holds nothing but the skeleton: content
    there was written before the PM chose `[C]`. §6, §8, §9 and §10 grow across the steps and
    are not read here; a table header is a frame, not content."""
    if up_to is None:
        return
    seen: set[tuple[int, int]] = set()
    for sec in doc.sections.values():
        if sec.number not in GATED_SECTIONS:
            continue
        inside = 0                          # lines left for a `[placeholder` to close
        skip_next = False                   # the closing line of a wrapped legend
        for i in range(sec.start + 1, sec.end):
            text = doc.lines[i]
            if skip_next:
                skip_next = False
                continue
            # a line carrying a placeholder is the skeleton's, whatever else it says — the
            # template's rows hold example ids, and a leftover slot is check_leftovers' finding;
            # an unclosed `[` is given five lines, not the rest of the section
            if inside:
                inside = 0 if "]" in text else inside - 1
                continue
            if PLACEHOLDER_RE.search(text):
                continue
            if "[" in text and "]" not in text[text.index("["):]:
                inside = 5
                continue
            # a legend in italics may wrap once: `*Ids are identifiers, …` closes on the next line;
            # an italic line that never closes is content (a persona, a note), not a legend
            if LEGEND_OPEN_RE.match(text) and not LABELLED_RE.match(text):
                if text.rstrip().endswith("*"):
                    continue
                nxt = doc.lines[i + 1].rstrip() if i + 1 < sec.end else ""
                if nxt.endswith("*") and not LEGEND_OPEN_RE.match(nxt):
                    skip_next = True
                    continue
            step = doc.owner[i]
            if step <= up_to or (sec.number, step) in seen or doc.masked[i]:
                continue
            nxt = doc.lines[i + 1] if i + 1 < len(doc.lines) else ""
            header = text.lstrip().startswith("|") and set(nxt.strip()) <= set("|-: ") \
                and "-" in nxt
            # a journey or FUNC heading with no placeholder left is written content
            heading = SUBSECTION_RE.match(text) and sec.number in (3, 4)
            if header or (not heading and not is_content(text)):
                continue
            seen.add((sec.number, step))
            what = "the acceptance-criteria bullets" if step == 4 and sec.number == 4 \
                else f"section {sec.number}"
            say(f, doc, "ERROR", step, f"{what} already hold content (line {i + 1}) but Step "
                                       f"{step}'s gate has not been passed — nothing reaches a "
                                       "section before the PM's [C]; only `## Parked` takes rows "
                                       "as they come")


def check_parked(doc: Document, up_to: int | None, f: list[Finding]) -> None:
    """A parked row is consumed at the `[C]` of the step it is parked for: once that gate has
    passed, a row still there is an item that was never given its home."""
    bound = up_to or LAST_STEP
    if doc.parked_span is not None and doc.fm.get("status", "").strip() in ("review", "accepted"):
        say(f, doc, "ERROR", LAST_STEP, f"`## Parked` is still in the file (line "
                                        f"{doc.parked_span[0] + 1}) with `status: "
                                        f"{doc.fm['status'].strip()}` — the block is deleted when "
                                        "the quality gate passes")
    for row in doc.parked:
        if row.for_step is not None and 2 <= row.for_step <= bound:
            say(f, doc, "ERROR", row.for_step,
                f"{row.item[:40]!r} is parked for Step {row.for_step} and was never consumed (line "
                f"{row.line}) — Step {row.for_step}'s [C] gives it a home (a row in its section, an "
                "NG in §6, an OQ in §9) and removes the row, or re-targets it to a later step")


def plain(s: str) -> str:
    """A cell for comparison: normalised, emphasis and terminal punctuation stripped, case folded
    — a full stop copied on one side and not the other is an editor's habit, not a divergence."""
    return norm(s).replace("*", "").replace("`", "").strip().rstrip(".;").strip().lower()


def record_prd_number(cell: str) -> str:
    m = re.search(r"(\d+)", cell)
    return m.group(1).lstrip("0") or "0" if m else ""


def check_vocabulary_mirror(doc: Document, up_to: int | None, f: list[Finding]) -> None:
    """§8 ↔ the record's Vocabulary: a term the PRD freezes has one row in the project's ledger,
    with the same definition — whichever PRD minted it. §8 is the PRD's own source; the record is
    what the next PRD reads before freezing a term."""
    if doc.record is None or (up_to is not None and up_to < 2) or doc.section(8) is None:
        return
    ledger: dict[str, tuple[str, str, int]] = {}             # term -> (definition, prd, line)
    for line, cells in doc.record.tables.get("Vocabulary", []):
        cells += [""] * (3 - len(cells))
        ledger.setdefault(plain(cells[0]), (cells[1], cells[2], line))
    mine = doc.number().lstrip("0") or "0"
    frozen: dict[str, str] = {}
    for i, cells in table_rows(doc, 8):
        term = plain(cells[0])
        if term == "term" or not term or PLACEHOLDER_RE.search(cells[0]):
            continue
        frozen[term] = cells[1] if len(cells) > 1 else ""
        hit = ledger.get(term)
        if hit is None:
            say(f, doc, "WARN", 2, f"QG-12: {cells[0]!r} is frozen in §8 (line {i + 1}) but has no "
                                   f"Vocabulary row in {doc.record.name} — the record is what the "
                                   "next PRD reads before freezing a term; add the row at [C]")
        elif plain(hit[0]) != plain(frozen[term]):
            say(f, doc, "ERROR", 2, f"QG-12: {cells[0]!r} is defined differently in §8 (line "
                                    f"{i + 1}) and in {doc.record.name} (line {hit[2]}, frozen by "
                                    f"PRD {hit[1] or '?'}) — a frozen term is reused, never "
                                    "re-frozen; a divergence is a question to the PM")
    for line, cells in doc.record.tables.get("Vocabulary", []):
        cells += [""] * (3 - len(cells))
        if record_prd_number(cells[2]) == mine and plain(cells[0]) not in frozen:
            say(f, doc, "WARN", 2, f"QG-12: {cells[0]!r} is recorded as frozen by this PRD "
                                   f"({doc.record.name} line {line}) but §8 does not define it")


def check_resolved_oqs(doc: Document, up_to: int | None, f: list[Finding]) -> None:
    """A Decisions row that resolves an OQ of this PRD means the answer was integrated and the
    §9 row removed — a row still there is a question both open and closed."""
    if doc.record is None or doc.section(9) is None:
        return
    open_oqs = {m.group(1) for i, _ in table_rows(doc, 9) if (m := OQ_ROW_RE.match(doc.clean[i]))}
    mine = doc.number().lstrip("0") or "0"
    for line, cells in doc.record.tables.get("Decisions", []):
        cells += [""] * (7 - len(cells))
        if record_prd_number(cells[1]) != mine:
            continue
        for oq in re.findall(r"\bOQ-\d+[a-z]?\b", cells[5]):
            if oq in open_oqs:
                say(f, doc, "ERROR", up_to or LAST_STEP,
                    f"QG-12: {cells[0]} in {doc.record.name} (line {line}) resolves {oq}, which "
                    "§9 still lists — a resolved question is integrated where it blocked and its "
                    "row removed")


def check_record(rec: Record, f: list[Finding]) -> None:
    """The project record keeps its shape and its ids, whichever PRD wrote last. Findings are
    reported under the file itself, step 0."""
    def tell(level: str, msg: str) -> None:
        f.append(Finding(level, rec.name, msg, 0))

    if "INSTANTIATION NOTES" in rec.text:
        tell("ERROR", "the record template's instantiation comment block was not deleted")
    h1 = next((ln for ln in rec.text.splitlines() if ln.startswith("# ")), "")
    if PLACEHOLDER_RE.search(h1):
        tell("WARN", f"the record's title still holds a placeholder: {h1.strip()!r}")
    for name in rec.missing:
        tell("WARN", f"the record has no `## {name}` table — four tables, by nature, even empty")
    for name, (cells, line) in rec.headers.items():
        expected = RECORD_TABLES[name]
        got = [plain(c) for c in cells]
        want = [c.lower() for c in expected]
        if got == want:
            continue
        if len(got) != len(want):
            tell("ERROR", f"the `{name}` table has {len(got)} columns (line {line}), expected "
                          f"{len(want)}: {expected} — every cell is read by position")
        elif sorted(got) == sorted(want):
            tell("ERROR", f"the `{name}` table has its columns in the order {cells} (line {line}), "
                          f"expected {expected}")
        else:
            tell("WARN", f"the `{name}` table has the columns {cells} (line {line}), expected "
                         f"{expected} — column headers are machine tokens")

    prd_dir = rec.path.parent.parent / "prd"
    on_disk = {record_prd_number(p.stem) for p in prd_dir.glob("[Pp][Rr][Dd]*.md")} \
        if prd_dir.is_dir() else None
    ids: dict[str, int] = {}
    for name, prefix in (("Decisions", "D"), ("Tensions", "T")):
        for line, cells in rec.tables.get(name, []):
            cells += [""] * (len(RECORD_TABLES[name]) - len(cells))
            m = RECORD_ID_RE.match(norm(cells[0]))
            if m is None:
                tell("WARN", f"`{name}` row at line {line} opens with {cells[0]!r}, not a "
                             f"`{prefix}-<NN>-XX` id")
            else:
                rid = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
                if rid in ids:
                    tell("ERROR", f"{rid} is defined twice (lines {ids[rid]} and {line}) — an id "
                                  "identifies one entry and is never reused")
                else:
                    ids[rid] = line
                if m.group(1) != prefix:
                    tell("WARN", f"{rid} sits in `{name}` (line {line}) but carries the other "
                                 "table's prefix")
                prd_no = record_prd_number(cells[1])
                # a row the brief wrote names `brief-NN`, not a PRD: no PRD number to agree with
                if prd_no and not cells[1].strip().lower().startswith("brief") \
                        and prd_no != (m.group(2).lstrip("0") or "0"):
                    tell("WARN", f"{rid} (line {line}) is numbered for PRD {m.group(2)} but its "
                                 f"PRD column says {cells[1]!r}")
            if name == "Tensions" and cells[3].strip() and plain(cells[3]) not in TENSION_STATUS:
                tell("WARN", f"{cells[0]} (line {line}) has status {cells[3]!r} — one of "
                             f"{sorted(TENSION_STATUS)}")
    terms: dict[str, int] = {}
    for line, cells in rec.tables.get("Vocabulary", []):
        cells += [""] * (3 - len(cells))
        term = plain(cells[0])
        if term in terms:
            tell("WARN", f"the term {cells[0]!r} is defined twice (lines {terms[term]} and {line}) "
                         "— one term, one definition, reused by every PRD of the project")
        else:
            terms[term] = line
    for line, cells in rec.tables.get("Sources", []):
        cells += [""] * (4 - len(cells))
        if cells[3].strip() and plain(cells[3]) not in SOURCE_GATE:
            tell("WARN", f"Sources row at line {line} has gate {cells[3]!r} — `kept` or `cut`")
    if on_disk is not None:
        named: dict[str, int] = {}
        for name in RECORD_TABLES:
            col = RECORD_TABLES[name].index("PRD")
            for line, cells in rec.tables.get(name, []):
                cell = cells[col] if len(cells) > col else ""
                if cell.strip() and not cell.strip().lower().startswith("brief"):
                    named.setdefault(record_prd_number(cell), line)
        reserved = str(max((int(n) for n in on_disk if n.isdigit()), default=0) + 1)
        for prd_no, line in sorted(named.items()):
            # the next number is reserved by the PRD being framed — its file exists only once
            # Step 1's gate has passed, and the record is written at that same gate
            if prd_no and prd_no not in on_disk and prd_no != reserved:
                tell("WARN", f"a row names PRD {prd_no} (first at line {line}) but prd/ holds no "
                             "such PRD")


# --------------------------------------------------------------------------- driver

STEP_CHECKS = {
    1: [check_frontmatter, check_title, check_brief, check_structure],
    2: [check_journey_shape, check_personas, check_journey_ui],
    3: [check_scenarios, check_func_journeys, check_func_ids, check_func_ui],
    4: [check_criteria, check_ac_tables],
    5: [check_metrics],
    6: [check_complexity, check_closing_sections],
}
EVERY_RUN = [check_references, check_leftovers, check_ahead_of_gate, check_parked,
             check_vocabulary_mirror, check_resolved_oqs]


def check_prd(path: Path, findings: list[Finding], up_to: int | None = None,
              records_seen: set[Path] | None = None) -> Document | None:
    """Validate one PRD; its project record, when it resolves, is checked once per run —
    `records_seen` is the set the caller keeps across PRDs."""
    # resolved first: a bare filename passed from inside `prd/` has `parent.parent == .`, and the
    # brief would be looked for in `./brief/` instead of `../brief/`
    doc = parse_document(path.resolve())
    doc.up_to = up_to
    if not doc.fm:
        findings.append(Finding("ERROR", path.name, "QG-9: no YAML frontmatter delimited by `---`", 1))
        return None
    rec = record_path(doc)
    if rec is not None and rec.is_file():
        doc.record = parse_record(rec)
        if records_seen is None or rec not in records_seen:
            check_record(doc.record, findings)
            if records_seen is not None:
                records_seen.add(rec)
    for step in range(1, (up_to or LAST_STEP) + 1):
        for check in STEP_CHECKS[step]:
            check(doc, findings)
    for check in EVERY_RUN:
        check(doc, up_to, findings)
    return doc


def is_record(path: Path) -> bool:
    """A file under `record/` is the project's decision record, never a PRD."""
    return path.resolve().parent.name == RECORD_DIR


def discover(paths: list[str]) -> list[Path]:
    out: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            # `canonical-memory.md` is the pre-1.8 project memory: never a PRD, still found in
            # docs trees written before the record existed
            skip = {"canonical-memory.md", "readme.md", "index.md"}
            out += [q for q in sorted(p.glob("*.md")) if q.name.lower() not in skip]
        else:
            out.append(p)
    return out


def next_step_card(up_to: int, parked_due: int) -> str:
    """What the agent does next, said by the script at the gate it just checked."""
    name, ref, elicitation = NEXT_STEP[up_to]
    lines = [f"Next: {name}."]
    if ref and up_to == 0:
        lines.append(f"  Read {ref} first; the PRD and its first record rows are written at this "
                     "step's [C].")
        lines.append("    [C] Validate → Step 2 — User journeys")
    elif ref:
        lines.append(f"  Read {ref} first.")
        lines.append(f"  Its gate block, the last thing presented, two fixed lines"
                     f"{' (the first offered at this step)' if elicitation else ' (no [A] here)'}:")
        if elicitation:
            lines.append("    [A] Advanced Elicitation")
        following = NEXT_STEP.get(up_to + 1, ("the quality gate",))[0]
        lines.append(f"    [C] Validate → {following}")
        lines.append("  Nothing reaches a numbered section before the PM answers that block; a `## Parked` "
                     "row is written as soon as an item is parked.")
    else:
        lines.append("  Three movements — this script in full, the Challenge Pass on the whole "
                     "document, the two crossings — then `## Parked` deleted and `status: review`.")
    if parked_due:
        lines.append(f"  {parked_due} row(s) parked for {name.split(' — ')[0]} — this step consumes them.")
    return "\n".join(lines)


def report(findings: list[Finding], count: int, up_to: int | None, parked_due: int = 0,
           records_only: bool = False) -> None:
    errors = [x for x in findings if x.level == "ERROR"]
    warns = [x for x in findings if x.level == "WARN"]
    scope = f" up to Step {up_to}" if up_to else ""
    print(f"Validated {count} file(s){scope}: {len(errors)} error(s), {len(warns)} warning(s)\n")
    if not findings:
        print("  ✓ all structural checks passed\n")
    for step in sorted({x.step for x in findings}):
        group = [x for x in findings if x.step == step]
        print(f"  Step {step} — {STEP_TITLES[step]}" if step else f"  {STEP_TITLES[0]}")
        for x in [g for g in group if g.level == "ERROR"] + [g for g in group if g.level == "WARN"]:
            mark = "✗ ERROR" if x.level == "ERROR" else "⚠ WARN "
            print(f"    {mark} [{x.prd}] {x.msg}")
        print()
    if up_to or records_only:
        print(("Once the errors above are fixed — " if errors else "")
              + next_step_card(up_to or 0, parked_due) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate PRDs generated by the prd skill, and their project record.",
        epilog="exit codes: 0 = clean, 1 = at least one ERROR, 2 = nothing to validate. "
               "Needs Python 3.8 or later; stdlib only.")
    ap.add_argument("prds", nargs="+", help="PRD .md files, or a directory containing them")
    ap.add_argument("--up-to", type=int, choices=range(1, LAST_STEP + 1), metavar="N",
                    help="check only what Steps 1..N have written — run at each step's [C]")
    args = ap.parse_args()

    # the report prints ✓ ✗ ⚠ —: on a console that cannot encode them, a clean PRD must not crash
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    prds = discover(args.prds)
    if not prds:
        print("No PRD file found — check the path (exit 2).", file=sys.stderr)
        return 2

    findings: list[Finding] = []
    records_seen: set[Path] = set()
    parked_due = 0
    records_only = all(is_record(p) for p in prds if p.exists())
    for p in prds:
        if not p.exists():
            findings.append(Finding("ERROR", p.name, "file not found"))
            continue
        try:
            if is_record(p):
                if p.resolve() not in records_seen:
                    check_record(parse_record(p.resolve()), findings)
                    records_seen.add(p.resolve())
            else:
                doc = check_prd(p, findings, args.up_to, records_seen)
                if doc is not None and args.up_to:
                    parked_due += sum(1 for r in doc.parked if r.for_step == args.up_to + 1)
        except Exception as e:                        # never let one bad file hide the others
            findings.append(Finding("ERROR", p.name,
                                    f"validator crashed on this file: {type(e).__name__}: {e}"))

    report(findings, len(prds), args.up_to, parked_due, records_only)
    return 1 if any(x.level == "ERROR" for x in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
