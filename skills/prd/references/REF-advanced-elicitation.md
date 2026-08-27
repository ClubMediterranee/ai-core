---
name: ref-advanced-elicitation
description: >
  Advanced Elicitation blocks by PRD artifact — patterns to identify and
  format for derived questions. One section per artifact (journeys, ACs, FUNCs).
type: reference
---

# Advanced Elicitation — Reference by Artifact

Advanced Elicitation [A] is triggered on the PM's request. The agent **reasons visibly** about what it does not yet know, identifies 2-3 patterns, then derives questions from that reasoning — never from a generic template.

**The questions are the agent's to produce.** `[A]` is a request to go deeper, not a request to be
told where to dig. Answering it with *what would you like to explore?* hands the analysis back to the
PM and skips the protocol entirely — it is the one response the option never means. If nothing is
genuinely unresolved, say so and re-present the gate; do not manufacture questions either.

**Common format:**
```
Let me think about what I don't yet know about [current artifact]...

[Identify 2-3 patterns from the list for the relevant artifact]

Questions derived from this reasoning: [1-3 questions]
```

After Advanced Elicitation: re-present the validation options.

---

## User Journeys

Patterns to identify (pick the 2-3 most relevant):

- **Missing step:** [user action implied by the opportunity but absent from the journey]
- **Implicit assumption:** [step that assumes a capability that does not exist or has not been validated]
- **Edge case:** [scenario variation that produces a different outcome from the nominal case]
- **Opportunity drift:** [journey that addresses a plausible problem but different from OPP-XXX]

---

## Acceptance Criteria

Patterns to identify (pick the 2-3 most relevant):

- **Non-testable rule:** [BR that cannot be verified by a binary pass/fail test]
- **Missing error:** [failure mode implied by a journey step or BR with no corresponding ERR]
- **Embedded assumption:** [BR that hides a business decision that should be surfaced as an OQ]
- **Missing state:** [object with multiple journey outcomes but no ST-XXX — implicit lifecycle not specified]
- **Missing permission:** [journey step with an actor restriction implied by a BR or persona but no PERM-XXX]

---

## Functional Blocks

Patterns to identify (pick the 2-3 most relevant):

- **HOW leakage:** [FUNC that describes an implementation rather than a user capability]
- **Orphan capability:** [FUNC that does not trace to any journey step — no validated use case]
- **Missing capability:** [journey step or BR that implies a capability with no corresponding FUNC]
- **Oversized FUNC:** [FUNC covering two independent user goals, each with its own observable outcome — split it]
- **Interaction-level FUNC:** [FUNC that describes a UI interaction with no standalone goal — "display", "show", "render" — merge into the parent capability]
- **Non-autonomous FUNC:** [FUNC whose scenario cannot be written without another FUNC acting first — its `GIVEN` names another FUNC's action rather than a state of the world; a merge candidate, see `REF-functional-blocks.md`, *The boundary discriminant*. A cut the PM arbitrates, which is why it lives here and not in the Challenge Pass]

---

## Leading Metrics

See `REF-metrics.md` — section "Advanced Elicitation — Patterns to Identify".
