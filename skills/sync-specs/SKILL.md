---
name: sync-specs
description: >
  Detect and document the synchronisation points between specs of *different* PRDs — the shared
  endpoints, shared editorial keys and shared mechanisms that no single spec owns. Joins the specs
  on the machine-readable keys of their §8 Data Contract, then either records a **synchro** in the
  register or extracts a **transversal feature** (a normative document carrying rules and their
  variation points, with no tests of its own). Proposes the citations to add to the carrier specs
  and, once confirmed, applies them. Use whenever the user says "/sync-specs", "synchro entre
  specs", "synchro inter-PRD", "adhérences fonctionnelles", "mécanique commune", "factoriser des
  règles partagées", "quelles specs partagent le même endpoint", "check the sync between specs",
  "find shared mechanisms across PRDs", or asks whether two features must stay aligned — even when
  they only say "est-ce que ces deux PRD se marchent dessus ?". Runs on specs produced by the `spec`
  skill; NOT for writing a spec (that is `spec`) or a PRD (that is `prd`).
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Skill, mcp__clubmed_api__*
version: 1.2.0
changelog:
  - version: 1.2.0
    date: 2026-08-13
    changes:
      - Drift check against the `spec` skill, run before the detector — the copied parsers can no longer diverge silently
      - Grouping hint in the report plus a rule-by-rule test for "one mechanism or two"
      - The machine-read constraints are written in the templates instead of only in the code
      - `TF-nn` id format and uniqueness enforced (QG-S1); unwritten labels have a destination
  - version: 1.1.0
    date: 2026-08-13
    changes:
      - Two gates — the mechanism is settled before the spec edits, which cannot be written until the rule ids exist
      - Steps extracted to `steps/`, loaded on demand
      - Variation points anchored in the §8 Data Contract, with no "not applicable" binding (QG-S17)
      - Degraded cases, naming conventions, and publication via `github-publish`
  - version: 1.0.0
    date: 2026-08-13
    changes:
      - Initial release — detector, register, transversal features, citation graph and quality gates
created-at: 2026-08-13
created-by: "Céline Net <celine.net.ext@clubmed.com>"
---

# Sync specs

Two specs of **different** PRDs can name the same endpoint or the same editorial key and say
different things about it. Nothing catches that today: the `spec` skill aligns everything **within**
one PRD, and no tool compares one PRD's specs with another's.

- **Never re-open what `spec` settled** — no endpoint re-validation, no label re-grounding, no
  PRD↔DRD confrontation. Start where each PRD's specs are already coherent among themselves.
- **The comparison is spec against spec.** The PRD is only the grouping dimension, the thing that
  tells a shared key apart from a merely sibling one. **No PRD file is ever read.**
- **A shared endpoint** *may* mean a shared rule — a candidate for judgement. **A shared CMS key**
  *must* mean the same label — a defect when it diverges.

## How the skill works

| Step | What happens | Gate | Full instructions |
|---|---|---|---|
| 0 | Resolve the roots, **read what already exists** — transversal features and register | — | `steps/step-0-context.md` |
| 1 | Run the detector | — | `steps/step-1-detect.md` |
| 2 | Deduplicate against what exists, **by key and never by title** | — | `steps/step-2-deduplicate.md` |
| **3** | Draft the rules and the variation points, then propose the **mechanism** | 🙋 **gate 1** | `steps/step-3-propose-mechanism.md` |
| 4 | Write the transversal features, then the register | — | `steps/step-4-write-documents.md` |
| **5** | Propose the **exact edits** to the carrier specs | 🙋 **gate 2** | `steps/step-5-propose-spec-edits.md` |
| 6 | Apply them by surgical `Edit` | — | `steps/step-6-apply-citations.md` |
| 7 | Quality gates, non-regression diff, report, publish | blocking on ERROR | `steps/step-7-validate.md` |

**Why two gates.** Gate 1 settles a *product* question — does this mechanism deserve a normative
document? Gate 2 settles a *surgical* one — do we edit specs someone else already wrote and reviewed?
Different risk, different reviewer. And gate 2's material does not exist before Step 4: a citation
names rule ids (`RULE-RSV-01`) that the feature creates.

**When they merge.** A run that creates **no new identifier** — attaching a carrier to an existing
feature, or a register entry alone — can state its edits at Step 3. Present them there and skip
gate 2. The rule, not an exception: *gate 2 exists because the ids do not exist yet.*

## Bundled resources

| Resource | When |
|---|---|
| `ADHERENCES-spec.md` | Step 1 — what `sync-specs` borrows from `spec`, and what breaks if it changes |
| `scripts/check_spec_drift.py` | Step 1 — proves the parsers borrowed from `spec` have not drifted |
| `scripts/sync_specs.py` | Step 1 — the detector. Deterministic, offline, stdlib only |
| `refs/REF-join-keys.md` | Step 1 — what is a join key, what is not, and why |
| `refs/REF-endpoint-resolution.md` | Step 1 — only if the detector reports an elided endpoint |
| `refs/REF-extraction-criteria.md` | Step 3 — register or transversal feature, and at what granularity |
| `refs/REF-challenge-pass.md` | Step 3 — the filter to run before *every* presentation |
| `refs/REF-quality-gates.md` | Step 3 — how what you are about to write will be measured; re-read at Step 7 |
| `assets/TEMPLATE-transversal-feature.md` | Step 3 to see the shape you must fill, Step 4 to write it |
| `assets/TEMPLATE-synchro.md` | Step 4 — the register |
| `refs/REF-citation-feature.md` | Step 5 — citation syntax and binding the variation points |
| `scripts/validate_sync.py` | Step 7 — the quality gates on everything produced |

`<skill-dir>` is this skill's own directory — the one containing this file. `<spec-skill-dir>` is the
`spec` skill's, a sibling of it (`../spec`).

## Golden Rules

### Human-In-The-Loop

Ask one question at a time. Up to two may be grouped when they are clearly independent and factual.
Wait for the answer before surfacing the gate.

### Step Confirmation

No passive progression. Nothing is created before gate 1, and no spec is touched before gate 2 —
this skill writes into documents that have already been reviewed.

### Language Adaptation

Detect the user's language from their first message and apply it to your messages and to the
documents you produce.

**What does not translate:** the HTML anchors (`sync:auto`, `sync:keys`, `dc:index`, `at:tests`), the
id prefixes (`RULE-`, `VAR-`, `TF-`, `QG-`, `BR-`, `ST-`, `ERR-`, `FUNC-`), frontmatter keys, and the
citation syntax. The scripts match on these — a translated anchor is an invisible break.

### Challenge Pass

Read `refs/REF-challenge-pass.md` and apply it before **every** presentation. It is a filter, not a
dialogue step: an anti-pattern found is named and corrected in the same message; none found means
you continue silently.

### Paths

Links **in the body** of a produced document are relative to the `knowledge-base` repo root
(`dcx/booking-engine/docs/specs/…`) — those documents are read on GitHub, where an absolute path is
dead. **Inside a spec's frontmatter**, `related_specs` and `transversal_features` keep the `spec`
skill's convention: relative to the spec file, so `validate_specs.py` resolves them.
