# Phase 1 — Init (inline, no subagent)

## What this phase does

Parse the skill arguments, resolve paths, create the output directory, and write the
initial `plan.json` with `meta` + empty `entries[]` + all `meta.steps` set to
`"pending"`.

## Actions

### 1. Parse arguments

From the full skill invocation string, extract in order:

1. **`FIGMA_URLS[]`** — all tokens matching `figma.com/(design|file|make|board)/`
2. **`PLAN_NAME`** — first remaining token that is kebab-case or a single word (not a URL, not a sentence)
3. **`HINTS`** — everything else after the name: free-text context the user provides to guide inference

Examples:
```
/tracking-plan https://figma.com/design/abc shopping-homepage
  → FIGMA_URLS=["https://..."]  PLAN_NAME="shopping-homepage"  HINTS=""

/tracking-plan https://figma.com/design/abc resort-pdp main CTA is the price widget, ignore the search bar
  → FIGMA_URLS=["https://..."]  PLAN_NAME="resort-pdp"  HINTS="main CTA is the price widget, ignore the search bar"

/tracking-plan https://figma.com/design/abc this is the BE funnel step 2, focus on the bottom bar and upsells
  → FIGMA_URLS=["https://..."]  PLAN_NAME="" (ask)  HINTS="this is the BE funnel step 2, focus on the bottom bar and upsells"
```

If `FIGMA_URLS` is empty → **stop**:
> No Figma URL detected. Provide at least one `figma.com/…` URL.

If `PLAN_NAME` is empty → ask (in the user's language):
```
AskUserQuestion(
  question: "What name for this tracking plan? (kebab-case — e.g. shopping-homepage, be-funnel)",
  options: ["shopping-homepage", "be-funnel", "customer-account", "Enter name"]
)
```

### 2. Detect site_section

From explicit arg, or infer from URL path:
- `/booking`, `/be/` → `booking_engine`
- `/account`, `/ca/` → `customer_account`
- `/d/`, `/o/`, `/r/`, `/s` → `shopping`
- auth/login patterns → `oidc`

If undetectable → ask via AskUserQuestion (options: shopping, booking_engine,
customer_account, oidc).

### 3. Resolve paths and create directories

```bash
PROJECT_ROOT=$(git rev-parse --show-toplevel)
SKILL_DIR="${CLAUDE_PLUGIN_ROOT:-${PROJECT_ROOT}/.claude/skills/tracking-plan}"
OUTPUT_DIR="${PROJECT_ROOT}/docs/tracking/plans/${PLAN_NAME}"
PLAN_FILE="${OUTPUT_DIR}/plan.json"
mkdir -p "${OUTPUT_DIR}/figma"
```

### 4. Resume check

If `PLAN_FILE` already exists with a `meta.steps` block:
- Find the first step that is NOT `"done"` (could be `"inprogress"` from a crashed run)
- Print: `↩ Resuming ${PLAN_NAME} — next phase: <step_key>`
- Return control to the orchestrator, which will skip done phases

### 5. Write initial plan.json

Only if `PLAN_FILE` does not already exist:

```json
{
  "meta": {
    "schema_version": "1.0",
    "name": "<PLAN_NAME>",
    "site_section": "<site_section>",
    "tms": "GTM",
    "analytics": "GA4",
    "data_layer": "clubMedLayer",
    "source": {
      "figma": ["<FIGMA_URL_1>"],
      "url": []
    },
    "generated_at": "<TODAY_ISO_DATE>",
    "hints": "<HINTS or null>",
    "status": "draft",
    "steps": {
      "validate":      "done",
      "gtm-snapshot":  "pending",
      "extract-figma": "pending",
      "infer":         "pending",
      "confirm":       "pending",
      "validate-plan": "pending",
      "enrich":        "pending"
    }
  },
  "entries": []
}
```

Print:
```
✓ plan: <PLAN_NAME> · section: <site_section> · figma: <n> URL(s)
  hints: <HINTS or "none">
  output: <output-dir>/plan.json
```
