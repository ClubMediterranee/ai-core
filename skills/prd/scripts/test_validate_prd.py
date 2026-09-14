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
  * and the worked examples of `REF-acceptance-criteria.md` are executed rather than trusted — the
    reference cannot drift away from the validator without a red test.

Dependency-free: stdlib only, fixtures written to a temporary directory.

Usage:
    python3 test_validate_prd.py          # or: python3 -m unittest test_validate_prd -v
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
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


def build(**overrides: str) -> str:
    """The nominal PRD, with any block replaced wholesale."""
    blocks = dict(BLOCKS)
    unknown = set(overrides) - set(blocks)
    assert not unknown, f"unknown block(s): {sorted(unknown)}"
    blocks.update(overrides)
    return FRONTMATTER + "".join(blocks[k] for k in ORDER)


def run(prd: str, brief_status: str = "validated",
        up_to: int | None = None) -> tuple[list[str], list[str]]:
    """Validate one PRD in a throwaway docs tree. Returns (error messages, warning messages).

    `up_to` is the `--up-to N` of the command line: only what Steps 1..N wrote is read."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "brief").mkdir()
        (root / "prd").mkdir()
        (root / "brief" / "brief-001.md").write_text(
            f"---\nstatus: {brief_status}\n---\n\n# Brief 001\n", encoding="utf-8")
        path = root / "prd" / "prd01-demo.md"
        path.write_text(prd, encoding="utf-8")

        findings: list[V.Finding] = []
        V.check_prd(path, findings, up_to)
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

    REF = Path(__file__).resolve().parent.parent / "references" / "REF-acceptance-criteria.md"

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

    TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "TEMPLATE-prd.md"

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
        s4 = BLOCKS["s4"].replace(
            "- **BR-001** — **Minimum amount:** cart total is 0 € → payment is skipped\n"
            "- **ERR-001** — Payment is declined by the bank\n",
            "[filled at Step 4]\n")
        prd = build(s4=s4)
        self.assertEqual(run(prd, up_to=3), ([], []))
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
        prd = build(s3=BLOCKS["s3"].replace("*Capabilities revealed:* FUNC-001",
                                            "*Capabilities revealed:* TBD"))
        code, out = self.cli(prd, "--up-to", "2")
        self.assertEqual(code, 0, out)
        self.assertIn("up to Step 2", out)
        code, _ = self.cli(prd, "--up-to", "3")
        self.assertEqual(code, 1)




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
