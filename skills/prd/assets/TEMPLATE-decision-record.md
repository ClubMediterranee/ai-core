# Decision record — [Project]

<!--
INSTANTIATION NOTES — delete this comment block in the working file.

One record per project — a project is a brief: Step 1's [C] copies this file once to
`{DOCS_ROOT}/record/<brief-stem>.md` (with no brief, the PM names the project and the file takes
that name) if that file does not exist yet. Never write back into this template: it ships inside the skill
and may sit in a read-only plugin cache.

Append-only: one row per entry, added at the end of its table, never a rewrite of the file. Ids are
prefixed by the PRD that mints them (`D-07-01`, `T-07-01`), so two PRDs written in parallel never
collide. Rows are written at a step's [C], never during derivation. The PRD holds the fact (a rule,
an exclusion, a constraint); this file holds the why no section of the PRD can carry. Tensions
carry a `Status` of `open`, `accepted` or `resolved`; Sources a `Gate` of `kept` or `cut`.

After `status: review`, the PM resolves the last open questions herself: the §9 row goes, and she
writes the Decisions row (`Resolves: OQ-XXX`) by hand as part of the sign-off.
-->

*The why no PRD section can carry: decisions, tensions, frozen vocabulary and sources of every PRD
of this project — one row each, appended at a step's `[C]`. A decision of another PRD is context to
cite, never a requirement to import without a gate.*

## Decisions

| ID | PRD | Step | Decision | Why | Resolves | Affects |
|---|---|---|---|---|---|---|

## Tensions

| ID | PRD | Tension | Status | Resolution | Affects |
|---|---|---|---|---|---|

## Vocabulary

| Term | Definition | PRD |
|---|---|---|

## Sources

| PRD | Source | What it produced | Gate |
|---|---|---|---|
