---
name: ref-challenge-pass
description: >
  Challenge Pass protocol: the anti-pattern filter applied before every presentation and
  re-presentation, and on the finished brief at the quality gate. Seven tables in one funnel
  order, holding only what a reader can decide.
type: reference
---

# Challenge Pass

An **automatic filter**, not a dialogue step. It applies to every statement headed for the brief,
yours or the PM's.

| When | On what |
|---|---|
| Before the first presentation of an artifact | Everything in it |
| Before every re-presentation | The **delta only** — what the PM corrected, what `[A]` added |
| At the quality gate | The finished document, every section |

**Behaviour.** Anti-pattern found → name it and show the fix, inside the presentation; several →
one grouped message. Nothing found → say nothing.

**Two kinds of fix.** A defect of **form** — a solution, an output, a symptom, a vague wording — is
yours to repair: name it, propose the corrected version. A defect of **evidence** — no baseline, no
source, an assumed consensus — is not: you cannot invent what was not observed. Correct it if the
inputs hold the missing piece; otherwise **downgrade it and say what would upgrade it** — « je le
note comme hypothèse ; un verbatim daté le ferait passer en signal direct ». A visible drop in
confidence brings a PM back to the evidence better than a question, and costs no turn.

**What belongs here.** Malformed statements a reader can judge. A well-formed claim that may be
wrong is *Challenge the framing*'s; what is missing is `[A]`'s; what a script can decide will be
the validator's. One check, one home.

## Reading order

Rows are sorted by band, in every table:

| Band | Question |
|---|---|
| 1. Existence | Does this belong in a brief at all? |
| 2. Cut | Is it cut at the right place? |
| 3. Altitude | Is it at the right level of the ladder? |
| 4. Evidence | What does it rest on? |
| 5. Wording | Is it stated so it can be tested? |

## Any statement

| Anti-pattern | What it looks like | Fix |
|---|---|---|
| Fuzzy term | A word that carries two meanings — « engagement » (of whom, measured how?), « disponibilité » (of a room, of a slot, of a price?) | Name the ambiguity and ask for the precise sense before building on it; an unresolved one becomes a tension |

## Outcomes

| Anti-pattern | What it looks like | Fix |
|---|---|---|
| Output, not outcome | "Ship 3 features" | Name it as a deliverable; ask what must change on the journey or the dashboard 3 to 12 months after delivery |
| Gameable metric | "Increase sessions" — it can rise with no value delivered | Propose the action inside it that signals value, or a guard-rail on what it could hide |
| Metric without baseline | "Increase engagement" | Evidence: look for T0 in the inputs; otherwise `TBD`, who can supply it, a tension |
| Unmeasurable outcome | "Improve the experience" | Ask what a user does today that signals a poor experience, and would do differently. *Observable how — on the journey, or on the dashboard?* |

## Signals

| Anti-pattern | What it looks like | Fix |
|---|---|---|
| Insight as observation | "Users are frustrated" | Ask what was seen or heard; keep the interpretation as an insight over several signals |
| Indirect signal as direct | A support or sales paraphrase given as the user's words | Evidence: ask for the original verbatim; without it, type it `Indirect signal` |
| Generalisation without source | "Everyone complains about…" | Evidence: who, when, in what context? No answer → `Intuition / deduction` |
| Absence of signal | A claim with nothing observed behind it | Evidence: `Intuition / deduction`, and say what observation would upgrade it |

## Persona

| Anti-pattern | What it looks like | Fix |
|---|---|---|
| Several personas in one | The description fits different people with different stakes | Ask which is primary — who bears the heaviest cost; the others are named, not served |
| Demographic only | "Families, 35–50, high income" | A profile — rewrite as the situation in which the problem hits them |
| Role only | "The travel agent" | Rewrite as what the role is trying to do when this becomes a problem |
| Persona not anchored | No signal shows this persona | Evidence: ask for the signal that shows this persona; none → `[ASSUMPTION: …]` until the gate, then `no persona — audience […]` and a tension |

## Key problem

| Anti-pattern | What it looks like | Fix |
|---|---|---|
| Solution-first | "We need an activity calendar" | Name it as a solution; propose the problem it would solve; park the solution for `/prd` and the need it serves as an OPP candidate |
| Feature parity | "Competitor X has it" | Ask what job the user hires this product for, and whether *our* users have it — a competitor's feature is a `Benchmark / analogy` signal, nothing more |
| Vague scope | "Booking is too complex" | Which problems, for which users, at which stage? |
| Symptom as root cause | "Conversion drops at step 3" | A symptom is *where it shows* — a rate that drops. The root cause is *what the persona runs into*, observable, at product altitude; the technical reason sits below the brief. Unknown → `Not established`, not a guess |
| Assumed consensus | "Everyone agrees that…" | Evidence: who validated it, when, on what? No answer → a hypothesis |

## Opportunities

| Anti-pattern | What it looks like | Fix |
|---|---|---|
| Disguised solution | "We need a chatbot" | Ask what the persona needs to *accomplish*; rewrite as an opportunity, park the solution |
| Already covered | The action falls inside a retained OPP | Note it under that OPP |
| Not independent | It cannot be delivered and measured without another OPP | Keep it; name the dependency in `Depends on` |
| Below altitude | Only one solution could address it — "compare two offers side by side" | Merge it into its parent OPP, or park it for `/prd` |
| Additive context | An end-to-end need while the initiative is incremental | Ask what makes it necessary for adoption now rather than later |
| No signal | Nothing from Step 2 supports it | Evidence: which observation? None → `Market` or `Redesign` if that is its real motive, otherwise a tension |
| Off format | Not expressible as `[infinitive verb] + [object] + [context]` | Reword it and show the corrected wording |

## Scope

| Anti-pattern | What it looks like | Fix |
|---|---|---|
| While-we're-at-it | An addition justified by proximity, not by the problem | Does it help address the key problem? If not, a cut |
| Nice-to-have creep | "It would be nice if…" | Nice for whom, measured how? Not needed to reach the target state → a cut |

## At the quality gate

The tables run once more on the **finished document**. *Solution-first* and *Disguised solution*
become transversal across **§1–§6**: a solution named in a tension, a cut, a signal's wording or
the central value fails like one in an opportunity. Three things are not leaks: a **quotation**
from a source — a user's words, a sponsor's deck — kept as evidence and typed as such; the
**Painted Door**, which describes a test; and **§7 Parked**, which is where solutions belong.
Report only what would change the document; every finding is fixed before `status: review`.

**For a reader who has only this file and the brief.** Levels, top to bottom: outcome · signal ·
persona · key problem · opportunity · central value; whatever says how the product responds or is
built sits below the brief. Signal types and grades are fixed by the skill — a study's count is a
`User verbatim`, an account relayed by the PM is an `Indirect signal`: do not propose retyping.
Ids carry no brackets; `Not established` and `None identified.` are legitimate states, not gaps.
