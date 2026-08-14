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
