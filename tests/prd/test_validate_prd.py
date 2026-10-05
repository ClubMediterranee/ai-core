#!/usr/bin/env python3
"""Regression tests for `validate_prd.py`.

The validator is the only deterministic gate in this skill: everything else is judged by the same
model that wrote the PRD. A silent regression here does not surface as a failure — it surfaces as a
PRD that passes while no longer being valid. Hence these tests.

Each case pins a decision the validator makes on purpose, so that changing it is a choice rather
than an accident:

  * a well-formed PRD is clean — no error, no warning, nothing to explain away;
  * a criterion is defined by a **table row**, never by the block form (`ERR-001 : …`);
  * cosmetic freedom does not fail a gate — a bold id is still a row, an escaped pipe is still one
    cell, and a short all-caps code such as `[FR]` is content, not an unfilled slot;
  * template leftovers still fail — `[XXX]`, a bracketed id, a surviving `[ASSUMPTION: …]`;
  * an unvalidated brief warns and does not block (references/REF-brief-contract.md);
  * every id family is defined once — FUNC, metric, exclusion and question ids, not only §5's —
    and a FUNC cited outside its own sections must exist;
  * a missing damage-control threshold warns like its neighbours, it no longer fails the gate;
  * `--up-to N` reads only what Steps 1..N own — a skeleton still holding its later placeholders
    passes the earlier gates, and each owed item is reported at the step that owes it;
  * one defect does not hide another: a duplicated row is still mirror-checked, and a document
    carrying one defect of every ERROR class reports all of them at once;
  * the worked examples of `REF-acceptance-criteria.md` are executed rather than trusted — the
    reference cannot drift away from the validator without a red test;
  * the gate is enforced by the script: under `--up-to N` a section a later step owns holds
    nothing but the skeleton, while §6/§8/§9 grow freely;
  * `## Parked` is scratch with a deadline — a row is owed by the step it is parked for, an
    unparseable `For` is an error, a finished PRD carries no row;
  * the project record (`record/<brief-stem>.md`) is mirrored: §8 ↔ Vocabulary, a resolved OQ is
    gone from §9, the record keeps its tables, ids and enumerations — and its template parses;
  * the brief is not a wall: `brief: none` warns and needs a `record`.

Dependency-free: stdlib only, fixtures written to a temporary directory.

The suite lives outside the skill directory on purpose: the plugin packages `skills/prd/` whole,
and these tests are the maintainer's, never a PM's.

Usage, from the repository root:
    python3 -m unittest tests.prd.test_validate_prd -v
    python3 tests/prd/test_validate_prd.py
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2] / "skills" / "prd"
sys.path.insert(0, str(SKILL / "scripts"))
import validate_prd as V  # noqa: E402


FRONTMATTER = """---
id: PRD01
title: "Demo"
version: "1.0"
status: in-progress
complexity: S
date: 2026-08-26
author: "Celine Net"
brief: brief-001
---

# Demo
"""

BLOCKS = {
    "s1": """
## 1. Executive Summary

**Source:** brief-001 — the checkout opportunity.
""",
    "s2": """
## 2. Personas

Every visitor going through checkout.
""",
    "s3": """
## 3. User Journeys

### Journey 1 — Pay for an order

*Goal:* the user has paid and holds a confirmation

1. The user submits their payment
2. The user sees a confirmation

*Capabilities revealed:* FUNC-001
""",
    "s4": """
## 4. Functional Specifications

### FUNC-001 — Users can pay their order

**Capability:** the user pays for the order they assembled.

**Acceptance criteria:**

- **BR-001** — **Minimum amount:** cart total is 0 € → payment is skipped
- **ERR-001** — Payment is declined by the bank

**Nominal scenario:**
- **WHEN** the user submits their payment
- **THEN** the user sees a confirmation
""",
    "s5": """
## 5. Acceptance Criteria

### Business Rules

| ID | Rule | Applies to |
|----|------|-----------|
| BR-001 | **Minimum amount:** cart total is 0 € → payment is skipped | FUNC-001 |

### States & Transitions

None identified.

### Permissions

None identified.

### Error Scenarios

| ID | Failure mode | Expected behavior |
|----|--------------|-------------------|
| ERR-001 | Payment is declined by the bank | the cart is preserved |
""",
    "s6": """
## 6. Out of Scope

None identified.
""",
    "s7": """
## 7. Metrics

### Lagging Metrics

| ID | Metric | Baseline (T0) | Threshold |
|----|--------|---------------|-----------|
| LGM-001 | checkout conversion | 12% | +5 pts |

### Damage Control

None identified.

### Leading Metrics

None defined.
""",
    "s8": """
## 8. Glossary

None identified.
""",
    "s9": """
## 9. Open Questions

None identified.
""",
}

ORDER = ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9"]

# what a section holds before its step writes it — the template's shape, placeholders included
SKELETON = {
    "s2": """
## 2. Personas

[One short paragraph per persona confirmed at Step 2]
""",
    "s3": """
## 3. User Journeys

### Journey 1 — [Short name for this flow]

*Goal:* [the confirmed goal this journey serves]

1. [Step 1 — entry point / trigger]
2. [Step 2 — the goal reached]

*Capabilities revealed:* TBD
""",
    "s4": """
## 4. Functional Specifications

*Ids are identifiers, not ranks: a gap left by a merged FUNC is normal.*

### FUNC-001 — [Capability, in the PM's language]

**Capability:** [keep this line only when it adds a boundary the title cannot carry]

**Acceptance criteria:**

- [Step 3 leaves this list empty — Step 4 back-fills one bullet per applicable criterion]

**Nominal scenario:**
- **WHEN** [triggering condition]
- **THEN** [observable result]
""",
    "s5": """
## 5. Acceptance Criteria

### Business Rules

| ID | Rule | Applies to |
|----|------|-----------|
| BR-001 | **[Recap — the case handled]:** [condition] → [expected behavior] | FUNC-001, FUNC-002 |

### States & Transitions

| ID | Object | States | Allowed transitions | Blocked transitions |
|----|--------|--------|--------------------|--------------------|
| ST-001 | [Object] | [States] | [Allowed] | [Blocked] |

### Permissions

| ID | Actor | Action | Allowed condition | Blocked condition |
|----|-------|--------|-------------------|-------------------|
| PERM-001 | [Actor] | [Action] | [Condition allowing the action] | [Condition blocking the action] |

### Error Scenarios

| ID | Failure mode | Expected behavior |
|----|-------------|-------------------|
| ERR-001 | [Condition that triggers the failure] | [What the product must do] |
""",
    "s7": """
## 7. Metrics

*Three lenses on outcome.*

### Lagging Metrics

| ID | Metric | Baseline (T0) | Threshold |
|----|--------|---------------|-----------|
| LGM-001 | [Imported from brief] | [Current value, or TBD] | [Numeric target] |

### Damage Control

| ID | Metric | Current baseline | Max acceptable degradation |
|----|--------|-----------------|---------------------------|
| DC-001 | [Existing metric name] | [Current value] | [Numeric threshold] |

### Leading Metrics

| ID | Observable behavior | Collection method | Review cadence |
|----|---------------------|-----------------|----------------|
| LDM-001 | [User behavior that predicts adoption] | [How it is collected] | [weekly / monthly / per release] |
""",
}
# the step that writes each block — §6, §8, §9 grow across the steps and are nominal from the start
BLOCK_STEP = {"s1": 1, "s2": 2, "s3": 2, "s4": 3, "s5": 4, "s7": 5}


def build_up_to(step: int, **overrides: str) -> str:
    """The nominal PRD as it stands once Steps 1..step have passed their [C]: nominal blocks
    for those steps, the skeleton for the later ones (§4's bullets are Step 4's)."""
    blocks = {k: (BLOCKS[k] if BLOCK_STEP.get(k, 0) <= step else SKELETON[k]) for k in ORDER}
    if step == 3:
        blocks["s4"] = BLOCKS["s4"].replace(
            "- **BR-001** — **Minimum amount:** cart total is 0 € → payment is skipped\n"
            "- **ERR-001** — Payment is declined by the bank\n",
            "- [Step 3 leaves this list empty — Step 4 back-fills it]\n")
    blocks.update(overrides)
    return FRONTMATTER + "".join(blocks[k] for k in ORDER)

# the project record the nominal PRD belongs to — `record/brief-001.md`, resolved from `brief:`
RECORD = """# Decision record — Demo

## Decisions

| ID | PRD | Step | Decision | Why | Resolves | Affects |
|---|---|---|---|---|---|---|

## Tensions

| ID | PRD | Tension | Status | Resolution | Affects |
|---|---|---|---|---|---|

## Vocabulary

| Term | Definition | PRD |
|---|---|---|

## Sources

| PRD | Source | What it produced | Gate |
|---|---|---|---|
"""


def parked(*rows: str) -> str:
    """A `## Parked` block holding the given `| Item | Kind | For | Origin |` rows."""
    return ("\n## Parked\n\n| Item | Kind | For | Origin |\n|---|---|---|---|\n"
            + "".join(r + "\n" for r in rows))


def record_with(table: str, *rows: str) -> str:
    """The nominal record with rows appended to one of its tables."""
    marker = {"Decisions": "|---|---|---|---|---|---|---|\n",
              "Tensions": "|---|---|---|---|---|---|\n",
              "Vocabulary": "|---|---|---|\n\n## Sources",
              "Sources": "|---|---|---|---|\n\"\"\""}
    head = RECORD.split("## " + table)[1]
    sep = next(line for line in head.splitlines() if line.startswith("|---"))
    before, after = RECORD.split("## " + table, 1)
    after = after.replace(sep + "\n", sep + "\n" + "".join(r + "\n" for r in rows), 1)
    return before + "## " + table + after


def build(**overrides: str) -> str:
    """The nominal PRD, with any block replaced wholesale."""
    blocks = dict(BLOCKS)
    unknown = set(overrides) - set(blocks)
    assert not unknown, f"unknown block(s): {sorted(unknown)}"
    blocks.update(overrides)
    return FRONTMATTER + "".join(blocks[k] for k in ORDER)


def run(prd: str, brief_status: str = "validated", up_to: int | None = None,
        record: str | None = RECORD, filename: str = "prd01-demo.md",
        findings_out: list | None = None) -> tuple[list[str], list[str]]:
    """Validate one PRD in a throwaway docs tree. Returns (error messages, warning messages).

    `up_to` is the `--up-to N` of the command line: only what Steps 1..N wrote is read. `record`
    is the project record written to `record/brief-001.md` — None leaves the tree without one."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "brief").mkdir()
        (root / "prd").mkdir()
        (root / "brief" / "brief-001.md").write_text(
            f"---\nstatus: {brief_status}\n---\n\n# Brief 001\n", encoding="utf-8")
        if record is not None:
            (root / "record").mkdir()
            (root / "record" / "brief-001.md").write_text(record, encoding="utf-8")
        path = root / "prd" / filename
        path.write_text(prd, encoding="utf-8")

        findings: list[V.Finding] = []
        V.check_prd(path, findings, up_to)
        if findings_out is not None:
            findings_out.extend(findings)
        return ([f.msg for f in findings if f.level == "ERROR"],
                [f.msg for f in findings if f.level == "WARN"])


def has(messages: list[str], *needles: str) -> bool:
    return any(all(n in m for n in needles) for m in messages)


class NominalPRD(unittest.TestCase):
    def test_a_well_formed_prd_is_clean(self):
        errors, warns = run(build())
        self.assertEqual(errors, [], "a conformant PRD must raise no error")
        self.assertEqual(warns, [], "a conformant PRD must raise no warning either")


class CriteriaAreTableRows(unittest.TestCase):
    """A criterion is defined by its table row. The block form defines nothing."""

    def test_block_form_does_not_define_a_criterion(self):
        s5 = BLOCKS["s5"].replace(
            "| ERR-001 | Payment is declined by the bank | the cart is preserved |",
            "ERR-001 : Payment is declined by the bank\n  Expected behavior : the cart is preserved")
        errors, _ = run(build(s5=s5))
        self.assertTrue(has(errors, "ERR-001", "not defined in section 5"), errors)

    def test_an_id_defined_twice_is_reported(self):
        s5 = BLOCKS["s5"].replace(
            "| BR-001 | **Minimum amount:** cart total is 0 € → payment is skipped | FUNC-001 |",
            "| BR-001 | **Minimum amount:** cart total is 0 € → payment is skipped | FUNC-001 |\n"
            "| BR-001 | **Duplicate:** another rule entirely | FUNC-001 |")
        errors, _ = run(build(s5=s5))
        self.assertTrue(has(errors, "BR-001", "defined twice"), errors)

    def test_a_bullet_after_a_grouping_heading_is_still_compared(self):
        """The invariant `spec` relies on: §4 and §5 may not carry two texts for one rule.

        A long FUNC groups its criteria under `####`. Ending the list at the first non-bullet line
        dropped every bullet after that heading — silently, since the earlier ones kept the block
        from looking empty.
        """
        s4 = BLOCKS["s4"].replace(
            "- **ERR-001** — Payment is declined by the bank",
            "#### Failure handling\n\n- **ERR-001** — Payment is refused")
        errors, _ = run(build(s4=s4))
        self.assertTrue(has(errors, "ERR-001", "differently"), errors)

    def test_a_func_bullet_must_match_its_definition(self):
        s4 = BLOCKS["s4"].replace(
            "- **BR-001** — **Minimum amount:** cart total is 0 € → payment is skipped",
            "- **BR-001** — **Minimum amount:** cart total is under 1 € → payment is skipped")
        errors, _ = run(build(s4=s4))
        self.assertTrue(has(errors, "BR-001", "differently"), errors)


class CosmeticChoicesDoNotFailAGate(unittest.TestCase):
    """Formatting freedom the author is entitled to, which the validator must not punish."""

    def test_a_bold_metric_id_is_still_a_row(self):
        s7 = BLOCKS["s7"].replace("| LGM-001 |", "| **LGM-001** |")
        errors, warns = run(build(s7=s7))
        self.assertFalse(has(errors, "Lagging Metrics", "empty"), errors)
        self.assertEqual((errors, warns), ([], []))

    def test_an_escaped_pipe_does_not_hide_a_damage_control_threshold(self):
        s7 = BLOCKS["s7"].replace(
            """### Damage Control

None identified.""",
            """### Damage Control

| ID | Metric | Current baseline | Max acceptable degradation |
|----|--------|------------------|----------------------------|
| DC-001 | bounce rate | 31% | -2 pts \\| never lower |""")
        errors, _ = run(build(s7=s7))
        self.assertFalse(has(errors, "DC-001", "numeric threshold"), errors)

    def test_a_quoted_example_is_not_a_second_definition(self):
        """Fenced blocks are illustrations — ids inside one must not register as definitions."""
        s5 = BLOCKS["s5"] + """
The shape expected above:

```
| BR-001 | **Minimum amount:** cart total is 0 € → payment is skipped | FUNC-001 |
```
"""
        s4 = BLOCKS["s4"] + """
Illustration only:

```
### FUNC-999 — Users can do something else
**WHEN** something happens
**THEN** the user sees it
```
"""
        errors, warns = run(build(s4=s4, s5=s5))
        self.assertEqual((errors, warns), ([], []))

    def test_a_byte_order_mark_does_not_hide_the_frontmatter(self):
        errors, warns = run("\ufeff" + build())
        self.assertEqual((errors, warns), ([], []))


class LeftoversStillFail(unittest.TestCase):
    """The other half of the placeholder rule: what must keep being caught."""

    def test_template_token_is_still_flagged(self):
        errors, warns = run(build(s1=BLOCKS["s1"].replace("brief-001 — the", "[XXX] — the")))
        self.assertTrue(has(warns, "placeholder"), warns)

    def test_a_bracketed_id_is_still_flagged(self):
        s6 = BLOCKS["s6"].replace(
            "None identified.",
            "| Item | Reason |\n|------|--------|\n| [NG-001] Guest checkout | deferred |")
        _, warns = run(build(s6=s6))
        self.assertTrue(has(warns, "placeholder", "[NG-001]"), warns)

    def test_country_variants_are_written_without_brackets(self):
        """`REF-acceptance-criteria.md` writes `Variants : FR 25 € / DE 30 €` — no brackets.

        A bracketed token is a template slot, always. Exempting `[FR]` would teach the validator to
        accept the form the methodology forbids, and no exemption narrow enough to mean "country
        code" exists: `[XX]`, `[TBD]` and `[TODO]` have the very same shape.
        """
        def with_variants(text: str):
            rule = "**Minimum amount:** cart total is 0 € → payment is skipped. Variants : " + text
            s5 = BLOCKS["s5"].replace(
                "**Minimum amount:** cart total is 0 € → payment is skipped | FUNC-001 |",
                rule + " | FUNC-001 |")
            s4 = BLOCKS["s4"].replace(
                "- **BR-001** — **Minimum amount:** cart total is 0 € → payment is skipped",
                "- **BR-001** — " + rule)
            return run(build(s4=s4, s5=s5))

        self.assertEqual(with_variants("FR 25 € / DE 30 €"), ([], []),
                         "the documented form must be clean")
        _, warns = with_variants("[FR] 25 € / [DE] 30 €")
        self.assertTrue(has(warns, "placeholder"), warns)

    def test_an_assumption_marker_never_survives_the_gate(self):
        s3 = BLOCKS["s3"].replace(
            "1. The user submits their payment",
            "1. The user submits their payment [ASSUMPTION: a card is already saved]")
        errors, _ = run(build(s3=s3))
        self.assertTrue(has(errors, "ASSUMPTION"), errors)

    def test_a_journey_left_at_tbd_reveals_nothing(self):
        s3 = BLOCKS["s3"].replace("*Capabilities revealed:* FUNC-001",
                                  "*Capabilities revealed:* TBD")
        errors, _ = run(build(s3=s3))
        self.assertTrue(has(errors, "QG-6", "still a placeholder"), errors)


class ReferenceExamplesStayValid(unittest.TestCase):
    """The `REF-acceptance-criteria.md` examples are executed, not just read.

    This is the loop that was missing. The reference used to document a block form
    (`ERR-001 : …`) that the template never used and the validator could not see — and nothing
    noticed, for as long as nobody copied an example into a real PRD. Here the examples ARE the
    fixture: the reference cannot drift from the validator without this test going red.
    """

    REF = SKILL / "references" / "REF-acceptance-criteria.md"

    @staticmethod
    def example_tables(text: str) -> dict[str, tuple[list[str], list[list[str]]]]:
        """The worked example of each criterion type, as (header cells, data rows).

        Only blocks introduced by `**Example:**` count. Reading any `| ID | … |` table would let a
        `Format:` skeleton stand in for a deleted example — the type would still be present, the
        test still green, and the reference would carry no worked example at all.
        """
        tables: dict[str, tuple[list[str], list[list[str]]]] = {}
        block: list[str] | None = None
        introduced_by: str | None = None
        for line in text.splitlines():
            head = line.strip()
            if head.startswith("**Format**") or head.startswith("**Format:**"):
                introduced_by = "format"
            elif head.startswith("**Example**") or head.startswith("**Example:**"):
                introduced_by = "example"
            if line.startswith("```"):
                if block is not None:
                    rows = [ln for ln in block if ln.strip().startswith("|")]
                    if (introduced_by == "example" and len(rows) >= 3
                            and rows[0].strip().startswith("| ID |")):
                        cells = [V.split_cells(r) for r in rows[2:]]  # skip header + separator
                        kind = V.ID_RE.search(cells[0][0])
                        if kind:
                            tables[kind.group(1)] = (V.split_cells(rows[0]), cells)
                    block = None
                else:
                    block = []
                continue
            if block is not None:
                block.append(line)
        return tables

    EXPECTED_HEADERS = {
        "BR": ["ID", "Rule", "Applies to"],
        "ST": ["ID", "Object", "States", "Allowed transitions", "Blocked transitions"],
        "PERM": ["ID", "Actor", "Action", "Allowed condition", "Blocked condition"],
        "ERR": ["ID", "Failure mode", "Expected behavior"],
    }

    def test_every_example_row_validates(self):
        tables = self.example_tables(self.REF.read_text(encoding="utf-8"))
        self.assertEqual(sorted(tables), ["BR", "ERR", "PERM", "ST"],
                         "the reference must carry one worked example per criterion type")

        for kind, (header, cells) in sorted(tables.items()):
            # the §4 side below is built from the same cells that feed §5, so a permuted column
            # would cancel itself out — the header is the only thing that catches it
            self.assertEqual(header, self.EXPECTED_HEADERS[kind],
                             f"{kind}: the reference's columns must match TEMPLATE-prd.md §5")
            # a worked example carries real content; a skeleton carries [placeholders]
            for row in cells:
                for cell in row:
                    self.assertIsNone(V.PLACEHOLDER_RE.search(cell),
                                      f"{kind}: {cell!r} is a skeleton, not an example")

        def table(kind: str) -> str:
            header, cells = tables[kind]
            return "\n".join(["| " + " | ".join(header) + " |", "|---" * len(header) + "|"]
                             + ["| " + " | ".join(c) + " |" for c in cells])

        s5 = "\n".join([
            "\n## 5. Acceptance Criteria\n",
            "### Business Rules\n", table("BR"),
            "\n### States & Transitions\n", table("ST"),
            "\n### Permissions\n", table("PERM"),
            "\n### Error Scenarios\n", table("ERR"),
            ""])

        # the §4 side of the mirror, linearised exactly as the reference prescribes
        bullets: dict[str, list[str]] = {}
        for c in tables["BR"][1]:
            for func in V.FUNC_RE.findall(c[-1]):
                bullets.setdefault(func, []).append(f"- **{c[0]}** — {c[1]}")
        host = sorted(bullets)[0]          # the cross-cutting criteria hang off one FUNC
        bullets[host] += [f"- **{c[0]}** — {c[1]}" for c in tables["ERR"][1]]
        bullets[host] += [f"- **{c[0]}** — {c[1]} — states: {c[2]}" for c in tables["ST"][1]]
        bullets[host] += [f"- **{c[0]}** — {c[1]} : {c[2]}" for c in tables["PERM"][1]]

        funcs = []
        for i, (fid, bs) in enumerate(sorted(bullets.items()), start=1):
            funcs.append(f"### {fid} — Users can complete checkout step {i}\n\n"
                         f"**Capability:** the user completes step {i}.\n\n"
                         "**Acceptance criteria:**\n\n" + "\n".join(bs) + "\n\n"
                         "**Nominal scenario:**\n"
                         f"- **WHEN** the user completes step {i}\n"
                         "- **THEN** the user sees the result\n")

        s4 = "\n## 4. Functional Specifications\n\n" + "\n".join(funcs)
        s3 = BLOCKS["s3"].replace("*Capabilities revealed:* FUNC-001",
                                  "*Capabilities revealed:* " + ", ".join(sorted(bullets)))

        errors, warns = run(build(s3=s3, s4=s4, s5=s5))
        self.assertEqual(errors, [], f"the reference's examples must validate: {errors}")
        self.assertEqual(warns, [], f"the reference's examples must not even warn: {warns}")

class TheFormatIsReadByPosition(unittest.TestCase):
    """Every cell in the validator is read by index. The headers are the contract that makes that safe."""

    def test_a_permuted_header_is_an_error(self):
        s5 = BLOCKS["s5"].replace("| ID | Rule | Applies to |", "| ID | Applies to | Rule |")
        errors, _ = run(build(s5=s5))
        self.assertTrue(has(errors, "Business Rules", "permuted header"), errors)

    def test_a_missing_column_is_an_error(self):
        s5 = BLOCKS["s5"].replace("| ID | Rule | Applies to |", "| ID | Rule |")
        errors, _ = run(build(s5=s5))
        self.assertTrue(has(errors, "Business Rules", "columns"), errors)

    def test_translated_headers_warn_but_do_not_fail(self):
        """The skill lets the prose be French. Failing a translated header would fail every
        PRD already written, to protect a positional read that a translation does not touch."""
        s5 = BLOCKS["s5"].replace("| ID | Rule | Applies to |", "| ID | Règle | Porte sur |")
        errors, warns = run(build(s5=s5))
        self.assertEqual(errors, [], errors)
        self.assertTrue(has(warns, "machine tokens"), warns)

    def test_a_missing_ac_subsection_warns_without_failing(self):
        """Ids are recognised by their prefix, so nothing breaks — but a reader looking for a type
        needs its heading. A warning, per the rule: errors are for what breaks parsing."""
        s5 = "\n## 5. Acceptance Criteria\n\n### Rules by domain\n" + BLOCKS["s5"].split(
            "### Business Rules", 1)[1]
        errors, warns = run(build(s5=s5))
        self.assertEqual(errors, [], errors)
        self.assertTrue(has(warns, "section 5 has no", "Business Rules"), warns)


class TheMirrorRunsBothWays(unittest.TestCase):
    """§4 lists the rules it leans on; §5 lists the capabilities each rule binds. They must agree."""

    def test_a_func_claiming_an_unbound_rule_is_reported(self):
        s5 = BLOCKS["s5"].replace("| FUNC-001 |", "| FUNC-002 |")
        _, warns = run(build(s5=s5))
        self.assertTrue(has(warns, "FUNC-001 lists BR-001", "does not name"), warns)

    def test_an_empty_applies_to_cell_switches_nothing_off(self):
        s5 = BLOCKS["s5"].replace(
            "payment is skipped | FUNC-001 |", "payment is skipped |  |")
        errors, _ = run(build(s5=s5))
        self.assertTrue(has(errors, "BR-001", "empty `Applies to`"), errors)


class TheMethodologyIsChecked(unittest.TestCase):
    """Rules the references state as MUST, which nothing verified until now."""

    def test_a_journey_without_a_goal_is_reported(self):
        s3 = BLOCKS["s3"].replace("*Goal:* the user has paid and holds a confirmation\n\n", "")
        _, warns = run(build(s3=s3))
        self.assertTrue(has(warns, "states no `*Goal:*`"), warns)

    def test_branch_notation_is_reported(self):
        s3 = BLOCKS["s3"].replace("2. The user sees a confirmation", "2a. The user sees a confirmation")
        _, warns = run(build(s3=s3))
        self.assertTrue(has(warns, "branch notation"), warns)

    def test_an_incomplete_leading_metric_is_reported(self):
        s7 = BLOCKS["s7"].replace(
            "### Leading Metrics\n\nNone defined.",
            "### Leading Metrics\n\n"
            "| ID | Observable behavior | Collection method | Review cadence |\n"
            "|----|---------------------|-------------------|----------------|\n"
            "| LDM-001 | share of sessions reaching payment | funnel event |  |")
        _, warns = run(build(s7=s7))
        self.assertTrue(has(warns, "LDM-001", "review cadence"), warns)

    def test_an_empty_personas_section_is_reported(self):
        _, warns = run(build(s2="\n## 2. Personas\n\n"))
        self.assertTrue(has(warns, "section 2 Personas is empty"), warns)

    def test_a_term_defined_twice_is_reported(self):
        s8 = ("\n## 8. Glossary\n\n| Term | Definition |\n|------|-----------|\n"
              "| Panier | the shopping cart |\n| Panier | the booking cart |\n")
        _, warns = run(build(s8=s8))
        self.assertTrue(has(warns, "glossary defines", "twice"), warns)

    def test_a_complexity_off_the_grid_is_reported(self):
        _, warns = run(build().replace("complexity: S", "complexity: XL"))
        self.assertTrue(has(warns, "complexity is XL", "grid says S"), warns)


class DiagnosticsSayWhatIsWrong(unittest.TestCase):
    """A check that misnames the cause sends the author to the wrong place."""

    def test_an_exotic_dash_is_not_a_divergence(self):
        s4 = BLOCKS["s4"].replace("- **BR-001** — **Minimum", "- **BR-001** \u2212 **Minimum")
        errors, warns = run(build(s4=s4))
        self.assertFalse(has(errors, "BR-001", "differently"),
                         f"a wrong dash must not read as a wrong text: {errors}")
        self.assertEqual((errors, warns), ([], []))

    def test_a_label_is_read_by_its_words_not_its_typography(self):
        """One or two asterisks, and the space French puts before a colon, are the same label."""
        variants = [
            ("s3", "*Capabilities revealed:* FUNC-001", "**Capabilities revealed:** FUNC-001"),
            ("s3", "*Capabilities revealed:* FUNC-001", "*Capabilities revealed :* FUNC-001"),
            ("s3", "*Goal:* the user", "**Goal:** the user"),
            ("s3", "*Goal:* the user", "*Goal :* the user"),
            ("s4", "**Acceptance criteria:**", "*Acceptance criteria:*"),
            ("s4", "**Acceptance criteria:**", "**Acceptance criteria :**"),
        ]
        for block, canonical, variant in variants:
            with self.subTest(variant=variant):
                self.assertIn(canonical, BLOCKS[block])
                result = run(build(**{block: BLOCKS[block].replace(canonical, variant)}))
                self.assertEqual(result, ([], []))

    def test_an_unclosed_fence_names_itself(self):
        errors, _ = run(build(s9=BLOCKS["s9"] + "\n```\nan example nobody closed\n"))
        self.assertTrue(has(errors, "never closed"), errors)


class BriefStatus(unittest.TestCase):
    """An unvalidated brief is a signal, not a wall — see references/REF-brief-contract.md."""

    def test_an_unvalidated_brief_warns_without_failing(self):
        errors, warns = run(build(), brief_status="draft")
        self.assertEqual(errors, [], errors)
        self.assertTrue(has(warns, "QG-11", "not validated"), warns)


class TheBriefResolvesFromAnyWorkingDirectory(unittest.TestCase):
    """A bare filename passed from inside `prd/` used to look for the brief in `./brief/`."""

    def test_a_bare_filename_still_resolves_the_brief(self):
        import os
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "brief").mkdir()
            (root / "prd").mkdir()
            (root / "brief" / "brief-001.md").write_text(
                "---\nstatus: validated\n---\n\n# Brief 001\n", encoding="utf-8")
            (root / "record").mkdir()
            (root / "record" / "brief-001.md").write_text(RECORD, encoding="utf-8")
            (root / "prd" / "prd01-demo.md").write_text(build(), encoding="utf-8")
            cwd = os.getcwd()
            os.chdir(root / "prd")
            try:
                findings: list[V.Finding] = []
                V.check_prd(Path("prd01-demo.md"), findings)
            finally:
                os.chdir(cwd)
        self.assertEqual([f.msg for f in findings], [], findings)


class EveryIdFamilyIsDefinedOnce(unittest.TestCase):
    """§5 had the rule; FUNCs, metrics, exclusions and questions get the same one."""

    def test_a_func_defined_twice_is_reported(self):
        s4 = BLOCKS["s4"] + BLOCKS["s4"].split("## 4. Functional Specifications", 1)[1]
        errors, _ = run(build(s4=s4))
        self.assertTrue(has(errors, "FUNC-001", "defined twice"), errors)

    def test_a_metric_defined_twice_is_reported(self):
        s7 = BLOCKS["s7"].replace(
            "| LGM-001 | checkout conversion | 12% | +5 pts |",
            "| LGM-001 | checkout conversion | 12% | +5 pts |\n"
            "| LGM-001 | repeat purchase | 3% | +1 pt |")
        errors, _ = run(build(s7=s7))
        self.assertTrue(has(errors, "LGM-001", "defined twice"), errors)

    def test_an_exclusion_defined_twice_is_reported(self):
        s6 = ("\n## 6. Out of Scope\n\n| Item | Reason |\n|------|--------|\n"
              "| NG-001 — Guest checkout | deferred |\n| NG-001 — Gift cards | out of the brief |\n")
        errors, _ = run(build(s6=s6))
        self.assertTrue(has(errors, "NG-001", "defined twice"), errors)

    def test_a_question_defined_twice_is_reported(self):
        s9 = ("\n## 9. Open Questions\n\n"
              "| ID | Question | Impact if unresolved | Blocks | Source |\n"
              "|----|----------|---------------------|--------|--------|\n"
              "| OQ-001 | Is a saved card required? | scope of FUNC-001 | FUNC-001 | Journey 1 |\n"
              "| OQ-001 | Which currencies? | pricing rules | BR-001 | PM |\n")
        errors, _ = run(build(s9=s9))
        self.assertTrue(has(errors, "OQ-001", "defined twice"), errors)


class ReferencesResolve(unittest.TestCase):
    """A FUNC cited outside the sections that define and mirror it must exist — an open question
    blocking a phantom capability used to pass."""

    @staticmethod
    def s9_blocking(func: str) -> str:
        return ("\n## 9. Open Questions\n\n"
                "| ID | Question | Impact if unresolved | Blocks | Source |\n"
                "|----|----------|---------------------|--------|--------|\n"
                f"| OQ-001 | Is a saved card required? | scope of the flow | {func} | Journey 1 |\n")

    def test_a_func_cited_in_an_open_question_must_exist(self):
        _, warns = run(build(s9=self.s9_blocking("FUNC-009")))
        self.assertTrue(has(warns, "FUNC-009", "defines no such FUNC"), warns)

    def test_a_func_that_exists_is_cited_silently(self):
        errors, warns = run(build(s9=self.s9_blocking("FUNC-001")))
        self.assertEqual(errors, [], errors)
        self.assertFalse(has(warns, "defines no such FUNC"), warns)


class DamageControlThreshold(unittest.TestCase):
    """A DC with no numeric bound warns, like an LGM with no threshold — it no longer fails."""

    def test_a_damage_control_row_without_threshold_warns_without_failing(self):
        s7 = BLOCKS["s7"].replace(
            "### Damage Control\n\nNone identified.",
            "### Damage Control\n\n"
            "| ID | Metric | Current baseline | Max acceptable degradation |\n"
            "|----|--------|------------------|----------------------------|\n"
            "| DC-001 | bounce rate | 31% | TBD |")
        errors, warns = run(build(s7=s7))
        self.assertEqual(errors, [], errors)
        self.assertTrue(has(warns, "DC-001", "numeric threshold"), warns)


class OneDefectDoesNotHideAnother(unittest.TestCase):
    """The validator used to `continue` on a duplicated id, dropping the row before the mirror
    check — fixing the id then surfaced a second error at the next run. Every row is read now."""

    def test_a_duplicated_row_is_still_mirror_checked(self):
        s5 = BLOCKS["s5"].replace(
            "| BR-001 | **Minimum amount:** cart total is 0 € → payment is skipped | FUNC-001 |",
            "| BR-001 | **Minimum amount:** cart total is 0 € → payment is skipped | FUNC-001 |\n"
            "| BR-001 | **Duplicate:** another rule entirely | FUNC-999 |")
        errors, _ = run(build(s5=s5))
        self.assertTrue(has(errors, "BR-001", "defined twice"), errors)
        self.assertTrue(has(errors, "BR-001 applies to FUNC-999", "does not define"), errors)

    def test_every_error_class_is_reported_at_once(self):
        """The kitchen sink: one defect of every ERROR class in a single document, and every one of
        them expected in the output. Masking — one finding swallowing another — shows up here."""
        func_block = BLOCKS["s4"].split("## 4. Functional Specifications", 1)[1]
        prd = build(
            s3=BLOCKS["s3"].replace("*Capabilities revealed:* FUNC-001",
                                    "*Capabilities revealed:* TBD"),
            s4=BLOCKS["s4"].replace("- **THEN** the user sees a confirmation\n", "") + func_block,
            s5=BLOCKS["s5"].replace(
                "| ID | Failure mode | Expected behavior |",
                "| ID | Expected behavior | Failure mode |",
            ).replace(
                "| BR-001 | **Minimum amount:** cart total is 0 € → payment is skipped | FUNC-001 |",
                "| BR-001 | **Minimum amount:** cart total is 0 € → payment is skipped | FUNC-001 |\n"
                "| BR-001 | **Duplicate:** another rule entirely | FUNC-001 |"),
            s6=("\n## 6. Out of Scope\n\n| Item | Reason |\n|------|--------|\n"
                "| NG-001 — Guest checkout | deferred |\n| NG-001 — Gift cards | out of the brief |\n"),
            s7=BLOCKS["s7"].replace("### Damage Control\n\nNone identified.\n", ""),
            s9=BLOCKS["s9"] + "\nStill open [ASSUMPTION: a card is already saved].\n",
        )
        prd = (prd.replace("status: in-progress", "status: draft")
                  .replace("brief: brief-001", "brief: brief-404")
                  .replace("# Demo\n", "# Demo (draft)\n\n<!--\nINSTANTIATION NOTES\n-->\n", 1))
        errors, _ = run(prd)
        for needle in ("`status` must be one of", "differs from the `title`", "does not resolve",
                       "instantiation comment", "no WHEN/THEN", "still a placeholder",
                       "FUNC-001 is defined twice", "BR-001 is defined twice", "permuted header",
                       "has no `### Damage Control`", "NG-001 is defined twice", "ASSUMPTION"):
            self.assertTrue(has(errors, needle), f"{needle!r} is missing from: {errors}")


class UpToReadsOnlyWhatTheStepsWrote(unittest.TestCase):
    """`--up-to N` runs the check groups 1..N and reads only the lines those steps own. The skill
    runs it at every `[C]`, so a form error is caught at the step that made it."""

    TEMPLATE = SKILL / "assets" / "TEMPLATE-prd.md"

    def skeleton_after_step_1(self) -> str:
        """The template as Step 1 leaves it: comment gone, frontmatter and §1 filled, the rest
        still holding every placeholder of the later steps."""
        text = self.TEMPLATE.read_text(encoding="utf-8")
        text = text[:text.index("<!--")] + text[text.index("-->") + 3:]
        for old, new in (
            ('title: "[Product Name]"', 'title: "Demo"'),
            ("date: YYYY-MM-DD", "date: 2026-08-26"),
            ('author: "Firstname Lastname"', 'author: "Celine Net"'),
            ("brief: brief-XXX", "brief: brief-001"),
            ("record: brief-XXX", "record: brief-001"),
            ("# [Product Name]", "# Demo"),
            ('**Source:** brief-XXX — "[Brief title]"',
             "**Source:** brief-001 — the checkout opportunity"),
            ("**Opportunity addressed:** [OPP-XXX — verbatim from brief. → See brief-XXX for full "
             "problem space context.]", "**Opportunity addressed:** OPP-001 — Let users pay"),
            ("**Solution:** [1-2 sentences: what approach, what scope.]",
             "**Solution:** a payment step at the end of checkout."),
        ):
            self.assertIn(old, text, "the template moved — realign this fixture")
            text = text.replace(old, new)
        return text

    def test_the_skeleton_passes_step_1_and_owes_step_2(self):
        prd = self.skeleton_after_step_1()
        self.assertEqual(run(prd, up_to=1), ([], []),
                         "a skeleton Step 1 just filled must be clean up to Step 1")
        errors, warns = run(prd, up_to=2)
        self.assertEqual(errors, [], errors)
        self.assertTrue(has(warns, "placeholder"), warns)

    def test_a_tbd_capabilities_line_is_owed_at_step_3_not_step_2(self):
        prd = build(s3=BLOCKS["s3"].replace("*Capabilities revealed:* FUNC-001",
                                            "*Capabilities revealed:* TBD"))
        errors, _ = run(prd, up_to=2)
        self.assertFalse(has(errors, "QG-6"), errors)
        errors, _ = run(prd, up_to=3)
        self.assertTrue(has(errors, "QG-6", "still a placeholder"), errors)

    def test_criteria_bullets_are_owed_at_step_4_not_step_3(self):
        self.assertEqual(run(build_up_to(3), up_to=3), ([], []))
        prd = build(s4=BLOCKS["s4"].replace(
            "- **BR-001** — **Minimum amount:** cart total is 0 € → payment is skipped\n"
            "- **ERR-001** — Payment is declined by the bank\n",
            "[filled at Step 4]\n"))
        _, warns = run(prd, up_to=4)
        self.assertTrue(has(warns, "FUNC-001 lists no acceptance criteria"), warns)
        self.assertTrue(has(warns, "placeholder"), warns)

    def test_an_assumption_in_section_5_is_owed_at_step_4(self):
        s5 = BLOCKS["s5"].replace(
            "| ERR-001 | Payment is declined by the bank | the cart is preserved |",
            "| ERR-001 | Payment is declined by the bank | the cart is preserved "
            "[ASSUMPTION: a retry is allowed] |")
        prd = build(s5=s5)
        errors, _ = run(prd, up_to=3)
        self.assertFalse(has(errors, "ASSUMPTION"), errors)
        errors, _ = run(prd, up_to=4)
        self.assertTrue(has(errors, "ASSUMPTION"), errors)

    def test_complexity_is_owed_at_step_6(self):
        prd = build().replace("complexity: S", "complexity: XL")
        _, warns = run(prd, up_to=5)
        self.assertFalse(has(warns, "grid says"), warns)
        _, warns = run(prd)
        self.assertTrue(has(warns, "grid says S"), warns)


class TheCommandLine(unittest.TestCase):
    """Exit codes and the grouped report — what the skill reads at each `[C]`."""

    def cli(self, prd: str, *flags: str) -> tuple[int, str]:
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "brief").mkdir()
            (root / "prd").mkdir()
            (root / "brief" / "brief-001.md").write_text(
                "---\nstatus: validated\n---\n\n# Brief 001\n", encoding="utf-8")
            (root / "record").mkdir()
            (root / "record" / "brief-001.md").write_text(RECORD, encoding="utf-8")
            path = root / "prd" / "prd01-demo.md"
            path.write_text(prd, encoding="utf-8")
            proc = subprocess.run([sys.executable, str(Path(V.__file__)), str(path), *flags],
                                  capture_output=True, text=True)
            return proc.returncode, proc.stdout

    def test_a_clean_prd_exits_zero(self):
        code, out = self.cli(build())
        self.assertEqual(code, 0, out)
        self.assertIn("all structural checks passed", out)

    def test_an_error_exits_one_and_names_its_step(self):
        code, out = self.cli(build(s4=BLOCKS["s4"].replace("- **THEN** the user sees a confirmation\n", "")))
        self.assertEqual(code, 1, out)
        self.assertIn("Step 3 — functional blocks", out)
        self.assertIn("✗ ERROR", out)

    def test_up_to_scopes_the_run(self):
        prd = build_up_to(2, s3=BLOCKS["s3"].replace("*Capabilities revealed:* FUNC-001",
                                                     "*Capabilities revealed:* TBD"))
        code, out = self.cli(prd, "--up-to", "2")
        self.assertEqual(code, 0, out)
        self.assertIn("up to Step 2", out)
        code, _ = self.cli(build_up_to(3, s3=BLOCKS["s3"].replace(
            "*Capabilities revealed:* FUNC-001", "*Capabilities revealed:* TBD")), "--up-to", "3")
        self.assertEqual(code, 1)

    def test_the_gate_card_names_the_next_step_and_its_reference(self):
        prd = build_up_to(2) + parked("| declined card | ERR candidate | Step 4 | PM |",
                                      "| refund rule | BR candidate | Step 3 | PM |")
        code, out = self.cli(prd, "--up-to", "2")
        self.assertEqual(code, 0, out)
        self.assertIn("Next: Step 3 — Functional blocks.", out)
        self.assertIn("references/REF-functional-blocks.md", out)
        self.assertIn("[C] Validate → Step 4 — Acceptance criteria", out)
        self.assertIn("1 row(s) parked for Step 3", out)
        _, out = self.cli(build(), "--up-to", "6")
        self.assertIn("Next: the quality gate.", out)
        _, out = self.cli(build())
        self.assertNotIn("Next:", out, "the full run has no next step")

    def test_every_reference_the_card_names_exists(self):
        root = Path(V.__file__).resolve().parent.parent
        for _, (_, ref, _) in V.NEXT_STEP.items():
            if ref:
                self.assertTrue((root / ref).is_file(), ref)

    def test_the_report_prints_on_a_console_that_cannot_encode_it(self):
        import os
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "brief").mkdir()
            (root / "prd").mkdir()
            (root / "brief" / "brief-001.md").write_text(
                "---\nstatus: validated\n---\n\n# Brief 001\n", encoding="utf-8")
            (root / "record").mkdir()
            (root / "record" / "brief-001.md").write_text(RECORD, encoding="utf-8")
            path = root / "prd" / "prd01-demo.md"
            path.write_text(build(), encoding="utf-8")
            proc = subprocess.run([sys.executable, str(Path(V.__file__)), str(path)],
                                  capture_output=True,
                                  env={**os.environ, "PYTHONIOENCODING": "ascii"})
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertNotIn(b"Traceback", proc.stderr)


class FormIsNotADefect(unittest.TestCase):
    """A false ERROR stops a run on a correct document: what markdown reads as the same content,
    the validator reads as the same content."""

    def test_a_scenario_in_a_fence_is_still_a_scenario(self):
        s4 = BLOCKS["s4"].replace(
            "- **WHEN** the user submits their payment\n- **THEN** the user sees a confirmation\n",
            "\n```gherkin\nWHEN the user submits their payment\n"
            "THEN the user sees a confirmation\n```\n")
        self.assertNotEqual(s4, BLOCKS["s4"])
        self.assertEqual(run(build(s4=s4)), ([], []))

    def test_an_editor_respelling_is_not_a_divergence(self):
        s4 = (BLOCKS["s4"].replace("0 € → payment", "0 € -> payment")
              .replace("declined by the bank", "declined by the user\u2019s bank"))
        s5 = BLOCKS["s5"].replace("declined by the bank", "declined by the user's bank")
        self.assertEqual(run(build(s4=s4, s5=s5)), ([], []))

    def test_a_tilde_fence_is_a_fence(self):
        s9 = BLOCKS["s9"] + "\n~~~\n## 4. Functional Specifications\n```\n~~~\n"
        self.assertEqual(run(build(s9=s9)), ([], []))

    def test_an_indented_heading_is_a_heading(self):
        prd = build(s2=BLOCKS["s2"].replace("## 2. Personas", " ## 2. Personas"),
                    s4=BLOCKS["s4"].replace("### FUNC-001", "  ### FUNC-001"),
                    s5=BLOCKS["s5"].replace("### Permissions", "   ### Permissions"))
        self.assertEqual(run(prd), ([], []))

    def test_a_comment_above_the_title_is_not_the_title(self):
        prd = build().replace("# Demo\n", "<!-- reviewed -->\n\n# Demo\n", 1)
        self.assertEqual(run(prd), ([], []))

    def test_a_forgotten_instantiation_block_is_named_once(self):
        prd = build().replace("# Demo\n", "<!--\nINSTANTIATION NOTES\n-->\n\n# Demo\n", 1)
        errors, _ = run(prd)
        self.assertEqual(len(errors), 1, errors)
        self.assertTrue(has(errors, "instantiation comment"), errors)

    def test_an_empty_marker_is_read_by_its_words(self):
        for marker in ("none identified", "None identified", "NONE DEFINED."):
            with self.subTest(marker=marker):
                s7 = BLOCKS["s7"].replace("None defined.", marker)
                self.assertEqual(run(build(s7=s7)), ([], []))


class TheGateIsEnforcedByTheScript(unittest.TestCase):
    """Nothing reaches a numbered section before its step's [C]. Under `--up-to N`, a section a
    later step owns holding content is a gate that was skipped — the skeleton never is."""

    def test_a_section_written_before_its_gate_is_an_error(self):
        findings: list = []
        errors, _ = run(build_up_to(2, s4=BLOCKS["s4"]), up_to=2, findings_out=findings)
        self.assertTrue(has(errors, "section 4 already hold content", "Step 3"), errors)
        self.assertEqual([f.step for f in findings if "already hold" in f.msg], [3, 4],
                         "§4's body is Step 3's, its criteria bullets Step 4's")

    def test_criteria_bullets_written_at_step_3_are_ahead_of_their_gate(self):
        errors, _ = run(build_up_to(3, s4=BLOCKS["s4"]), up_to=3)
        self.assertTrue(has(errors, "acceptance-criteria bullets already hold content"), errors)

    def test_the_skeleton_is_silent_at_every_gate(self):
        template = UpToReadsOnlyWhatTheStepsWrote("skeleton_after_step_1").skeleton_after_step_1()
        for step in range(1, 7):
            with self.subTest(step=step):
                errors, _ = run(build_up_to(step), up_to=step)
                self.assertFalse(has(errors, "already hold content"), errors)
                errors, _ = run(template, up_to=step)
                self.assertFalse(has(errors, "already hold content"), f"template at {step}: {errors}")

    def test_a_filled_func_heading_and_a_persona_paragraph_are_content(self):
        s4 = SKELETON["s4"].replace("### FUNC-001 — [Capability, in the PM's language]",
                                    "### FUNC-001 — Users can pay their order")
        errors, _ = run(build_up_to(2, s4=s4), up_to=2)
        self.assertTrue(has(errors, "section 4 already hold content"), errors)
        s2 = SKELETON["s2"].replace("[One short paragraph per persona confirmed at Step 2]",
                                    "Elodie, 38, orders for her family.")
        errors, _ = run(build_up_to(1, s2=s2), up_to=1)
        self.assertTrue(has(errors, "section 2 already hold content"), errors)
        # known limit: a persona written as one italic line reads as a legend and is not seen

    def test_the_closing_sections_grow_across_the_steps(self):
        s6 = BLOCKS["s6"].replace("None identified.",
                                  "| Item | Reason |\n|---|---|\n| NG-001 — Gift cards | Another PRD |")
        self.assertEqual(run(build_up_to(2, s6=s6), up_to=2), ([], []))

    def test_the_full_run_never_reads_ahead(self):
        self.assertEqual(run(build()), ([], []))


class ParkedRowsAreScratchWithADeadline(unittest.TestCase):
    """`## Parked` takes rows as they come and gives them back at the step they are parked for:
    a row still there once that gate has passed is an item that never found its home."""

    ROW = "| default preselection rule | BR candidate | Step 4 | PM, Step 2 |"

    def test_a_parked_heading_is_not_a_stray_subheading(self):
        self.assertEqual(run(build_up_to(2) + parked(self.ROW), up_to=2), ([], []))

    def test_a_row_is_due_at_its_step_and_not_before(self):
        prd = build_up_to(3) + parked(self.ROW)
        self.assertEqual(run(prd, up_to=3), ([], []))
        errors, _ = run(build_up_to(4) + parked(self.ROW), up_to=4)
        self.assertTrue(has(errors, "parked for Step 4", "never consumed"), errors)

    def test_a_finished_prd_with_parked_rows_fails_the_full_run(self):
        errors, _ = run(build() + parked(self.ROW))
        self.assertTrue(has(errors, "never consumed"), errors)
        self.assertEqual(run(build() + parked()), ([], []), "an empty block is accepted")

    def test_a_row_parked_for_no_step_is_an_error(self):
        errors, _ = run(build() + parked("| an idea | Solution | /prd | PM |"))
        self.assertTrue(has(errors, "targets no step"), errors)

    def test_a_placeholder_in_a_row_is_owed_by_its_step(self):
        prd = build_up_to(3) + parked("| [to be refined] | ERR candidate | Step 4 | PM |")
        self.assertEqual(run(prd, up_to=3), ([], []))
        errors, warns = run(build_up_to(4) + parked("| [to be refined] | ERR candidate | Step 4 | PM |"),
                            up_to=4)
        self.assertTrue(has(warns, "placeholder"), warns)

    def test_the_parked_table_keeps_its_columns(self):
        prd = build() + "\n## Parked\n\n| Item | For | Origin |\n|---|---|---|\n"
        errors, _ = run(prd)
        self.assertTrue(has(errors, "`Parked` table has 3 columns"), errors)

    def test_an_id_cited_only_in_parked_is_owed_by_its_step(self):
        """A row's citation is read when its step is owned — never as a §9 definition."""
        row = "| OQ-009 — a question | Question | Step 4 | PM |"
        self.assertEqual(run(build_up_to(3) + parked(row), up_to=3), ([], []))
        errors, warns = run(build_up_to(4) + parked(row), up_to=4)
        self.assertTrue(has(warns, "OQ-009", "defined nowhere"), warns)
        self.assertTrue(has(errors, "never consumed"), errors)

    def test_a_section_after_parked_warns(self):
        prd = build_up_to(2) + parked(self.ROW) + "\n## 10. Constraints\n\n### Business\n\n- **CB-001** A dependency\n"
        _, warns = run(prd, up_to=2)
        self.assertTrue(has(warns, "sits after `## Parked`"), warns)

    def test_a_legacy_canonical_memory_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "prd").mkdir()
            (root / "prd" / "canonical-memory.md").write_text("# memory\n", encoding="utf-8")
            (root / "prd" / "prd01-demo.md").write_text(build(), encoding="utf-8")
            self.assertEqual([p.name for p in V.discover([str(root / "prd")])], ["prd01-demo.md"])


class TheProjectRecordIsMirrored(unittest.TestCase):
    """§8 ↔ the record's Vocabulary, a resolved OQ, and the record's own shape."""

    GLOSSARY = ("| Term | Definition |\n|------|-----------|\n"
                "| Cart | The items a visitor assembled before paying |")

    def test_a_missing_record_warns(self):
        _, warns = run(build(), record=None)
        self.assertTrue(has(warns, "project record", "does not exist"), warns)

    def test_a_glossary_term_absent_from_the_record_warns(self):
        _, warns = run(build(s8=BLOCKS["s8"].replace("None identified.", self.GLOSSARY)))
        self.assertTrue(has(warns, "'Cart'", "no Vocabulary row"), warns)

    def test_a_diverging_definition_is_an_error(self):
        rec = record_with("Vocabulary", "| Cart | The basket | PRD03 |")
        errors, _ = run(build(s8=BLOCKS["s8"].replace("None identified.", self.GLOSSARY)), record=rec)
        self.assertTrue(has(errors, "'Cart'", "defined differently", "PRD03"), errors)

    def test_a_term_frozen_by_another_prd_is_reused_silently(self):
        rec = record_with("Vocabulary",
                          "| Cart | The items a visitor assembled before paying | PRD03 |")
        errors, warns = run(build(s8=BLOCKS["s8"].replace("None identified.", self.GLOSSARY)),
                            record=rec)
        self.assertEqual(errors, [], errors)
        self.assertFalse(has(warns, "Cart"), warns)       # only PRD03's absence from disk warns

    def test_a_record_term_of_this_prd_missing_from_its_glossary_warns(self):
        rec = record_with("Vocabulary", "| Cart | The basket | PRD01 |")
        _, warns = run(build(), record=rec)
        self.assertTrue(has(warns, "'Cart'", "frozen by this PRD", "§8 does not define it"), warns)

    def test_the_mirror_is_silent_before_step_2(self):
        rec = record_with("Vocabulary", "| Cart | The basket | PRD01 |")
        self.assertEqual(run(build_up_to(1), up_to=1, record=rec), ([], []))

    def test_a_decision_resolving_an_open_question_is_an_error(self):
        s9 = BLOCKS["s9"].replace("None identified.",
                                  "| ID | Question | Impact if unresolved | Blocks | Source |\n"
                                  "|---|---|---|---|---|\n| OQ-001 | Which currencies? | scope | FUNC-001 | PM |")
        rec = record_with("Decisions", "| D-01-01 | PRD01 | 4 | EUR only | market | OQ-001 | — |")
        errors, _ = run(build(s9=s9), record=rec)
        self.assertTrue(has(errors, "D-01-01", "resolves OQ-001", "§9 still lists"), errors)

    def test_an_accepted_prd_with_open_questions_is_an_error(self):
        s9 = BLOCKS["s9"].replace("None identified.",
                                  "| ID | Question | Impact if unresolved | Blocks | Source |\n"
                                  "|---|---|---|---|---|\n| OQ-001 | Which currencies? | scope | FUNC-001 | PM |")
        errors, _ = run(build(s9=s9).replace("status: in-progress", "status: accepted"))
        self.assertTrue(has(errors, "`accepted`", "open question"), errors)

    def test_a_record_id_defined_twice_is_an_error(self):
        rec = record_with("Decisions", "| D-01-01 | PRD01 | 1 | OPP-001 | scope | — | — |",
                          "| D-01-01 | PRD01 | 2 | Another | — | — | — |")
        errors, _ = run(build(), record=rec)
        self.assertTrue(has(errors, "D-01-01", "defined twice"), errors)

    def test_a_record_id_numbered_for_another_prd_warns(self):
        rec = record_with("Tensions", "| T-03-01 | PRD01 | brief not validated | accepted | — | — |")
        _, warns = run(build(), record=rec)
        self.assertTrue(has(warns, "T-03-01", "numbered for PRD 03"), warns)

    def test_a_row_naming_an_absent_prd_warns(self):
        rec = record_with("Sources", "| PRD09 | DRD | BR-004 | kept |")
        _, warns = run(build(), record=rec)
        self.assertTrue(has(warns, "names PRD 9", "no such PRD"), warns)

    def test_a_missing_table_warns(self):
        rec = RECORD.split("## Sources")[0]
        _, warns = run(build(), record=rec)
        self.assertTrue(has(warns, "no `## Sources` table"), warns)

    def test_an_enumeration_is_checked(self):
        rec = record_with("Sources", "| PRD01 | DRD | BR-004 | maybe |")
        _, warns = run(build(), record=rec)
        self.assertTrue(has(warns, "gate 'maybe'"), warns)

    def test_the_record_template_is_well_formed(self):
        template = SKILL / "assets" / "TEMPLATE-decision-record.md"
        text = template.read_text(encoding="utf-8")
        text = text[:text.index("<!--")] + text[text.index("-->") + 3:]
        text = text.replace("[Project]", "Demo")
        self.assertEqual(run(build(), record=text), ([], []))

    def test_a_record_passed_alone_is_checked_as_a_record(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "record").mkdir()
            path = root / "record" / "brief-001.md"
            path.write_text(record_with("Sources", "| PRD01 | DRD | BR-004 | maybe |"),
                            encoding="utf-8")
            proc = subprocess.run([sys.executable, str(Path(V.__file__)), str(path)],
                                  capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("gate 'maybe'", proc.stdout)
        self.assertNotIn("section 1", proc.stdout)


class GapsTheReviewFound(unittest.TestCase):
    """Five checks that existed and had a hole — review of PR #20, points 45–49."""

    def test_a_scenario_under_a_notes_heading_does_not_count_for_the_func(self):
        s4 = BLOCKS["s4"].replace(
            "**Nominal scenario:**\n- **WHEN** the user submits their payment\n"
            "- **THEN** the user sees a confirmation\n",
            "### Notes\n\n- **WHEN** the user submits their payment\n- **THEN** the user sees a confirmation\n")
        errors, _ = run(build(s4=s4))
        self.assertTrue(has(errors, "QG-4", "FUNC-001"), errors)

    def test_a_cited_id_is_compared_whole_not_as_a_substring(self):
        s6 = BLOCKS["s6"].replace("None identified.",
                                  "| Item | Reason |\n|---|---|\n| NG-10 — Gift cards | Another PRD |")
        s1 = BLOCKS["s1"] + "\nOut of scope: NG-1.\n"
        _, warns = run(build(s1=s1, s6=s6))
        self.assertTrue(has(warns, "NG-1 is cited", "defined nowhere"), warns)

    def test_an_open_question_without_an_id_warns_like_an_exclusion(self):
        s9 = BLOCKS["s9"].replace("None identified.",
                                  "| ID | Question | Impact if unresolved | Blocks | Source |\n"
                                  "|---|---|---|---|---|\n| Which currencies? | — | scope | FUNC-001 | PM |")
        _, warns = run(build(s9=s9))
        self.assertTrue(has(warns, "open-question row", "no OQ-XXX id"), warns)

    def test_a_brief_reference_does_not_take_a_longer_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "brief").mkdir()
            (root / "prd").mkdir()
            (root / "brief" / "brief10-transfers.md").write_text(
                "---\nstatus: validated\n---\n", encoding="utf-8")
            path = root / "prd" / "prd01-demo.md"
            path.write_text(build().replace("brief: brief-001", "brief: brief-1"), encoding="utf-8")
            self.assertIsNone(V.resolve_brief(path, "brief-1"))
            (root / "brief" / "brief1-shopping.md").write_text("---\nstatus: validated\n---\n",
                                                                encoding="utf-8")
            self.assertEqual(V.resolve_brief(path, "brief-1").name, "brief1-shopping.md")

    def test_claude_code_is_not_a_human_author_but_claude_is(self):
        errors, _ = run(build().replace('author: "Celine Net"', 'author: "Claude Code"'))
        self.assertTrue(has(errors, "QG-9", "author"), errors)
        errors, _ = run(build().replace('author: "Celine Net"', 'author: "Claude Martin"'))
        self.assertFalse(has(errors, "author"), errors)


class LanguageAndLexicon(unittest.TestCase):
    def test_the_ui_lexicon_file_loads_and_covers_both_languages(self):
        self.assertTrue(V.UI_LEXICON.is_file(), V.UI_LEXICON)
        for word in ("onglet", "modal", "popin", "liste déroulante", "case à cocher"):
            with self.subTest(word=word):
                self.assertIsNotNone(V.UI_COMPONENT_RE.search(f"the user opens the {word} here"))
        self.assertIsNone(V.UI_COMPONENT_RE.search("the user confirms the booking"))

    def test_a_translated_header_is_reported_once(self):
        s6 = BLOCKS["s6"].replace("None identified.",
                                  "| Élément | Raison |\n|---|---|\n| NG-001 — Gift cards | Another PRD |")
        _, warns = run(build(s6=s6))
        self.assertTrue(has(warns, "column headers are machine tokens"), warns)
        self.assertFalse(has(warns, "'Élément'", "no NG-XXX id"), warns)


class TheTemplateAndTheValidatorAgree(unittest.TestCase):
    """Review of PR #20, point 60 — the test that was missing when the reference's example and
    the template's token list drifted from the validator: the template's section titles and
    every table header are the validator's constants, read from the file, not trusted."""

    TEMPLATE = SKILL / "assets" / "TEMPLATE-prd.md"

    def tables_of(self, text: str) -> dict[str, list[str]]:
        """Header cells of every table, keyed by the nearest heading above it."""
        lines = text.splitlines()
        heading, out = "", {}
        for i, line in enumerate(lines):
            if line.startswith("#"):
                heading = line.lstrip("#").strip()
                heading = heading.split(". ", 1)[1] if ". " in heading[:4] else heading
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            if line.startswith("|") and set(nxt.strip()) <= set("|-: ") and "-" in nxt:
                out[heading] = V.split_cells(line)
        return out

    def test_section_titles_are_the_validators(self):
        text = self.TEMPLATE.read_text(encoding="utf-8")
        titles = [m.group(2) for m in map(V.SECTION_RE.match, text.splitlines()) if m]
        self.assertEqual(titles, V.SECTIONS + [V.OPTIONAL_SECTIONS[10]])

    def test_every_table_header_is_the_validators_first_form(self):
        text = self.TEMPLATE.read_text(encoding="utf-8")
        tables = self.tables_of(text)
        for title, forms in V.TABLE_HEADERS.items():
            with self.subTest(table=title):
                self.assertIn(title, tables, f"the template has no `{title}` table")
                self.assertEqual(tables[title], forms[0])

    def test_the_subsections_are_the_validators(self):
        text = self.TEMPLATE.read_text(encoding="utf-8")
        subs = [m.group(1) for m in map(V.SUBSECTION_RE.match, text.splitlines()) if m]
        for expected in V.AC_SUBSECTIONS + V.METRIC_SUBSECTIONS:
            self.assertIn(expected, subs)

    def test_the_record_template_headers_are_the_validators(self):
        text = (SKILL / "assets" / "TEMPLATE-decision-record.md").read_text(encoding="utf-8")
        tables = self.tables_of(text)
        for name, header in V.RECORD_TABLES.items():
            self.assertEqual(tables.get(name), header, name)

    def test_the_validator_runs_on_python_3_8(self):
        import ast
        ast.parse((SKILL / "scripts" / "validate_prd.py").read_text(encoding="utf-8"),
                  feature_version=(3, 8))


class ChecksThatHadNoTest(unittest.TestCase):
    """Review of PR #20, point 61 — one negative case per check that nothing exercised."""

    def test_a_missing_h1_is_an_error(self):
        errors, _ = run(build().replace("# Demo\n", "Demo\n", 1))
        self.assertTrue(has(errors, "QG-10", "not an H1"), errors)

    def test_an_h1_differing_from_the_title_is_an_error(self):
        errors, _ = run(build().replace("# Demo\n", "# Demo v2\n", 1))
        self.assertTrue(has(errors, "QG-10", "differs from the `title`"), errors)

    def test_an_unknown_status_is_an_error(self):
        errors, _ = run(build().replace("status: in-progress", "status: draft"))
        self.assertTrue(has(errors, "QG-9", "`status`"), errors)

    def test_an_unknown_complexity_is_an_error(self):
        errors, _ = run(build().replace("complexity: S", "complexity: XXL"))
        self.assertTrue(has(errors, "QG-9", "`complexity`"), errors)

    def test_a_non_iso_date_is_reported(self):
        errors, warns = run(build().replace("date: 2026-08-26", "date: 26/08/2026"))
        self.assertTrue(has(errors + warns, "date"), errors + warns)

    def test_an_email_in_author_is_reported(self):
        errors, warns = run(build().replace('author: "Celine Net"', 'author: "celine@example.com"'))
        self.assertTrue(has(errors + warns, "author"), errors + warns)

    def test_an_id_not_matching_the_filename_is_an_error(self):
        errors, _ = run(build().replace("id: PRD01", "id: PRD02"))
        self.assertTrue(has(errors, "QG-9", "does not match the number in the filename"), errors)

    def test_a_malformed_id_is_an_error(self):
        errors, _ = run(build().replace("id: PRD01", "id: 01"))
        self.assertTrue(has(errors, "QG-9", "must look like PRD01"), errors)

    def test_a_filename_without_a_number_warns(self):
        _, warns = run(build(), filename="demo.md")
        self.assertTrue(has(warns, "QG-9", "filename carries no PRD number"), warns)

    def test_sections_out_of_order_are_an_error(self):
        prd = FRONTMATTER + "".join(BLOCKS[k] for k in ["s1", "s3", "s2", "s4", "s5", "s6", "s7", "s8", "s9"])
        errors, _ = run(prd)
        self.assertTrue(has(errors, "structure", "out of order"), errors)

    def test_a_duplicated_section_is_an_error(self):
        errors, _ = run(build(s9=BLOCKS["s9"] + BLOCKS["s9"]))
        self.assertTrue(has(errors, "structure", "section 9 appears 2 times"), errors)

    def test_a_stray_h2_inside_a_section_warns(self):
        _, warns = run(build(s4=BLOCKS["s4"] + "\n## Notes\n\nsome\n"))
        self.assertTrue(has(warns, "structure", "own heading level"), warns)

    def test_a_translated_section_title_warns(self):
        _, warns = run(build(s2=BLOCKS["s2"].replace("## 2. Personas", "## 2. Personae")))
        self.assertTrue(has(warns, "structure", "section 2 is titled"), warns)

    def test_crlf_line_endings_are_read_like_lf(self):
        self.assertEqual(run(build().replace("\n", "\r\n")), ([], []))

    def test_a_func_without_when_then_is_an_error(self):
        s4 = BLOCKS["s4"].replace("- **WHEN** the user submits their payment\n", "")
        errors, _ = run(build(s4=s4))
        self.assertTrue(has(errors, "QG-4", "FUNC-001"), errors)

    def test_a_missing_metrics_subsection_is_an_error(self):
        s7 = BLOCKS["s7"].replace("### Damage Control\n\nNone identified.\n", "")
        errors, _ = run(build(s7=s7))
        self.assertTrue(has(errors, "QG-8", "Damage Control"), errors)

    def test_a_leftover_token_of_any_prefix_warns(self):
        for token in ("OQ-XXX", "ST-XXX", "NG-XXX", "T-XXX"):
            with self.subTest(token=token):
                _, warns = run(build(s1=BLOCKS["s1"] + f"\nSee {token}.\n"))
                self.assertTrue(has(warns, "template token"), warns)

    def test_an_empty_directory_exits_two(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run([sys.executable, str(Path(V.__file__)), tmp],
                                  capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2, proc.stderr)

    def test_a_directory_validates_every_prd_and_skips_the_index(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "brief").mkdir()
            (root / "prd").mkdir()
            (root / "record").mkdir()
            (root / "brief" / "brief-001.md").write_text("---\nstatus: validated\n---\n", encoding="utf-8")
            (root / "record" / "brief-001.md").write_text(RECORD, encoding="utf-8")
            (root / "prd" / "prd01-demo.md").write_text(build(), encoding="utf-8")
            (root / "prd" / "prd02-other.md").write_text(build().replace("id: PRD01", "id: PRD02"), encoding="utf-8")
            (root / "prd" / "index.md").write_text("# index\n", encoding="utf-8")
            proc = subprocess.run([sys.executable, str(Path(V.__file__)), str(root / "prd")],
                                  capture_output=True, text=True)
        self.assertIn("Validated 2 file(s)", proc.stdout)

    def test_a_crash_on_one_file_does_not_hide_the_others(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "prd").mkdir()
            bad = root / "prd" / "prd03-bad.md"
            bad.write_bytes(b"\xff\xfe\x00 not utf-8 \xff")
            proc = subprocess.run([sys.executable, str(Path(V.__file__)), str(bad)],
                                  capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("validator crashed on this file", proc.stdout)


class TheLastReviewsFindings(unittest.TestCase):
    """Adversarial review before publication — every finding pinned."""

    def test_a_single_asterisk_scenario_label_closes_the_criteria_block(self):
        s4 = build_up_to(3).split("## 4.")[1]
        prd = build_up_to(3).replace("**Nominal scenario:**", "*Nominal scenario:*")
        self.assertEqual(run(prd, up_to=3), ([], []))

    def test_a_translated_parked_header_is_reported_once(self):
        prd = build_up_to(2) + "\n## Parked\n\n| Élément | Type | Pour | Origine |\n|---|---|---|---|\n"
        errors, warns = run(prd, up_to=2)
        self.assertFalse(has(errors, "targets no step"), errors)
        self.assertTrue(has(warns, "`Parked` table has the columns"), warns)

    def test_a_bold_for_cell_is_read(self):
        prd = build_up_to(3) + parked("| rule | BR candidate | **Step 4** | PM |")
        self.assertEqual(run(prd, up_to=3), ([], []))

    def test_a_trailing_period_is_not_a_divergent_definition(self):
        s8 = BLOCKS["s8"].replace("None identified.",
                                  "| Term | Definition |\n|------|-----------|\n"
                                  "| Cart | The items a visitor assembled before paying. |")
        rec = record_with("Vocabulary", "| Cart | The items a visitor assembled before paying | PRD01 |")
        self.assertEqual(run(build(s8=s8), record=rec), ([], []))

    def test_every_sub_table_of_a_subsection_is_shape_checked(self):
        s5 = BLOCKS["s5"].replace(
            "| BR-001 | **Minimum amount:** cart total is 0 € → payment is skipped | FUNC-001 |",
            "| BR-001 | **Minimum amount:** cart total is 0 € → payment is skipped | FUNC-001 |\n\n"
            "#### Delivery\n\n| ID | Applies to | Rule |\n|---|---|---|\n"
            "| BR-002 | FUNC-001 | **Delivery:** the slot is confirmed |")
        errors, _ = run(build(s5=s5))
        self.assertTrue(has(errors, "`Business Rules` table has its columns in the order"), errors)

    def test_a_record_heading_without_a_table_warns(self):
        rec = "# Decision record — Demo\n\n## Decisions\n\n## Tensions\n\n## Vocabulary\n\n## Sources\n"
        _, warns = run(build(), record=rec)
        self.assertTrue(has(warns, "no `## Decisions` table"), warns)

    def test_a_parked_block_after_review_is_an_error(self):
        prd = build().replace("status: in-progress", "status: review") + parked()
        errors, _ = run(prd)
        self.assertTrue(has(errors, "`## Parked` is still in the file"), errors)

    def test_an_empty_or_missing_lexicon_matches_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "ui-lexicon.txt"
            empty.write_text("# nothing yet\n", encoding="utf-8")
            self.assertIsNone(V.load_ui_lexicon(empty).search("the user opens the modal"))
            self.assertIsNone(V.load_ui_lexicon(Path(tmp) / "absent.txt").search("a modal"))

    def test_section_10_placeholders_are_not_criteria_before_step_6(self):
        template = UpToReadsOnlyWhatTheStepsWrote("skeleton_after_step_1").skeleton_after_step_1()
        for step in (4, 5):
            with self.subTest(step=step):
                _, warns = run(template, up_to=step)
                self.assertFalse(has(warns, "CB-001"), warns)
                self.assertFalse(has(warns, "CL-001"), warns)

    def test_a_prd_never_resolves_as_its_own_brief(self):
        errors, _ = run(build().replace("brief: brief-001", "brief: checkout\nrecord: brief-001"),
                        filename="prd01-checkout.md")
        self.assertTrue(has(errors, "QG-11", "does not resolve"), errors)

    def test_record_leftovers_are_reported(self):
        template = (SKILL / "assets" / "TEMPLATE-decision-record.md").read_text(encoding="utf-8")
        errors, warns = run(build(), record=template)
        self.assertTrue(has(errors, "record template's instantiation comment"), errors)
        self.assertTrue(has(warns, "title still holds a placeholder"), warns)

    def test_the_reserved_prd_number_is_not_missing(self):
        rec = record_with("Decisions", "| D-02-01 | PRD02 | 1 | OPP-002 | scope | — | — |")
        _, warns = run(build(), record=rec)
        self.assertFalse(has(warns, "names PRD 2"), warns)
        rec = record_with("Decisions", "| D-05-01 | PRD05 | 1 | OPP-005 | scope | — | — |")
        _, warns = run(build(), record=rec)
        self.assertTrue(has(warns, "names PRD 5", "no such PRD"), warns)

    def test_a_brief_row_is_not_numbered_against_a_prd(self):
        rec = record_with("Tensions", "| T-01-01 | brief-001 | KR without baseline | open | — | — |")
        _, warns = run(build(), record=rec)
        self.assertFalse(has(warns, "numbered for PRD"), warns)

    def test_a_record_alone_prints_the_first_step_card(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "record").mkdir()
            path = root / "record" / "brief-001.md"
            path.write_text(RECORD, encoding="utf-8")
            proc = subprocess.run([sys.executable, str(Path(V.__file__)), str(path)],
                                  capture_output=True, text=True)
        self.assertIn("Next: Step 1 — Frame & scope.", proc.stdout)
        self.assertIn("Validated 1 file(s)", proc.stdout)


class TheBriefIsNotAWall(unittest.TestCase):
    def test_no_brief_warns_without_failing(self):
        prd = build().replace("brief: brief-001", "brief: none\nrecord: brief-001")
        errors, warns = run(prd)
        self.assertEqual(errors, [], errors)
        self.assertTrue(has(warns, "QG-11: no brief"), warns)

    def test_no_brief_and_no_record_is_an_error(self):
        errors, _ = run(build().replace("brief: brief-001", "brief: none"))
        self.assertTrue(has(errors, "`record` must name"), errors)

    def test_the_record_defaults_to_the_brief(self):
        self.assertEqual(run(build()), ([], []))

    def test_qg11_names_the_record(self):
        _, warns = run(build(), brief_status="draft")
        self.assertTrue(has(warns, "QG-11", "project record"), warns)


class V173Additions(unittest.TestCase):
    """v1.7.3 — honest complexity message, punctuation-insensitive brief, italic personas,
    and the QG-2 lexical half (UI components in journeys and FUNCs)."""

    def test_complexity_message_names_the_func_count_alone(self):
        _, warns = run(build().replace("complexity: S", "complexity: XL"))
        self.assertTrue(has(warns, "complexity is XL", "grid says S", "FUNC count alone"), warns)

    def test_a_brief_id_with_different_punctuation_resolves(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "brief").mkdir()
            (root / "prd").mkdir()
            (root / "brief" / "brief001-shopping.md").write_text(
                "---\nstatus: validated\n---\n\n# Brief\n", encoding="utf-8")
            path = root / "prd" / "prd01-demo.md"
            path.write_text(build(), encoding="utf-8")
            findings: list[V.Finding] = []
            V.check_prd(path, findings, None)
            self.assertFalse(has([f.msg for f in findings], "does not resolve"),
                             [f.msg for f in findings])

    def test_personas_in_italics_are_content(self):
        s2 = BLOCKS["s2"].replace("Every visitor going through checkout.",
                                  "*Elodie, 38, books for her family.*")
        _, warns = run(build(s2=s2))
        self.assertFalse(has(warns, "Personas is empty"), warns)

    def test_a_ui_component_in_a_journey_step_warns(self):
        s3 = BLOCKS["s3"].replace("1. The user submits their payment",
                                  "1. The user submits their payment in a modal")
        _, warns = run(build(s3=s3))
        self.assertTrue(has(warns, "QG-2", "journey step", "modal"), warns)

    def test_a_ui_component_in_a_func_warns_and_names_the_func(self):
        s4 = BLOCKS["s4"].replace("the user pays for the order they assembled.",
                                  "the user pays for the order in a centered modale.")
        _, warns = run(build(s4=s4))
        self.assertTrue(has(warns, "QG-2", "FUNC-001", "modale"), warns)

    def test_a_ui_word_in_a_fence_or_the_glossary_does_not_warn(self):
        s8 = BLOCKS["s8"].replace(
            "None identified.",
            "| Term | Definition |\n|------|-----------|\n| Onglet | the DRD's tab component |")
        s3 = BLOCKS["s3"] + "\n```\nthe mockup shows a modal here\n```\n"
        _, warns = run(build(s3=s3, s8=s8))
        self.assertFalse(has(warns, "QG-2"), warns)


if __name__ == "__main__":
    unittest.main(verbosity=2)
