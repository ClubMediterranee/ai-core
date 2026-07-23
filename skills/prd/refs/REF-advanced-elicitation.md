---
name: ref-advanced-elicitation
description: >
  Advanced Elicitation blocks by PRD artifact — patterns to identify and
  format for derived questions. One section per artifact (journeys, ACs, FUNCs).
type: reference
---

# Advanced Elicitation — Reference by Artifact

Advanced Elicitation [A] is triggered on the PM's request. The agent **reasons visibly** about what it does not yet know, identifies 2-3 patterns, then derives questions from that reasoning — never from a generic template.

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

---

## Leading Metrics

See `REF-metrics.md` — section "Advanced Elicitation — Patterns to Identify".
