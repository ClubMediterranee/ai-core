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

| ID | Metric | Threshold |
|----|--------|-----------|
| LGM-001 | checkout conversion | +5 pts |

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


def run(prd: str, brief_status: str = "validated") -> tuple[list[str], list[str]]:
    """Validate one PRD in a throwaway docs tree. Returns (error messages, warning messages)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "brief").mkdir()
        (root / "prd").mkdir()
        (root / "brief" / "brief-001.md").write_text(
            f"---\nstatus: {brief_status}\n---\n\n# Brief 001\n", encoding="utf-8")
        path = root / "prd" / "prd01-demo.md"
        path.write_text(prd, encoding="utf-8")

        findings: list[V.Finding] = []
        V.check_prd(path, findings)
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

    def test_country_variant_tags_are_content_not_placeholders(self):
        rule = ("**Minimum amount:** cart total is 0 € → payment is skipped. "
                "Variants : [FR] 25 € / [DE] 30 €")
        s5 = BLOCKS["s5"].replace(
            "**Minimum amount:** cart total is 0 € → payment is skipped | FUNC-001 |",
            rule + " | FUNC-001 |")
        s4 = BLOCKS["s4"].replace(
            "- **BR-001** — **Minimum amount:** cart total is 0 € → payment is skipped",
            "- **BR-001** — " + rule)
        errors, warns = run(build(s4=s4, s5=s5))
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
    def example_tables(text: str) -> dict[str, list[list[str]]]:
        """The worked example of each criterion type, as parsed cells.

        Every `| ID | … |` table found in a fenced block is read; the later one of a type wins, so
        a `Format:` skeleton is superseded by the `Example:` that follows it.
        """
        tables: dict[str, list[list[str]]] = {}
        block: list[str] | None = None
        for line in text.splitlines():
            if line.startswith("```"):
                if block is not None:
                    rows = [ln for ln in block if ln.strip().startswith("|")]
                    if len(rows) >= 3 and rows[0].strip().startswith("| ID |"):
                        cells = [V.split_cells(r) for r in rows[2:]]   # skip header + separator
                        kind = V.ID_RE.search(cells[0][0])
                        if kind:
                            tables[kind.group(1)] = cells
                    block = None
                else:
                    block = []
                continue
            if block is not None:
                block.append(line)
        return tables

    def test_every_example_row_validates(self):
        tables = self.example_tables(self.REF.read_text(encoding="utf-8"))
        self.assertEqual(sorted(tables), ["BR", "ERR", "PERM", "ST"],
                         "the reference must carry one worked example per criterion type")

        def table(kind: str, header: str) -> str:
            width = header.count("|") - 1
            return "\n".join([header, "|---" * width + "|"]
                              + ["| " + " | ".join(c) + " |" for c in tables[kind]])

        s5 = "\n".join([
            "\n## 5. Acceptance Criteria\n",
            "### Business Rules\n",
            table("BR", "| ID | Rule | Applies to |"),
            "\n### States & Transitions\n",
            table("ST", "| ID | Object | States | Allowed transitions | Blocked transitions |"),
            "\n### Permissions\n",
            table("PERM", "| ID | Actor | Action | Allowed condition | Blocked condition |"),
            "\n### Error Scenarios\n",
            table("ERR", "| ID | Failure mode | Expected behavior |"),
            ""])

        # the §4 side of the mirror, linearised exactly as the reference prescribes
        bullets: dict[str, list[str]] = {}
        for c in tables["BR"]:
            for func in V.FUNC_RE.findall(c[-1]):
                bullets.setdefault(func, []).append(f"- **{c[0]}** — {c[1]}")
        host = sorted(bullets)[0]          # the cross-cutting criteria hang off one FUNC
        bullets[host] += [f"- **{c[0]}** — {c[1]}" for c in tables["ERR"]]
        bullets[host] += [f"- **{c[0]}** — {c[1]} — states: {c[2]}" for c in tables["ST"]]
        bullets[host] += [f"- **{c[0]}** — {c[1]} : {c[2]}" for c in tables["PERM"]]

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


class BriefStatus(unittest.TestCase):
    """An unvalidated brief is a signal, not a wall — see references/REF-brief-contract.md."""

    def test_an_unvalidated_brief_warns_without_failing(self):
        errors, warns = run(build(), brief_status="draft")
        self.assertEqual(errors, [], errors)
        self.assertTrue(has(warns, "QG-11", "not validated"), warns)


if __name__ == "__main__":
    unittest.main(verbosity=2)
