---
name: ref-metrics
description: >
  Methodological reference for the three PRD metric types: LGM (Lagging
  Metrics), DC (Damage Control), LDM (Leading Metrics). Covers feature type
  inference, formulation standards, and validation criteria.
type: reference
---

# Metrics — Methodological Reference

The PRD uses **three complementary metric lenses**:

| Type | Role | Origin |
|------|------|---------|
| **LGM-XXX** (Lagging Metrics) | What we aim to achieve — success criteria for the initiative | Imported from the brief (Desired Outcomes) |
| **DC-XXX** (Damage Control) | What must not degrade while optimizing LGMs | Imported from the brief (Damage Control) |
| **LDM-XXX** (Leading Metrics) | Observable user behaviors that predict adoption **before** LGMs are measurable | Derived during the Leading Metrics definition step |

---

## LGMs and DCs

Imported from the brief and validated during the brief import — **do not re-present during Leading Metrics derivation**.

Each LGM must have:
- A numeric threshold or a measurable direction of change
- A baseline (T0) — may be "TBD" if unavailable, but must be noted

Each DC must have:
- A maximum acceptable degradation threshold
- The current baseline

---

## LDMs — Feature Type Inference

**Internal rule (apply before proposing examples):**

> Infer the dominant interaction type from the validated journeys:
> - All steps are "the user views / sees / reads / explores" → **consultation feature** → propose engagement metrics: view rate, time spent, return rate.
> - Steps include "the user selects / configures / submits / validates" → **action feature** → propose completion metrics: step completion rate, drop-off point, back-navigation rate.
> - Mixed → combine both families.
>
> Calibrate all examples to this type. **Never propose completion metrics for a pure consultation feature.**

---

## LDM Format

```
LDM-001 : [Observable user behavior]
  Collection method : [How it is collected — analytics event, survey, session recording...]
  Review cadence : [weekly / monthly / per release]
```

**Formulation rule:**
- Write as an **observable user behavior**, not a technical indicator
- Good: "Rate of users who view ≥ 2 accommodations in a single session"
- Bad: "Number of clicks on the comparison component"

---

## Elicitation (before derivation)

> Now that the journeys and functional blocks are defined:
> What observable behaviors would indicate that this feature is producing the expected effect — **before** overall conversion metrics are measurable?

Wait for the answer. Then formalize as LDM-XXX with collection method and review cadence. Write "None defined." explicitly if not applicable.

---

## Advanced Elicitation — Patterns to Identify

> - **Unmeasurable LDM:** [leading metric with no identifiable collection method]
> - **Missing LDM:** [FUNC that generates a user behavior not yet captured as a leading signal]
> - **Lagging disguised as leading:** [metric that only becomes available after the brief's KR timeframe]

---

## Validation Criteria

A set of metrics is valid if:

1. The document has **3 metric subsections** (LGM, DC, LDM) — each is either filled in or marked "None identified." / "None defined."
2. Every **DC-XXX** has a numeric threshold — no DC without a threshold
3. Every **LDM-XXX** has a collection method and a review cadence
4. No LDM is a completion metric for a pure consultation feature
5. No LDM only becomes measurable after the brief's KR timeframe (lagging disguised as leading)
6. LGMs and DCs trace to the brief (Desired Outcomes and Damage Control) — any LGM introduced without a brief anchor has an open divergence tension
