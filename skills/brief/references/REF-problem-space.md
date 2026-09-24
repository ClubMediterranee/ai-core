---
name: ref-problem-space
description: >
  Step 2 — Problem space: signal types and grading, the persona as a situation, the key problem
  and its supporting elements, the confidence level and its validation plan, checkpoints, and the
  legitimate "not established" states.
type: reference
---

# Problem Space — Step 2

Order, always: **signals → persona → key problem.** A persona confirmed on the wrong signals, or a
problem framed for the wrong persona, is rework that invalidates everything validated after it.

## Signals

**Definition.** One isolated, dated, attributable fact — not yet an insight. An *insight*
interprets several signals; keep the two apart.

| Type | Examples | Grade |
|---|---|---|
| `User verbatim` | Interview quote, support ticket, NPS comment | `Strong` if recent and recurring |
| `Observed behaviour` | Analytics, session replay, funnel drop | `Strong` if statistically significant, or descriptive over the whole traffic with its base and period stated; `Medium` otherwise |
| `Indirect signal` | CS escalation, lost sale, recurring feature request, an account of someone's experience — relayed by a third party, the PM included | `Medium` if its origin is identifiable (who, when) — otherwise `Weak` |
| `Benchmark / analogy` | A competitor's pattern, another product | `Weak` — different context |
| `Intuition / deduction` | "We know that…" — and anything *you* bring | `Hypothesis` |

Type and grade names are prose: they follow the document's language, one wording per brief. An old or isolated verbatim is graded down, not retyped. A study's
count ("9 of 12 interviews") is typed like what it aggregates — `User verbatim` — and cites the
study's section.

**Derive / Ask.** Signals are never derived. Extract them from the inputs — verbatims word for
word, with their location — then ask what is missing: what the PM **saw or heard, not what they
think**. More than 8: show a representative 6–8 and say you work on all of them. If Step 0 brought
inputs but no study, ask once whether one exists; whatever surfaces joins §3 at `[C]`.

**Close on a convergence statement** — signals grouped by common tension, journey stage or
mechanism: *"several signals converge on [X]"*, or *"no convergence yet — they point toward [A]
and [B]"*. The second is a finding, not a failure.

## Persona

**Definition.** A situation, not a title — what someone is trying to accomplish, what blocks, what
it costs — anchored in at least one signal. The brief serves the person whose experience is the
most painful.

**Shape.**
- *Triggering situation* — "When [context], [persona] needs to [action] but [friction]."
- *Functional job* — "When [situation], I want to [action], so that [result]."
- *Emotional job* — "To feel: [state]. To avoid: [emotional friction]."

**No persona is a valid answer** — an internal tool, a homogeneous audience: write
`no persona — audience [description]`, carry a tension, invent nobody.

## Key problem

**Definition.** What in the experience keeps the persona from a critical action, with an observable
consequence. The root cause is stated **at product altitude** — what the persona runs into:
« le programme des activités n'est consultable qu'une fois sur place ». The technical reason behind it
(a planning entered by hand at the resort) sits below the brief: it is `/prd`'s and engineering's, and not knowing
it does not make the root cause unknown.

**Shape.**
> **[Persona]** cannot **[critical action]** because **[observable root cause]**, which results in
> **[measurable or observable consequence]**.

**Several root causes?** Test each: *would resolving this cause alone move the outcome?* One passes
→ state it. A few pass → distinct problems: show each with its cost to the persona, the PM chooses,
the others go to §7 (`Future brief`) or a tension. Many pass → the scope is overloaded: say so, and
reopen the outcomes through the backward check. The count is a symptom to read, not a quota.

**Supporting elements** — one line each in §2; derive from the signals, ask only what is missing:

| Element | Answers |
|---|---|
| Root cause | The structural reason the problem persists |
| Why now | What changed recently — behaviour, competition, technical capacity, strategy |
| Workaround | What people do today to get around it |
| Adoption risk | What could keep the persona from changing even with a solution in hand |
| Consequence | What happens to the person who lives it if it is never solved |

## Confidence

Computed from the **typed signals linked to the key problem** — never from how sure anyone sounds.
It grades the evidence that the problem **exists**, not how well its cause is understood: an
unknown cause is a tension and weighs on the readiness verdict, never on this level.

| Level | Criteria |
|---|---|
| `High` | At least one statistically significant `Observed behaviour`, **or** two or more recent, recurring `User verbatim` from independent sources |
| `Medium` | At least one signal graded `Medium` or better, short of `High` — an identifiable `Indirect signal`, an isolated verbatim, partial data |
| `Hypothetical` | Only `Weak` or `Hypothesis` signals — hearsay of unknown origin, benchmarks, deduction |

Below `High`: a **minimal validation plan** — the signal to collect, the method, the acceptable
delay. It is also the home of a discriminating observation raised by *Challenge the framing*.

## Not established — legitimate states

| Situation | Write | And |
|---|---|---|
| Nothing shows what the persona runs into | The sentence without its *because* clause — « [Persona] cannot [critical action], which results in […] » — and `Root cause: Not established`, with the candidates | A `T-XX` — `Blocks`: `—` at Step 2, set to the top opportunity at Step 3's `[C]`. What to collect goes in the validation plan — or, at `High`, in the `T-XX` and the readiness line. The verdict will be *not yet*; confidence is unaffected |
| A supporting element has no source | `Not established` | The same `T-XX` — never an unmarked deduction |
| No persona can be anchored | `no persona — audience […]` | A tension |
| No convergence | The statement says so | The PM chooses the thread; failing that, the brief goes on with `Not established` and its verdict will be *not yet* |

## Checkpoints

With convergent inputs, present the whole chain at the gate. Confirm a layer first — one question —
only when it is uncertain: no input, several candidate personas, no convergence. The answer confirms
that layer, never the step.

## Check

`REF-challenge-pass.md` — *Signals*, *Persona*, *Key problem*. The key problem and the persona
served are the brief's most load-bearing claims: below `High`, *Challenge the framing* usually has
something to say; at `High`, it usually has nothing.
