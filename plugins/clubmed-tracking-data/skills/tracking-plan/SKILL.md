---
name: tracking-plan
description: "GA4 tracking-plan engine. From a Figma link, infers trackable moments via the 13 interaction patterns, confirms each event candidate with the user, and emits a validated plan.json. Triggers: '/tracking-plan', 'create a tracking plan', 'plan de marquage', 'plan de tracking', 'GA4 plan for this figma', 'what should we track on this page', 'tracking plan for this figma'."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent
version: 2.0.0
created-at: 2026-06-16
created-by: "Jeremy Wallez <jeremy.wallez@clubmed.com>"
---

# Tracking Plan — GA4 measurement-plan engine

From a **Figma link**, infer trackable moments via the **13 interaction patterns**,
confirm each candidate with the user, and emit a **validated `plan.json`**.

This skill stops at the validated plan. Rendering (Excel/Confluence/Markdown) is handled
by separate renderer skills that consume `plan.json`.

---

## Architecture — 2 subagents + 2 inline phases + 1 inline validation

The skill orchestrates 2 isolated subagents and 3 inline phases.
State is tracked in `meta.steps` and `meta.status` inside `plan.json` throughout.

**Critical constraint:** `AskUserQuestion` is only available in the main orchestrator
context — it cannot be called from inside a spawned `Agent()`. Phase 4 (confirm) MUST
be inline.

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
  ├─ Phase 2 — SUBAGENT  [steps/figma/agent.md]
  │    → figma/*.json per screen
  │    → orchestrator sets meta.steps["extract-figma"]: "done"
  │
  ├─ Phase 3 — SUBAGENT  [steps/infer/agent.md]
  │    rules: steps/infer/rules/*.md
  │    reads gtm-snapshot.json → confirmed events + validated param names
  │    → entries[] with _status: "pending_approval"
  │    → orchestrator sets meta.steps["infer"]: "done", meta.status: "inprogress"
  │
  ├─ Phase 4 — INLINE (orchestrator) ← AskUserQuestion only works in main context
  │    steps/confirm/agent.md + rules loaded as instructions
  │    → AskUserQuestion per pending_approval entry, one call per entry
  │    → _status: "approved" | "rejected" written after each answer
  │    → orchestrator sets meta.steps["confirm"]: "done", meta.status: "ready"
  │       only when 0 pending_approval remain
  │
  ├─ Phase 5 — INLINE BASH (guaranteed, no LLM)
  │    python3 scripts/validate_schema.py plan.json
  │    Fix errors · retry max 3
  │    → meta.steps["validate-plan"]: "done"
  │
  └─ Phase 6 — INLINE (orchestrator)  [steps/enrich/agent.md]
       → Propose adding new event patterns to event-catalog.json
       → Ask user for missing events not proposed by inference
       → Manually added events written with origin: confirmed
       → meta.steps["enrich"]: "done"
```

**Ownership rule — strictly enforced:**
- Agents write their own `meta.steps[<their_key>]` only for `"inprogress"` signals (optional).
- **Only the orchestrator** sets `meta.steps[key] = "done"` and `meta.status`.
- This prevents the retry loop from being short-circuited by an agent marking itself done.

### `meta.status` — global plan lifecycle
- `draft`      — init done, inference not yet run
- `inprogress` — inference ran, `pending_approval` entries exist (expected, not an error)
- `ready`      — all entries confirmed/rejected, document finalized

The validator gates on `meta.status`:
- `draft | inprogress` → `pending_approval` entries = warning only
- `ready`              → `pending_approval` entries = hard error (claimed done but isn't)

**`meta.status` must reach `ready` before the plan can be rendered.**

### `meta.steps` — per-phase execution state
- `pending`    — not started
- `inprogress` — subagent currently running (set before spawn, guards against lost crashes)
- `done`       — completed successfully

### `_status` on entries
- `pending_approval` — written by inference-agent, awaiting user confirmation
- `approved`         — user confirmed in confirm-agent
- `rejected`         — user skipped (kept in entries[] for audit, excluded by renderers)

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

### Phase 2 — Figma extraction (subagent)

```bash
# Mark inprogress before spawning
python3 -c "
import json; p=json.load(open('${PLAN_FILE}'))
p['meta']['steps']['extract-figma']='inprogress'
json.dump(p,open('${PLAN_FILE}','w'),indent=2)
"
```

Read `steps/figma/agent.md` → `<FIGMA_AGENT>`, then spawn:

```
Agent(prompt: "<FIGMA_AGENT>\n\nCONTEXT:\n  PLAN_FILE=${PLAN_FILE}\n  OUTPUT_DIR=${OUTPUT_DIR}\n  FIGMA_URLS=${FIGMA_URLS}\n  SKILL_DIR=${SKILL_DIR}\n  PROJECT_ROOT=${PROJECT_ROOT}\n  HINTS=${HINTS}")
```

When the agent returns, verify `${OUTPUT_DIR}/figma/` contains at least one `.json`:
```bash
ls "${OUTPUT_DIR}/figma/"*.json 2>/dev/null | wc -l
```

Then set done:
```bash
python3 -c "
import json; p=json.load(open('${PLAN_FILE}'))
p['meta']['steps']['extract-figma']='done'
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

Then spawn:
```
Agent(prompt: "<INFER_AGENT>\n\nRULES:\n<R1>\n<R2>\n<R3>\n<R4>\n\nCONTEXT:\n  PLAN_FILE=${PLAN_FILE}\n  OUTPUT_DIR=${OUTPUT_DIR}\n  SKILL_DIR=${SKILL_DIR}\n  HINTS=${HINTS}")
```

When the agent returns, verify entries with `pending_approval` exist:
```bash
python3 -c "
import json; p=json.load(open('${PLAN_FILE}'))
n=sum(1 for e in p['entries'] if e.get('_status')=='pending_approval')
print(f'{n} pending_approval entries')
"
```

Then set done:
```bash
python3 -c "
import json; p=json.load(open('${PLAN_FILE}'))
p['meta']['steps']['infer']='done'
p['meta']['status']='inprogress'
json.dump(p,open('${PLAN_FILE}','w'),indent=2)
"
```

### Phase 4 — Confirmation (subagent, retry loop)

Read the following files once (reuse across retries):
- `steps/confirm/agent.md` → `<CONFIRM_AGENT>`
- `steps/confirm/rules/ask-before-emit.md` → `<R1>`
- `steps/confirm/rules/double-push-pattern.md` → `<R2>`
- `steps/confirm/rules/plan-language.md` → `<R3>`

```
CONFIRM_PROMPT = "<CONFIRM_AGENT>\n\nRULES:\n<R1>\n<R2>\n<R3>\n\nCONTEXT:\n  PLAN_FILE=${PLAN_FILE}\n  OUTPUT_DIR=${OUTPUT_DIR}\n  HINTS=${HINTS}"
```

**Retry loop — max 3 attempts:**

```python
for attempt in 1..3:
    set meta.steps["confirm"] = "inprogress"
    Agent(prompt: CONFIRM_PROMPT)

    pending_count = python3 -c "
        import json; p=json.load(open('${PLAN_FILE}'))
        print(sum(1 for e in p['entries'] if e.get('_status')=='pending_approval'))
    "

    if pending_count == 0:
        break
    else:
        if attempt < 3:
            print(f"⚠ {pending_count} entries still pending — retry {attempt+1}/3")
        else:
            AskUserQuestion(
                question: f"{pending_count} events are still unconfirmed. What would you like to do?",
                options: [
                    "Continue later — save progress and stop",
                    "Skip all remaining — mark them rejected",
                    "Review them now — run confirmation again"
                ]
            )
            # handle: stop | reject all | loop again
```

**When pending_count = 0, set done (orchestrator only):**
```bash
python3 -c "
import json; p=json.load(open('${PLAN_FILE}'))
p['meta']['steps']['confirm']='done'
p['meta']['status']='ready'
json.dump(p,open('${PLAN_FILE}','w'),indent=2)
"
```

### Phase 5 — Validation (inline Bash — guaranteed)

```bash
python3 "${SKILL_DIR}/scripts/validate_schema.py" "${PLAN_FILE}"
```

The validator will now enforce B1 as a hard error because `meta.status = "ready"`.

On failure: read the error report, fix offending entries in plan.json, retry. Max 3 attempts.
On success: set `meta.steps["validate-plan"] = "done"` and continue to Phase 6.

### Phase 6 — Enrichment (inline)

Read `steps/enrich/agent.md` → `<ENRICH_AGENT>` and execute inline.

**Step 1 — New patterns:**
Check if any approved entries use event names not already covered by the GTM snapshot (ga4_events_confirmed).
If found, offer to add them to the catalog (persistent — benefits future runs).

**Step 2 — Missing events:**
Always ask the user if there are interactions they know should be tracked but weren't proposed.
Let them describe events in free text. Construct the payload, confirm with AskUserQuestion,
write with `origin: "confirmed"`, `_status: "approved"`.

When complete:
```bash
python3 -c "
import json; p=json.load(open('${PLAN_FILE}'))
p['meta']['steps']['enrich']='done'
json.dump(p,open('${PLAN_FILE}','w'),indent=2)
"
```

Print final summary:
```
✓ <PLAN_NAME> — plan finalized
  entries   : approved <a> · rejected <r>
  events    : <distinct event names>
  new catalog entries : <n> | none
  open q's  : open-questions.md
  artifacts : <output-dir>/plan.json
```

---

## Output

Default: `docs/tracking/plans/<plan-name>/plan.json`

```
<output-dir>/
  plan.json          ← canonical validated plan
  figma/             ← raw figma-client outputs (intermediary)
  open-questions.md  ← rejected + uncertain entries (optional)
  gtm-snapshot.json  ← GTM variables + tags cache (24h)
```

---

## Notes

- Never read raw figma-client JSON with the Read tool — always use the compact reader.
- Re-run with new Figma URLs to extend an existing plan (resume picks up from last done step).
- `meta.schema_version` is required; the schema is closed (unknown keys fail validation).
