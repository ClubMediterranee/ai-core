---
name: ref-brief-contract
description: >
  The contract between a brief and this skill: which fields the PRD consumes,
  what each one becomes downstream, and how to proceed when a brief does not
  carry them. Read at Step 1, before summarizing the brief.
type: reference
---

# Brief Contract — What the PRD Consumes

A PRD translates a **validated problem** into a solution. The problem, the personas and the scope of
opportunities live in the brief; the PRD picks exactly one opportunity and resolves its solution
space. Everything below is what this skill reads out of the brief — and nothing else is expected
from it.

The `brief` skill produces briefs, but real briefs still vary in shape, and a PRD may be framed
without one. This file exists so that the skill degrades **explicitly** rather than improvising:
each field says what it becomes, and what to do when it is missing.

---

## Fields consumed

| Field in the brief | Becomes in the PRD | Missing → |
|---|---|---|
| `status: validated` (frontmatter) | Nothing — it is the precondition | Ask the PM to confirm out loud; a Tensions row (`accepted`) in the record at Step 1's `[C]`; continue (see below) |
| Problem statement | Framing of §1 Executive Summary | State "Not in the brief" and ask the PM |
| Personas | §2 Personas | Ask the PM — a PRD without an actor cannot produce ACs |
| Opportunities `OPP-XXX` | The Step 1 choice, quoted verbatim in §1 | Ask the PM to name the opportunity; it becomes an untraced scope — a Tensions row at Step 1's `[C]` |
| Desired Outcomes / KRs | §7 Lagging Metrics (`LGM-XXX`) | Write "None identified." in §7 Lagging and a Tensions row at Step 5's `[C]` — the PRD has no success criterion. Leaving the subsection blank is a QG-8 **error**, not a warning |
| Damage Control | §7 Damage Control (`DC-XXX`) | Write "None identified." — an explicit absence, not a silent one |
| §5 Cuts | A journey never crosses a cut; a cut this PRD must restate is an NG in §6 at the `[C]` that meets it | Nothing |
| §5 Constraints | §10 Constraints (`CB-XXX` / `CL-XXX`), where a constraint shapes a capability | Nothing: §10's legend states the baseline |
| §6 Open Tensions `T-XX` | A question to the PM before the gate that meets it; still open afterwards → a Tensions row in the record | Nothing |
| §7 Parked, rows `For: /prd` | Candidates judged at the step that consumes them — a section row, from Step 1's `[C]` on a `## Parked` row, or an NG | Nothing: the table may hold no `/prd` row |

`brief` in the PRD frontmatter references the source file, so that `validate_prd.py` can resolve it
and check its `status` (QG-11).

---

## Degradation path

The brief being validated matters because a PRD built on a moving problem is rework waiting to
happen — that is why QG-11 exists. But an unvalidated brief is a **signal, not a wall**: the PM may
legitimately want to explore ahead of formal validation, and this skill's own rule at Step 1 is to
open a tension rather than block a step gate.

So, at Step 1, when the brief has no `status: validated`:

1. Say it plainly — which file, what its status is (or that it has none).
2. Ask the PM whether to continue anyway. Wait for the answer.
3. If they continue, the tension (`accepted`) is written to `{DOCS_ROOT}/record/<brief-stem>.md`
   at Step 1's `[C]`, so the final quality gate reports a known, accepted divergence instead of a
   surprise.

**No brief at all** is not a wall either. The fields above are what Step 1 expects; look for them
in `{DOCS_ROOT}` (context documents, a glossary, other PRDs), and ask the PM for what is missing in
one `AskUserQuestion` call — never invent a problem statement. The PM names the project (the
record's stem); the frontmatter carries `brief: none` and `record: <project>`; §1's Source line
carries the frame confirmed at Step 1; the absence is a Tensions row (`accepted`).
`validate_prd.py` warns (QG-11) and does not fail, provided `record` is set.

---

## Any metric introduced without a brief anchor is a tension

`LGM-XXX` and `DC-XXX` are **imported**, not invented: they are the initiative's success criteria and
they belong to the brief. If the work reveals a metric the brief does not carry, do not quietly add
it — add it and record the divergence as a tension, so the brief can be updated. QG-11 checks exactly this.

Leading metrics (`LDM-XXX`) are the exception: they are *derived* in the PRD at Step 5 and have no
brief anchor by design. See `references/REF-metrics.md`.
