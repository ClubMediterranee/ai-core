---
name: ref-functional-blocks
description: >
  Methodological reference for deriving and validating functional blocks
  (FUNCs). Covers the boundary discriminant, derivation from journeys,
  ordering and id stability, the nominal scenario format, and validation
  criteria.
type: reference
---

# Functional Blocks — Methodological Reference

A **FUNC** is a distinct user capability with an **autonomous observable outcome** — one that can be
demonstrated without another FUNC first being acted on, or first being in a specific state.

A FUNC's observable outcome sits at the **same altitude as a journey step outcome** — by design:
this is what lets journey steps reveal capabilities. The journey outcome (a goal accomplished) sits
one level above and never becomes a FUNC.

Everything below follows from that single test. Apply the test; the table states its consequences,
it is not a second set of rules to memorise.

---

## The boundary discriminant

| Signal | Expected result |
|---|---|
| A user initiates the action and the outcome is autonomous | FUNC — `Users can [verb] [object]` |
| The trigger is a system condition (page load, quota reached, match found) **and** the outcome is autonomous | FUNC — `Users benefit from [X] when [condition]`; the user stays the subject |
| No autonomous outcome — the behaviour constrains how other FUNCs behave | **BR**, not a FUNC |
| No autonomous outcome — the scenario is incomplete without another FUNC's action | **Merge** into the FUNC it depends on |
| The same capability is reachable from several entry points, with the same observable outcome | **One** FUNC — the entry point belongs in the `WHEN` ("from X or from Y") |
| Two independent outcomes, each with its own WHEN/THEN | **Split** |
| A single UI interaction with no standalone meaning (click, scroll, display) | **Merge** into the capability it serves |

**Never:** `"The system displays"` / `"The API returns"` / `"The page renders"`. A system-triggered
FUNC still states what the user gets, never what the machine does.

Two FUNCs for the same capability on two surfaces are justified **only** when the business rules or
the observable result actually differ between them.

### Worked examples — illustrative, not templates

**Autonomous, system-triggered → a FUNC.**
`Users benefit from a pre-filled delivery address when a saved address matches the selected country`
— GIVEN a saved address for that country / WHEN the checkout step opens / THEN the address fields
are pre-filled. Testable on its own: nothing else has to happen first.

**Not autonomous → stays a BR.**
"Field validation runs when the field loses focus" has no outcome of its own — it changes how every
form capability behaves. It is a constraint across FUNCs: one BR, referenced by each form FUNC.

**Same capability, two entry points → one FUNC.**
"Users can add an item to the cart" reached from the listing and from the product page produces the
same observable result. One FUNC, with `WHEN the user adds an item from the listing or from the
product page`. Two FUNCs would duplicate near-identical acceptance criteria.

**Carved by container → re-cut by capability.**
A details panel with three tabs — floor plan, amenities, 360° view — is not "open the panel"
plus one FUNC per tab: `GIVEN the panel is open` binds each to the component. Apply the
discriminant to the outcomes instead: consulting the floor plan and consulting the amenities are
each autonomous (`Users can view … without leaving the room sheet`); the panel, its tabs and
their default state belong to the DRD.

**No standalone scenario → merge.**
A "Users can confirm their slot selection" whose WHEN/THEN cannot be written without the slot picker
having been used first is not a separate capability. Merge it into the picker FUNC, or restate the
constraint as a BR.

---

## Derivation

FUNCs are derived from **validated journeys** + PM answers. Business rules and error scenarios do
not exist yet — they are derived at Step 4, and Step 4 comes back to fill each FUNC's
`**Acceptance criteria:**` bullets. Writing a FUNC around an id that has not been assigned is how a
capability ends up shaped by a rule nobody validated.

**The output of this step is not a list of FUNCs — it is each journey's `*Capabilities revealed:*`
line, filled in.** Derive by filling those lines. A journey step carrying an observable outcome that
appears in no line is either a missing FUNC, or a step you must explicitly name as covered by a
cross-cutting FUNC. Leaving it unnamed is how a capability disappears until review.

- One FUNC per distinct user capability
- Every FUNC must trace to **at least one journey step**
- Which `ERR-XXX` a FUNC carries is settled **at Step 4**, once the error scenarios exist. At Step 3,
  note the failure modes the capability implies and leave them with the parked ERR candidates

**Saturation signal, optional.** A FUNC that would carry far more business rules than its
neighbours — roughly more than fifteen, the threshold the `spec` skill applies per spec — is
probably two capabilities. Treat it as a prompt to re-read the discriminant, never as a bound.

---

## Ordering and id stability

**Order is decided at derivation, not in review.**

1. Feature areas follow the **first appearance** of the capability in the journeys (§3, read in
   order).
2. Inside a feature area, user-initiated before system-triggered.
3. Cross-cutting FUNCs (global validation, auth, legal) close the list.

**Ids are identifiers, not ordinals.** Once assigned at the Step 3 gate, a FUNC id is never reused
and never renumbered: a merge **retires** its id — a gap in the sequence is normal and expected —
and a late insertion takes the next free number. **Reading order is carried by the position in §4,
not by the number.**

Renumbering to close a gap looks tidy and costs a cascade through §3 *Capabilities revealed*, §5
*Applies to*, scenario `AND` clauses, PERM conditions and ST transitions — for zero new content. A
retired id is never re-created for a different capability: two blocks sharing an id is a defect, and
the validator reports it.

---

## The FUNC block divides the work

The title **names** the capability — the scannable inventory. A `**Capability:**` line **bounds**
it — kept only when it adds a boundary the title cannot carry (the precise object, the scope
edge: "without leaving the room sheet"), deleted when it would restate the title. The nominal
scenario **proves** it. What overflows the one Capability sentence is not lost: an enumeration of
content or a condition is rule detail, parked for Step 4 (*Park and Surface*).

---

## Nominal Scenario Format

Every FUNC has **at least one nominal scenario** that proves the capability is testable:

```
**Nominal scenario:**
- **GIVEN** [prerequisite state — only when it is not obvious from the WHEN]
- **WHEN** [triggering condition]
- **THEN** [observable outcome]
- **AND** [additional outcome if needed]
```

`GIVEN` is **optional**. It states the conditions under which the test runs — logged in or not, a
booking that already holds a child, an option still valid. Skip it when the context is neutral: a
`GIVEN` that says "the user is on the site" adds noise, not precision.

**`GIVEN` also makes the autonomy test visible.** A prerequisite describing a **state of the world**
is legitimate, and the FUNC stays autonomous. A prerequisite describing **another FUNC's action**
("the user has submitted the form of FUNC-004") is the merge signal from the discriminant above,
written down instead of judged from memory. And a `GIVEN` naming a **UI container's state** —
"the layer is open", "the modal is displayed" — is not a state of the world either: it binds the
FUNC to a component. Carve FUNCs by capability, never by container: three tabs in one panel are
one, two or three capabilities **by the discriminant**, never three FUNCs because the mockup
shows three tabs.

Autonomy is a cut, decided here with the PM. The Challenge Pass does not re-litigate it: `[A]`
offers it as a pattern (*Non-autonomous FUNC*, `REF-advanced-elicitation.md`) when the PM wants to
go deeper, and the merge stays their call.

`GIVEN` / `WHEN` / `THEN` / `AND` are machine tokens — they stay in English in every language.

---

## Quality check

Read `REF-challenge-pass.md` — section "Challenge Pass — Functional Blocks" — and apply it before
presenting.

---

## Validation Criteria

A set of FUNCs is valid if:

1. Every FUNC has an **autonomous observable outcome** — demonstrable without another FUNC first
   being acted on or being in a specific state
2. Every FUNC keeps the user as the subject — `Users can [verb] [object]` for user-initiated
   capabilities, `Users benefit from [X] when [condition]` for system-triggered ones — shapes, not tokens: the words take the PM's language (« L'utilisateur.rice peut [verbe] [objet] »)
3. No FUNC names a framework, endpoint, SQL type, protocol, UI component, or layout detail
   *(judged by the Challenge Pass — Technical HOW / Design HOW rows; named components also trip
   the validator's QG-2 lexicon)*
4. Every FUNC traces to **at least one journey step** (it appears in that journey's *Capabilities
   revealed* list), and every journey reveals at least one FUNC *(decided by
   `scripts/validate_prd.py`, QG-6)*
5. Every FUNC has **at least one testable nominal scenario** (WHEN/THEN, plus `GIVEN` wherever the
   prerequisite is not obvious) *(the WHEN/THEN presence is decided by `scripts/validate_prd.py`,
   QG-4)*
6. Every FUNC references the **applicable ERR-XXX** from the acceptance criteria — *verified at
   Step 4, when the error scenarios exist; not gateable at Step 3*
7. No FUNC sits at the "UI interaction" level without a standalone user goal
8. No FUNC covers two independent capabilities without having been split
9. The same capability on several surfaces is a single FUNC, unless the rules or the observable
   result differ
10. FUNC ids follow first appearance in the journeys with cross-cutting last, and no id has been
    renumbered since the Step 3 gate
