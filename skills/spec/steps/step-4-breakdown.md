# Step 4 — Propose the spec breakdown

Before writing anything, present your proposed breakdown to the user and wait for their confirmation.

**Anchor the breakdown on the FUNC-xxx of the PRD.** A spec covers one coherent, valuable, testable and as-independent-as-possible increment — targeting a single testable user outcome an AI developer can implement in under 2 hours. Group the FUNCs into specs, then apply the three patterns below.

**Foundation** — when a dependency is unavoidable, declare a foundation spec explicitly: keep its scope minimal and document what it unblocks. Other specs depend on it and can then be built in parallel.

**Split** — split when the spec covers two independent surfaces (e.g. desktop sticky vs mobile panel with distinct DRD viewports), each deployable without the other, or contains an "and also" of two independent actions each with its own observable outcome.

**Merge** — merge when a piece has no user-facing value on its own, or its observable result only makes sense inside another spec (e.g. a compact mode that is never demoed without its expand/collapse parent, sharing the same lifecycle object).

Present the breakdown like this (illustrative — write it in the user's language):

```
Proposed spec breakdown for PRD-XX — <theme>:

Foundation (implement first — unblocks the others):
0. booking-summary-shell (FUNC-001)
   The user sees the stay summary (destination, dates, participants) on every page.
   → Foundation. Unblocks specs 1–4b.

Independent specs (parallel once spec 0 is delivered):
1. formula-breakdown (FUNC-002) — depends on 0
2. additional-fees (FUNC-003) — depends on 0
3. section-interactions (FUNC-004 + FUNC-005) [MERGE]
   Merge reason: FUNC-005 (compact mode) is not demoed without FUNC-004 (expand/collapse)
   — both share the ST-001 lifecycle object. Depends on 0.
4a. summary-desktop (FUNC-006 — desktop surface) [SPLIT] — DRD SummaryWidget / Desktop. Depends on 0.
4b. summary-mobile  (FUNC-006 — mobile surface)  [SPLIT] — DRD SummaryWidget / Mobile.
    Split reason: distinct DRD viewport + independent deployability. Depends on 0, 4a.

6 FUNCs → 6 specs (1 foundation, 1 merge, 1 split). Specs 1, 2, 3, 4a in parallel.

Does this breakdown look right? Any adjustments?
```

**Coverage gate — mechanical, before asking for confirmation.** Extract every id the PRD declares (`grep -oE '(FUNC|BR|ERR|ACC|PERM|ST)-[0-9]+[a-z]?' | sort -u` on the PRD file) and compare with the ids the breakdown claims. Show the result in the proposal:

```
Coverage: 24/26 ids — not covered: BR-033, ERR-005
```

An uncovered id must end up either **assigned to a spec** or **explicitly declared out of scope by the user** at confirmation — record those exclusions, they go into the `index.md` manifest (Step 6.9). Never confirm a breakdown with silently orphaned ids. (The deterministic validator sees one file at a time and never reads the PRD — this gate and the Step 7.2 reviewer are the only coverage checks.)

**Sizing:** each spec should stay implementable by an AI in under ~2 hours — as a rough gauge, more than ~15 business rules or ~5 endpoints in one spec is a split signal (the validator will WARN).

**If the count exceeds ~10 specs before all FUNCs are covered:** pause and flag to the user that the PRD may need an intermediate epic-level breakdown before spec generation — do not silently produce 15 fragments.

Only proceed once the user confirms (or adjusts the breakdown).

---

## Asking the user — one question at a time

This step is the pipeline's main HITL gate, and it owns the questioning style used everywhere:
**ask one question at a time, never a batch**, and wait for the answer before continuing.

Raise here anything only the product owner can settle:
- **Unclear business rules** — a BR that is contradictory or underspecified.
- **Missing acceptance criteria** — a FUNC with no clear "done" condition.
- **Scope ambiguity** — you cannot tell whether something is in or out of scope.

Do **not** block generation on an unresolved question: record what you could not settle in the
spec's **§2 Attention points** as an `❓ Open question` (§2 is the single home for open questions —
never a separate section, never a free-floating `[OPEN]` marker) and carry on.
