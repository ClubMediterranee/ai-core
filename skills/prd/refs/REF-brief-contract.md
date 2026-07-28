---
name: ref-brief-contract
description: >
  The contract between a brief and this skill: which fields the PRD consumes,
  what each one becomes downstream, and how to proceed when a brief does not
  carry them. Read at Step 0, before summarizing the brief.
type: reference
---

# Brief Contract — What the PRD Consumes

A PRD translates a **validated problem** into a solution. The problem, the personas and the scope of
opportunities live in the brief; the PRD picks exactly one opportunity and resolves its solution
space. Everything below is what this skill reads out of the brief — and nothing else is expected
from it.

No skill in this repository produces briefs today, so real briefs vary in shape. This file exists so
that the skill degrades **explicitly** rather than improvising: each field says what it becomes, and
what to do when it is missing.

---

## Fields consumed

| Field in the brief | Becomes in the PRD | Missing → |
|---|---|---|
| `status: validated` (frontmatter) | Nothing — it is the precondition | Ask the PM to confirm out loud, log a tension, continue (see below) |
| Problem statement | Framing of §1 Executive Summary | State "Not in the brief" and ask the PM |
| Personas | §2 Personas | Ask the PM — a PRD without an actor cannot produce ACs |
| Opportunities `OPP-XXX` | The Step 1 choice, quoted verbatim in §1 | Ask the PM to name the opportunity; it becomes an untraced scope, log a tension |
| Desired Outcomes / KRs | §7 Lagging Metrics (`LGM-XXX`) | §7 Lagging stays empty and QG-11 warns — the PRD has no success criterion |
| Damage Control | §7 Damage Control (`DC-XXX`) | Write "None identified." — an explicit absence, not a silent one |

`brief` in the PRD frontmatter references the source file, so that `validate_prd.py` can resolve it
and check its `status` (QG-11).

---

## Degradation path

The brief being validated matters because a PRD built on a moving problem is rework waiting to
happen — that is why QG-11 exists. But an unvalidated brief is a **signal, not a wall**: the PM may
legitimately want to explore ahead of formal validation, and this skill's own rule at Step 1 is to
open a tension rather than block a step gate.

So, at Step 0, when the brief has no `status: validated`:

1. Say it plainly — which file, what its status is (or that it has none).
2. Ask the PM whether to continue anyway. Wait for the answer.
3. If they continue, log the tension in `{DOCS_ROOT}/prd/canonical-memory.md` under the PRD's
   section, so the final quality gate reports a known, accepted divergence instead of a surprise.

The two cases that **do** stop the run, because there is nothing to translate:

- `{DOCS_ROOT}/prd/../brief/` does not exist, or contains no `.md` — say so and stop.
- The PM has no brief at all — a PRD needs a problem to translate. Point them at the upstream work
  rather than inventing a problem statement.

---

## Any metric introduced without a brief anchor is a tension

`LGM-XXX` and `DC-XXX` are **imported**, not invented: they are the initiative's success criteria and
they belong to the brief. If the work reveals a metric the brief does not carry, do not quietly add
it — add it and log the divergence, so the brief can be updated. QG-11 checks exactly this.

Leading metrics (`LDM-XXX`) are the exception: they are *derived* in the PRD at Step 5 and have no
brief anchor by design. See `refs/REF-metrics.md`.
