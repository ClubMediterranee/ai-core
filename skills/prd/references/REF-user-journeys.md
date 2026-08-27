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

The question, in Cockburn's own terms: **can the primary actor go away satisfied, having done this?**
A user goal is what someone sets out to finish **in one sitting** — one person, one place, one
session.

"Correct the search criteria": yes, they can stop there satisfied. "Choose which criterion to edit":
no, nothing is accomplished — that is a subfunction.

A candidate that fails the question is a step inside someone else's goal. One that clearly holds
several such goals is a summary — split it.

**Every journey states its goal in writing**, on a `*Goal:*` line under its heading. The heading is
a short name for the flow; the goal is the proposition the journey has to satisfy, and it is what
the question above is applied to. Left implicit in a title, a goal cannot be tested and two readers
will hold two different versions of it — which is how a journey set ends up re-cut on every
re-reading, dragging along everything that referenced it.

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

**The nominal path reaches the goal**, and every step on it is a necessary move toward that goal.
That is the whole test, and it needs no reference to the capabilities that come later — those are
verified afterwards, when *Capabilities revealed* is filled.

Variation steps are judged differently. One may legitimately stop short of the goal — abandoning an
edit is precisely a non-attainment, and writing it as though it reached the goal would be false.
What a variation may not be is a dead end with no reading: one that never leads anywhere is either
an error path, to be parked as an ERR candidate, or a step belonging to another journey.

**Place each variation where it diverges from the nominal path**, not at the end of the list. A
reader follows the numbering as a sequence, so a variation parked after the closing step reads as
something that happens afterwards — which it is not.

A step that is neither a move toward the goal nor a variation of one belongs to another journey, or
to no journey at all — route it below.

---

## How many journeys

Once the goals are settled, **the number of journeys is a readability decision, not a correctness one**. Three things justify writing more journeys than there are goals:

- a journey long enough that its thread is hard to follow — split it at a natural pause;
- a variation whose path diverges so far that inlining it would obscure both;
- **one goal pursued from two situations where the user's stake or precondition differs.** The test:
  does a reader lose something by being shown only one of them? Correcting a search before
  committing to anything and correcting it after building a basket share a goal, but one risks
  nothing and the other discards work already done. A rule can state that difference in a sentence;
  only a separate flow makes a PM decide about it.

**Splitting deserves as much thought as merging.** Most of what this reference says pushes toward
fewer journeys — parameters over variations, one goal over many, entry points folded into a step —
because duplication is the more common failure. That pressure is deliberate, and it is not free:
when two situations carry different consequences for the user, folding them together hides the
decision the PM has to make.

**The invariant:** re-organising for readability never changes the set of capabilities the journeys reveal. If merging two journeys makes a capability disappear, or splitting one invents another, that was not a readability change — it was a scope change wearing its clothes, and it has to be named as one.

---

## Anchoring Rules

- Anchor journeys to the OPP-XXX selected upstream. The Key Problem from the brief provides global context — it does not determine the scope of the journeys.
- When a boundary is ambiguous, consult the other opportunities in the brief to determine which one owns the scenario — and explain the assignment.
- Exclude any scenario that touches an NG-XXX from the brief's explicit cuts.

---

## Derivation process

### Start with the goals, not the flows

Before writing any flow, list what people come to this opportunity to accomplish: one line per
**persona → goal**, drawn from OPP-XXX and the brief. Cockburn calls this the actor-goal list, and
it is the cheapest artefact in the step — correcting a goal here costs a line, correcting it once
the flows are written costs every step hanging off it.

Apply the user-goal question to each candidate, then put the list in front of the PM in one message:
here is what people come here to do — is anything missing, and is anything on this list not really
a goal?

**This is where the scope of the section is settled.** A single-goal PRD is legitimate once
confirmed. Log the confirmation in the canonical memory, along with anything the PM adds or removes.

**The confirmed list is a starting point, not a closed set.** Goals surface while flows are being
written: the routing section below sends an orphan action back up to the goal it serves, and a goal
in scope that nobody had listed is a journey to derive, not an intruder to reject. Bring it back to
the PM rather than absorbing it silently.

### Sufficiency check — skeleton-based

For each confirmed goal, attempt to fill this skeleton from OPP-XXX + the brief only:

- **Persona** — who pursues this goal. "Every user going through this flow" is a full,
  valid answer, not an empty field: a PRD covering a cross-cutting step (a checkout form, a
  confirmation page, an error page) documents the population of that flow rather than inventing
  a persona for it. Section 2 then states that population, and no fictional persona is created.
- **Trigger** — what makes them start
- **Known variations** — cases that produce a different path or outcome

Each field is either **traced** (points to a brief/OPP element), **assumed** (plausible but not stated in the brief), or **empty**.

### Route on the result

- **All fields traced or assumed, none empty** → derive directly. Mark every assumed element inline: `[ASSUMPTION: ...]`. A step without a marker must trace to the brief or the OPP — no silent assumptions.
- **1–2 fields empty** → derive what is derivable, then present ONE AskUserQuestion call grouping the empty fields. Options = plausible hypotheses derived from the brief, never generic; "Other" covers free input. This grouped call is the documented exception to the one-question-at-a-time rule.
- **Skeleton mostly empty** (OPP is a title with no exploitable context) → full bootstrap canvas: one AskUserQuestion call with every field, same option rule. When the goals themselves could not be drawn from the brief, that canvas is the goal-list conversation and this one, held together.

If AskUserQuestion is unavailable, present the canvas as markdown in a single message and wait for one grouped answer.

### User check after derivation

Ask the user to confirm, complete, modify or delete journeys.

### Before the step gate

Every remaining `[ASSUMPTION]` marker is either confirmed by the PM or converted to an `OQ-XXX` (with the journey in the *Blocks* column). No marker survives into the validated Section 3. Confirming one is a question, so it happens **before** the gate is surfaced — like the vocabulary freeze below.

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

   The result is **what the user ends up with, not what they had to supply to get there**. Being
   asked for one more value along the way — a date of birth for each child, say — is an extra input
   for the same outcome: rule detail, not a variation.
2. Same goal, different path, revealing a distinct capability or rule → one inline variation step in the same journey — flat numbering, prefixed `Variation:`. No branch notation (2a/2b).
3. Different goal → separate journey.
4. Response to a failure (payment declined, no availability…) → NOT a journey element. Park it in the canonical memory under the PRD's section as an **ERR candidate** — Step 4 derives it as ERR-XXX.

Established use-case practice does the same thing when it collapses create / update / delete of one
object into a single "manage X" goal, and promotes one of those operations into a goal of its own
only once it grows too important to sit inside. The test is unchanged: does the goal change?

**Saturation signal:** ≥ 3 inline variations in one journey → it is carrying more than it can show. Which remedy applies depends on what the variations are:

- one that only changes **how a rule applies**, with no different consequence for the user, is
  business-rule detail → it becomes a BR at Step 4, not a step;
- one that leads to a **different consequence for the user** is not rule detail → it stays a step,
  and the journey splits around it if that is what makes both readable.

The count is the alarm, not the remedy. Demoting a variation to a BR in order to get back under
three is gaming the signal rather than heeding it — the question is what the variation carries, not
how many there are. **Re-apply this after any merge**: a journey assembled from several others is
exactly where variations pile up unnoticed.

### Preconditions

A journey may state what has to be true before its first step — a transport already selected, an account already created. A precondition is not a step: nothing is done and nothing is observed. Keep it at the journey level, and let Step 4 turn it into a BR or a PERM if it constrains behaviour rather than merely framing the scenario.

---

## Quality check

Read `REF-challenge-pass.md` — section "Challenge Pass — User Journeys" — and apply it before presenting.

A journey set is ready when each journey **passes the goal test**, **reaches its goal at its last step**, and **clears the Challenge Pass**. Those three are the validation — there is no separate checklist to run afterwards.

---

## Where the variation axis comes from

The idea that variations carry the wanted-but-not-critical capabilities comes from user story mapping (Jeff Patton, *User Story Mapping*, O'Reilly, 2014), where the alternatives hang under each activity in order of necessity. The PRD keeps that ordering intent without the release slicing that goes with it — slicing belongs downstream, to the `spec` skill.
