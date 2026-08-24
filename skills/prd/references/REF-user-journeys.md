---
name: ref-user-journeys
description: >
  Methodological reference for deriving and validating user journeys
  (userflows). Covers the goal test, step granularity, journey completeness,
  how many journeys to write, the skeleton-based sufficiency check, and
  variation routing.
type: reference
---

# User Journeys — Methodological Reference

A user journey in the PRD is a **userflow** — what the user does and gets, at the level of product behavior. It is not a **wireflow** — how the UI is structured (screens, components, navigation mechanics, layout).

Journeys do two jobs: they **reveal the capabilities** to build, and they **prove the user's intent is reachable** with those capabilities. Both are judged against the journey's goal, which is why naming that goal correctly is the first thing to get right.

---

## What counts as a goal

A journey covers **one user goal** — the **user-goal level**, colloquially "sea level", in Alistair
Cockburn's *Writing Effective Use Cases* (Addison-Wesley, 2000). His hierarchy runs from summary
goals (a kite, above the water) down through the user goal (at sea level) to subfunctions (a fish,
below it). A PRD journey sits at sea level.

Two tests decide whether a candidate belongs there:

- **The boss test** — would a manager accept that this is what someone did all day? "Correct the
  search criteria": yes. "Choose which criterion to edit": no, that is a subfunction.
- **The elementary-business-process test** — one person, one place, one time, producing a result of
  value and leaving things in a coherent state.

A candidate that fails both is a step inside someone else's goal. One that clearly contains several
such goals is a summary — split it.

**Why this test earns its place.** Without it, "modify the dates" and "correct my search" are both
defensible as goals, and the journey set is re-cut every time someone re-reads it. Each
reorganisation drags along everything that referenced it.

---

## What counts as a step

**One step = one user action → one observable product result.** Not a gesture ("clicks compare"), not a macro-goal ("configures their stay").

- **Too coarse:** the step bundles several distinct user actions ("the user picks destination, dates and family composition") → split into one step per action.
- **Too fine:** the step is a UI gesture with no standalone result (click, scroll, open) → merge into the action it serves.

Treat this as the readiness test for Step 3 rather than a matter of style: a step producing no
observable result reveals nothing to build, and a step producing three hides two capabilities.

**The user is the subject of every step, including when the system is the one acting.** "The user
sees their criteria updated", not "the system updates the criteria" — the first states what is
observable and testable, the second states an implementation. This is also how a system-triggered
capability gets revealed without any exception to the rule.

**Do not name capabilities yet.** Step 2 reasons in observable results; `FUNC-` ids are assigned and
frozen at Step 3. An id written here is a commitment made before the journey set is stable, and
every later reorganisation renumbers it. Leave `*Capabilities revealed:*` as `TBD` — Step 3 fills it.

---

## A journey is complete when its goal is reached

The last step reaches the goal named in the title, and every step before it is a necessary move
toward that goal. That is the whole test, and it needs no reference to the capabilities that come
later — those are verified afterwards, when *Capabilities revealed* is filled.

A step that is not a move toward the goal belongs to another journey, or to no journey at all — route it below.

---

## How many journeys

Once the goals are settled, **the number of journeys is a readability decision, not a correctness one**. Two reasons justify writing more journeys than there are goals:

- a journey long enough that its thread is hard to follow — split it at a natural pause;
- a variation whose path diverges so far that inlining it would obscure both.

**The invariant:** re-organising for readability never changes the set of capabilities the journeys reveal. If merging two journeys makes a capability disappear, or splitting one invents another, that was not a readability change — it was a scope change wearing its clothes, and it has to be named as one.

---

## Anchoring Rules

- Anchor journeys to the OPP-XXX selected upstream. The Key Problem from the brief provides global context — it does not determine the scope of the journeys.
- When a boundary is ambiguous, consult the other opportunities in the brief to determine which one owns the scenario — and explain the assignment.
- Exclude any scenario that touches an NG-XXX from the brief's explicit cuts.

---

## Derivation process

### Sufficiency check — skeleton-based

Before deriving, attempt to fill this skeleton for each candidate journey, from OPP-XXX + the brief only:

- **Persona** — who goes through this journey. "Every user going through this flow" is a full,
  valid answer, not an empty field: a PRD covering a cross-cutting step (a checkout form, a
  confirmation page, an error page) documents the population of that flow rather than inventing
  a persona for it. Section 2 then states that population, and no fictional persona is created.
- **Trigger** — what makes the user start
- **Goal** — what the user came to accomplish, at the user-goal level above
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

**Freeze the behavioural vocabulary before continuing.** The journeys are where the words that
will propagate into the FUNCs, BRs and ERRs are chosen. Pick out the terms that carry an
**implementation implication** — "validation on keystroke" and "validation on field exit" are two
different behaviours, with different costs and different accessibility consequences — and put the
exact wording in front of the PM in **one** message: here are the two to four terms I will use,
confirm or correct them. Record what comes back in the *Project glossary* section of the canonical
memory as frozen vocabulary.

A term corrected here costs one exchange. The same term corrected after Step 4 has to be replaced
across the journeys, the FUNCs, the BRs, the ERRs and the glossary at once. Only include terms
that are load-bearing: confirming ordinary words is friction with no return.

---

## Routing variations and orphan actions

Every candidate element gets an explicit destination — nothing is silently dropped.

**An outcome reachable through a single user action** is a step, not a journey. Route it:

1. It fits an existing journey → integrate it as a step where it occurs in the flow.
2. It fits no journey → apply the goal test to what it serves. Goal in OPP scope → a missing journey was just revealed; derive it. Goal out of scope → log a drift tension in the canonical memory.
3. It duplicates an existing step → merge.

**A variation** routes by what it changes:

1. **Same action, different object** (edit the dates / the participants / the transport) → a
   parameter, not a variation. Keep one step and let the object vary — unless the **rules** differ,
   in which case the difference belongs in a BR at Step 4, or the **observable result** differs, in
   which case it earns its own variation step.
2. Same goal, different path, revealing a distinct capability or rule → one inline variation step in the same journey — flat numbering, prefixed `Variation:`. No branch notation (2a/2b).
3. Different goal → separate journey.
4. Response to a failure (payment declined, no availability…) → NOT a journey element. Park it in the canonical memory under the PRD's section as an **ERR candidate** — Step 4 derives it as ERR-XXX.

Established use-case practice does the same thing when it collapses create / update / delete of one
object into a single "manage X" goal, and promotes one of those operations into a goal of its own
only once it grows too important to sit inside. The test is unchanged: does the goal change?

**Saturation signal:** ≥ 3 inline variations in one journey → either two goals coexist (split the journey) or the variations are business-rule detail (they become BRs at Step 4, not steps). **Re-apply this after any merge** — a journey assembled from several others is exactly where variations pile up unnoticed.

### Preconditions

A journey may state what has to be true before its first step — a transport already selected, an account already created. A precondition is not a step: nothing is done and nothing is observed. Keep it at the journey level, and let Step 4 turn it into a BR or a PERM if it constrains behaviour rather than merely framing the scenario.

---

## Quality check

Read `REF-challenge-pass.md` — section "Challenge Pass — User Journeys" — and apply it before presenting.

A journey set is ready when each journey **passes the goal test**, **reaches its goal at its last step**, and **clears the Challenge Pass**. Those three are the validation — there is no separate checklist to run afterwards.

---

## Where the variation axis comes from

The idea that variations carry the wanted-but-not-critical capabilities comes from user story mapping (Jeff Patton, *User Story Mapping*, O'Reilly, 2014), where the alternatives hang under each activity in order of necessity. The PRD keeps that ordering intent without the release slicing that goes with it — slicing belongs downstream, to the `spec` skill.
