---
name: ref-challenge-pass
description: >
  Challenge Pass protocol: automatic anti-pattern filter applied before
  every artifact presentation (journeys, FUNCs, ACs). Consolidated anti-pattern
  tables for all three artifact types.
type: reference
---

# Challenge Pass — Reference Protocol

The Challenge Pass is an **automatic filter**, not a dialogue step. It applies before every artifact presentation, whether the artifacts were derived by the agent or provided by the PM.

**Behavior:**
- Anti-pattern detected → name it + propose the corrected version.
- No anti-pattern → continue silently, no comment.
- Multiple anti-patterns in the same pass → group into one message (these are parallel filters, not sequential questions).

**Trigger — without exception:** before any presentation, whether the artifact was derived by the agent or provided by the PM.

---

## Challenge Pass — User Journeys

| Anti-pattern | What it looks like | How to fix |
|---|---|---|
| Design HOW | The step describes a layout position, a scroll mechanic, or a named UI component. A journey step is no longer true if the mockup changes. | Rewrite as: [user action] → [observable outcome], without the UI detail. |
| Technical HOW | The step names a technical mechanism (API call, data load, endpoint, protocol) | Rewrite as a user action + observable outcome for the user. |
| System as subject | The step uses "The system displays / loads / renders" as the subject | Rewrite with the user as the subject. |
| Macro step | The step bundles several distinct user actions ("picks destination, dates and family composition") | Split into one step per user action. |
| Bi-goal journey | Two distinct final outcomes coexist in the same flow | Split into two journeys — one goal accomplished per journey. |
| Error path as step | The step describes the product's response to a failure | Remove from the journey; park in the canonical memory as an ERR candidate for Step 4. |

---

## Challenge Pass — Functional Blocks

| Anti-pattern | What it looks like | How to fix |
|---|---|---|
| Tech HOW leakage | The FUNC names a framework, endpoint, SQL type, or protocol | Flag it. Rewrite as "Users can [verb] [object]" without the technical reference. |
| Design HOW leakage | The FUNC names a UI component, a layout, or an interaction mechanic | Flag it. Rewrite as a user capability with an observable outcome. |
| System as subject | The FUNC starts with "The system displays / The API returns / The page renders" | Flag it. Rewrite with the user as the subject. |

---

## Challenge Pass — Acceptance Criteria

| Anti-pattern | What it looks like | How to fix |
|---|---|---|
| Technical HOW in a BR | The BR names an API, endpoint, database, or protocol | Flag it. Rewrite as an observable condition (e.g. "if the API returns content" → "if content is available for the selected resort"). |
| Design HOW in a BR | The BR prescribes a layout, alignment, named UI component, or interaction mechanic | Flag it. If a product rule is recoverable: propose it without the design detail. If design-only: mark as a design spec, remove from BR. |
| Non-testable BR | The BR uses subjective language ("clear", "sufficient", "appropriate") with no measurable condition | Flag it. Propose a rewrite with a precise, binary-testable condition. |
| AC that formalizes an ambiguity | The AC encodes an unvalidated answer to an open question — the "rule" hides a business decision that has not been made | Flag it. If the answer is known: keep as AC. If uncertain: remove the AC, create an OQ-XXX open question instead. |
| BR referencing a BR | The body of a BR cites another BR ("see BR-XXX", "aligned with BR-XXX") | Flag it. Rewrite the rule so it stands alone. If an object's state is involved, cite ST-XXX instead. |
| State re-enumeration | A BR lists an object's states while an ST-XXX is defined for that object | Flag it. Point the BR to ST-XXX rather than repeating the states — one source of truth. |
| Out-of-scope leak | A clause can only be violated in a scenario an NG-XXX already excludes | Flag it. Remove the clause. Test: if the NG disappeared, would the clause become necessary again? Yes → it deserves its own BR. No → drop it. |
| Perimeter leak | A clause describes an outcome for logic that no FUNC, BR or ST of *this* PRD governs — it says what happens without this PRD saying why or under which rule | Flag it. Ask the PM which perimeter owns it, then remove the clause and record an NG-XXX naming that perimeter. |

**Applying the last two.** These are signals, not verdicts. A perimeter leak is the likeliest false
positive when the knowledge base is thin — a redesign starting from little. Ask the PM where the
logic belongs; open an `OQ-XXX` only when they cannot say or choose to defer. Guessing a
destination, or silently logging an open question instead of asking, produces a document that looks
resolved while encoding an unvalidated assumption.
