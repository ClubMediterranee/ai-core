---
name: ref-user-journeys
description: >
  Methodological reference for deriving and validating user journeys
  (userflows). Covers userflow vs. wireflow rules, opportunity anchoring,
  drift/gap report format, and validation criteria.
type: reference
---

# User Journeys — Methodological Reference

A user journey in the PRD is a **userflow** — it describes what the user does and gets, at the level of product behavior. It is not a **wireflow** — which describes how the UI is structured (screens, components, navigation mechanics, layout).

## Anchoring Rules

- Anchor journeys to the OPP-XXX selected upstream. The Key Problem from the brief provides global context — it does not determine the scope of the journeys.
- When a boundary is ambiguous, consult the other opportunities in the brief to determine which one owns the scenario — and explain the assignment.
- Exclude any scenario that touches an NG-XXX from the brief's explicit cuts.

---

## Derivation process 

### Sufficiency check before derivation

> Do I have enough in OPP-XXX + the brief to identify ≥ 2 distinct user scenarios?
> - **Yes** (OPP has a description of ≥ 1 sentence AND the brief provides user context) → derive directly, no preliminary question needed.
> - **No** (OPP is a title with no description, or cuts create ambiguity about what is in scope) → ask a targeted question before deriving:
>   > *"OPP-XXX in the brief gives me [X]. Is there a critical scenario I should cover before I derive the journeys?"*


### User check after derivation

Ask to the user to confirm, complete, modify or delete journeys.

---

## Quality check

### Challenge Pass

See `REF-challenge-pass.md` — section "Challenge Pass — User Journeys".

---

## Validation Criteria

A journey is valid if:

1. Every step describes **a user action + an observable product outcome** — and remains true if the mockup changes
2. No step names a technical mechanism (API, endpoint, data load, protocol) in any role
3. No step contains a layout detail, named UI component, or navigation mechanic
4. The subject of every step is the user, not the system
5. The set of journeys covers at least **2 distinct scenarios** anchored to OPP-XXX
6. No journey addresses an out-of-scope problem without an open drift tension
7. Every journey lists the **FUNCs revealed** (filled in after FUNC derivation)
