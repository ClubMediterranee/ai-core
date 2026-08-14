# Step 4 — Write the normative documents

The mechanical counterpart of the Step 3 gate: nothing is re-decided here. Transversal features
first, then the register — so a later citation never points at a document that does not exist yet.
The carrier specs are not touched at this step.

## Conventions to settle before writing

Ask **one question**, grouping the two identity items — they are independent and factual:

> Ask "What is your name?" unless the user's identity is already clear from context.

The name fills `owner:`. Say what the field commits to: the owner is **who arbitrates the §2
attention points**. Without that, it is decorative — and nobody chases a decorative field.

**Id `TF-nn`** — glob `{DOCS_ROOT}/transversal-features/`, extract the leading number of each match,
take the highest, increment by 1. Start at `01` if none exist. If a file matches but carries no
extractable number, **say so and ask** rather than silently restarting at `01`: a colliding id is
exactly the failure this scan exists to prevent.

**File slug** — lowercase kebab-case, no spaces and no `&`. Those characters break the filename
regexes used downstream and turn every shell path into an escaping exercise.

**Rule prefix** — 3 to 4 uppercase letters derived from the slug (`reservation-service` → `RSV`),
**unique** among the existing features; check by glob before fixing it. The prefix is what makes
`RULE-RSV-01` unambiguous in a spec that cites two features.

## Transversal features

One single **Write**, complete, from `assets/TEMPLATE-transversal-feature.md`, into
`{DOCS_ROOT}/transversal-features/` — created here if this is a first run. Never a skeleton filled
over several passes.

Delete the template's instantiation comment (QG-S15 fails while it is there) and leave no
`[placeholder]` behind.

## The register

From `assets/TEMPLATE-synchro.md`, at `{DOCS_ROOT}/SYNCHRO.md`. On an existing one, replace **only**
what sits between the `sync:auto` markers — a replacement is idempotent and position-independent,
whereas computing *where* to insert is what duplicates entries. Everything a human wrote is
preserved.

An entry whose key has disappeared is **marked obsolete**, never deleted: a silent deletion loses the
reasoning that went with it.
