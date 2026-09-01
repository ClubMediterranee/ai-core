---
name: ref-advanced-elicitation
description: >
  Advanced Elicitation patterns by PRD artifact — what may be missing or cut wrong in the
  artifact just derived. Read whenever the PM chooses [A]. Holds only what [A] adds: the
  protocol is in SKILL.md, and what is wrong at altitude is the Challenge Pass's.
type: reference
---

# Advanced Elicitation — Patterns by Artifact

The protocol — reason visibly about what is not settled, identify 2–3 patterns, derive 1–3
questions, then re-present the gate — lives in `SKILL.md` (*Advanced Elicitation*, Golden Rules).
This reference holds only the pattern lists.

**What `[A]` asks is what is missing, or cut where the PM would cut differently.** What is
*wrong* — a technical or design HOW, a non-testable rule, an embedded assumption, a capability
no journey reveals — is the Challenge Pass's and the quality gate's, and is not repeated here:
an `[A]` that re-runs those filters adds nothing the gate does not already do.

Pick the 2–3 patterns most relevant to the artifact at hand; never all of them, never a generic
template.

---

## User Journeys

- **Missing step:** [user action implied by the opportunity but absent from the journey]
- **Edge case:** [scenario variation that produces a different outcome from the nominal case, and
  that no variation step carries]

---

## Functional Blocks

- **Oversized FUNC:** [FUNC covering two independent user goals, each with its own observable
  outcome — a split the PM may want]
- **Interaction-level FUNC:** [FUNC that describes a UI interaction with no standalone goal —
  "display", "show", "render" — a merge into the parent capability]
- **Non-autonomous FUNC:** [FUNC whose scenario cannot be written without another FUNC acting
  first — its `GIVEN` names another FUNC's action rather than a state of the world; a merge
  candidate, see `REF-functional-blocks.md`, *The boundary discriminant*. A cut the PM
  arbitrates, which is why it lives here and not in the Challenge Pass]

---

## Acceptance Criteria

- **Missing error:** [failure mode implied by a journey step or a BR with no corresponding ERR]
- **Missing state:** [object with several journey outcomes but no ST-XXX — an implicit lifecycle
  left unspecified]
- **Missing permission:** [journey step with an actor restriction implied by a BR or a persona,
  but no PERM-XXX]

---

## Leading Metrics

- **Missing LDM:** [FUNC that generates a user behavior not yet captured as a leading signal]

What is *wrong* with a metric — unmeasurable, lagging disguised as leading, no brief anchor — is
the Challenge Pass's Metrics table, not an `[A]` pattern.
