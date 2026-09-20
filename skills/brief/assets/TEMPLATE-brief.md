---
id: BRIEF01
title: "[Initiative or product area]"
version: "1.0"
status: in-progress
date: YYYY-MM-DD
author: "Firstname Lastname"
# amended_from: brief<NN>-<short-name>
---

<!--
INSTANTIATION NOTES — delete this whole comment block in the generated brief.

Step 0's [C] copies this skeleton verbatim into `{DOCS_ROOT}/brief/brief<NN>-<short-name>.md`; each
later step fills its own section IN PLACE, in as few edits as possible, once the PM has chosen [C]. This
file is the only state: a section still holding placeholders is a step not yet validated.

Frontmatter
  id            `BRIEF<NN>`, matching the number in the filename
  title         the initiative or the product area, never a solution — repeated verbatim as the H1
  version       "1.0" — an amendment is a new file, not a new version
  date          the day the file is created
  status        in-progress → review (set by the skill) → validated (a person, by hand)
  author        the PM running the skill, name only
  amended_from  Amendment only — the parent brief's filename stem; delete the line otherwise

Language — kept exactly as written here, in English: section titles and sub-headings, table column
headers, ids, frontmatter keys and status values, the markers "None identified." and "Not
established". Everything else follows the PM's language: labels (« Cause racine : »), cell
contents, values (« élevé », « verbatim utilisateur »), reading notes, the words of the shapes.

Ids are written without brackets (PER-001, OPP-001, T-01). The validation-plan block of §2 is
deleted when confidence is High, like "Painted Door".

An empty subsection carries "None identified." — an absent section is indistinguishable from a
forgotten one. "Painted Door" is the one conditional subsection: delete it when confidence is High
and demand is not in doubt.

§1–§6 are the commitment; §7 is outside it — nothing in §1–§6 relies on an item of §7. A §7 row
"For: Step N" is transient: that step brings the item back and its [C] removes the row; only
"/prd" and "Future brief" rows remain in a finished brief.

Length: §1 within ten lines; one sentence per tension impact; evidence tables as long as the
evidence.
-->

# [Initiative or product area]

*Context:* [revamp / new product / migration / incremental evolution — one line on the initiative]

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Key Problem & Persona](#2-key-problem--persona)
3. [Inputs & Evidence](#3-inputs--evidence)
4. [Desired Outcomes](#4-desired-outcomes)
5. [Opportunities & Scope](#5-opportunities--scope)
6. [Open Tensions](#6-open-tensions)
7. [Parked](#7-parked)

---

## 1. Executive Summary

> **Central value:** [One sentence — what becomes possible for the persona that was not: a transformation, not a capability or a feature.]

**Key problem:** [PER-001] cannot [critical action] because [observable root cause].

**Scope:** [OPP-001 · OPP-002 · …]

---

## 2. Key Problem & Persona

> **[PER-001]** cannot **[critical action]** because **[observable root cause]**, which results in **[measurable or observable consequence]**.

[One paragraph: what happens today, who bears the cost, how it accumulates. Evidence-based — cite the sources. No solution framing.]

**Root cause:** [The structural reason the problem persists — or "Not established", with the candidates and the T-XX that carries it]

**Why now:** [What changed recently — behaviour, competition, technical capacity, strategy]

**Workaround:** [What people do today to get around it]

**Adoption risk:** [What could keep the persona from changing behaviour even with a solution in hand]

**Consequence:** [What happens to the person who lives it if it is never solved]

### Persona

**[PER-001] —** [One paragraph: why this persona and not another — cite the sources. Or: no persona — audience [description].]

| Field | Content |
|---|---|
| Triggering situation | When [context], [persona] needs to [action] but [friction]. |
| Functional job | When [situation], I want to [action], so that [result]. |
| Emotional job | To feel: [state]. To avoid: [emotional friction]. |

### Signals

| Signal | Type | Source | Grade |
|---|---|---|---|
| [Signal 1] | [User verbatim · Observed behaviour · Indirect signal · Benchmark / analogy · Intuition / deduction] | [Origin, with location] | [Strong · Medium · Weak · Hypothesis] |

*Emerging pattern:* [Convergence statement — or "no convergence yet"]

### Confidence

**Confidence level:** [High / Medium / Hypothetical]

[Below High — minimal validation plan:]
- Signal to collect: [what]
- Method: [how]
- Acceptable delay: [when]

---

## 3. Inputs & Evidence

### Documents

| Document | Type | Status | Notes |
|---|---|---|---|
| [Document name] | [Quali / Quanti / Personas / JTBD / Kick-off / CRO / Session replay / Competitive / Oral report / …] | [Provided / Partial / Missing] | [Notes] |

### Research Links

| Reference | Status | Link |
|---|---|---|
| [Title or description] | [validated / hypothesis / to link] | [URL or "to link"] |

---

## 4. Desired Outcomes

### Lagging Metrics

| Metric | Baseline (T0) | Threshold | Pillar / OKR |
|---|---|---|---|
| [Metric 1] | [Current value, or TBD + who can supply it] | [Numeric target or direction, with its timeframe] | [Pillar / OKR] |

### Damage Control

| Indicator | Baseline (T0) | Threshold |
|---|---|---|
| [Indicator 1] | [Current value] | [Maximum acceptable degradation — or "to be set once T0 is known"] |

---

## 5. Opportunities & Scope

*Ids are identifiers, not ranks: a gap left by a removed opportunity is normal — reading order is the Priority column. Each retained opportunity generates one PRD.*

### Opportunities

| ID | Opportunity | Anchor | Key problem anchor | Priority | Depends on |
|---|---|---|---|---|---|
| OPP-001 | [Infinitive verb + object + context / moment] | [Key Problem / Redesign / Market] | [Element of the key problem addressed, or —] | 1 | — |

### Success Signal

**[PER-001]** will go from **[current observable state]** to **[target observable state]**, measurable by **[indicator or proxy]**.

*Anchored on:* [OPP-001]

### Cuts

| Item | Reason |
|---|---|
| [Cut 1] | [Why it is out of this iteration] |

### Constraints

| Type | Constraint |
|---|---|
| [Technical / Business / Legal / Compliance / Stakeholder] | [Fixed constraint, or who must be aligned before /prd] |

### Painted Door

[What an unbuilt version of the product would look like, which behavioural signal it would generate, and what threshold would justify building it.]

---

## 6. Open Tensions

**Ready for /prd:** [yes / not yet — what to collect first]

*To be resolved or knowingly carried before `/prd`.*

| ID | Tension | Impact depending on the resolution | Blocks |
|---|---|---|---|
| T-01 | [What is open — challenged, not established, or undecided] | [One sentence: what changes depending on the answer] | [What /prd cannot start on until this is resolved — OPP-XXX, a §4 metric, an undecided lever named in words — or — when it can be carried] |

---

## 7. Parked

*Outside this brief's commitment. What came up and belongs elsewhere — kept so nothing is lost. For `/prd`, these are candidates to judge against §1–§6, never requirements.*

| Item | Kind | For | Origin |
|---|---|---|---|
| [What was parked, in the PM's words] | [Solution / Capability / Need / Rule detail / Problem / Lever / Constraint / Signal] | [Step N / /prd / Future brief] | [Who brought it, at which step — and the signals behind it, if any] |

