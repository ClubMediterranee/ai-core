---
name: ref-challenge-pass
description: >
  Challenge Pass protocol: the judged anti-pattern filter applied before every artifact
  presentation and re-presentation (journeys, FUNCs, ACs, metrics), and re-run on the finished
  document at the quality gate. Four tables in one funnel order, holding only what a reader can
  decide — everything a script can decide lives in scripts/validate_prd.py.
type: reference
---

# Challenge Pass — Reference Protocol

The Challenge Pass is an **automatic filter**, not a dialogue step. It applies before every artifact
presentation, whether the artifacts were derived by the agent or provided by the PM.

**Behaviour:**
- Anti-pattern detected → name it + propose the corrected version.
- No anti-pattern → continue silently, no comment.
- Multiple anti-patterns in the same pass → group into one message (these are parallel filters, not
  sequential questions).

**When it runs — without exception:**
- before the **first presentation** of an artifact, on everything derived;
- before every **re-presentation**: an artifact modified since its last pass — the PM's corrections,
  an `[A]` follow-up — goes through the pass again, **on the delta only**: what changed, not the whole
  step's output. The pass may therefore run several times before one `[C]`. That is cheaper than a
  defect frozen after the PM has converged, because rework past convergence invalidates validated
  material;
- at the **quality gate**, once more on the finished document — every table, every section (see
  *At the quality gate* below).

**What belongs here.** Only what a reader can decide. Anything a script can decide — a duplicated
id, a rule citing another rule, a missing column, a dangling reference — belongs to
`scripts/validate_prd.py` and only there. One check, one home: two definitions of the same rule
drift apart, and nobody notices which one the gate applied.

---

## Reading order — the funnel

The four tables share one reading order, so the same question is asked at the same place everywhere.
The rows of each table are sorted by band, and a row shared by several tables sits in the same
relative position in each.

| Band | Question | Why in this position |
|---|---|---|
| 1. Existence | Does this artifact belong here at all? | An artifact outside the perimeter makes every other question moot — nobody fixes the altitude of a step that should not exist |
| 2. Cut | Is it cut at the right place? | A misplaced or duplicated element is wrong before it is badly worded |
| 3. Altitude | Is it at the right level — **technical HOW before design HOW**? | A technical leak binds the PRD to an implementation across the product boundary; a design leak stays recoverable on the product side |
| 4. Wording | Is it stated so it can be tested? | Last, because it only matters for an artifact that has passed the three questions above |

---

## Challenge Pass — User Journeys

| Anti-pattern | What it looks like | How to fix |
|---|---|---|
| Out-of-scope leak | The step covers ground that an `NG-XXX` or the selected `OPP-XXX` excludes — a flow that leaves the opportunity, an action the brief keeps out | Remove the step. If it reveals a real capability, it belongs to another PRD: name that perimeter, log it in the canonical memory → written as an `NG-XXX` in §6 at this step's `[C]` — never mid-derivation, never waiting for Step 6. |
| Error path as step | The step describes the product's response to a failure | Remove from the journey; park in the canonical memory as an ERR candidate for Step 4. |
| Variation misplaced | A `Variation:` step sits after the closing step instead of at the step where it diverges from the nominal path | Move it to the point of divergence — see `REF-user-journeys.md`, *Place each variation where it diverges*. A reader follows the numbering as a sequence. |
| Rule detail in a step | The step states conditions, thresholds, eligibility or content enumerations that do not change the observable path — true, but rule-level. A condition that changes the user's outcome is a variation (see the routing) — this row is for same-outcome detail | Strip the step to action → outcome; park the detail in the canonical memory as a **BR candidate** for Step 4 (*Park and Surface*). |
| Technical HOW | The step names a technical mechanism (API call, data load, endpoint, protocol) | Rewrite as a user action + observable outcome for the user. |
| Design HOW | The step describes a layout position, a scroll mechanic, or a named UI component. A journey step is no longer true if the mockup changes. | Rewrite as: [user action] → [observable outcome], without the UI detail. |
| System as subject | The step uses "The system displays / loads / renders" as the subject | Rewrite with the user as the subject — what they observe, not what the machine does: "the user sees their criteria updated". This holds even when the system is what acts. |

---

## Challenge Pass — Functional Blocks

| Anti-pattern | What it looks like | How to fix |
|---|---|---|
| Out-of-scope leak | The FUNC delivers a capability that an `NG-XXX` or the selected `OPP-XXX` excludes | Drop it. If the capability is real, it belongs to another PRD: name that perimeter and log it in the canonical memory. |
| Rule detail in the capability | The Capability states a rule's conditions — a preselection, a threshold, an eligibility — instead of the capability they serve | Flag it. Keep the capability sentence; the rule goes to §5 as a BR (a BR candidate in the canonical memory until Step 4). |
| Technical HOW leakage | The FUNC names a framework, endpoint, SQL type, or protocol | Flag it. Rewrite as "Users can [verb] [object]" without the technical reference. |
| Design HOW leakage | The FUNC names a UI component, a layout, or an interaction mechanic — in its title, its Capability, its GIVEN or its scenario. **The capability is no longer true if the mockup changes.** | Flag it. Rewrite at product altitude — what the user gets, not the container it arrives in: *view the floor plan without leaving the room sheet*, never *in a modal*. |
| System as subject | The FUNC starts with "The system displays / The API returns / The page renders" | Flag it. Rewrite with the user as the subject. |

Whether a FUNC is **autonomous** — demonstrable without another FUNC acting first — is a cut decided
at derivation, with the PM, by the boundary discriminant of `REF-functional-blocks.md`. It is not
re-litigated here: `[A]` carries it as a pattern when the PM wants to go deeper.

---

## Challenge Pass — Acceptance Criteria

Applies to the four criterion types alike — `BR`, `ST`, `PERM`, `ERR` — unless a row says otherwise.

| Anti-pattern | What it looks like | How to fix |
|---|---|---|
| Out-of-scope leak | A clause can only be violated in a scenario an NG-XXX already excludes | Flag it. Remove the clause. Test: if the NG disappeared, would the clause become necessary again? Yes → it deserves its own BR. No → drop it. |
| Perimeter leak | A clause describes an outcome for logic that no FUNC, BR or ST of *this* PRD governs — it says what happens without this PRD saying why or under which rule | Flag it. Ask the PM which perimeter owns it, then remove the clause and record an NG-XXX naming that perimeter. |
| State re-enumeration | A BR lists an object's states while an ST-XXX is defined for that object | Flag it. Point the BR to ST-XXX rather than repeating the states — one source of truth. |
| Technical HOW | The criterion names an API, endpoint, database, or protocol — in a rule, a transition, a permission condition, or a failure mode | Flag it. Rewrite as an observable condition (e.g. "if the API returns content" → "if content is available for the selected resort"). An `ERR` failure mode is an observable unavailability ("no availability for the new criteria"), never a mechanism ("timeout", "HTTP 500"). |
| Design HOW | The criterion prescribes a layout, alignment, named UI component, or interaction mechanic | Flag it. If a product rule is recoverable: propose it without the design detail. If design-only: mark it as a design spec and remove it from the criteria. |
| Non-testable | The criterion uses subjective language ("clear", "sufficient", "appropriate") with no measurable condition — **or** its expected outcome is not observable at product level (an `ERR` whose expected behaviour is "the error is logged") | Flag it. Propose a rewrite with a precise, binary-testable condition and an outcome someone can observe. |

**Applying the first two.** These are signals, not verdicts. A perimeter leak is the likeliest false
positive when the knowledge base is thin — a redesign starting from little. Ask the PM where the
logic belongs; open an `OQ-XXX` only when they cannot say or choose to defer. Guessing a
destination, or silently logging an open question instead of asking, produces a document that looks
resolved while encoding an unvalidated assumption.

Whether a criterion **encodes an unvalidated assumption** is not a per-artifact question. It is
asked before the gate — *Name the Arbitrations*: a PM-decidable ambiguity is asked, never absorbed —
and verified once, on the whole document, at the quality gate (QG-7).

---

## Challenge Pass — Metrics

| Anti-pattern | What it looks like | How to fix |
|---|---|---|
| LGM/DC without brief anchor | A lagging or damage-control metric that no Desired Outcome or Damage Control item of the brief carries, or one altered on import — with no divergence tension logged | Flag it. Trace it back to the brief line it comes from, or log the divergence as a tension and keep the brief's wording. `LGM` and `DC` are imported, not derived: the brief is their source of truth. |
| Wrong family for the feature | A completion metric (step completion, drop-off) on a pure consultation feature, or an engagement metric on a pure action feature | Flag it. Re-derive from the journeys' dominant interaction type — see `REF-metrics.md`, "LDMs — Feature Type Inference". |
| Lagging disguised as leading | The LDM only becomes measurable after the brief's KR timeframe, so it predicts nothing in time to act on | Flag it. Propose an earlier observable behaviour on the same causal chain. |
| Unmeasurable LDM | The leading metric names a behaviour with no identifiable collection method | Flag it. Name the event that would capture it, or drop the metric — an indicator nobody can read is not one. |

---

## At the quality gate

The same four tables run once more, on the **finished document** — the second movement of the
quality gate in `SKILL.md`. Two things change:

- **Every section is swept**, not only the artifact of a step. The Technical HOW and Design HOW rows
  are transversal here and apply to §1–§10 alike: an endpoint in an open question, a component name
  in a glossary entry, a protocol in an out-of-scope reason fail the same row as they would in a
  FUNC.
- **A finding is fixed before the PRD carries `status: review`** — the pass stays silent when
  clean, as always, but nothing it names is carried into a reviewed document.
