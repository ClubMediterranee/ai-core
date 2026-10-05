# `prd` — write a PRD from a brief, one gated step at a time

A PM runs it in Claude Code; the agent derives scope, user journeys, functional blocks, acceptance
criteria and metrics, one step at a time, and writes nothing to the PRD before the PM validates the
step at its gate. A deterministic validator runs at every gate; a project-level decision record
keeps the why no PRD section can carry. This file is for maintainers and forkers — Claude Code
never loads it.

## Layout

| Path | Role |
|---|---|
| `SKILL.md` | The process overview and the golden rules first (they must survive a context compaction), then Steps 1–6 and the quality gate |
| `references/REF-*.md` | One methodology per step, read when the step starts |
| `references/ui-lexicon.txt` | UI-component nouns the validator warns on (QG-2) — calibrate here, not in the script |
| `assets/TEMPLATE-prd.md` | The PRD skeleton copied at Step 1 |
| `assets/TEMPLATE-decision-record.md` | The project record created at Step 1's `[C]`, `{DOCS_ROOT}/record/<brief-stem>.md` |
| `scripts/validate_prd.py` | The validator — stdlib only, Python 3.8+; `--up-to N` at each gate, full at the quality gate |
| `decision-record.md` | Why the skill is designed this way (in French — a sanctioned exception) |
| `CHANGELOG.md` | Full version history |
| `../../tests/prd/` | The validator's tests, outside the packaged skill |

Tests, from the repository root: `python3 -m unittest tests.prd.test_validate_prd`.

## Adapting this skill

What is specific to the organisation that wrote it, where it lives, and why it is there.

| Tunable | Where | Why it exists |
|---|---|---|
| UI-component lexicon (QG-2's script half) | `references/ui-lexicon.txt` | Calibrated per campaign; one `lang:` line per language — add yours |
| AI-author guard | `scripts/validate_prd.py`, `AI_AUTHOR_RE` | `claude` alone is a human first name — keep it out of the pattern |
| Legacy 3-column Lagging Metrics header | `scripts/validate_prd.py`, `TABLE_HEADERS["Lagging Metrics"]` | PRDs written before the `Baseline (T0)` column; drop once they are migrated |
| Brief contract fields | `references/REF-brief-contract.md` | What a brief must carry; the `brief` skill of this repository produces them |
| Machine tokens — section titles, §5/§7 sub-headings, id prefixes, labels, markers, record headings | `SKILL.md` *Language Adaptation* | Read literally by the validator and by the downstream `spec` skill: change both, never one |
| Docs-root layout (`brief/`, `prd/`, `record/`) | `SKILL.md` Step 1 | `brief/` and `prd/` shared with `spec`; `briefs/` is accepted |
| Examples | the references | A neutral online shop — replace them or not, they are never facts about your product |
| Design source name (DRD) | `SKILL.md` *Derive from everything* | Your mockups, Figma file or design requirement document |
| Complexity grid | `references/REF-complexity-sizing.md`, `COMPLEXITY_GRID` | Consultative (WARN, never ERROR) |
| Compaction hook | `plugins/clubmed-product/hooks/` | Re-anchors a session after a context compaction; plugin install only — a skill copied by hand has none |
| Confirmation words | `SKILL.md` *What validates a step* | Given in the PM's language; the French ones are examples |

The validator's checks are listed step by step in its own docstring; `one check, one home` is the
rule that keeps the script, the Challenge Pass and the gate's judged crossings from restating each
other.
