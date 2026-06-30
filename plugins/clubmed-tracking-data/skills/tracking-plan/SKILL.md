---
name: tracking-plan
description: "GA4 tracking-plan engine. From a Figma link, a DRD (Design Requirement Details), or a live URL, infers trackable moments via the 13 interaction patterns, auto-approves every event with a confidence score, and emits a validated plan.json plus a review markdown. Triggers: '/tracking-plan', 'create a tracking plan', 'plan de marquage', 'plan de tracking', 'GA4 plan for this figma', 'tracking plan from this DRD', 'plan de tracking depuis un DRD', 'what should we track on this page', 'tracking plan for this figma'."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent
version: 2.0.0
created-at: 2026-06-16
created-by: "Jeremy Wallez <jeremy.wallez@clubmed.com>"
---

# Tracking Plan — GA4 measurement-plan engine

From a **Figma link**, a **DRD** (Design Requirement Details), or a **live URL**, infer
trackable moments via the **13 interaction patterns**, auto-approve every event with a
confidence score, and emit a **validated `plan.json`** plus a **review markdown** the user
reads and adjusts afterwards.

This is a fully automatic flow — no per-event confirmation. The source is pluggable: a
Phase 2 resolver branches to the right adapter (figma / drd / url), and every adapter
produces the same signal shape so inference is source-agnostic. Other renderers
(Excel/Confluence/PDF) consume the same `plan.json`.

---

## Architecture — 3 subagents + 2 inline phases + 1 inline validation

**Fully automatic flow — no interactive confirmation.** The skill infers a complete,
viable plan, auto-approves every entry (each carries its `confidence` score), validates
it, and renders the review markdown. The user reviews the rendered `.md` afterwards and
adjusts outside the skill.

State is tracked in `meta.steps` and `meta.status` inside `plan.json` throughout.

```
SKILL (orchestrator — owns meta.status and meta.steps transitions)
  │
  ├─ Phase 0 — SUBAGENT  [steps/gtm/agent.md]  ← required, blocks if GTM MCP absent
  │    → reads mcp__gtm__list_variables + mcp__gtm__list_tags
  │    → writes OUTPUT_DIR/gtm-snapshot.json  (cache 24h, --refresh to force)
  │    → orchestrator sets meta.steps["gtm-snapshot"]: "done"
  │
  ├─ Phase 1 — INLINE
  │    steps/init.md
  │    → meta.status: "draft" · meta.steps all "pending"
  │
  ├─ Phase 2 — SUBAGENT  [source resolver, branches on meta.source_type]
  │    ├─ figma → steps/figma/agent.md   (figma-client per URL)
  │    ├─ drd   → steps/drd/agent.md      (copy DRD screens + extract drd-context.md)
  │    └─ url   → steps/url/agent.md      (agent-browser: observe live + explore, then
  │                                        scripts/url_to_signals.py normalises signals)
  │    → all branches write OUTPUT_DIR/signals/*.json (figma-client shape)
  │      (drd also writes OUTPUT_DIR/drd-context.md — human-validated, primary for infer)
  │      (url also writes observed_events[] inside each signal — existing live tracking)
  │    → orchestrator sets meta.steps["extract-source"]: "done"
  │
  ├─ Phase 3 — SUBAGENT  [steps/infer/agent.md]
  │    rules: steps/infer/rules/*.md
  │    reads signals/*.json + gtm-snapshot.json (+ drd-context.md if present)
  │    → confirmed events + validated param names; DRD context PRIMES when present
  │    → entries[] with _status: "approved" (best-effort viable payload + params)
  │    → orchestrator sets meta.steps["infer"]: "done", meta.status: "ready"
  │
  ├─ Phase 4 — INLINE BASH (guaranteed, no LLM)
  │    python3 scripts/validate_schema.py plan.json
  │    Fix errors · retry max 3
  │    → meta.steps["validate-plan"]: "done"
  │
  └─ Phase 5 — INLINE (orchestrator)  [render markdown]
       → python3 ../tracking-plan-render/scripts/render_markdown.py plan.json OUTPUT_DIR
       → writes OUTPUT_DIR/<plan-name>.md  (review document for the user)
       → meta.steps["render"]: "done"
```

**Ownership rule — strictly enforced:**
- Agents write their own `meta.steps[<their_key>]` only for `"inprogress"` signals (optional).
- **Only the orchestrator** sets `meta.steps[key] = "done"` and `meta.status`.
- This prevents the retry loop from being short-circuited by an agent marking itself done.

### `meta.status` — global plan lifecycle
- `draft` — init done, inference not yet run
- `ready` — inference ran, all entries auto-approved, plan ready to validate and render

`inprogress` remains in the schema enum for backward compatibility but is no longer an
expected resting state — the flow goes `draft → ready` in one inference pass.

The validator still gates on `meta.status`: any `pending_approval` entry when
`meta.status = "ready"` is a hard error. In the automatic flow no entry should be
`pending_approval`, so this is a safety net against manually-introduced ones.

**`meta.status` must reach `ready` before the plan can be rendered.**

### `meta.steps` — per-phase execution state
- `pending`    — not started
- `inprogress` — subagent currently running (set before spawn, guards against lost crashes)
- `done`       — completed successfully

### `_status` on entries
- `approved`         — written by inference-agent (the automatic flow's default)
- `pending_approval` — legacy/manual only; flagged by the validator when status is ready
- `rejected`         — manual only (kept in entries[] for audit, excluded by renderers)

---

## Seed data (`data/`)

- `data/event-catalog.json`       — 13 patterns + 29 canonical events. Match here first.
- `data/plan.schema.json`         — closed JSON Schema the output MUST satisfy.
- `data/live-coverage.json`       — which events are confirmed live.

---

## Orchestration script

Follow these phases in order. Never skip a phase whose step key is not `"done"`.

**On resume:** read `meta.steps` from `plan.json`. Skip all phases whose key is `"done"`.
Start from the first `"pending"` or `"inprogress"` phase.

### Phase 0 — GTM snapshot (subagent, required)

**The GTM MCP is required.** Before doing anything else, verify it is connected.
Try calling `mcp__gtm__list_accounts`. If it fails or is unavailable — **stop immediately**
and display:

```
❌ The GTM MCP server is not connected.

The tracking-plan skill requires access to Google Tag Manager to:
  • Confirm which events already have a GA4 tag (origin: confirmed)
  • Validate parameter names against declared Data Layer variables

To install it, run:
  claude mcp add -t http gtm https://mcp.gtmeditor.com

Then authenticate with your Google account and re-run the skill.
```

Do NOT proceed to Phase 1 until the MCP is available and authenticated.

Once confirmed available, read `steps/gtm/agent.md` → `<GTM_AGENT>`, then spawn:
```
Agent(prompt: "<GTM_AGENT>\n\nCONTEXT:\n  OUTPUT_DIR=${OUTPUT_DIR}\n  GTM_ACCOUNT=${GTM_ACCOUNT:-}\n  GTM_CONTAINER=${GTM_CONTAINER:-}\n  FORCE_REFRESH=${FORCE_REFRESH:-false}")
```

Set step done:
```bash
python3 -c "
import json; p=json.load(open('${PLAN_FILE}'))
p['meta']['steps']['gtm-snapshot']='done'
json.dump(p,open('${PLAN_FILE}','w'),indent=2)
"
```

### Phase 1 — Init (inline)

Read and execute `steps/init.md`.

### Phase 2 — Source extraction (subagent, branches on source_type)

Read `meta.source_type` from plan.json and pick the matching adapter. All adapters write
`${OUTPUT_DIR}/signals/*.json` in the figma-client shape; the `drd` branch also writes
`${OUTPUT_DIR}/drd-context.md`.

```bash
# Mark inprogress before spawning
python3 -c "
import json; p=json.load(open('${PLAN_FILE}'))
p['meta']['steps']['extract-source']='inprogress'
json.dump(p,open('${PLAN_FILE}','w'),indent=2)
"
SOURCE_TYPE=$(python3 -c "import json;print(json.load(open('${PLAN_FILE}'))['meta'].get('source_type','figma'))")
```

Branch on `${SOURCE_TYPE}`:

- **`figma`** — read `steps/figma/agent.md` → `<SRC_AGENT>`, spawn:
  ```
  Agent(prompt: "<SRC_AGENT>\n\nCONTEXT:\n  PLAN_FILE=${PLAN_FILE}\n  OUTPUT_DIR=${OUTPUT_DIR}\n  FIGMA_URLS=${FIGMA_URLS}\n  SKILL_DIR=${SKILL_DIR}\n  PROJECT_ROOT=${PROJECT_ROOT}\n  HINTS=${HINTS}")
  ```
- **`drd`** — read `steps/drd/agent.md` → `<SRC_AGENT>`, spawn:
  ```
  Agent(prompt: "<SRC_AGENT>\n\nCONTEXT:\n  PLAN_FILE=${PLAN_FILE}\n  OUTPUT_DIR=${OUTPUT_DIR}\n  DRD_PATH=${DRD_PATH}\n  SKILL_DIR=${SKILL_DIR}\n  PROJECT_ROOT=${PROJECT_ROOT}\n  HINTS=${HINTS}")
  ```
- **`url`** — read `steps/url/agent.md` → `<SRC_AGENT>`, spawn:
  ```
  Agent(prompt: "<SRC_AGENT>\n\nCONTEXT:\n  PLAN_FILE=${PLAN_FILE}\n  OUTPUT_DIR=${OUTPUT_DIR}\n  URLS=${URLS}\n  SKILL_DIR=${SKILL_DIR}\n  PROJECT_ROOT=${PROJECT_ROOT}\n  HINTS=${HINTS}")
  ```
  The url agent observes live tracking (GA4 /collect + data layer) and explores the page,
  then `scripts/url_to_signals.py` writes `signals/*.json` with an `observed_events[]` block.

When the agent returns, verify `${OUTPUT_DIR}/signals/` has at least one `.json`:
```bash
ls "${OUTPUT_DIR}/signals/"*.json 2>/dev/null | wc -l
```

Then set done:
```bash
python3 -c "
import json; p=json.load(open('${PLAN_FILE}'))
p['meta']['steps']['extract-source']='done'
json.dump(p,open('${PLAN_FILE}','w'),indent=2)
"
```

### Phase 3 — Inference (subagent)

```bash
python3 -c "
import json; p=json.load(open('${PLAN_FILE}'))
p['meta']['steps']['infer']='inprogress'
json.dump(p,open('${PLAN_FILE}','w'),indent=2)
"
```

Read the following files:
- `steps/infer/agent.md` → `<INFER_AGENT>`
- `steps/infer/rules/reuse-before-invent.md` → `<R1>`
- `steps/infer/rules/double-push-pattern.md` → `<R2>`
- `steps/infer/rules/confidence-and-origin.md` → `<R3>`
- `steps/infer/rules/anchor-target.md` → `<R4>`
- `steps/infer/rules/plan-language.md` → `<R5>`

If `${OUTPUT_DIR}/drd-context.md` exists (DRD source), read it → `<DRD_CONTEXT>` and inject
it. It is the **primary** event source — it primes over raw signals. If it does not exist
(Figma/URL source), omit the DRD_CONTEXT block entirely.

Then spawn (include the `DRD_CONTEXT:` line only when the file exists):
```
Agent(prompt: "<INFER_AGENT>\n\nRULES:\n<R1>\n<R2>\n<R3>\n<R4>\n<R5>\n\nDRD_CONTEXT:\n<DRD_CONTEXT>\n\nCONTEXT:\n  PLAN_FILE=${PLAN_FILE}\n  OUTPUT_DIR=${OUTPUT_DIR}\n  SKILL_DIR=${SKILL_DIR}\n  HINTS=${HINTS}")
```

When the agent returns, verify entries were written and none are `pending_approval`
(the automatic flow approves everything):
```bash
python3 -c "
import json; p=json.load(open('${PLAN_FILE}'))
total=len(p['entries'])
approved=sum(1 for e in p['entries'] if e.get('_status')=='approved')
pending=sum(1 for e in p['entries'] if e.get('_status')=='pending_approval')
print(f'{total} entries · {approved} approved · {pending} pending')
"
```

Then set done and mark the plan ready (all entries are auto-approved):
```bash
python3 -c "
import json; p=json.load(open('${PLAN_FILE}'))
p['meta']['steps']['infer']='done'
p['meta']['status']='ready'
json.dump(p,open('${PLAN_FILE}','w'),indent=2)
"
```

### Phase 4 — Validation (inline Bash — guaranteed)

```bash
python3 "${SKILL_DIR}/scripts/validate_schema.py" "${PLAN_FILE}"
```

`meta.status = "ready"`, so the validator enforces B1 (no `pending_approval` entries) as a
hard error. In the automatic flow every entry is already `approved`, so this is a safety
net — if it trips, an entry was left unapproved and must be fixed.

On failure: read the error report, fix offending entries in plan.json, retry. Max 3 attempts.
On success: set `meta.steps["validate-plan"] = "done"` and continue to Phase 5.

### Phase 5 — Render markdown (inline)

Render the review document the user will read. Reuse the existing markdown renderer from
the `tracking-plan-render` skill (sibling directory). Language defaults to the user's
language (`fr` or `en`).

```bash
python3 "${SKILL_DIR}/../tracking-plan-render/scripts/render_markdown.py" "${PLAN_FILE}" "${OUTPUT_DIR}" "${LANG:-en}"
```

This writes `${OUTPUT_DIR}/<plan-name>.md` with every approved event, each showing its
confidence level (colour-coded bar). Set the step done:
```bash
python3 -c "
import json; p=json.load(open('${PLAN_FILE}'))
p['meta']['steps']['render']='done'
json.dump(p,open('${PLAN_FILE}','w'),indent=2)
"
```

Print final summary:
```
✓ <PLAN_NAME> — plan generated (auto-approved)
  entries   : <a> approved
  events    : <distinct event names>
  review    : <output-dir>/<plan-name>.md  ← read & adjust here
  artifacts : <output-dir>/plan.json
```

---

## Output

Default: `docs/tracking/plans/<plan-name>/plan.json`

```
<output-dir>/
  plan.json          ← canonical validated plan (all entries auto-approved)
  <plan-name>.md     ← review document with per-event confidence (read & adjust here)
  signals/           ← per-screen extraction in figma-client shape (any source) + images/
  drd-context.md     ← condensed human-validated DRD context (DRD source only)
  gtm-snapshot.json  ← GTM variables + tags cache (24h)
```

---

## Notes

- Never read raw figma-client JSON with the Read tool — always use the compact reader.
- Re-run with new Figma URLs to extend an existing plan (resume picks up from last done step).
- `meta.schema_version` is required; the schema is closed (unknown keys fail validation).
