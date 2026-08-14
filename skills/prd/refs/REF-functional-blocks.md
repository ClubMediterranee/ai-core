---
name: ref-functional-blocks
description: >
  Methodological reference for deriving and validating functional blocks
  (FUNCs). Covers derivation rules, upper/lower bounds, nominal scenario
  format, and validation criteria.
type: reference
---

# Functional Blocks — Methodological Reference

A **FUNC** is a distinct user capability — an action a user initiates that produces an observable outcome. It is not a system behavior, not a display, not an isolated UI interaction.

A FUNC's observable outcome sits at the **same altitude as a journey step outcome** — by design: this is what lets journey steps reveal capabilities. The journey outcome (a goal accomplished) sits one level above and never becomes a FUNC.

**Required format:** `"Users can [verb] [object]"`
**Never:** `"The system displays"` / `"The API returns"` / `"The page renders"`

---

## Derivation

FUNCs are derived from **validated journeys** + **business rules (BRs)** + PM answers.

- One FUNC per distinct user capability
- Every FUNC must trace to **at least one journey step**
- For each FUNC, identify which ERR-XXX defined in the acceptance criteria apply — list them in the FUNC's acceptance criteria

---

## Upper Bound (split)

If a FUNC can be broken down into 2+ independent capabilities, each with its own observable outcome → **split it**.

Signal: the FUNC contains "and also" or "as well as" to describe two independent actions.

---

## Lower Bound (merge)

If a FUNC describes a single UI interaction with no standalone meaning (e.g. "click", "scroll", "display") → **merge it** into the parent capability.

Signal: the FUNC only makes sense in the context of another FUNC.

---

## Nominal Scenario Format

Every FUNC has **at least one nominal scenario** that proves the capability is testable:

```
Nominal scenario:
  WHEN [triggering condition]
  THEN [observable outcome]
  AND [additional outcome if needed]
```

---

## Validation Criteria

A set of FUNCs is valid if:

1. Every FUNC is written as `"Users can [verb] [object]"` with an observable outcome
2. No FUNC names a framework, endpoint, SQL type, protocol, UI component, or layout detail
3. Every FUNC traces to **at least one journey step** (appears in the journey's *Capabilities revealed* list)
4. Every FUNC has **at least one testable nominal scenario** (WHEN/THEN)
5. Every FUNC references the **applicable ERR-XXX** from the acceptance criteria
6. No FUNC is at the "UI interaction" level without a standalone user goal
7. No FUNC covers two independent capabilities without having been split
