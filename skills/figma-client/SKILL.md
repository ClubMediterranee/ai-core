---
name: figma-client
description: "Figma REST client — fetches node metadata, auto-layout with css_hints, sub-frame hierarchy, INSTANCE children (variants, visual_signatures, designer_notes), texts with font_class, image fills with local_path, icon SVGs, hidden layers, carousel signals, list item shapes, interactions, and component descriptions."
allowed-tools: Bash, Read
version: 1.0.0
created-at: 2026-06-12
created-by: "Jeremy Wallez <jeremy.wallez@clubmed.com>"
---

# figma-client

Figma REST client that returns raw structural data for a node: metadata, auto-layout with pre-computed Tailwind hints, sub-frame hierarchy, INSTANCE children with variant enrichment and designer notes, texts with font class, image fills downloaded to disk, icon SVGs, hidden layers, carousel signals, list item shapes, prototype interactions, and designer-authored component descriptions.

> **Why not the Figma MCP?**
> - `get_design_context` returns generated JSX/Tailwind — not raw structural data
> - `get_screenshot` returns an image in the conversation only — cannot be persisted
> - The MCP does not return INSTANCE children, variants, or their visual signatures
> - The MCP does not return auto-layout data, css_hints, image fills, or icon SVGs

---

## Prerequisites

The token is resolved automatically in this order:
1. `$FIGMA_TOKEN` environment variable
2. `env.FIGMA_TOKEN` key in `.claude/settings.local.json`

If no token is found → invoke the `figma-authentication` skill.

---

## Usage

```bash
python3 .claude/skills/figma-client/scripts/figma_client.py <figma_url> [options]
```

### Options

| Option | Default | Description |
|---|---|---|
| `--output-dir <dir>` | `.figma/screenshots` | Root output directory. Screenshots → `images/previews/`, fills → `images/fills/`. |
| `--depth <n>` | `10` | Max traversal depth for instances, texts, layouts, fills, and interactions |
| `--screenshot true\|false` | `true` | Download root screenshot, per-instance screenshots, and icon SVGs |
| `--format png\|svg` | `png` | Export format for root screenshot — `png` (@2x raster) or `svg` (vector) |
| `--scale <n>` | `2` | PNG resolution multiplier. Ignored for SVG. |
| `--output-json <path>` | — | Write JSON output to this file in addition to stdout |

### Accepted URLs

```
figma.com/design/:fileKey/:name?node-id=:nodeId
figma.com/make/:fileKey/:name?node-id=:nodeId
figma.com/board/:fileKey/:name
figma.com/file/:fileKey/:name?node-id=:nodeId
```

The `-` or `:` separator in node-id is normalized automatically.

---

## JSON Output

```json
{
  "file_key":        "nVuBJ12TqnLaYC3aajiEMM",
  "node_id":         "3276:8287",
  "name":            "AccommodationSection",
  "type":            "COMPONENT",
  "description":     "Hotel room selection with tabs, carousel, and feature list.",
  "dimensions":      { "width": 780, "height": 1046 },
  "corner_radius":   null,
  "layout": {
    "mode":               "VERTICAL",
    "padding":            { "top": 0, "right": 0, "bottom": 0, "left": 0 },
    "gap":                16,
    "primary_axis_align": "MIN",
    "counter_axis_align": "MIN",
    "wrap":               "NO_WRAP",
    "sizing":             { "horizontal": "FIXED", "vertical": "HUG" }
  },
  "screenshot_path": "images/previews/3276-8287.png",
  "screenshots": {
    "I3276:8287;3298:9136": "images/previews/I3276-8287-3298-9136.png",
    "I3276:8287;3281:33160": "images/previews/I3276-8287-3281-33160.png"
  },
  "layouts": [
    {
      "path":        "AccommodationSection/SectionContentBlock",
      "id":          "3282:33362",
      "type":        "FRAME",
      "dimensions":  { "width": 780, "height": 880 },
      "corner_radius": 16,
      "layout": {
        "mode": "VERTICAL", "gap": 20,
        "padding": { "top": 0, "right": 0, "bottom": 0, "left": 0 },
        "primary_axis_align": "MIN", "counter_axis_align": "MIN",
        "wrap": "NO_WRAP",
        "sizing": { "horizontal": "FILL", "vertical": "HUG" }
      },
      "css_hints": {
        "flex_direction": "flex-col",
        "gap":            "gap-20",
        "width":          "w-full",
        "height":         "h-fit",
        "rounded":        "rounded-[16px]",
        "background_color": "#FFFFFF"
      }
    }
  ],
  "instances": [
    {
      "name":           "Tabs/Pill",
      "id":             "I3298:9136;5800:21924",
      "component_name": "Tabs",
      "component_id":   "7228:23575",
      "variant":        "Pill",
      "depth":          2,
      "parent_id":      "3298:9136",
      "path":           "AccommodationSection/SectionHeader/Tabs/Pill",
      "designer_notes": "Use pill variant for room type navigation. Active tab fills with navy.",
      "variants_available": {
        "properties": {
          "Variant": { "type": "VARIANT", "options": ["Pill", "Underline"], "default": "Underline" }
        },
        "current_combination": { "Variant": "Pill" },
        "visual_signatures": {
          "Pill":      { "bg": "#1E2643", "text_color": "#FFFFFF", "radius": 100 },
          "Underline": { "bg": "transparent", "text_color": "#1E2643", "border": { "color": "#1E2643", "weight": 2 } }
        }
      }
    }
  ],
  "texts": [
    {
      "name":        "Room title",
      "content":     "Deluxe Family Room",
      "path":        "AccommodationSection/SectionHeader/Main title",
      "font_family": "Newsreader",
      "font_class":  "font-serif",
      "font_size":   32,
      "font_weight": 700,
      "line_height": 40.0,
      "text_align":  "LEFT"
    }
  ],
  "image_fills": [
    {
      "path":       "AccommodationSection/SectionContentBlock/Main visuel rooms selected",
      "node_id":    "I3282:33362;3281:33160",
      "imageRef":   "32b3707e52609b1fd385...",
      "dimensions": { "width": 780, "height": 660 },
      "scaleMode":  "FILL",
      "local_path": "fill-32b3707e52609b1f.png"
    }
  ],
  "icon_instances": [
    {
      "node_id":        "I3282:33362;3281:33165;5663:20883",
      "path":           "AccommodationSection/SectionContentBlock/FeatureList/Icon buttons",
      "category":       "Actions",
      "figma_variant":  "Arrows",
      "svg_local_path": "images/fills/icon-Actions-Arrows.svg",
      "dimensions":     { "width": 24, "height": 24 }
    }
  ],
  "hidden_layers": [
    {
      "path":           "AccommodationSection/SectionContentBlock/DescriptiveNotice",
      "name":           "DescriptiveNotice",
      "type":           "INSTANCE",
      "depth":          2,
      "likely_purpose": "conditional_notice",
      "purpose_note":   "contextual notice shown under specific conditions"
    }
  ],
  "carousel_signals": [
    {
      "node_id":    "I3282:33362;3281:33160",
      "path":       "AccommodationSection/SectionContentBlock/Main visuel rooms selected",
      "fill_count": 4
    }
  ],
  "list_items_shape": [
    {
      "component_name": "FeatureItem",
      "count": 4,
      "fields": [
        { "type": "text", "example": "Lounge area", "font_size": 14, "font_weight": 400, "font_class": "font-sans" }
      ]
    }
  ],
  "interactions": [
    {
      "path":     "AccommodationSection/SectionContentBlock/Change rooms",
      "node_id":  "I3282:33362;3281:33164",
      "name":     "Change rooms",
      "depth":    3,
      "triggers": ["ON_CLICK"],
      "actions":  [{ "type": "NODE" }],
      "source":   "page"
    }
  ],
  "component_descriptions": {
    "Tabs": "Use pill variant for room type navigation. Active tab fills with navy.",
    "Market tags": "Shown when room is included in the package."
  },
  "semantic_hints": {
    "component_type":     "accommodation_section",
    "layout_pattern":     "vertical_stack",
    "interaction_patterns": ["tab_switch", "carousel_navigation", "feature_list_expand"]
  }
}
```

---

## Key fields

| Field | Usage |
|---|---|
| `layouts[].css_hints` | Pre-computed Tailwind classes — read verbatim, do not re-derive from `layout` |
| `layouts[].css_hints.background_color` | Frame fill hex — map to token (`#F6EFE7` → `bg-lightSand`) |
| `layouts[].css_hints.rounded` | Corner radius class — use directly (`rounded-[16px]`, `rounded-pill`) |
| `texts[].font_class` | `"font-serif"` (Newsreader) or `"font-sans"` (Inter) — pre-resolved |
| `image_fills[].local_path` | Filename in `images/fills/` — copy to `public/mocks/{Name}/` before use in mock |
| `image_fills[].imageRef` | Figma content hash — stable across file saves |
| `carousel_signals[]` | Node with 2+ distinct imageRefs → use `SliderFrame` or carousel component |
| `icon_instances[].svg_local_path` | Downloaded SVG in `images/fills/` — used by forge-trident-icons-map for visual matching |
| `icon_instances[].figma_variant` | Hint for Trident icon resolution (e.g. `"Arrows"` → `ArrowDefaultRight`) |
| `hidden_layers[].likely_purpose` | Inferred toggle pattern — map to `show{Name}?: boolean` prop |
| `list_items_shape[].fields` | Schema of one repeated item — drives prop typing in design contract |
| `interactions[].triggers` | `ON_CLICK`, `ON_HOVER` → callback prop names |
| `component_descriptions` | Designer-authored intent — read before defining props |
| `instances[].designer_notes` | Same text, inline on each instance |
| `instances[].variants_available.visual_signatures` | Per-variant bg/border/text — use to match Trident variant |
| `screenshots` | `{node_id: relative_path}` — per-instance reference PNGs for molecule diffs |
| `semantic_hints` | LLM-written summary — `component_type`, `layout_pattern`, `interaction_patterns` |

---

## Usage example

```bash
DATA=$(python3 .claude/skills/figma-client/scripts/figma_client.py "<FIGMA_URL>" \
  --output-dir "${WORKING_DIR}" \
  --output-json "${WORKING_DIR}/tree.json")

echo "$DATA" | python3 - <<'EOF'
import sys, json
d = json.load(sys.stdin)
print("Name       :", d["name"])
print("Dimensions :", d["dimensions"])
print("Fills      :", len(d["image_fills"]), "image fill(s)")
print("Carousel   :", d["carousel_signals"])
print()
for layout in d["layouts"]:
    hints = layout.get("css_hints", {})
    print(f"  Layout: {layout['path']}")
    print(f"    flex: {hints.get('flex_direction')} gap: {hints.get('gap')} w: {hints.get('width')}")
print()
for i in d["instances"]:
    v = f" / {i['variant']}" if i.get("variant") else ""
    notes = f" ← {i['designer_notes'][:40]}" if i.get("designer_notes") else ""
    print(f"  {'  ' * i['depth']}Instance: {i['component_name']}{v}{notes}")
EOF
```

---

## Output file locations

After a run with `--output-dir <dir>`:

```
<dir>/
  images/
    previews/
      <node_id>.png          ← root screenshot
      <instance_id>.png      ← per-instance reference screenshots
    fills/
      fill-<ref>.png         ← downloaded image fills (local_path values)
      icon-<Cat>-<Var>.svg   ← downloaded icon SVGs (svg_local_path values)
```

`local_path` in `image_fills[]` is the **filename only** (e.g. `fill-32b3707e.png`).
Resolve against `<dir>/images/fills/` to get the absolute path.

---

## Common errors

| Error | Cause | Fix |
|---|---|---|
| `FIGMA_TOKEN not set` | Token missing from env and settings.local.json | Invoke `figma-authentication` |
| `403` / `Token expired` | Token expired or invalid | Invoke `figma-authentication` |
| `No node-id found` | URL has no `?node-id=` | Select the node in Figma → Copy link to selection |
| `Node not found` | Invalid node-id or deleted node | Check the URL in Figma |
| `screenshot_path: "ERROR: ..."` | Image download failed (network) | Retry or pass `--screenshot false` |
| `image_fills[].local_path: null` | Fill download failed — CDN URL expired or network error | Re-run the script; CDN URLs are short-lived |
