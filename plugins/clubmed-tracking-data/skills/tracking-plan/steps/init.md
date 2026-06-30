# Phase 1 — Init (inline, no subagent)

## What this phase does

Parse the skill arguments, resolve paths, create the output directory, and write the
initial `plan.json` with `meta` + empty `entries[]` + all `meta.steps` set to
`"pending"`.

## Actions

### 1. Parse arguments and detect the source

The skill accepts **one of three source types**. Detect `SOURCE_TYPE` from the arguments
by priority:

1. **`figma`** — any token matching `figma.com/(design|file|make|board)/`.
   → `FIGMA_URLS[]` = all such tokens.
2. **`drd`** — a token that is a path ending in `.drd.md`, OR a directory path that
   contains a `<X>.drd.md` file together with a `screens/` subfolder.
   → `DRD_PATH` = that path.
3. **`url`** — any other `https?://` token (not figma.com).
   → `URLS[]` = all such tokens.

Then extract:
- **`PLAN_NAME`** — first remaining token that is kebab-case or a single word (not a URL, not a path, not a sentence).
- **`HINTS`** — everything else after the name: free-text context guiding inference.

Examples:
```
/tracking-plan https://figma.com/design/abc shopping-homepage
  → SOURCE_TYPE=figma  FIGMA_URLS=["https://..."]  PLAN_NAME="shopping-homepage"

/tracking-plan /Volumes/Work/figma-live/docs/drd/Dashboard dashboard-be
  → SOURCE_TYPE=drd  DRD_PATH="/Volumes/.../Dashboard"  PLAN_NAME="dashboard-be"

/tracking-plan https://www.clubmed.fr/r/punta-cana resort-pdp focus on upsells
  → SOURCE_TYPE=url  URLS=["https://..."]  PLAN_NAME="resort-pdp"  HINTS="focus on upsells"
```

If **no recognised source** is found → **stop** (in the user's language):
> No source detected. Provide one of:
>   • a Figma link            (figma.com/design/…)
>   • a DRD path              (a .drd.md file or its folder)
>   • a live URL              (https://… — analyses the live page)

If `PLAN_NAME` is empty → ask (in the user's language):
```
AskUserQuestion(
  question: "What name for this tracking plan? (kebab-case — e.g. shopping-homepage, be-funnel)",
  options: ["shopping-homepage", "be-funnel", "customer-account", "Enter name"]
)
```

### 2. Detect site_section

From explicit arg, or infer from a Figma/live URL path, or (DRD) from the `.drd.md`
frontmatter `figma-sources[].url`:
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
mkdir -p "${OUTPUT_DIR}/signals"
```

`signals/` is the source-agnostic extraction directory — every source adapter (Figma,
DRD, URL) writes its compact per-screen JSON here in the same figma-client shape.

### 4. Resume check

If `PLAN_FILE` already exists with a `meta.steps` block:
- Find the first step that is NOT `"done"` (could be `"inprogress"` from a crashed run)
- Print: `↩ Resuming ${PLAN_NAME} — next phase: <step_key>`
- Return control to the orchestrator, which will skip done phases

### 5. Write initial plan.json

Only if `PLAN_FILE` does not already exist:

Fill `meta.source` and `meta.source_type` according to the detected `SOURCE_TYPE`:
- `figma` → `"source": { "figma": ["<FIGMA_URL_1>", …], "url": [] }`
- `drd`   → `"source": { "drd": "<DRD_PATH>", "figma": [], "url": [] }`
- `url`   → `"source": { "url": ["<URL_1>", …], "figma": [] }`

```json
{
  "meta": {
    "schema_version": "1.0",
    "name": "<PLAN_NAME>",
    "site_section": "<site_section>",
    "tms": "GTM",
    "analytics": "GA4",
    "data_layer": "clubMedLayer",
    "source": { "<see above per SOURCE_TYPE>": "…" },
    "source_type": "<figma | drd | url>",
    "generated_at": "<TODAY_ISO_DATE>",
    "hints": "<HINTS or null>",
    "status": "draft",
    "steps": {
      "validate":       "done",
      "gtm-snapshot":   "pending",
      "extract-source": "pending",
      "infer":          "pending",
      "validate-plan":  "pending",
      "render":         "pending"
    }
  },
  "entries": []
}
```

Print:
```
✓ plan: <PLAN_NAME> · section: <site_section> · source: <SOURCE_TYPE> (<n> screen(s)/URL(s) or DRD path)
  hints: <HINTS or "none">
  output: <output-dir>/plan.json
```
