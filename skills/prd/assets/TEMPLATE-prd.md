---
id: PRD01
title: "[Product Name]"
version: "1.0"
status: in-progress
complexity: M
date: YYYY-MM-DD
author: "Firstname Lastname"
brief: brief-XXX
---

<!--
INSTANTIATION NOTES — delete this whole comment block in the generated PRD.

This file is a skeleton, not a description of one: Step 1 copies it verbatim into
`{DOCS_ROOT}/prd/prd<NN>-<short-name>.md`, and each later step fills its section IN PLACE by
replacing the [placeholders]. Nothing here is illustrative — every line you leave behind ends up
in the PRD, so a placeholder still visible at the quality gate is an unfinished section.

Frontmatter — the 8 required fields, all validated by `scripts/validate_prd.py` (QG-9):
  id          `PRD<NN>`, matching the number in the filename
  title       repeated verbatim as the H1 below (QG-10)
  version     "1.0" on first write
  status      in-progress → review (quality gate passed) → accepted (human sign-off)
  complexity  S / M / L / XL — set at Step 6
  date        YYYY-MM-DD
  author      the PM running the skill, name only
  brief       the source brief this PRD translates

Language: the PRD body is written in the PM's language, but section titles, id prefixes and the
structural markers "None identified." / "None defined." stay exactly as written here. The validator
and the downstream `spec` skill match on them.

Sections that stay empty: write "None identified." (§5 States, §5 Permissions, §7 Damage Control)
or "None defined." (§7 Leading Metrics) rather than deleting the section — QG-8 checks that the
three §7 subsections are present, and an absent section is indistinguishable from a forgotten one.
-->

# [Product Name]

*Translated from [brief-XXX]. Defines what must be built, for whom, to what acceptance bar — and nothing else.*

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

[One short paragraph describing the persona, from the information in the brief. If this PRD covers
a cross-cutting step that every user of the flow goes through, say so and describe that
population — do not invent a persona for it.]

---

## 3. User Journeys

*End-to-end flows anchored on [OPP-XXX]. One journey carries one user goal, and the heading states that goal.*

### Journey 1 — [The goal: what the user came to accomplish]

*Precondition:* [what must already be true before step 1 — delete this line if the journey needs none]

1. [Step 1 — entry point / trigger]
2. [Step 2 — main action]
3. [Step 3 — optional variation, prefixed "Variation:" — flat numbering, no 2a/2b branches]
4. [Step 4 — the goal reached]

*Capabilities revealed:* FUNC-001, FUNC-002

### Journey 2 — [The goal: what the user came to accomplish]

1. [Step 1 — entry point / trigger]
2. [Step 2 — main action]
3. [Step 3 — optional variation, prefixed "Variation:" — flat numbering, no 2a/2b branches]
4. [Step 4 — the goal reached]

*Capabilities revealed:* FUNC-003

---

## 4. Functional Specifications

*Capabilities focus on WHAT exists and WHAT the user can do.*

*Order follows the first appearance of each capability in the journeys, cross-cutting ones last.
Ids are identifiers, not ranks: never renumber. A merged FUNC leaves its id retired and the gap
stays — reading order is the position below, not the number.*

### FUNC-001 — [Capability — "Users can [verb] [object]", or "Users benefit from [X] when [condition]" for a system-triggered one]

**Actor:** [persona — if relevant]

**Capability:** [1 sentence: what the user can do.]

**Acceptance criteria:**

- **BR-001** — [the `Rule` cell of BR-001, copied verbatim from §5]
- **ERR-001** — [the `Failure mode` cell of ERR-001, copied verbatim from §5]

**Nominal scenario:**
- **GIVEN** [prerequisite state — keep this line only when it is not obvious from the WHEN]
- **WHEN** [triggering condition]
- **THEN** [observable result]
- **AND** [additional result if needed]

### FUNC-002 — [Capability — "Users can [verb] [object]"]

**Actor:** [persona — if relevant]

**Capability:** [1 sentence: what the user can do.]

**Acceptance criteria:**

- **BR-002** — [the `Rule` cell of BR-002, copied verbatim from §5]

**Nominal scenario:**
- **WHEN** [triggering condition]
- **THEN** [observable result]
- **AND** [additional result if needed]

---

## 5. Acceptance Criteria

### Business Rules

*Each rule opens with a short bold recap naming the case handled. Past ~10 rules, group them into
`#### ` thematic sub-sections by business domain — never by FUNC, and never at `###` or `##`.*

| ID | Rule | Applies to |
|----|------|-----------|
| BR-001 | **[Recap — the case handled]:** [condition] → [expected behavior] | FUNC-001, FUNC-002 |

### States & Transitions

| ID | Object | States | Allowed transitions | Blocked transitions |
|----|--------|--------|--------------------|--------------------|
| ST-001 | [Object] | [States] | [Allowed] | [Blocked] |

*Write "None identified." if no lifecycle object exists.*

### Permissions

| ID | Actor | Action | Allowed condition | Blocked condition |
|----|-------|--------|-------------------|-------------------|
| PERM-001 | [Actor] | [Action] | [Condition allowing the action] | [Condition blocking the action] |

*Write "None identified." if no access restriction exists.*

### Error Scenarios

| ID | Failure mode | Expected behavior |
|----|-------------|-------------------|
| ERR-001 | [Condition that triggers the failure] | [What the product must do] |

---

## 6. Out of Scope

*What is explicitly not built — and why. First line of defense against scope creep.*

| Item | Reason |
|------|--------|
| [NG-001] [Excluded capability] | [Why out of scope] |
| [NG-002] [Excluded capability] | [Why out of scope] |

---

## 7. Metrics

*Three lenses on outcome: what to achieve (LGM), what not to break (DC), and what signals predict adoption before KRs are measurable (LDM).*

### Lagging Metrics

*Imported from the brief's Desired Outcomes. These are the success criteria for the initiative.*

| ID | Metric | Threshold |
|----|--------|-----------|
| LGM-001 | [Imported from brief] | [Numeric target] |

### Damage Control

*Existing metrics that must not regress under a threshold. Write "None identified." if not applicable.*

| ID | Metric | Current baseline | Max acceptable degradation |
|----|--------|-----------------|---------------------------|
| DC-001 | [Existing metric name] | [Current value] | [Numeric threshold] |

### Leading Metrics

*Observable user behaviors that predict adoption — defined here in the PRD. Write "None defined." if not applicable.*

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

*Product ambiguities unresolved at PRD write time. Each one blocks work that depends on it — answer it, integrate into the relevant FUNC or section, then remove the row.*

| ID     | Question | Impact if unresolved | Blocks | Source |
|--------|----------|---------------------|--------|--------|
| OQ-001 | [Question] | [What changes depending on the answer] | [FUNC / section] | [FUNC-XXX / BR-XXX / Journey — name] |

---

## 10. Constraints

*Conditions this PRD inherits rather than defines — a BR is a rule this PRD decides, a constraint
is a boundary it accepts. Keep only the constraints that actually shape a FUNC or a BR here.
Delete this section and its Table of Contents entry if the PRD inherits none.*

### Business

- **CB-001** [Dependency on another PRD, an existing platform behaviour, or an entry point owned elsewhere]

### Legal / Compliance

- **CL-001** [What a locale or a regulation imposes]
