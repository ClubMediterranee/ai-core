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

---

## 1. Executive Summary

**Source:** brief-XXX — "[Brief title]"

**Opportunity addressed:** [OPP-XXX — verbatim from brief. → See brief-XXX for full problem space context.]

**Solution:** [1-2 sentences: what approach, what scope.]

---

## 2. Personas

[One short paragraph describing the persona, from the information in the brief.]

---

## 3. User Journeys

*End-to-end flows anchored on [OPP-XXX].*

### Journey 1 — [Scenario name]

1. [Step 1 — entry point]
2. [Step 2 — main action]
3. [Step 3 — variation or edge case]
4. [Step 4 — outcome]

*Capabilities revealed:* FUNC-001, FUNC-002

### Journey 2 — [Scenario name]

1. [Step 1 — entry point]
2. [Step 2 — main action]
3. [Step 3 — variation or edge case]
4. [Step 4 — outcome]

*Capabilities revealed:* FUNC-003

---

## 4. Functional Specifications

*Capabilities focus on WHAT exists and WHAT the user can do.*

### FUNC-001 — [Capability — "Users can [verb] [object]"]

**Actor:** [persona — if relevant]
**Capability:** [1 sentence: what the user can do.]
**Acceptance criteria:** [ids defined in §5 — e.g. BR-001, ERR-001]

**Nominal scenario:**
- **WHEN** [triggering condition]
- **THEN** [observable result]
- **AND** [additional result if needed]

### FUNC-002 — [Capability — "Users can [verb] [object]"]

**Actor:** [persona — if relevant]
**Capability:** [1 sentence: what the user can do.]
**Acceptance criteria:** [ids defined in §5]

**Nominal scenario:**
- **WHEN** [triggering condition]
- **THEN** [observable result]
- **AND** [additional result if needed]

---

## 5. Acceptance Criteria

### Business Rules

| ID | Rule | Applies to |
|----|------|-----------|
| BR-001 | [Condition] → [Expected behavior] | FUNC-001, FUNC-002 |

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
