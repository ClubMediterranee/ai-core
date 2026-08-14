---
name: ref-user-journeys
description: >
  Methodological reference for deriving and validating user journeys
  (userflows). Covers granularity, outcome altitudes, the skeleton-based
  sufficiency check, guided derivation, variation routing, and validation
  criteria.
type: reference
---

# User Journeys — Methodological Reference

A user journey in the PRD is a **userflow** — it describes what the user does and gets, at the level of product behavior. It is not a **wireflow** — which describes how the UI is structured (screens, components, navigation mechanics, layout).

## Anchoring Rules

- Anchor journeys to the OPP-XXX selected upstream. The Key Problem from the brief provides global context — it does not determine the scope of the journeys.
- When a boundary is ambiguous, consult the other opportunities in the brief to determine which one owns the scenario — and explain the assignment.
- Exclude any scenario that touches an NG-XXX from the brief's explicit cuts.

---

## Granularity

**One step = one user action → one observable product result.** Not a gesture ("clicks compare"), not a macro-goal ("configures their stay").

- **Too coarse:** the step bundles several distinct user actions ("the user picks destination, dates and family composition") → split into one step per action.
- **Too fine:** the step is a UI gesture with no standalone result (click, scroll, open) → merge into the action it serves.
- A journey runs **4–8 steps**: trigger → main action(s) → variation or decision point → outcome. Under 3 steps: probably a single action in disguise (see Routing). Over ~10: two scenarios are mixed, or the flow drifted into wireflow.
- **One journey = one goal accomplished end-to-end.** Two distinct final outcomes → two journeys.

### The two altitudes of "outcome"

| Level | Definition | Example | Test |
|---|---|---|---|
| Journey outcome | A user **goal accomplished** — what the user came to do | "The user has booked the stay matching their constraints" | Asking "why?" exits the product scope. Requires **several** user actions to be reached. |
| Step outcome | The **observable product result of one user action** | "Available stays for the flexible period are shown" | Asking "why?" points to the journey outcome. Reached by a **single** action. |

Stop the "why" ladder at what the user would name as "what I came to do *today*" — "the user has saved a selection to discuss with family" is a valid journey outcome, distinct from "the user has booked".

A journey whose outcome is reachable through a single user action is a step in disguise; a step whose "result" is a goal accomplished is a compressed journey — unfold it. Both route per the Routing section below.

Leave `*Capabilities revealed:*` as TBD in Section 3 — it is filled at Step 3.

---

## Derivation process

### Sufficiency check — skeleton-based

Before deriving, attempt to fill this skeleton for each candidate journey, from OPP-XXX + the brief only:

- **Persona** — who goes through this journey
- **Trigger** — what makes the user start
- **Successful outcome** — what the user came to accomplish, stated as a goal achieved, not a product action (test: asking "why?" on it exits the product scope)
- **Known variations** — cases that produce a different path or outcome

Each field is either **traced** (points to a brief/OPP element), **assumed** (plausible but not stated in the brief), or **empty**.

### Route on the result

- **All fields traced or assumed, none empty** → derive directly. Mark every assumed element inline: `[ASSUMPTION: ...]`. A step without a marker must trace to the brief or the OPP — no silent assumptions.
- **1–2 fields empty** → derive what is derivable, then present ONE AskUserQuestion call grouping the empty fields. Options = plausible hypotheses derived from the brief, never generic; "Other" covers free input. This grouped call is the documented exception to the one-question-at-a-time rule.
- **Skeleton mostly empty** (OPP is a title with no exploitable context) → full bootstrap canvas: one AskUserQuestion call with the 4 fields, same option rule.

If AskUserQuestion is unavailable, present the canvas as markdown in a single message and wait for one grouped answer.

### Coverage check — separate question

Once ≥ 1 journey is derivable: can I identify a 2nd distinct scenario anchored to OPP-XXX? If not, ask one targeted question:

> "OPP-XXX gives me [scenario A]. Is there another distinct case this PRD must cover, or is a single journey the actual scope?"

A single-journey PRD is acceptable if confirmed — log the confirmation in the canonical memory.

### User check after derivation

Ask the user to confirm, complete, modify or delete journeys.

### At the step gate

Every remaining `[ASSUMPTION]` marker is either confirmed by the PM or converted to an `OQ-XXX` (with the journey in the *Blocks* column). No marker survives into the validated Section 3.

---

## Routing variations and orphan actions

Every candidate element gets an explicit destination — nothing is silently dropped.

**An outcome reachable through a single user action** is a step, not a journey. Route it:

1. It fits an existing journey → integrate it as a step where it occurs in the flow.
2. It fits no journey → climb the "why" ladder to the goal it serves. Goal in OPP scope → a missing journey was just revealed; derive it. Goal out of scope → log a drift tension in the canonical memory.
3. It duplicates an existing step → merge.

**A variation** routes by what it changes:

1. Same goal, different path, reveals a distinct capability or rule → one inline variation step in the same journey — flat numbering, prefixed `Variation:`. No branch notation (2a/2b).
2. Different final goal → separate journey.
3. Response to a failure (payment declined, no availability…) → NOT a journey element. Park it in the canonical memory under the PRD's section as an **ERR candidate** — Step 4 derives it as ERR-XXX.

**Saturation signal:** ≥ 3 inline variations in one journey → either two goals coexist (split the journey) or the variations are business-rule detail (they become BRs at Step 4, not steps).

---

## Quality check

### Challenge Pass

See `REF-challenge-pass.md` — section "Challenge Pass — User Journeys".

---

## Validation Criteria

A journey is valid if:

1. Every step describes **one user action + an observable product outcome** — and remains true if the mockup changes
2. No step names a technical mechanism (API, endpoint, data load, protocol) in any role
3. No step contains a layout detail, named UI component, or navigation mechanic
4. The subject of every step is the user, not the system
5. The journey's outcome is a goal accomplished (the "why" test exits the product scope) requiring several user actions
6. The set of journeys covers ≥ 2 distinct scenarios anchored to OPP-XXX — OR a single-journey scope explicitly confirmed by the PM and logged in the canonical memory
7. No journey addresses an out-of-scope problem without an open drift tension
8. No step describes the product's response to a failure — ERR candidates are parked in the canonical memory for Step 4
9. No `[ASSUMPTION]` marker remains in the validated section — each is confirmed or converted to an OQ-XXX
10. Every journey lists its *Capabilities revealed* (TBD until Step 3 fills it)
