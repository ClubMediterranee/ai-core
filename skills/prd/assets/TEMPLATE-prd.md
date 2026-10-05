---
id: PRD01
title: "[Product Name]"
version: "1.0"
status: in-progress
complexity: M
date: YYYY-MM-DD
author: "Firstname Lastname"
brief: brief-XXX
record: brief-XXX
---

<!--
INSTANTIATION NOTES — delete this whole comment block in the generated PRD.

This file is a skeleton, not a description of one: Step 1 copies it verbatim into
`{DOCS_ROOT}/prd/prd<NN>-<short-name>.md`, and each later step fills its section IN PLACE by
replacing the [placeholders] — but only once the PM has chosen [C] at that step's gate. Nothing is
written here before a validation, a `## Parked` row excepted. Nothing here is illustrative — every line you leave behind ends up
in the PRD, so a placeholder still visible at the quality gate is an unfinished section.

Frontmatter — the 8 required fields, plus `record` (required when `brief` is `none`), validated by
`scripts/validate_prd.py` (QG-9):
  id          `PRD<NN>`, matching the number in the filename
  title       repeated verbatim as the H1 below (QG-10)
  version     "1.0" on first write
  status      in-progress → review (quality gate passed) → accepted (human sign-off, §9 empty —
              each last question answered gets its Decisions row in the record)
  complexity  S / M / L / XL — set at Step 6
  date        YYYY-MM-DD
  author      the PM running the skill, name only
  brief       the source brief this PRD translates, as its filename stem (e.g. brief01-checkout)
              — never its frontmatter id: the validator resolves it on disk in {DOCS_ROOT}/brief/.
              `none` when the PRD was framed without a brief: §1's Source line then reads
              "no brief — frame confirmed with the PM at Step 1:" followed by the problem, the
              persona, the opportunities and the KRs, so the PRD stands on its own
  record      the project's decision record, as its filename stem in {DOCS_ROOT}/record/ — the
              brief's stem by default; required when `brief` is `none`

Language: the PRD body is written in the PM's language, but the machine tokens listed in SKILL.md
(*Language Adaptation*) stay exactly as written here — the validator and the downstream `spec`
skill match on them.

Section 10 Constraints stays in every PRD — its legend states the baseline every capability
inherits; write "None identified." under a heading when nothing is inherited there.

Sections that stay empty: write "None identified." (§5 States, §5 Permissions, §6, §7 Lagging Metrics,
§7 Damage Control, §8, §9, each heading of §10) or "None defined." (§7 Leading Metrics) rather than deleting the section — QG-8
checks that the three §7 subsections are present, and an absent section is indistinguishable from a
forgotten one. A brief with no Desired Outcomes leaves §7 Lagging at "None identified." and a
Tensions row in the decision record; it is not a reason to fail the gate.

`## Parked`, at the very end, is not a section of the PRD: unnumbered, outside the table of contents,
scratch. A row is written the moment an item is parked for a later step (`For: Step N`, 2–6), removed
at that step's [C] once the item has its home, and the whole block is deleted when the quality gate
passes. The validator fails a row whose step's gate has already passed.
-->

# [Product Name]

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Personas](#2-personas)
3. [User Journeys](#3-user-journeys)
4. [Functional Specifications](#4-functional-specifications)
5. [Acceptance Criteria](#5-acceptance-criteria)
6. [Out of Scope](#6-out-of-scope)
7. [Metrics](#7-metrics)
8. [Glossary](#8-glossary)
9. [Open Questions](#9-open-questions)
10. [Constraints](#10-constraints)

---

## 1. Executive Summary

**Source:** brief-XXX — "[Brief title]"

**Opportunity addressed:** [OPP-XXX — verbatim from brief. → See brief-XXX for full problem space context.]

**Solution:** [1-2 sentences: what approach, what scope.]

---

## 2. Personas

[One short paragraph per persona confirmed at Step 2, from the information in the brief. If this
PRD covers a cross-cutting step that every user of the flow goes through, say so and describe that
population as one — do not invent a persona for it.]

---

## 3. User Journeys

### Journey 1 — [Short name for this flow]

*Goal:* [the confirmed goal this journey serves — one accomplishment infinitive + object + the stake that makes "satisfied" testable. Never an activity verb, never the path; the implicit subject is the actor. The last step must reach it — never reword the goal to fit the flow]

*Precondition:* [what must already be true before step 1 — delete this line if the journey needs none]

1. [Step 1 — entry point / trigger]
2. [Step 2 — main action]
3. [Step 3 — optional variation, prefixed "Variation:" — flat numbering, no 2a/2b branches]
4. [Step 4 — the goal reached]

*Capabilities revealed:* TBD

### Journey 2 — [Short name for this flow]

*Goal:* [the confirmed goal this journey serves — one accomplishment infinitive + object + the stake that makes "satisfied" testable. Never an activity verb, never the path; the implicit subject is the actor. The last step must reach it — never reword the goal to fit the flow]

1. [Step 1 — entry point / trigger]
2. [Step 2 — main action]
3. [Step 3 — optional variation, prefixed "Variation:" — flat numbering, no 2a/2b branches]
4. [Step 4 — the goal reached]

*Capabilities revealed:* TBD

---

## 4. Functional Specifications

*Ids are identifiers, not ranks: a gap left by a merged FUNC is normal — reading order is the
position, not the number.*

### FUNC-001 — [Capability, in the PM's language — "Users can [verb] [object]" / « L'utilisateur.rice peut [verbe] [objet] », or "Users benefit from [X] when [condition]" for a system-triggered one]

**Actor:** [persona — if relevant]

**Capability:** [keep this line only when it adds a boundary the title cannot carry — the precise object, the scope edge; delete it when it would restate the title. One sentence; an enumeration or a condition is rule detail for Step 4.]

**Acceptance criteria:**

- [Step 3 leaves this list empty — Step 4 back-fills one bullet per applicable criterion (BR, ERR, ST, PERM, CB/CL), its cell per the linearisation table of REF-acceptance-criteria.md. Delete this line when deriving the FUNC.]

**Nominal scenario:**
- **GIVEN** [prerequisite state — keep this line only when it is not obvious from the WHEN]
- **WHEN** [triggering condition]
- **THEN** [observable result]
- **AND** [additional result if needed]

### FUNC-002 — [Capability, in the PM's language — "Users can [verb] [object]" / « L'utilisateur.rice peut [verbe] [objet] »]

**Actor:** [persona — if relevant]

**Capability:** [keep this line only when it adds a boundary the title cannot carry — the precise object, the scope edge; delete it when it would restate the title. One sentence; an enumeration or a condition is rule detail for Step 4.]

**Acceptance criteria:**

- [Step 3 leaves this list empty — Step 4 back-fills one bullet per applicable criterion (BR, ERR, ST, PERM, CB/CL), its cell per the linearisation table of REF-acceptance-criteria.md. Delete this line when deriving the FUNC.]

**Nominal scenario:**
- **WHEN** [triggering condition]
- **THEN** [observable result]
- **AND** [additional result if needed]

---

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

---

## 6. Out of Scope

*What is explicitly not built — and why.*

| Item | Reason |
|------|--------|
| NG-001 — [Excluded capability] | [Why out of scope] |
| NG-002 — [Excluded capability] | [Why out of scope] |

---

## 7. Metrics

*Three lenses on outcome: what to achieve (LGM), what not to break (DC), and what signals predict adoption before KRs are measurable (LDM).*

### Lagging Metrics

*Imported from the brief's Desired Outcomes — the initiative's success criteria.*

| ID | Metric | Baseline (T0) | Threshold |
|----|--------|---------------|-----------|
| LGM-001 | [Imported from brief] | [Current value, or TBD] | [Numeric target] |

### Damage Control

*Existing metrics that must not regress below a threshold.*

| ID | Metric | Current baseline | Max acceptable degradation |
|----|--------|-----------------|---------------------------|
| DC-001 | [Existing metric name] | [Current value] | [Numeric threshold] |

### Leading Metrics

*Observable user behaviors that predict adoption.*

| ID | Observable behavior | Collection method | Review cadence |
|----|---------------------|-----------------|----------------|
| LDM-001 | [User behavior that predicts adoption] | [How it is collected] | [weekly / monthly / per release] |

---

## 8. Glossary

*Shared vocabulary — one definition per term.*

| Term   | Definition |
|--------|-----------|
| [Term] | [Precise definition in the context of this product.] |

---

## 9. Open Questions

*Unresolved product ambiguities — each blocks the work its `Blocks` column names; answered means integrated, then the row is removed.*

| ID     | Question | Impact if unresolved | Blocks | Source |
|--------|----------|---------------------|--------|--------|
| OQ-001 | [Question] | [What changes depending on the answer] | [FUNC / Journey / section] | [FUNC-XXX / BR-XXX / Journey — name] |

---

## 10. Constraints

*Conditions this PRD inherits rather than defines — a BR is a rule this PRD decides, a constraint
a boundary it accepts. The legal and accessibility baseline — GDPR, accessibility law, consumer law —
applies to every capability without being restated; a `CL` is written where it shapes one, and a
BR may go beyond it.*

### Business

- **CB-001** [Dependency on another PRD, an existing platform behaviour, or an entry point owned elsewhere]

### Legal / Compliance

- **CL-001** [What a locale or a regulation imposes]

---

## Parked

*Scratch for the steps to come — nothing here is validated. A row is written the moment an item is parked; it is consumed by its step's `[C]`; the block is deleted when the quality gate passes.*

| Item | Kind | For | Origin |
|---|---|---|---|
