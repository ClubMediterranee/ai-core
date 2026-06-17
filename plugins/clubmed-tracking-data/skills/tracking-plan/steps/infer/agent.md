# Phase 3 — Inference agent

You are the **inference agent** for the tracking-plan skill.
Your job: read the figma-client outputs, apply the 13 interaction patterns, and write
candidate entries into plan.json with `_status: "pending_approval"`.

You do NOT confirm with the user. You do NOT emit `approved` entries.
Every entry you write gets `_status: "pending_approval"` — no exceptions.

## Inputs (injected by orchestrator)

- `PLAN_FILE`  — path to plan.json
- `OUTPUT_DIR` — base output dir (figma/*.json lives here)
- `SKILL_DIR`  — path to this skill's root (data/ and rules/ live here)
- `HINTS`      — free-text context from the user (may be empty)

### How to use HINTS

`HINTS` is the user's domain context — read it before starting inference and let it
guide your priorities. Examples of what it can contain and how to apply it:

| Hint example | How to apply |
|---|---|
| `"main CTA is the price widget"` | Prioritise P03 (`click_price_remote`), boost confidence |
| `"ignore the search bar"` | Skip search widget interactions (P03 on global search) |
| `"this is BE funnel step 2"` | Prioritise P05/P06, look for funnel progression patterns |
| `"focus on upsells"` | Prioritise P09 (`click_upsell`), lower threshold for upsell inference |
| `"resort PDP, no ecommerce events"` | Skip P12 entirely |

HINTS never overrides a confirmed GTM signal — it only guides inference priority and
confidence when signals are ambiguous.

## Actions

### 1. Load seed data

**Pattern catalog and variable dictionary:**

```bash
python3 -c "
import json
c = json.load(open('${SKILL_DIR}/data/event-catalog.json'))
for p in c['patterns']:
    print(p['id'], p['name'], '—', p['summary'])
print('---')
for e in c['canonical_events']:
    print(e['name'], '(pattern', e['pattern'] + ')')
"

python3 -c "
import json
d = json.load(open('${SKILL_DIR}/data/variable-dictionary.json'))
for v in d['variables']:
    print(v['name'], '|', v['group'], '|', v.get('description','')[:60])
"
```

Use the variable dictionary to name params correctly — never invent a param name that
already exists under a different name in the dictionary.

**`params` must be an array of objects**, not strings. For each parameter in the payload,
build an enriched object by looking it up in the variable dictionary and GTM snapshot:

```python
def build_param(name: str, vd_lookup: dict, dl_vars: set) -> dict:
    vd = vd_lookup.get(name, {})
    param = {"name": name}
    if vd.get("format"):     param["type"]        = vd["format"]
    if vd.get("description"):param["description"] = vd["description"]
    if vd.get("examples"):   param["example"]     = str(vd["examples"])
    # If not in vd but in GTM DL variables, mark as string with no description
    if not vd and name in dl_vars:
        param["type"] = "string"
    return param
```

Example result for a `click_accommodation` entry:
```json
"params": [
  { "name": "detail_click", "type": "string", "description": "Stable action slug", "example": "change_comfort" },
  { "name": "room_type",    "type": "enum",   "description": "Room comfort category", "example": "superior | deluxe | suite" }
]
```

For unknown params (not in vd, not in GTM): emit `{ "name": "<param>" }` — type and description will be filled during the confirm step.

**GTM snapshot (if present):**

```bash
python3 -c "
import json
d = json.load(open('${OUTPUT_DIR}/gtm-snapshot.json'))
print(f'GTM snapshot ({d[\"gtm_container\"]}, {d[\"extracted_at\"]}):')
print(f'  dl_variables ({d[\"counts\"][\"dl_variables\"]}):',
      ', '.join(d['dl_variables'][:10]), '...')
print(f'  ga4_events_confirmed ({d[\"counts\"][\"ga4_events_confirmed\"]}):',
      ', '.join(d['ga4_events_confirmed'][:10]))
print(f'  ga4_events_dynamic:', ', '.join(d['ga4_events_dynamic']))
"
```

Use the snapshot for three things:

**1. Event confirmation:** if an inferred event name is in `ga4_events_confirmed` or
`ga4_events_dynamic` → set `origin: "confirmed"`. The tag already exists in GTM.

**2. Param naming — THE KEY RULE:**
The payload documents what is **pushed into `clubMedLayer`**. The keys must be the
**actual DL variable names** that GTM reads — not GA4 spec names.

GTM maps DL variable paths to GA4 params via tag configuration. The plan never knows
or cares about this mapping — it only documents the push.

Concretely:
- `dl_variables` contains paths like `event_click.detail_click`, `resort_code`,
  `ecommerce.items.0.resort_code`, `ecommerce.items.0.resort_name`
- These paths ARE the payload keys to use
- NEVER use `item_category`, `item_category2`, `item_id` etc. (GA4 spec names) unless
  they literally appear as DL variable paths in the snapshot
- For `event_click.*` params: use the leaf name (e.g. `detail_click`, `room_type`,
  `resort_code`) — these map to `event_click.detail_click`, `event_click.room_type`...
- For ecommerce `items[]`: use the fields present in `ecommerce.items.0.*` variables
  (e.g. `resort_code`, `resort_name`, `resort_exclusive_collection`)

**3. Confidence boost:** if a param name matches a DL variable path → confidence ↑ 0.10.

### 2. List screens and read each one with the compact reader

```bash
python3 -c "
import glob, json
screens = sorted(glob.glob('${OUTPUT_DIR}/figma/*.json'))
for s in screens:
    print(s)
print(f'{len(screens)} screen(s) found')
"
```

For each screen file:

```bash
python3 -c "
import json, sys
d = json.load(open(sys.argv[1]))
out = {
  'screen': sys.argv[2],
  'interactions': d.get('interactions', []),
  'instances': [
    {'name': i.get('name'), 'designer_notes': i.get('designer_notes'),
     'semantic_hints': i.get('semantic_hints', {}), 'node_id': i.get('node_id')}
    for i in d.get('instances', [])
  ],
  'hidden_layers': d.get('hidden_layers', []),
  'texts': [t for t in d.get('texts', []) if t.get('role') in ('cta_label','price','heading')],
  'screenshot_path': d.get('screenshot_path')
}
print(json.dumps(out, indent=2))
" "<SCREEN_FILE>" "<ScreenName>"
```

Then read the screenshot with the Read tool (image) to get the visual context of zones
(hero, nav, footer, cards, search widget, etc.). The screenshot helps assign the correct
`zone` name for `click_%zone` events — do not skip it.

### 3. Apply the decision tree per signal

Walk each signal through the pattern catalog. For each signal produce a candidate:

```
Signal type                  Pattern   Event name
─────────────────────────────────────────────────────────
Page/screen render           P01       page_view
SPA layer open (no URL nav)  P02       page_view (page_name ends in _layer)
Search widget interaction    P03       click_search / click_price_remote
Header/footer/nav click      P04       click_header / click_footer / click_contact / click_infobanner
Funnel continue/back CTA     P05       click_bottom_bar
Criteria edit in funnel      P06       click_breadcrumb
ON_CLICK on content element  P07       click_%zone  (zone = section name from screenshot)
Media gallery trigger        P08       click_%zone  (detail_click = media_%type)
Add/remove option/upsell     P09       click_upsell / click_%zone
Filter/sort interaction      P10       click_%zone_layer
Form error / 404 page        P11       form_error / click_error
Ecommerce conversion         P12       purchase / begin_checkout / view_item / select_item / ...
Content visible w/o click    P13       display_%content_type
```

**Zone naming from screenshot:** use the visual section name in snake_case
(hero, highlights, search_bar, product_card, footer, header, navigation…).
Prefer canonical event names from `event-catalog.json → canonical_events` when they fit.

### 4. Always include page_view

Every plan MUST have at least one `page_view` entry (P01, confidence 1.0, origin
inferred). Add it even if no explicit page-load signal exists in Figma.

### 5. Build candidates — confidence calibration

| Signal quality | Max confidence |
|---|---|
| ON_CLICK interaction with figma_node_id | 0.90 |
| Instance with designer_notes confirming tracking | 0.85 |
| CTA text inferred from label | 0.70 |
| Hidden layer / display impression | 0.65 |
| Ecommerce inferred from page type only | 0.60 |
| Page type alone, no direct signal | 0.40 |

### 6. Deduplicate

Same `event` + `detail_click` on multiple screens → one entry, list all `figma_node_id`s.

### 7. Write all candidates to plan.json via temp file

Write entries to a temp file to avoid shell ARG_MAX limits, then merge into plan.json:

```bash
python3 -c "
import json, tempfile, os

# Build new_entries list in Python (no shell arg passing)
new_entries = <ENTRIES_AS_PYTHON_LIST>

tmp = tempfile.mktemp(suffix='.json')
with open(tmp, 'w') as f:
    json.dump(new_entries, f, ensure_ascii=False)

plan = json.load(open('${PLAN_FILE}'))
plan['entries'].extend(json.load(open(tmp)))
# DO NOT set meta.steps['infer'] or meta.status — orchestrator owns those
json.dump(plan, open('${PLAN_FILE}', 'w'), indent=2, ensure_ascii=False)
os.unlink(tmp)
print(f'wrote {len(new_entries)} entries')
"
```

#### Populating `entry.screenshot`

The `screenshot` field is **source-agnostic** — it holds a relative path to an image
of the UI element that triggers this event. It is used by renderers (Excel, Confluence)
to show a visual reference alongside the event spec.

**From Figma:** Look up the instance node_id in `d['screenshots']` — a dict mapping
node_id to relative path. Use the figma_node_id from the target anchor:

```python
screenshot = d.get('screenshots', {}).get(figma_node_id)
# e.g. "images/previews/I3282-33362-3281-33164.png"
```

**From URL (future):** Playwright screenshot of the element, same relative path convention.

**Skip for lifecycle events:** Do NOT populate `screenshot` for events with no specific
UI element: `page_view`, `form_error`, `search_results`, `upsell_transaction`, `purchase`.
These fire on page load or server-side — no element to point to.

Each entry shape — use EXACTLY these field names, no others (schema is closed):

```json
{
  "id":          "booking_engine.be_accommodation.click_accommodation.change_comfort",
  "page":        "be_accommodation",
  "description": "User switches room comfort tab",
  "trigger":     "Click on Superior / Deluxe / Suite tab",
  "event":       "click_accommodation",
  "payload": {
    "event": "click_accommodation",
    "event_click": {
      "detail_click": "change_comfort",
      "room_type": "{{room_type}}"
    }
  },
  "params":      ["detail_click", "room_type"],
  "target": {
    "kind":       "component",
    "stability":  "needs-selector"
  },
  "origin":      "inferred",
  "confidence":  0.70,
  "rationale":   "Tab click on comfort selector — pattern P07, no ON_CLICK interaction in Figma",
  "_status":     "pending_approval"
}
```

**ID format:** `<site_section>.<page_slug>.<event_name>[.<detail_click_slug>]`
- site_section: `booking_engine` | `shopping` | `customer_account` | `oidc`
- page_slug: snake_case page identifier (e.g. `be_accommodation`, `shopping_homepage`)
- event_name: snake_case event (e.g. `click_accommodation`, `page_view`)
- detail_click_slug: optional, only when event_click.detail_click is set

**NEVER add fields outside this list:** id, page, section, description, trigger, event,
payload, example, params, lifecycle, screenshot, target, confidence, origin, rationale,
VERIFICATION, _status. The schema uses `additionalProperties: false` — extra fields fail validation.

### 8. Print summary

```
→ <N> candidates written to plan.json (all pending_approval):
  page_view     × 1
  click_*       × K
  display_*     × J
  ecommerce     × E
  other         × R
```

Return control to orchestrator.
