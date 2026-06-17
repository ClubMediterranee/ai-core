---
name: tracking-plan-render
description: "Renders a validated plan.json into Excel, Markdown, and/or PDF. Replicates the Club Med legacy tracking plan Excel layout with improvements (embedded screenshots, origin/confidence column, target anchor). Triggers: '/tracking-plan-render', 'generate excel from plan', 'exporter le plan de tracking', 'render tracking plan', 'générer le fichier excel du plan'."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent
version: 1.0.0
created-at: 2026-06-16
created-by: "Jeremy Wallez <jeremy.wallez@clubmed.com>"
---

# tracking-plan-render — Tracking plan renderer

Transforms a validated `plan.json` into one or more output formats:
- **Excel** — replicates the legacy Club Med tracking plan layout with improvements
- **Markdown** — readable spec document, zero dependencies
- **PDF** — shareable document for stakeholders, via reportlab

---

## Prerequisites — install before running

The skill checks for required libraries and installs them if missing.
You can also install them manually:

```bash
# Excel renderer
pip3 install openpyxl pillow

# PDF renderer
pip3 install reportlab

# Markdown renderer — no dependencies
```

**Required versions:**
| Library | Min version | Usage |
|---|---|---|
| `openpyxl` | 3.1+ | Excel file generation |
| `pillow` | 10.0+ | Image embedding in Excel cells |
| `reportlab` | 4.0+ | PDF generation |

The skill will print a clear error and stop if a required library is missing
and auto-install fails (e.g. no pip access in the environment).

---

## Usage

```
/tracking-plan-render <path/to/plan.json> [--format excel,markdown,pdf]
```

If `--format` is omitted, the skill asks which formats to generate.

Input must be a `plan.json` with `meta.status = "ready"`. If `meta.status` is
not `"ready"`, the skill stops with an error — run `/tracking-plan` first.

---

## Architecture — parallel renderers

```
SKILL (orchestrator)
  │  1. Validate plan.json (meta.status = "ready")
  │  2. Ask formats if not specified
  │  3. Auto-install missing libraries
  │  4. Spawn renderers in parallel
  │
  ├─ SUBAGENT [steps/excel/agent.md]     → <plan-name>.xlsx
  ├─ SUBAGENT [steps/markdown/agent.md]  → <plan-name>.md
  └─ SUBAGENT [steps/pdf/agent.md]       → <plan-name>.pdf
```

All renderers receive the same inputs and run independently.
Wall-clock time = slowest single renderer (not sum).

---

## Orchestration script

### Step 1 — Validate input

```bash
python3 -c "
import json, sys
plan = json.load(open('${PLAN_FILE}'))
status = plan.get('meta', {}).get('status')
if status != 'ready':
    print(f'ERROR: plan.json has status={status}, expected ready.')
    print('Run /tracking-plan first to complete the confirmation phase.')
    sys.exit(1)
approved = sum(1 for e in plan['entries'] if e.get('_status') == 'approved')
print(f'OK: {approved} approved entries, status=ready')
"
```

### Step 2 — Ask formats and language (if not provided)

Ask both in a single AskUserQuestion call (2 questions = 2 tabs):

```
AskUserQuestion(questions: [
  {
    header: "Formats",
    question: "Which formats do you want to generate?",
    options: [
      { label: "Excel + PDF + Markdown", description: "All 3 formats in parallel." },
      { label: "Excel only",             description: ".xlsx file only." },
      { label: "Markdown only",          description: ".md file only." },
      { label: "PDF only",               description: ".pdf file only." }
    ]
  },
  {
    header: "Language",
    question: "In which language should the documents be rendered?",
    options: [
      { label: "English (default)", description: "All labels, headers and column names in English." },
      { label: "French",            description: "Tous les labels en français." }
    ]
  }
])
```

Default: **English** if no answer provided.

### Step 3 — Translate plan content (if lang != "en")

If the user chose a non-English language, translate the **textual fields** of the plan
before rendering. The payload (JS code) is never translated — only human-readable fields.

**Fields to translate per entry:**
- `description` — what this event measures
- `trigger` — when it fires
- `rationale` — why it was inferred / justification

**Fields to leave untouched:**
- `event`, `id`, `params`, `payload`, `origin`, `confidence`, `_status`, `target`
- Any field containing code, slugs, or variable names

Translate inline and write a temporary `<plan-name>.<lang>.json` alongside plan.json:

```python
import json, copy

plan = json.load(open(PLAN_FILE))
translated = copy.deepcopy(plan)

# Translate each approved entry's textual fields
for entry in translated["entries"]:
    if entry.get("_status") != "approved":
        continue
    entry["description"] = translate(entry.get("description", ""), lang)
    entry["trigger"]     = translate(entry.get("trigger", ""), lang)
    entry["rationale"]   = translate(entry.get("rationale", ""), lang)

# Also translate open questions rationale for rejected entries
for entry in translated["entries"]:
    if entry.get("_status") == "rejected":
        entry["rationale"] = translate(entry.get("rationale", ""), lang)

translated["meta"]["lang"] = lang
json.dump(translated, open(TRANSLATED_PLAN_FILE, "w"), ensure_ascii=False, indent=2)
```

The `translate()` function is Claude itself — process all entries in a single pass,
not one LLM call per field. Build a JSON object of all strings to translate, translate
the whole object at once, then apply results back. Prefer batch over per-field calls.

The translated file is used only for rendering — `plan.json` (the source of truth) is
never modified.

If `lang == "en"`: skip this step, use `plan.json` directly as `RENDER_PLAN_FILE`.

### Step 4 — Check and install libraries

```bash
python3 "${SKILL_DIR}/scripts/check_deps.py" --formats "${FORMATS}"
```

### Step 5 — Spawn renderers in parallel

Read each selected agent file, then spawn all in a single message:

```
# For each selected format, read steps/<format>/agent.md → <AGENT_CONTENT>
# Then spawn all in one parallel call:

Agent(prompt: "<EXCEL_AGENT>\n\nCONTEXT:\n  PLAN_FILE=${RENDER_PLAN_FILE}\n  OUTPUT_DIR=${OUTPUT_DIR}\n  SKILL_DIR=${SKILL_DIR}\n  LANG=${LANG}")
Agent(prompt: "<MARKDOWN_AGENT>\n\nCONTEXT:\n  PLAN_FILE=${RENDER_PLAN_FILE}\n  OUTPUT_DIR=${OUTPUT_DIR}\n  SKILL_DIR=${SKILL_DIR}\n  LANG=${LANG}")
Agent(prompt: "<PDF_AGENT>\n\nCONTEXT:\n  PLAN_FILE=${RENDER_PLAN_FILE}\n  OUTPUT_DIR=${OUTPUT_DIR}\n  SKILL_DIR=${SKILL_DIR}\n  LANG=${LANG}")

# RENDER_PLAN_FILE = translated plan (lang != "en") or original plan.json (lang == "en")
```

### Step 5 — Print summary

```
✓ Rendering complete
  Excel    : <output-dir>/<plan-name>.xlsx
  Markdown : <output-dir>/<plan-name>.md
  PDF      : <output-dir>/<plan-name>.pdf
```

---

## Output

Files are written alongside `plan.json` in the same `<output-dir>/`:

```
<output-dir>/
  plan.json                    ← source of truth (NEVER modified)
  <plan-name>.<lang>.json      ← translated plan (only when lang != "en"), temp
  <plan-name>.xlsx             ← Excel workbook
  <plan-name>.md               ← Markdown document
  <plan-name>.pdf              ← PDF for sharing
```
