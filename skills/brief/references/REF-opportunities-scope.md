---
name: ref-opportunities-scope
description: >
  Step 3 — Opportunities & scope: what an opportunity is and its format, anchors and ids, the
  necessity and sufficiency filters, the success signal, cuts, constraints, the painted door, and
  the legitimate "undecided" state.
type: reference
---

# Opportunities & Scope — Step 3

## Opportunities

**Definition.** A lever on the persona's behaviour that several distinct solutions could pull. It
names what the persona needs to accomplish, never how the product would let them — if only one
solution could address it, it is a capability and belongs to `/prd`. Each retained opportunity
becomes one PRD.

**Shape** — `[infinitive verb] + [object] + [context / moment]`, with its anchor:

> **OPP-001 —** Connaître les activités proposées pendant son séjour avant d'arriver au resort
> → *anchored on:* the critical action of the key problem (planning the stay ahead)

Anchor on whichever element of the key problem the lever addresses — the critical action, the
consequence, the workaround, the adoption risk; on the root cause only when it is established.

| `Anchor` | Meaning |
|---|---|
| `Key Problem` | Addresses a pain of the key problem directly — say which element |
| `Redesign` | End-to-end completeness required by a revamp |
| `Market` | Competitive or positioning motive |

An opportunity with no signal behind it is legitimate only under `Redesign` or `Market`.

**Derive.** From the key problem, the persona's job, the workaround, the adoption risk, and the
rows §7 holds for this step (needs, constraints, cut candidates) — present them directly,
every distinct lever first, priorities after. Beyond four or so, suspect capability-sized items or an overloaded scope rather than trim to
a number. Ids are never renumbered: reading order is the `Priority` column.

## Scope

| Element | Who | What |
|---|---|---|
| **Necessity** | The PM decides | Which opportunity is indispensable to address the key problem in this iteration, and why; the order, if several |
| **Sufficiency** | You derive | One line per retained opportunity on what the persona can now do; then check that nothing they must accomplish end to end is left uncovered. A gap the PM names goes through the Challenge Pass like any opportunity |
| **Success signal** | You derive | **[Persona]** will go from **[current observable state]** to **[target observable state]**, measurable by **[indicator or proxy]** — a lagging metric of §4 or a named proxy of one. A threshold with no baseline behind it is `TBD`, with who can supply the base — do not invent a number |
| **Cuts** | The PM decides | What is explicitly **not** in this iteration, *even if it seems obvious* — the cut list protects the scope at every later stage. A cut you propose is named as yours. A cut is worded at opportunity altitude; the feature behind it goes to §7 |
| **Constraints, stakeholders** | The PM decides | Fixed constraints (deadline, compliance, budget); who must be aligned before `/prd`. A stakeholder to align is a `Stakeholder` row of *Constraints*; one whose alignment blocks `/prd` is a tension — never a blocker of the brief |
| **Painted door** | You derive | When confidence is below `High` or demand is in doubt: what an unbuilt version would look like, the behavioural signal it generates, the threshold that would justify building. It describes a **test**, so it may name a fake entry point — the one place in §1–§6 where that is not a solution leak; a threshold with no baseline behind it is `TBD`, with who can supply the base — do not invent a number |

Ask the PM's decisions in one grouped question.

## Shape of §5

```
### Opportunities
| ID | Opportunity | Anchor | Key problem anchor | Priority | Depends on |
|---|---|---|---|---|---|
| OPP-001 | Connaître les activités… | Key Problem | critical action | 1 | — |

### Success Signal
### Cuts            | Item | Reason |
### Constraints     | Type | Constraint |
### Painted Door    (conditional)
```

One table holds the retained opportunities — there is no separate scope table to keep in sync.

## Not established — legitimate states

| Situation | Write | And |
|---|---|---|
| The PM will neither retain nor cut an opportunity | Keep it out of the table and out of *Cuts*; it takes no id | A `T-XX` stating it is **undecided**, with what each outcome would mean — its `Blocks` names the lever in words; a row in §7, `Future brief`, with its signals |
| A single opportunity | One row | Say the brief generates one PRD; check sufficiency with particular care |
| The PM arrives with a feature list | The accomplishment each item serves, grouped | The features go to §7, `/prd` |
| No constraint known | `None identified.` | — |
| Amendment | Start from the parent's table: keep every id; add, reword or cut | The parent's cuts stay cuts unless the PM reopens one |

## Check

`REF-challenge-pass.md` — *Opportunities* and *Scope*. The top-priority opportunity is a
load-bearing claim: *Challenge the framing* applies when the evidence supports another lever at
least as well.
