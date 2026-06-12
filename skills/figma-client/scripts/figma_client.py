#!/usr/bin/env python3
"""
figma_client — Figma REST API client for structural node inspection.

PURPOSE
-------
Fetch raw structural data from a Figma node for use in component mapping
and design implementation workflows. Unlike the MCP Figma tools, this script
returns machine-readable JSON suitable for downstream processing: persistent
screenshots, INSTANCE hierarchy, text content, and resolved variables.


OUTPUT CONTRACT
---------------
All top-level fields are always present. Optional fields are omitted when
absent or at neutral defaults (zero, false, "NONE", etc.).

{
  "file_key":        str,
  "node_id":         str,
  "name":            str,
  "type":            str,
  "description":     str | null,
  "dimensions":      {"width": int, "height": int} | null,
  "corner_radius":   int | null,
  "layout":          {                    // Auto-layout of root node, null if none
    "mode":                str,           // "HORIZONTAL" | "VERTICAL"
    "padding":             {"top": int, "right": int, "bottom": int, "left": int},
    "gap":                 int,
    "primary_axis_align":  str,           // "MIN" | "CENTER" | "MAX" | "SPACE_BETWEEN"
    "counter_axis_align":  str,
    "wrap":                str,           // "NO_WRAP" | "WRAP"
    "sizing":              {"horizontal": str, "vertical": str}  // "FIXED"|"HUG"|"FILL"
  } | null,
  "screenshot_path": str | null,

  // ── Structural data (Pass 1) ──────────────────────────────────────────────

  "layouts": [                            // Auto-layout sub-frames, stops at INSTANCE boundaries
    {
      "path":           str,              // Breadcrumb: "Card/Content/Header"
      "id":             str,
      "type":           str,
      "dimensions":     {"width": int, "height": int} | null,
      "corner_radius":  int | {"tl":int,"tr":int,"br":int,"bl":int},  // Omitted if zero
      "clips_content":  true,             // Omitted if false
      "opacity":        float,            // Omitted if 1.0
      "description":    str,              // Omitted if absent
      "min_width":      int,              // Omitted if unset
      "max_width":      int,
      "min_height":     int,
      "max_height":     int,
      "layout":         { ... },
      "css_hints": {                      // Pre-computed Tailwind classes from layout data
        "flex_direction":  str,           // "flex-row" | "flex-col"
        "gap":             str,           // "gap-[20px]" — omitted if 0
        "padding":         str,           // "pt-[16px] pr-[24px] ..." or "p-[16px]"
        "width":           str,           // "w-full" | "w-fit" | "w-[380px]"
        "height":          str,           // "h-full" | "h-fit" | "h-[240px]"
        "justify_content": str,           // Omitted if MIN (default)
        "align_items":     str,           // Omitted if MIN (default)
        "wrap":            str            // "flex-wrap" — omitted if NO_WRAP
      },
      "effects": [                        // Shadows and blurs — omitted if none
        {
          "type":   str,                  // "DROP_SHADOW"|"INNER_SHADOW"|"LAYER_BLUR"|"BACKGROUND_BLUR"
          "color":  str,                  // hex or rgba — shadows only
          "offset": {"x": int, "y": int}, // shadows only
          "radius": int,
          "spread": int                   // shadows only
        }
      ],
      "border": {                         // Omitted if no strokes
        "weight": int,
        "align":  str,                    // "INSIDE"|"OUTSIDE"|"CENTER"
        "color":  str                     // hex of first solid stroke
      }
    }
  ],
  "instances": [                          // Unique INSTANCE children
    {
      "name":           str,
      "id":             str,
      "component_name": str,
      "component_id":   str | null,
      "variant":        str,              // Omitted if none
      "depth":          int,
      "parent_id":      str | null,
      "variants_available": {             // Omitted if component enrichment unavailable
        "properties": {                   // From componentPropertyDefinitions
          "<PropName>": {
            "type":    str,               // "VARIANT"|"BOOLEAN"|"TEXT"|"INSTANCE_SWAP"
            "options": [str],             // VARIANT only
            "default": str
          }
        },
        "current_combination": {          // Parsed from instance variant string
          "<PropName>": "<value>"
        },
        "visual_signatures": {            // Per-variant visual diff
          "<variant_name>": {
            "bg":         str,            // hex | "transparent" | "image"
            "text_color": str,            // hex — omitted if unresolved
            "border":     {"color": str, "weight": int},  // omitted if none
            "radius":     int             // omitted if 0
          }
        }
      }
    }
  ],
  "texts": [                              // Unique TEXT nodes (deduplicated by content)
    {
      "name":           str,
      "content":        str,
      "path":           str,              // Breadcrumb path in the tree
      "font_family":    str,
      "font_class":     str,              // "font-serif" | "font-sans"
      "font_size":      number,
      "font_weight":    int,
      "line_height":    number,
      "letter_spacing": number,
      "text_align":     str,
      "text_decoration": str
    }
  ],
  "variables": {                          // Design token bindings
    "<variable_name>": "<hex>"
  },
  "image_fills": [                        // IMAGE-type fills with downloaded originals
    {
      "path":       str,
      "node_id":    str,
      "imageRef":   str,
      "dimensions": {"width": int, "height": int} | null,
      "scaleMode":  str,
      "local_path": str                   // Omitted if download failed
    }
  ],
  "hidden_layers": [                      // Visible=false nodes — state/toggle candidates
    {
      "path":           str,
      "name":           str,
      "type":           str,
      "depth":          int,
      "likely_purpose": str,              // e.g. "conditional_notice", "loading_state"
      "purpose_note":   str               // Human-readable description
    }
  ],
  "carousel_signals": [                   // Nodes with 2+ distinct image fills = carousel
    {
      "node_id":    str,
      "path":       str,
      "fill_count": int                   // Number of distinct image refs on this node
    }
  ],
  "list_items_shape": [                   // Schema of one item for each repeated organism
    {
      "component_name": str,
      "count":          int,
      "fields": [
        // image_fill: { "type": "image_fill", "fill_count", "dimensions", "scale_mode" }
        // text:       { "type": "text", "example", "font_size", "font_weight", "font_class" }
        // instance:   { "type": "instance", "component_name", "variant"? }
      ]
    }
  ],
  "interactions": [                       // Prototype interactions (page nodes + master components)
    {
      "path":             str,
      "node_id":          str,
      "name":             str,
      "depth":            int,
      "triggers":         [str],
      "actions":          [{ "type": str, "destination_id"?: str, "url"?: str }],
      "source":           str             // "page" | "master_component"
      "component_name":   str             // master_component source only
    }
  ],

  // ── Semantic interpretation (Pass 2) ─────────────────────────────────────

  "semantic_hints": { ... },
  "mock_data":      { ... }
}

FIGMA APIs USED
---------------
  GET /v1/files/{key}/nodes?ids={id}&depth={n}   — node tree (main + component enrichment)
  GET /v1/images/{key}?ids={id}&format=png        — screenshot export URL
  GET /v1/files/{key}/variables/local             — variable name resolution (optional)
  GET /v1/files/{key}/images                      — raw image fill CDN URLs
  GET <s3-url>                                    — binary download

  Component enrichment (variants + master interactions) — 2 batched calls max:
  GET /v1/files/{key}/nodes?ids={componentSetIds}&depth=2   — variant definitions + visual sigs
  GET /v1/files/{key}/nodes?ids={standaloneComponentIds}&depth=2  — standalone master interactions

INTERPRETATION
--------------
Structural signals always run — deterministic Python only, no LLM.
"""

from __future__ import annotations

import shutil
import sys
import os
import re
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import argparse
import subprocess
from collections import Counter, defaultdict
from pathlib import Path


SETTINGS_PATH = ".claude/settings.local.json"
_API_BATCH_SIZE = 50  # Max node IDs per Figma /nodes batch request

# Trident Icons category names — component_name matching one of these = icon instance
TRIDENT_ICON_CATEGORIES = {
    "Actions", "Activities", "Brand", "Covid", "Food", "HappyToCare",
    "Iconic", "Places", "ResortFill", "ResortFill-EC", "ResortOutline",
    "ResortOutline-EC", "Room", "Services", "Socials", "Transports", "Utilities",
}


# ─── Token resolution ─────────────────────────────────────────────────────────

def resolve_token() -> str:
    token = os.environ.get("FIGMA_TOKEN", "")
    if token:
        return token
    try:
        with open(SETTINGS_PATH) as f:
            data = json.load(f)
        return data.get("env", {}).get("FIGMA_TOKEN", "")
    except Exception:
        return ""


# ─── URL Parsing ──────────────────────────────────────────────────────────────

def parse_figma_url(url: str) -> tuple[str, str | None]:
    patterns = [
        r"figma\.com/design/([^/?#]+)",
        r"figma\.com/make/([^/?#]+)",
        r"figma\.com/board/([^/?#]+)",
        r"figma\.com/file/([^/?#]+)",
    ]
    file_key = None
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            file_key = m.group(1)
            break
    if not file_key:
        raise ValueError(f"Cannot extract file key from URL: {url}")
    node_id = None
    m = re.search(r"[?&]node-id=([^&]+)", url)
    if m:
        raw = urllib.parse.unquote(m.group(1))
        node_id = raw.replace("-", ":")
    return file_key, node_id


# ─── API Helpers ──────────────────────────────────────────────────────────────

def api_get(path: str, token: str, timeout: int = 15, retries: int = 3) -> dict:
    """GET a Figma API endpoint. Retries on timeout/network errors with exponential backoff."""
    req = urllib.request.Request(
        f"https://api.figma.com/v1{path}",
        headers={"X-Figma-Token": token},
    )
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Figma API {e.code} on {path}: {body[:200]}") from e
        except (TimeoutError, OSError) as e:
            last_exc = e
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # 1s, 2s, 4s
    raise RuntimeError(f"Figma API timeout after {retries} attempts on {path}") from last_exc


def download_file(url: str, dest: Path, retries: int = 3) -> None:
    """Download a binary file. Retries on timeout with exponential backoff."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "figma-client/5.0"})
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
                f.write(r.read())
            return
        except (TimeoutError, OSError) as e:
            last_exc = e
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"Download timeout after {retries} attempts: {url[:80]}") from last_exc


# ─── Paint / color helpers ────────────────────────────────────────────────────

def hex_from_color(c: dict) -> str:
    """Convert a Figma RGBA color dict to hex or rgba() string."""
    r = round(c.get("r", 0) * 255)
    g = round(c.get("g", 0) * 255)
    b = round(c.get("b", 0) * 255)
    a = c.get("a", 1.0)
    if a < 1.0:
        return f"rgba({r},{g},{b},{round(a, 2)})"
    return f"#{r:02X}{g:02X}{b:02X}"


def hex_from_paint(paint: dict) -> str | None:
    """Return a hex/rgba string from a Figma paint object, or None if not a solid color."""
    if paint.get("type") != "SOLID":
        return None
    color = paint.get("color")
    if not color:
        return None
    opacity = paint.get("opacity", 1.0)
    c = dict(color)
    c["a"] = c.get("a", 1.0) * opacity
    return hex_from_color(c)


def process_effect(e: dict) -> dict:
    """Normalise a Figma effect entry to the output contract shape."""
    entry: dict = {"type": e.get("type", "")}
    etype = e.get("type", "")
    if etype in ("DROP_SHADOW", "INNER_SHADOW"):
        color = e.get("color", {})
        entry["color"] = hex_from_color(color)
        offset = e.get("offset", {})
        entry["offset"] = {"x": round(offset.get("x", 0)), "y": round(offset.get("y", 0))}
        entry["radius"] = round(e.get("radius", 0))
        spread = e.get("spread", 0)
        if spread:
            entry["spread"] = round(spread)
    elif etype in ("LAYER_BLUR", "BACKGROUND_BLUR"):
        entry["radius"] = round(e.get("radius", 0))
    return entry


# ─── Node Parsing ─────────────────────────────────────────────────────────────

def extract_dimensions(node: dict) -> dict | None:
    bb = node.get("absoluteBoundingBox") or node.get("absoluteRenderBounds")
    if bb:
        return {"width": round(bb["width"]), "height": round(bb["height"])}
    return None


def extract_auto_layout(node: dict) -> dict | None:
    mode = node.get("layoutMode")
    if not mode or mode == "NONE":
        # Absolute-positioned frame — no auto-layout but still a structural container.
        # Return a minimal descriptor so collect_layouts can capture its visual properties.
        if node.get("type") in ("FRAME", "COMPONENT", "GROUP"):
            return {
                "mode": "ABSOLUTE",
                "x": round(node.get("x") or 0),
                "y": round(node.get("y") or 0),
            }
        return None
    result: dict = {
        "mode":               mode,
        "padding": {
            "top":    node.get("paddingTop",    0),
            "right":  node.get("paddingRight",  0),
            "bottom": node.get("paddingBottom", 0),
            "left":   node.get("paddingLeft",   0),
        },
        "gap":                node.get("itemSpacing", 0),
        "primary_axis_align": node.get("primaryAxisAlignItems", "MIN"),
        "counter_axis_align": node.get("counterAxisAlignItems", "MIN"),
        "wrap":               node.get("layoutWrap", "NO_WRAP"),
    }
    sizing: dict = {}
    h = node.get("layoutSizingHorizontal")
    v = node.get("layoutSizingVertical")
    if h:
        sizing["horizontal"] = h
    if v:
        sizing["vertical"] = v
    if sizing:
        result["sizing"] = sizing
    return result


# ─── CSS hints ────────────────────────────────────────────────────────────────

def compute_css_hints(layout: dict, dims: dict | None) -> dict:
    """Pre-compute Tailwind utility classes from auto-layout data."""
    hints: dict = {}

    # Flex direction
    mode = layout.get("mode", "VERTICAL")
    if mode == "ABSOLUTE":
        return {}   # No flex hints for absolute frames — position captured in layout dict
    hints["flex_direction"] = "flex-row" if mode == "HORIZONTAL" else "flex-col"

    # Gap
    gap = layout.get("gap", 0)
    if gap:
        hints["gap"] = f"gap-[{int(gap)}px]"

    # Padding
    pad   = layout.get("padding", {})
    top   = int(pad.get("top",    0))
    right = int(pad.get("right",  0))
    bot   = int(pad.get("bottom", 0))
    left  = int(pad.get("left",   0))
    if top or right or bot or left:
        if top == right == bot == left:
            hints["padding"] = f"p-[{top}px]"
        elif top == bot and right == left:
            parts = []
            if top:   parts.append(f"py-[{top}px]")
            if right: parts.append(f"px-[{right}px]")
            hints["padding"] = " ".join(parts)
        else:
            parts = []
            if top:   parts.append(f"pt-[{top}px]")
            if right: parts.append(f"pr-[{right}px]")
            if bot:   parts.append(f"pb-[{bot}px]")
            if left:  parts.append(f"pl-[{left}px]")
            hints["padding"] = " ".join(parts)

    # Width / height from sizing mode
    sizing = layout.get("sizing", {})
    h_sizing = sizing.get("horizontal")
    v_sizing = sizing.get("vertical")
    w = dims["width"]  if dims else None
    h = dims["height"] if dims else None

    if h_sizing == "FILL":
        hints["width"] = "w-full"
    elif h_sizing == "HUG":
        hints["width"] = "w-fit"
    elif h_sizing == "FIXED" and w is not None:
        hints["width"] = f"w-[{int(w)}px]"

    if v_sizing == "FILL":
        hints["height"] = "h-full"
    elif v_sizing == "HUG":
        hints["height"] = "h-fit"
    elif v_sizing == "FIXED" and h is not None:
        hints["height"] = f"h-[{int(h)}px]"

    # Alignment (omit MIN — it's the default)
    justify_map = {
        "CENTER":        "justify-center",
        "MAX":           "justify-end",
        "SPACE_BETWEEN": "justify-between",
    }
    align_map = {
        "CENTER":        "items-center",
        "MAX":           "items-end",
        "SPACE_BETWEEN": "items-stretch",
    }
    primary = layout.get("primary_axis_align", "MIN")
    counter = layout.get("counter_axis_align", "MIN")
    if primary in justify_map:
        hints["justify_content"] = justify_map[primary]
    if counter in align_map:
        hints["align_items"] = align_map[counter]

    # Wrap
    if layout.get("wrap") == "WRAP":
        hints["wrap"] = "flex-wrap"

    return {k: v for k, v in hints.items() if v}


# ─── Font class ───────────────────────────────────────────────────────────────

_SERIF_FAMILIES = {"newsreader", "georgia", "times", "palatino", "garamond",
                   "merriweather", "playfair", "lora", "eb garamond", "libre baskerville"}

def compute_font_class(font_family: str) -> str:
    """Return 'font-serif' for serif fonts, 'font-sans' for everything else."""
    if any(s in font_family.lower() for s in _SERIF_FAMILIES):
        return "font-serif"
    return "font-sans"



# ─── Layout collector ─────────────────────────────────────────────────────────

def collect_layouts(node: dict, depth: int, max_depth: int, results: list, path: str = "") -> None:
    """
    Recursively collect all auto-layout sub-frames in the tree.

    Each entry is enriched with: clips_content, opacity, description,
    min/max sizing constraints, effects (shadows/blurs), border (strokes),
    and css_hints (pre-computed Tailwind classes).
    Traversal continues into INSTANCE children (full depth).
    Hidden nodes are skipped.
    """
    if depth > max_depth:
        return
    if node.get("visible", True) is False:
        return

    node_type = node.get("type", "")
    name = node.get("name", "")
    current_path = f"{path}/{name}" if path else name

    if depth > 0 and node_type in ("FRAME", "COMPONENT", "COMPONENT_SET", "GROUP", "INSTANCE"):
        layout = extract_auto_layout(node)
        if layout is not None:
            dims = extract_dimensions(node)
            entry: dict = {
                "path":       current_path,
                "id":         node.get("id", ""),
                "type":       node_type,
                "dimensions": dims,
                "layout":     layout,
            }

            # Corner radius — uniform or per-corner
            cr = node.get("cornerRadius")
            tl = node.get("topLeftRadius",     0) or 0
            tr = node.get("topRightRadius",    0) or 0
            br = node.get("bottomRightRadius", 0) or 0
            bl = node.get("bottomLeftRadius",  0) or 0
            if tl or tr or br or bl:
                if tl == tr == br == bl:
                    entry["corner_radius"] = tl
                else:
                    entry["corner_radius"] = {"tl": tl, "tr": tr, "br": br, "bl": bl}
            elif cr:
                entry["corner_radius"] = cr

            # Clip / overflow
            if node.get("clipsContent"):
                entry["clips_content"] = True

            # Opacity
            opacity = node.get("opacity")
            if opacity is not None and opacity != 1.0:
                entry["opacity"] = round(opacity, 3)

            # Description
            desc = node.get("description", "")
            if desc:
                entry["description"] = desc

            # Min/max constraints
            for fig_key, out_key in [
                ("minWidth",  "min_width"),
                ("maxWidth",  "max_width"),
                ("minHeight", "min_height"),
                ("maxHeight", "max_height"),
            ]:
                val = node.get(fig_key)
                if val is not None and val > 0:
                    entry[out_key] = round(val)

            # Effects (shadows, blurs)
            effects = [e for e in node.get("effects", []) if e.get("visible", True)]
            if effects:
                entry["effects"] = [process_effect(e) for e in effects]

            # Border (strokes)
            strokes = node.get("strokes", [])
            stroke_weight = node.get("strokeWeight")
            if strokes and stroke_weight:
                stroke_align = node.get("strokeAlign", "INSIDE")
                has_image_fill = any(f.get("type") == "IMAGE" for f in node.get("fills", []))
                solid_colors = [hex_from_paint(s) for s in strokes if hex_from_paint(s)]
                border_entry = {
                    "weight": round(stroke_weight),
                    "align":  stroke_align,
                    "color":  solid_colors[0] if solid_colors else None,
                }
                if stroke_align == "INSIDE" and has_image_fill:
                    # INSIDE border on an image-filled node is invisible in Figma —
                    # the image covers it. Mark explicitly so step 10 never renders it.
                    border_entry["css_visible"] = False
                else:
                    border_entry["css_visible"] = True
                entry["border"] = border_entry

            # CSS hints (pre-computed Tailwind)
            css = compute_css_hints(layout, dims)

            # Inline corner_radius into css_hints as rounded-[Npx]
            # corner_radius is already stored in entry["corner_radius"] — mirror it here
            # so subagents read css_hints directly without needing to check a separate field.
            cr_val = entry.get("corner_radius")
            if cr_val is not None:
                if isinstance(cr_val, dict):
                    # Per-corner: tl/tr/br/bl — no single Tailwind shorthand, use individual classes
                    tl = cr_val.get("tl", 0)
                    tr = cr_val.get("tr", 0)
                    br = cr_val.get("br", 0)
                    bl = cr_val.get("bl", 0)
                    css["rounded"] = (
                        f"rounded-tl-[{tl}px] rounded-tr-[{tr}px] "
                        f"rounded-br-[{br}px] rounded-bl-[{bl}px]"
                    )
                elif cr_val > 0:
                    if cr_val >= 9999:
                        css["rounded"] = "rounded-pill"
                    else:
                        css["rounded"] = f"rounded-[{int(cr_val)}px]"

            # Inline resolved background color from the first solid fill of this frame.
            # This replaces the root-level variables dict which has no per-frame context.
            fills = node.get("fills", [])
            solid_fill = next(
                (f for f in fills if f.get("type") == "SOLID" and f.get("visible", True) is not False),
                None,
            )
            if solid_fill and solid_fill.get("color"):
                hex_bg = hex_from_color(solid_fill["color"])
                if hex_bg and hex_bg.upper() not in ("#FFFFFF", "#000000"):
                    # Only store non-trivial backgrounds (white/black are assumed defaults)
                    css["background_color"] = hex_bg

            # Gradient fill — capture type for css_hints
            gradient_fill = next(
                (f for f in fills if f.get("type", "").startswith("GRADIENT")
                 and f.get("visible", True) is not False),
                None,
            )
            if gradient_fill:
                css["gradient"] = gradient_fill.get("type", "GRADIENT_LINEAR").lower().replace("gradient_", "")

            # Blend mode — skip NORMAL and PASS_THROUGH (default)
            blend = node.get("blendMode", "NORMAL")
            if blend not in ("NORMAL", "PASS_THROUGH"):
                entry["blend_mode"] = blend

            if css:
                entry["css_hints"] = css

            results.append(entry)

    for child in node.get("children", []):
        collect_layouts(child, depth + 1, max_depth, results, current_path)


# ─── Instance collector ───────────────────────────────────────────────────────

def collect_instances(node: dict, depth: int, max_depth: int, results: list,
                      parent_id: str | None = None, path: str = "") -> None:
    """Collect all INSTANCE nodes. Hidden nodes are skipped."""
    if depth > max_depth:
        return
    if node.get("visible", True) is False:
        return

    name = node.get("name", "")
    current_path = f"{path}/{name}" if path else name

    if node.get("type") == "INSTANCE":
        parts = [p.strip() for p in name.split("/")]
        entry: dict = {
            "name":           name,
            "id":             node.get("id", ""),
            "component_name": parts[0],
            "component_id":   node.get("componentId"),
            "depth":          depth,
            "parent_id":      parent_id,
            "path":           current_path,
            "dimensions":     extract_dimensions(node),
        }
        if len(parts) > 1:
            entry["variant"] = "/".join(parts[1:])
        results.append(entry)
        for child in node.get("children", []):
            collect_instances(child, depth + 1, max_depth, results, node.get("id"), current_path)
        return

    for child in node.get("children", []):
        collect_instances(child, depth + 1, max_depth, results, parent_id, current_path)


# ─── Text collector ───────────────────────────────────────────────────────────

def collect_texts(node: dict, depth: int, max_depth: int, results: list, path: str = "") -> None:
    """Collect all TEXT nodes. Hidden nodes are skipped."""
    if depth > max_depth:
        return
    if node.get("visible", True) is False:
        return

    name = node.get("name", "")
    current_path = f"{path}/{name}" if path else name

    if node.get("type") == "TEXT":
        chars = node.get("characters", "").strip()
        if chars:
            style = node.get("style", {})
            entry: dict = {
                "name":    name,
                "content": chars,
                "path":    current_path,
            }
            family = style.get("fontFamily", "")
            if family:
                entry["font_family"] = family
                entry["font_class"]  = compute_font_class(family)
            if style.get("fontSize") is not None:
                entry["font_size"] = style["fontSize"]
            if style.get("fontWeight") is not None:
                entry["font_weight"] = style["fontWeight"]
            lh = style.get("lineHeightPx")
            if lh:
                entry["line_height"] = round(lh, 2)
            ls = style.get("letterSpacing")
            if ls is not None and ls != 0:
                entry["letter_spacing"] = ls
            align = style.get("textAlignHorizontal")
            if align:
                entry["text_align"] = align
            deco = style.get("textDecoration")
            if deco and deco != "NONE":
                entry["text_decoration"] = deco
            results.append(entry)

            # Detect mixed inline styles (e.g. bold date in normal text)
            style_table = node.get("styleOverrideTable", {})
            char_overrides = node.get("characterStyleOverrides", [])
            if style_table and char_overrides:
                unique_ids = set(char_overrides) - {0}
                mixed: list = []
                for sid in sorted(unique_ids):
                    override = style_table.get(str(sid)) or style_table.get(sid) or {}
                    fs = override.get("fontSize")
                    fw = override.get("fontWeight")
                    italic = override.get("italic", False)
                    if fs or fw or italic:
                        mixed.append({
                            k: v for k, v in {
                                "font_size":   fs,
                                "font_weight": fw,
                                "italic":      italic if italic else None,
                            }.items() if v is not None
                        })
                if mixed:
                    entry["mixed_styles"] = mixed

    for child in node.get("children", []):
        collect_texts(child, depth + 1, max_depth, results, current_path)


# ─── Hidden layer collector ───────────────────────────────────────────────────

_HIDDEN_PURPOSE_PATTERNS: list[tuple[list[str], str, str]] = [
    (["descriptivenotice", "notice"],           "conditional_notice",  "contextual notice shown under specific conditions"),
    (["featurelist"],                            "expandable_list",     "expandable feature list, hidden in default state"),
    (["description"],                            "expandable_text",     "text panel toggled on expand or detail view"),
    (["tooltip"],                                "tooltip",             "shown on hover or focus"),
    (["tilte & age", "title & age", "& age"],   "age_restriction",     "alternate card state showing age constraints"),
    (["buttons plan", "plan/details"],           "plan_actions",        "replaces arrow CTA in plan-change state"),
    (["inlinedatalist"],                         "alt_header_layout",   "alternate section header with inline data"),
    (["modal", "dialog"],                        "modal",               "overlay dialog"),
    (["overlay"],                                "overlay",             "overlay layer"),
    (["empty"],                                  "empty_state",         "shown when list has no items"),
    (["loading", "skeleton"],                    "loading_state",       "skeleton or spinner state"),
    (["error"],                                  "error_state",         "error feedback state"),
    (["hover"],                                  "hover_state",         "visual feedback on hover"),
    (["disabled"],                               "disabled_state",      "disabled interaction state"),
    (["selected", "active"],                     "active_state",        "selected or active state"),
    (["tabs"],                                   "tab_bar",             "alternate tab state or inactive tab variant"),
    (["change"],                                 "edit_state",          "edit or change mode"),
]

def _infer_hidden_purpose(name: str) -> tuple[str, str] | None:
    name_lower = name.lower().strip()
    for patterns, purpose, note in _HIDDEN_PURPOSE_PATTERNS:
        if any(p in name_lower for p in patterns):
            return purpose, note
    return None


def collect_hidden_layers(node: dict, depth: int, max_depth: int, results: list, path: str = "") -> None:
    """
    Collect hidden nodes (visible=false) as state/toggle candidates.

    Unlike other collectors, this one specifically targets invisible nodes.
    Hidden nodes are not traversed further — only their immediate presence
    is recorded. A hidden frame named "Tooltip" next to a visible "Trigger"
    strongly signals a toggle/hover state pattern.
    """
    if depth > max_depth:
        return

    name = node.get("name", "")
    current_path = f"{path}/{name}" if path else name

    if node.get("visible") is False and depth > 0:
        entry: dict = {
            "path":  current_path,
            "name":  name,
            "type":  node.get("type", ""),
            "depth": depth,
        }
        purpose_result = _infer_hidden_purpose(name)
        if purpose_result:
            entry["likely_purpose"] = purpose_result[0]
            entry["purpose_note"]   = purpose_result[1]
        results.append(entry)
        # Do not recurse into hidden subtrees — the parent is enough signal
        return

    for child in node.get("children", []):
        collect_hidden_layers(child, depth + 1, max_depth, results, current_path)


# ─── Interaction collector ────────────────────────────────────────────────────

def collect_interactions(node: dict, depth: int, max_depth: int, results: list, path: str = "") -> None:
    """
    Collect nodes that carry Figma prototype interactions.

    The Figma API exposes interactions[] on nodes when prototype connections
    are defined. Each interaction has a trigger (ON_CLICK, ON_HOVER, etc.)
    and one or more actions (navigate to node, open URL, swap state, etc.).

    Hidden nodes are skipped — hidden triggers would be unreachable anyway.
    """
    if depth > max_depth:
        return
    if node.get("visible", True) is False:
        return

    name = node.get("name", "")
    current_path = f"{path}/{name}" if path else name

    interactions = node.get("interactions", [])
    if interactions:
        triggers = []
        actions = []
        for ia in interactions:
            trigger = ia.get("trigger", {})
            trigger_type = trigger.get("type", "")
            if trigger_type:
                triggers.append(trigger_type)
            for action in ia.get("actions", []) or []:
                if action is None:
                    continue
                a: dict = {"type": action.get("type", "")}
                dest = action.get("destinationId")
                if dest:
                    a["destination_id"] = dest
                url = action.get("url")
                if url:
                    a["url"] = url
                actions.append(a)
        results.append({
            "path":     current_path,
            "node_id":  node.get("id", ""),
            "name":     name,
            "depth":    depth,
            "triggers": triggers,
            "actions":  actions,
            "source":   "page",
        })

    for child in node.get("children", []):
        collect_interactions(child, depth + 1, max_depth, results, current_path)


# ─── Variable extractor ───────────────────────────────────────────────────────

def extract_variables(node: dict, file_key: str, token: str, max_depth: int) -> dict:
    """Extract design token bindings from fill/stroke paints, resolved to human-readable names."""
    raw: dict[str, str] = {}

    def scan(obj: dict, depth: int = 0) -> None:
        if depth > max_depth:
            return
        if obj.get("visible", True) is False:
            return
        for paint in obj.get("fills", []) + obj.get("strokes", []):
            color = paint.get("color")
            bound = paint.get("boundVariables", {}).get("color", {})
            if color and bound.get("id"):
                raw[bound["id"]] = hex_from_color(color)
        for child in obj.get("children", []):
            scan(child, depth + 1)

    scan(node)
    if not raw:
        return {}

    try:
        vars_data = api_get(f"/files/{file_key}/variables/local", token)
        variables_meta = vars_data.get("meta", {}).get("variables", {})
        resolved: dict[str, str] = {}
        for var_id, hex_val in raw.items():
            meta = variables_meta.get(var_id)
            name = meta.get("name", var_id) if meta else var_id
            resolved[name] = hex_val
        return resolved
    except Exception:
        return raw


# ─── Image post-processing ────────────────────────────────────────────────────

def flatten_png_to_white(path: Path) -> None:
    try:
        from PIL import Image  # type: ignore
        img = Image.open(path).convert("RGBA")
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        Image.alpha_composite(bg, img).convert("RGB").save(path)
        return
    except ImportError:
        pass
    try:
        result = subprocess.run(
            ["convert", str(path), "-background", "white", "-flatten", str(path)],
            capture_output=True,
        )
        if result.returncode == 0:
            return
    except FileNotFoundError:
        pass


# ─── Image fills ──────────────────────────────────────────────────────────────

def collect_image_fills(node: dict, depth: int, max_depth: int, results: list, path: str = "") -> None:
    """Collect all IMAGE-type fill nodes. Hidden nodes are skipped.

    Emits every IMAGE fill on every node. Inherited master fills are removed
    afterwards by strip_master_fills() using a targeted API call.
    """
    if depth > max_depth:
        return
    if node.get("visible", True) is False:
        return

    name = node.get("name", "")
    current_path = f"{path}/{name}" if path else name

    image_fills = [f for f in node.get("fills", []) if f.get("type") == "IMAGE" and f.get("imageRef") and f.get("visible", True) is not False]
    for fill in image_fills:
        results.append({
            "path":       current_path,
            "node_id":    node.get("id", ""),
            "imageRef":   fill["imageRef"],
            "dimensions": extract_dimensions(node),
            "scaleMode":  fill.get("scaleMode", "FILL"),
        })

    for child in node.get("children", []):
        collect_image_fills(child, depth + 1, max_depth, results, current_path)


def strip_master_fills(raw_fills: list, file_key: str, token: str) -> list:
    """Remove inherited master-component fills from instance nodes.

    When a component instance overrides an image fill, the Figma API returns the
    full paint stack on that node: [master_fill_1, ..., override_fill_N]. The
    master fills are the component defaults the designer replaced — they must not
    be treated as intentional content (they cause false carousel signals).

    Strategy: for every node that has 2+ distinct imageRefs, derive its master
    component node ID (last semicolon-separated segment of the instance node ID,
    e.g. "I6490:31349;3294:33490;3284:8563" → "3284:8563"), then batch-fetch those
    master nodes from the Figma API (depth=0, fills only). The fills present on the
    master are the inherited ones — subtract them from the instance node's fills.

    Nodes with a single fill are returned as-is (no ambiguity, no API call needed).
    """
    from collections import defaultdict

    # Group fills by node_id
    fills_by_node: dict = defaultdict(list)
    for f in raw_fills:
        fills_by_node[f["node_id"]].append(f)

    # Only nodes with 2+ distinct imageRefs need disambiguation
    ambiguous_node_ids = [
        nid for nid, fills in fills_by_node.items()
        if len({f["imageRef"] for f in fills}) >= 2
    ]

    if not ambiguous_node_ids:
        return raw_fills

    # Derive master component node ID from instance node ID.
    # Instance IDs follow the Figma convention: "I<root>;<comp1>;<comp2>;...;<leaf>"
    # The leaf segment is the master component node for this specific sub-node.
    def master_id(instance_nid: str) -> str:
        parts = instance_nid.split(";")
        return parts[-1] if len(parts) > 1 else instance_nid

    master_ids = list({master_id(nid) for nid in ambiguous_node_ids})

    # Batch-fetch master nodes (depth=0 — we only need their fills[])
    master_docs, _ = _batch_fetch_nodes(master_ids, depth=0, file_key=file_key, token=token)

    # Collect all imageRefs present on each master node
    master_fills_by_id: dict = {}
    for mid, doc in master_docs.items():
        master_fills_by_id[mid] = {
            f["imageRef"]
            for f in doc.get("fills", [])
            if f.get("type") == "IMAGE" and f.get("imageRef")
        }

    # Filter: for each ambiguous instance node, remove fills whose imageRef
    # exists on its master component. Keep all fills for unambiguous nodes.
    result: list = []
    for f in raw_fills:
        nid = f["node_id"]
        if nid not in ambiguous_node_ids:
            result.append(f)
            continue
        mid = master_id(nid)
        inherited = master_fills_by_id.get(mid, set())
        if f["imageRef"] not in inherited:
            result.append(f)

    return result


def fetch_raw_image_fills(file_key: str, image_refs: list, token: str, output_dir: Path) -> dict:
    if not image_refs:
        return {}
    try:
        resp = api_get(f"/files/{file_key}/images", token)
        cdn_map: dict = resp.get("meta", {}).get("images", {})
    except Exception:
        return {}
    output_dir.mkdir(parents=True, exist_ok=True)
    result: dict = {}
    for ref in image_refs:
        url = cdn_map.get(ref)
        if not url:
            continue
        dest = output_dir / f"fill-{ref[:20]}.png"
        try:
            download_file(url, dest)
            flatten_png_to_white(dest)
            result[ref] = str(dest.resolve())
        except Exception:
            pass
    return result


# ─── Image export ─────────────────────────────────────────────────────────────

def fetch_image(file_key: str, node_id: str, token: str, output_dir: Path, scale: int = 2, fmt: str = "png") -> Path | None:
    node_id_dashed = node_id.replace(":", "-")
    scale_param = f"&scale={scale}" if fmt == "png" else ""
    # Figma image export can be slow for large frames — use extended timeout
    resp = api_get(
        f"/images/{file_key}?ids={urllib.parse.quote(node_id)}&format={fmt}{scale_param}",
        token,
        timeout=60,
    )
    images = resp.get("images", {})
    image_url = images.get(node_id) or images.get(node_id_dashed)
    if not image_url:
        return None
    dest = output_dir / f"{node_id_dashed}.{fmt}"
    download_file(image_url, dest)
    if fmt == "png":
        flatten_png_to_white(dest)
    return dest.resolve()


# ─── Batch instance screenshots ──────────────────────────────────────────────

def batch_fetch_instance_screenshots(
    file_key: str,
    node_ids: list,
    token: str,
    output_dir: Path,
    json_dir: Path,
    scale: int = 2,
) -> dict:
    """Batch-export screenshots for a list of node IDs in a single API call per batch.

    Skips nodes whose file already exists (e.g. root screenshot already downloaded).
    Returns {node_id: path_relative_to_json_dir}.
    """
    if not node_ids:
        return {}

    output_dir.mkdir(parents=True, exist_ok=True)
    result: dict = {}

    for i in range(0, len(node_ids), _API_BATCH_SIZE):
        batch = node_ids[i : i + _API_BATCH_SIZE]

        # Collect URLs for nodes not already on disk
        to_download: list = []
        for nid in batch:
            dest = output_dir / f"{nid.replace(':', '-')}.png"
            if dest.exists():
                try:
                    result[nid] = str(dest.resolve().relative_to(json_dir))
                except ValueError:
                    result[nid] = str(dest.resolve())
            else:
                to_download.append(nid)

        if not to_download:
            continue

        try:
            ids_param = urllib.parse.quote(",".join(to_download))
            resp = api_get(
                f"/images/{file_key}?ids={ids_param}&format=png&scale={scale}",
                token,
                timeout=60,
            )
            images = resp.get("images", {})
        except Exception:
            continue

        for nid in to_download:
            url = images.get(nid) or images.get(nid.replace(":", "-"))
            if not url:
                continue
            dest = output_dir / f"{nid.replace(':', '-')}.png"
            try:
                download_file(url, dest)
                flatten_png_to_white(dest)
                try:
                    result[nid] = str(dest.resolve().relative_to(json_dir))
                except ValueError:
                    result[nid] = str(dest.resolve())
            except Exception:
                pass

    return result


# ─── Carousel signals ─────────────────────────────────────────────────────────

def compute_carousel_signals(raw_fill_nodes: list) -> list:
    """
    Detect nodes that carry 2+ distinct image fills — strong carousel signal.

    By the time this is called, strip_master_fills() has already removed inherited
    master-component fills. So 2+ fills on a single node_id means the designer
    intentionally stacked multiple images (slider/carousel use case).
    """
    fills_by_node: dict = defaultdict(list)
    path_by_node:  dict = {}
    for f in raw_fill_nodes:
        nid = f["node_id"]
        fills_by_node[nid].append(f["imageRef"])
        if nid not in path_by_node:
            path_by_node[nid] = f.get("path", "")

    signals = []
    for nid, refs in fills_by_node.items():
        unique_refs = list(dict.fromkeys(refs))  # deduplicate, preserve order
        if len(unique_refs) >= 2:
            signals.append({
                "node_id":    nid,
                "path":       path_by_node[nid],
                "fill_count": len(unique_refs),
            })
    return signals


# ─── Icon instances ───────────────────────────────────────────────────────────

def fetch_icon_svgs(
    instances: list,
    file_key: str,
    token: str,
    output_dir: Path,
    json_dir: Path,
) -> list:
    """
    Detect icon instances (component_name in TRIDENT_ICON_CATEGORIES), export
    their SVG from the Figma API, save to output_dir, and return icon_instances[].

    Output entry:
        {
          "node_id":        str,        // Figma node id
          "path":           str,        // breadcrumb path in tree
          "category":       str,        // Trident category e.g. "Actions"
          "figma_variant":  str,        // variant string e.g. "Arrows" — hint for LLM resolution
          "svg_local_path": str,        // relative path to saved SVG e.g. "icon-Actions-Arrows.svg"
          "dimensions":     dict|None,  // {"width": int, "height": int} — icon bounding box from Figma
        }
    // trident_name is NOT resolved here — figma-forge Phase 2c reads svg_local_path + catalog

    SVG naming: icon-{category}-{variant_slug}.svg (or icon-{category}-{node_suffix}.svg
    if no variant). Deduplication: same node_id is only exported once.
    """
    icon_nodes = [
        inst for inst in instances
        if inst.get("component_name") in TRIDENT_ICON_CATEGORIES
    ]
    if not icon_nodes:
        return []

    # Deduplicate by node_id
    seen: set = set()
    unique_icons: list = []
    for inst in icon_nodes:
        nid = inst.get("id") or inst.get("node_id", "")
        if nid and nid not in seen:
            seen.add(nid)
            unique_icons.append(inst)

    # Batch export SVGs — Figma /images endpoint accepts comma-separated IDs
    node_ids = [inst.get("id") or inst.get("node_id", "") for inst in unique_icons]
    node_ids = [n for n in node_ids if n]

    svg_urls: dict = {}
    try:
        ids_param = ",".join(node_ids)
        resp = api_get(f"/images/{file_key}?ids={ids_param}&format=svg", token)
        svg_urls = resp.get("images", {})
    except Exception as e:
        import sys
        print(f"[figma-client] icon SVG export failed: {e}", file=sys.stderr)

    results = []
    for inst in unique_icons:
        nid       = inst.get("id") or inst.get("node_id", "")
        category  = inst.get("component_name", "")
        variant   = inst.get("variant") or inst.get("name", "").split("/")[-1].strip()
        svg_url   = svg_urls.get(nid)

        # Build a safe filename
        variant_slug = variant.replace(" ", "-").replace("/", "-") if variant else nid[-8:]
        filename = f"icon-{category}-{variant_slug}.svg"
        local_path: str | None = None

        if svg_url:
            dest = output_dir / filename
            try:
                download_file(svg_url, dest)
                try:
                    local_path = str(dest.relative_to(json_dir))
                except ValueError:
                    local_path = str(dest)
            except Exception as e:
                import sys
                print(f"[figma-client] SVG download failed for {nid}: {e}", file=sys.stderr)

        results.append({
            "node_id":        nid,
            "path":           inst.get("path", ""),
            "category":       category,
            "figma_variant":  variant,   # hint: e.g. "Arrows" → helps narrow to ArrowDefault*/ArrowTail*
            "svg_local_path": local_path,
            "dimensions":     inst.get("dimensions"),
        })

    return results


# ─── List items shape ─────────────────────────────────────────────────────────

def compute_list_items_shape(
    raw_instances: list,
    raw_fill_nodes: list,
    raw_texts: list,
    layouts: list,
) -> list:
    """
    For each repeated organism (component appearing 2+ times), extract the
    schema of one canonical item: image fills, text styles, child instances.

    Uses path-prefix matching on the instance's own path (tracked during
    collect_instances traversal) to scope fields to one item.
    """
    # Count component occurrences (all instances, not deduplicated)
    name_counts = Counter(i["component_name"] for i in raw_instances)
    organism_names = {name for name, count in name_counts.items() if count >= 2}

    # Build parent_id index once — avoids O(n²) scan per organism
    children_by_parent: dict = defaultdict(list)
    for inst in raw_instances:
        pid = inst.get("parent_id")
        if pid:
            children_by_parent[pid].append(inst)

    items: list = []
    seen_organisms: set = set()

    for inst in raw_instances:
        cname = inst["component_name"]
        if cname not in organism_names or cname in seen_organisms:
            continue
        seen_organisms.add(cname)

        count     = name_counts[cname]
        inst_path = inst.get("path")  # Tracked in collect_instances traversal
        fields: list = []

        if inst_path:
            # Image fills within this instance's subtree (path-prefix scoped)
            inst_fills  = [f for f in raw_fill_nodes if f.get("path", "").startswith(inst_path)]
            unique_refs = list(dict.fromkeys(f["imageRef"] for f in inst_fills))
            if unique_refs:
                dims     = inst_fills[0].get("dimensions") if inst_fills else None
                dims_str = f"{dims['width']}x{dims['height']}" if dims else None
                fields.append({
                    "type":       "image_fill",
                    "fill_count": len(unique_refs),
                    "dimensions": dims_str,
                    "scale_mode": inst_fills[0].get("scaleMode", "FILL") if inst_fills else None,
                })

            # Texts within this instance's subtree — deduplicate by (font_size, font_weight)
            inst_texts  = [t for t in raw_texts if t.get("path", "").startswith(inst_path)]
            seen_styles: set = set()
            for t in inst_texts:
                style_key = (t.get("font_size"), t.get("font_weight"))
                if style_key not in seen_styles:
                    seen_styles.add(style_key)
                    field: dict = {
                        "type":        "text",
                        "example":     t["content"],
                        "font_size":   t.get("font_size"),
                        "font_weight": t.get("font_weight"),
                    }
                    fc = t.get("font_class")
                    if fc:
                        field["font_class"] = fc
                    fields.append(field)

        # Direct child instances — O(1) lookup via pre-built index
        children = [c for c in children_by_parent.get(inst["id"], []) if c["component_name"] != cname]
        seen_child_keys: set = set()
        for child in children:
            key = (child["component_name"], child.get("variant"))
            if key in seen_child_keys:
                continue
            seen_child_keys.add(key)
            child_field: dict = {
                "type":           "instance",
                "component_name": child["component_name"],
            }
            if child.get("variant"):
                child_field["variant"] = child["variant"]
            fields.append(child_field)

        items.append({
            "component_name": cname,
            "count":          count,
            "fields":         fields,
        })

    return items


# ─── Component enrichment (variants + master interactions) ────────────────────

def _parse_variant_combination(variant_str: str) -> dict:
    """Parse 'Prop1=Val1, Prop2=Val2' or 'Val1' into a dict."""
    combo: dict = {}
    if not variant_str:
        return combo
    for pair in variant_str.split(", "):
        pair = pair.strip()
        if "=" in pair:
            k, v = pair.split("=", 1)
            combo[k.split("#")[0].strip()] = v.strip()
        else:
            combo["Variant"] = pair
    return combo


def _extract_visual_signature(component_node: dict) -> dict:
    """Extract background, border, text color, and corner radius from a COMPONENT node."""
    sig: dict = {}

    # Background fill (on the COMPONENT itself or its first FRAME child)
    def get_bg(node: dict) -> str | None:
        fills = [f for f in node.get("fills", []) if f.get("visible", True)]
        for fill in fills:
            if fill.get("type") == "SOLID":
                return hex_from_paint(fill)
            if fill.get("type") == "IMAGE":
                return "image"
        return None

    bg = get_bg(component_node)
    if bg is None:
        for child in component_node.get("children", [])[:1]:
            bg = get_bg(child)
            if bg:
                break
    sig["bg"] = bg or "transparent"

    # Border
    strokes = [s for s in component_node.get("strokes", []) if s.get("visible", True)]
    sw = component_node.get("strokeWeight")
    if strokes and sw:
        color = hex_from_paint(strokes[0])
        if color:
            sig["border"] = {"color": color, "weight": round(sw)}

    # Foreground color — first TEXT or icon-shape node at depth ≤ 4
    # Icon buttons have no TEXT; their arrow is a BOOLEAN_OPERATION/VECTOR with a solid fill.
    # We capture both so the agent knows what color the text/icon uses per state.
    _ICON_TYPES = {"TEXT", "VECTOR", "BOOLEAN_OPERATION", "ELLIPSE", "STAR", "POLYGON", "LINE"}

    def find_fg_color(node: dict, d: int = 0) -> str | None:
        if d > 4:
            return None
        if node.get("type") in _ICON_TYPES:
            for tf in [f for f in node.get("fills", []) if f.get("visible", True)]:
                c = hex_from_paint(tf)
                if c:
                    return c
        for child in node.get("children", []):
            result = find_fg_color(child, d + 1)
            if result:
                return result
        return None

    # Also check child FRAME border (catches circle-button stroke-only default state)
    def find_child_border(node: dict) -> str | None:
        for child in node.get("children", [])[:2]:
            strokes = [s for s in child.get("strokes", []) if s.get("visible", True)]
            if strokes:
                return hex_from_paint(strokes[0])
        return None

    fg_color = find_fg_color(component_node)
    if fg_color:
        sig["icon_color"] = fg_color

    # Also capture child frame border as border if not already set on root
    if not sig.get("border"):
        child_border = find_child_border(component_node)
        if child_border:
            sig["border"] = {"color": child_border}

    # Corner radius
    cr = component_node.get("cornerRadius")
    tl = component_node.get("topLeftRadius", 0) or 0
    if tl or cr:
        sig["radius"] = tl or cr

    return sig


def _batch_fetch_nodes(
    ids: list,
    depth: int,
    file_key: str,
    token: str,
) -> tuple[dict, dict]:
    """Fetch Figma node documents in batches.

    Returns:
        docs:          {node_id: document_dict}
        comp_key_map:  {node_id: component_key}  — keys live in wrapper.components per node

    Component keys are in the per-node wrapper, not in the top-level response.components.
    """
    docs: dict      = {}
    comp_keys: dict = {}
    for i in range(0, len(ids), _API_BATCH_SIZE):
        batch = ids[i : i + _API_BATCH_SIZE]
        try:
            resp = api_get(
                f"/files/{file_key}/nodes"
                f"?ids={urllib.parse.quote(','.join(batch))}&depth={depth}",
                token,
            )
            for nid, wrapper in resp.get("nodes", {}).items():
                doc = wrapper.get("document")
                if doc:
                    docs[nid] = doc
                for cid, cmeta in wrapper.get("components", {}).items():
                    if cmeta.get("key"):
                        comp_keys[cid.replace("-", ":")] = cmeta["key"]
        except Exception:
            pass
    return docs, comp_keys


def _resolve_component_set_ids(
    unique_component_ids: list,
    file_key: str,
    token: str,
) -> tuple[dict, dict, dict]:
    """Query the design file's component list to map each component to its COMPONENT_SET.

    Returns:
        comp_to_set:   {component_id: component_set_id}
        comp_fullname: {component_id: "ComponentName/VariantName"}
        comp_description: {component_id: "designer description text"}
    """
    comp_to_set:       dict = {}
    comp_fullname:     dict = {}
    comp_description:  dict = {}
    try:
        resp = api_get(f"/files/{file_key}/components", token)
        for entry in resp.get("meta", {}).get("components", []):
            nid = entry.get("node_id", "").replace("-", ":")
            if nid not in unique_component_ids:
                continue
            comp_fullname[nid] = entry.get("name", "")
            desc = entry.get("description", "").strip()
            if desc:
                comp_description[nid] = desc
            sid = entry.get("component_set", {}).get("node_id", "").replace("-", ":")
            if sid:
                comp_to_set[nid] = sid
    except Exception:
        pass
    return comp_to_set, comp_fullname, comp_description


def _build_component_set_data(
    set_nodes: dict,
    token: str,
) -> tuple[dict, dict, list]:
    """Extract property definitions, visual signatures, and prototype interactions from COMPONENT_SET nodes.

    Returns:
        set_to_props:        {set_id: {prop_name: prop_def}}
        set_to_sigs:         {set_id: {variant_name: visual_sig}}
        master_interactions: list of interaction entries with source="master_component"
    """
    set_to_props:        dict = {}
    set_to_sigs:         dict = {}
    master_interactions: list = []

    for set_id, set_doc in set_nodes.items():
        set_to_props[set_id] = _parse_property_definitions(set_doc)
        sigs, ias = _extract_variant_sigs_and_interactions(set_doc)
        set_to_sigs[set_id] = sigs
        master_interactions.extend(ias)

    return set_to_props, set_to_sigs, master_interactions


def _parse_property_definitions(set_doc: dict) -> dict:
    """Parse componentPropertyDefinitions from a COMPONENT_SET node into clean property dicts."""
    properties: dict = {}
    for raw_name, prop_data in set_doc.get("componentPropertyDefinitions", {}).items():
        clean = raw_name.split("#")[0]
        prop: dict = {"type": prop_data.get("type", "VARIANT")}
        if prop_data.get("variantOptions"):
            prop["options"] = prop_data["variantOptions"]
        if prop_data.get("defaultValue") is not None:
            prop["default"] = str(prop_data["defaultValue"])
        properties[clean] = prop
    return properties


def _extract_variant_sigs_and_interactions(set_doc: dict) -> tuple[dict, list]:
    """Extract visual signatures and prototype interactions from COMPONENT children of a COMPONENT_SET."""
    sigs: dict = {}
    interactions: list = []

    for child in set_doc.get("children", []):
        if child.get("type") != "COMPONENT":
            continue
        cname = child.get("name", "")
        sig   = _extract_visual_signature(child)
        sigs[cname] = sig
        # Also index by simplified key ("On demand" for "Variant=On demand")
        simple = ", ".join(_parse_variant_combination(cname).values())
        if simple != cname:
            sigs[simple] = sig

        child_ias: list = []
        collect_interactions(child, depth=0, max_depth=2, results=child_ias)
        for ia in child_ias:
            interactions.append({**ia, "source": "master_component", "component_name": cname})

    return sigs, interactions


def _resolve_library_pseudo_variants(
    orphan_ids: list,
    comp_nodes: dict,
    comp_fullname: dict,
    comp_key_map: dict,
    file_key: str,
    token: str,
) -> tuple[dict, dict]:
    """Discover all sibling components for slash-named standalone COMPONENTs in external libraries.

    Heuristic for slash-named pseudo-variants:
      - component name contains "/"
      - base part (before "/") has no "=" (excludes COMPONENT_SET variant names like "Device=Desktop, ...")

    Returns:
        base_to_members:  {base_name: [(variant_name, lib_node_id, lib_fk)]}
        lib_node_to_sig:  {(lib_fk, node_id): visual_sig}
    """
    # Group slash-named orphans by base name
    base_groups: dict = defaultdict(list)
    for cid in orphan_ids:
        doc  = comp_nodes.get(cid)
        name = comp_fullname.get(cid, doc.get("name", "") if doc else "")
        if name and "/" in name:
            base = name.split("/")[0]
            if "=" not in base:
                base_groups[base].append(cid)

    # Discover library file_key — one /components/{key} call per base group
    base_to_lib_fk: dict = {}
    for base_name, cids in base_groups.items():
        for cid in cids:
            ckey = comp_key_map.get(cid)
            if not ckey:
                continue
            try:
                info   = api_get(f"/components/{ckey}", token, timeout=10)
                lib_fk = info.get("meta", {}).get("file_key")
                if lib_fk:
                    base_to_lib_fk[base_name] = lib_fk
                    break
            except Exception:
                pass

    # Fetch all components from each discovered library — one call per library
    lib_all_comps: dict = {}
    for lib_fk in set(base_to_lib_fk.values()):
        try:
            resp = api_get(f"/files/{lib_fk}/components", token, timeout=20)
            lib_all_comps[lib_fk] = resp.get("meta", {}).get("components", [])
        except Exception:
            lib_all_comps[lib_fk] = []

    # Match library components to each base name
    base_to_members: dict = {}
    for base_name, lib_fk in base_to_lib_fk.items():
        base_to_members[base_name] = _match_library_members(
            base_name, lib_all_comps.get(lib_fk, []), lib_fk
        )

    # Batch-fetch visual signatures from each library
    lib_nodes_needed: dict = defaultdict(set)
    for members in base_to_members.values():
        for _, cnid, lib_fk in members:
            lib_nodes_needed[lib_fk].add(cnid)

    lib_node_to_sig: dict = {}
    for lib_fk, node_ids in lib_nodes_needed.items():
        lib_docs, _ = _batch_fetch_nodes(list(node_ids), depth=2, file_key=lib_fk, token=token)
        for nid, doc in lib_docs.items():
            lib_node_to_sig[(lib_fk, nid.replace("-", ":"))] = _extract_visual_signature(doc)

    return base_to_members, lib_node_to_sig


def _match_library_members(
    base_name: str,
    lib_components: list,
    lib_fk: str,
) -> list:
    """Return [(variant_name, node_id, lib_fk)] for all components in lib_components that belong to base_name."""
    base_stripped = base_name.strip()
    members = []
    for c in lib_components:
        cname = c.get("name", "")
        cnid  = c.get("node_id", "").replace("-", ":")
        # Primary: exact prefix (preserves spaces-around-slash conventions like "Actions / Search")
        if cname == base_name:
            members.append((cname.strip(), cnid, lib_fk))
        elif cname.startswith(base_name + "/"):
            members.append((cname[len(base_name) + 1:].strip(), cnid, lib_fk))
        # Fallback: stripped comparison for inconsistent spacing edge cases
        elif cname.strip() == base_stripped:
            members.append((cname.strip(), cnid, lib_fk))
        elif cname.strip().startswith(base_stripped + "/"):
            members.append((cname.strip()[len(base_stripped) + 1:].strip(), cnid, lib_fk))
    return members


def _build_variants_entry(
    cid: str,
    sid: str | None,
    comp_nodes: dict,
    comp_fullname: dict,
    set_to_props: dict,
    set_to_sigs: dict,
    set_nodes: dict,
    base_to_members: dict,
    lib_node_to_sig: dict,
) -> tuple[dict, list]:
    """Build the variants_available entry and collect master interactions for one component.

    Priority:
      1. COMPONENT_SET  — full property defs + all variants
      2. Library pseudo-variants  — all siblings discovered via library API
      3. Observed variant only  — visual sig of the rendered variant
    """
    entry: dict = {}
    comp_ias: list = []

    if sid and sid in set_to_props:
        entry["properties"] = set_to_props[sid]

    if sid and sid in set_to_sigs:
        entry["visual_signatures"] = set_to_sigs[sid]
    elif not sid:
        doc  = comp_nodes.get(cid)
        name = comp_fullname.get(cid, doc.get("name", "") if doc else "")
        base = name.split("/")[0] if name else ""
        members = base_to_members.get(base, [])
        if members:
            entry["all_members"] = [m[0] for m in members]
            sigs = {
                variant: lib_node_to_sig[(lib_fk, cnid)]
                for variant, cnid, lib_fk in members
                if (lib_fk, cnid) in lib_node_to_sig
            }
            if sigs:
                entry["visual_signatures"] = sigs

    if not entry.get("visual_signatures") and cid in comp_nodes:
        doc   = comp_nodes[cid]
        name  = comp_fullname.get(cid, doc.get("name", ""))
        parts = name.split("/")
        vkey  = "/".join(parts[1:]) if len(parts) > 1 else name
        sig   = _extract_visual_signature(doc)
        entry["visual_signatures"] = {vkey: sig}
        if vkey != name:
            entry["visual_signatures"][name] = sig

    if cid in comp_nodes and not (sid and sid in set_nodes):
        comp_doc = comp_nodes[cid]
        collect_interactions(comp_doc, depth=0, max_depth=2, results=comp_ias)
        for ia in comp_ias:
            ia["source"]         = "master_component"
            ia["component_name"] = comp_doc.get("name", "")

    return entry, comp_ias


def fetch_component_enrichments(
    file_key: str,
    raw_instances: list,
    token: str,
    root_node_id: str = "",
) -> tuple[dict, list, dict]:
    """Enrich instances with variant definitions, visual signatures, and master interactions.

    Orchestrates 4 distinct phases — each delegated to a focused helper:
      1. Resolve which components belong to a COMPONENT_SET
      2. Fetch COMPONENT_SET property definitions + visual signatures (primary path)
      3. Discover library pseudo-variants for slash-named standalone components (fallback)
      4. Assign variants_available per component using priority 1 > 2 > 3
    """
    if not raw_instances:
        return {}, [], {}

    unique_component_ids = list({
        i["component_id"] for i in raw_instances if i.get("component_id")
    })
    # Include root node so its description is captured (root is a COMPONENT but not an instance)
    if root_node_id and root_node_id not in unique_component_ids:
        unique_component_ids.append(root_node_id)

    if not unique_component_ids:
        return {}, [], {}

    comp_to_set, comp_fullname, comp_description = _resolve_component_set_ids(
        unique_component_ids, file_key, token
    )
    set_nodes, _ = _batch_fetch_nodes(
        list(set(comp_to_set.values())), depth=2, file_key=file_key, token=token
    ) if comp_to_set else ({}, {})
    comp_nodes, comp_key_map = _batch_fetch_nodes(
        unique_component_ids, depth=2, file_key=file_key, token=token
    )

    # ── Remote library sets: fetch COMPONENT_SET from the library file ────────
    # Remote components (from external Figma libraries) are not listed in
    # /files/{key}/components, so comp_to_set stays empty for them and only
    # State=Default is ever resolved. Fix: use the component key (from comp_key_map)
    # to call /v1/components/{key} which returns the library file_key + the
    # containingStateGroup node_id. Then fetch the full COMPONENT_SET from there.
    # This gives us all variants: Default, Rollhover/Hover, Disabled, etc.
    # UX/UI overrides (instance-level property overrides) are preserved separately
    # in the instance's own visual_signatures — they take priority over library defaults.
    for cid in list(unique_component_ids):
        if cid in comp_to_set:
            continue  # already resolved from local file
        comp_key = comp_key_map.get(cid, "")
        if not comp_key:
            continue
        lib_file_key = None
        lib_set_id   = None
        try:
            meta_resp    = api_get(f"/components/{comp_key}", token)
            lib_file_key = meta_resp.get("meta", {}).get("file_key")
            csng         = meta_resp.get("meta", {}).get("containing_frame", {}) \
                                    .get("containingStateGroup", {})
            lib_set_id   = csng.get("nodeId", "").replace("-", ":")
            if not lib_file_key or not lib_set_id:
                # Standalone component (no COMPONENT_SET) — try parent frame nodeId
                lib_set_id = meta_resp.get("meta", {}).get("node_id", "").replace("-", ":")
        except Exception:
            pass
        if lib_file_key and lib_set_id and lib_set_id not in set_nodes:
            lib_set_nodes, _ = _batch_fetch_nodes(
                [lib_set_id], depth=2, file_key=lib_file_key, token=token
            )
            set_nodes.update(lib_set_nodes)
            comp_to_set[cid] = lib_set_id
            if cid not in comp_fullname:
                doc = comp_nodes.get(cid, {})
                comp_fullname[cid] = doc.get("name", "")

    set_to_props, set_to_sigs, set_master_ias = _build_component_set_data(set_nodes, token)

    orphan_ids = [cid for cid in unique_component_ids if cid not in comp_to_set]
    base_to_members, lib_node_to_sig = _resolve_library_pseudo_variants(
        orphan_ids, comp_nodes, comp_fullname, comp_key_map, file_key, token
    )

    variants_map:        dict = {}
    master_interactions: list = list(set_master_ias)

    for cid in unique_component_ids:
        entry, comp_ias = _build_variants_entry(
            cid,
            comp_to_set.get(cid),
            comp_nodes, comp_fullname,
            set_to_props, set_to_sigs, set_nodes,
            base_to_members, lib_node_to_sig,
        )
        if entry:
            variants_map[cid] = entry
        master_interactions.extend(comp_ias)

    return variants_map, master_interactions, comp_description


# ─── Pass 2a — Structural interpretation (deterministic) ──────────────────────

_CTA_KEYWORDS = [
    "book", "discover", "see", "view", "explore", "reserve", "buy",
    "shop", "learn", "get", "start", "try", "find", "search", "read more",
    "en savoir", "réserver", "découvrir", "voir",
]


def infer_text_role(text: dict, max_size: float, min_size: float) -> str:
    """Infer semantic role of a text node given pre-computed size bounds for the text set."""
    size    = text.get("font_size", 16)
    weight  = text.get("font_weight", 400)
    content = text.get("content", "").strip()

    if re.search(r"[\d\s,.]+\s*(€|\$|£|¥|USD|EUR)", content) or \
       (any(c in content for c in ["€", "$", "£"]) and len(content) < 20):
        return "price"

    if len(content) <= 15 and (content.isupper() or re.match(r"^\[.+\]$|^\(.+\)$", content)):
        return "badge"

    if len(content.split()) <= 6 and any(
        re.search(rf"\b{re.escape(p)}\b", content.lower()) for p in _CTA_KEYWORDS
    ):
        return "cta_label"

    if size >= max_size * 0.85:
        return "heading"
    if size >= max_size * 0.65 or (weight >= 600 and size >= 16):
        return "subheading"
    if size <= min_size + 1:
        return "caption"
    if weight >= 600 and size < 16:
        return "label"
    return "body"


def infer_image_role(fill: dict) -> str:
    """Infer image role from node path name and dimensions."""
    path = fill.get("path", "").lower()
    dims = fill.get("dimensions")

    for keyword, role in [
        ("avatar", "avatar"), ("profile", "avatar"), ("user", "avatar"),
        ("logo",   "logo"),   ("brand",   "logo"),
        ("hero",   "background"), ("bg",  "background"), ("background", "background"),
        ("banner", "banner"),
        ("thumb",  "thumbnail"), ("card", "thumbnail"),
        ("icon",   "icon"),
    ]:
        if keyword in path:
            return role

    if dims and dims["height"] > 0:
        ratio = dims["width"] / dims["height"]
        if ratio > 2.5:
            return "banner"
        if abs(ratio - 1.0) < 0.15:
            return "square_image"

    return "image"


def aspect_ratio_str(dims: dict | None) -> str:
    if not dims or dims["height"] == 0:
        return "unknown"
    ratio = dims["width"] / dims["height"]
    # Common ratios
    for (w, h) in [(16, 9), (4, 3), (3, 2), (1, 1), (2, 3), (9, 16), (21, 9)]:
        if abs(ratio - w / h) < 0.08:
            return f"{w}:{h}"
    return f"{round(ratio, 2)}:1"


def interpret_structural(
    node: dict,
    raw_instances: list,
    unique_instances: list,
    layouts: list,
    texts: list,
    hidden_layers: list,
    interactions: list,
    image_fills: list,
    variables: dict,
) -> tuple[dict, dict]:
    """
    Deterministic Pass 2a: derive semantic hints and mock_data from collected data.
    Returns (semantic_hints, mock_data).
    """
    hints: dict = {"inferred": True}
    mock: dict = {}

    # Viewport
    dims = extract_dimensions(node)
    if dims:
        w = dims["width"]
        hints["viewport"] = "desktop" if w >= 1200 else ("tablet" if w >= 768 else "mobile")

    # List patterns — same component used 3+ times
    name_counts = Counter(i["component_name"] for i in raw_instances)
    list_patterns = [
        {"component_name": name, "count": count}
        for name, count in name_counts.items()
        if count >= 3
    ]
    if list_patterns:
        hints["list_patterns"] = sorted(list_patterns, key=lambda x: -x["count"])

    # State candidates from hidden layers
    if hidden_layers:
        hints["state_candidates"] = [
            {"path": h["path"], "name": h["name"]}
            for h in hidden_layers[:15]
        ]

    # Primary action — shallowest interactive node
    if interactions:
        primary = min(interactions, key=lambda x: x["depth"])
        hints["primary_action"] = {
            "node_id": primary["node_id"],
            "name":    primary["name"],
            "trigger": primary["triggers"][0] if primary.get("triggers") else None,
        }

    # Pre-compute size bounds once — infer_text_role is called per-text so this is O(n) not O(n²)
    all_sizes = [t.get("font_size", 16) for t in texts if t.get("font_size")]
    max_size  = max(all_sizes) if all_sizes else 16
    min_size  = min(all_sizes) if all_sizes else 16

    # Content roles from texts
    content_roles: dict = {
        "primary_heading": None,
        "subheading":      None,
        "body_text":       None,
        "cta_primary":     None,
        "cta_secondary":   None,
        "price":           None,
        "badge":           None,
    }
    for t in texts:
        role    = infer_text_role(t, max_size, min_size)
        content = t["content"]
        if role == "heading" and content_roles["primary_heading"] is None:
            content_roles["primary_heading"] = content
        elif role == "subheading" and content_roles["subheading"] is None:
            content_roles["subheading"] = content
        elif role == "body" and content_roles["body_text"] is None:
            content_roles["body_text"] = content
        elif role == "cta_label":
            if content_roles["cta_primary"] is None:
                content_roles["cta_primary"] = content
            elif content_roles["cta_secondary"] is None:
                content_roles["cta_secondary"] = content
        elif role == "price" and content_roles["price"] is None:
            content_roles["price"] = content
        elif role == "badge" and content_roles["badge"] is None:
            content_roles["badge"] = content
    hints["content_roles"] = content_roles

    # Mock data — strings
    mock_strings = [
        {
            "content":   t["content"],
            "role":      infer_text_role(t, max_size, min_size),
            "node_name": t["name"],
            "font_size": t.get("font_size"),
        }
        for t in texts
    ]
    mock["strings"] = mock_strings

    # Mock data — images grouped by node_id.
    # strip_master_fills has already removed inherited master fills, so each node
    # only carries its intentional fills (1 for a static image, N for a slider).
    from collections import OrderedDict
    fills_by_node: OrderedDict = OrderedDict()
    for fill in image_fills:
        nid = fill.get("node_id", "")
        if nid not in fills_by_node:
            fills_by_node[nid] = []
        local = fill.get("local_path")
        # deduplicate within the same node
        if local and local not in [f["path"] for f in fills_by_node[nid]]:
            fills_by_node[nid].append({
                "path":         local,
                "role":         infer_image_role(fill),
                "dimensions":   fill.get("dimensions"),
                "aspect_ratio": aspect_ratio_str(fill.get("dimensions")),
                "scale_mode":   fill.get("scaleMode", "FILL"),
            })

    if len(fills_by_node) == 1:
        # Single image node — flat list (backward compatible)
        mock["images"] = list(fills_by_node.values())[0]
    else:
        # Multiple nodes — grouped: [{node_id, fills: [...]}]
        # fills are in Figma paint-stack order (bottom → top)
        mock["images"] = [
            {"node_id": nid, "fills": fills}
            for nid, fills in fills_by_node.items()
        ]

    return hints, mock


# ─── Arg parsing ──────────────────────────────────────────────────────────────

def str_to_bool(value: str) -> bool:
    return value.lower() not in ("false", "0", "no", "off")


# ─── Main ─────────────────────────────────────────────────────────────────────

def _collect_pass1(node: dict, depth: int) -> dict:
    """Run all structural collectors on the node tree. Returns raw extraction data."""
    raw_instances: list = []
    collect_instances(node, depth=0, max_depth=depth, results=raw_instances)
    raw_instances.sort(key=lambda i: i["depth"])

    # Count occurrences per (component_name, variant) to mark list patterns
    from collections import Counter as _Counter
    occ_counts: _Counter = _Counter(
        (i["component_name"], i.get("variant")) for i in raw_instances
    )
    occ_seen: dict = {}
    for inst in raw_instances:
        key = (inst["component_name"], inst.get("variant"))
        idx = occ_seen.get(key, 0)
        inst["occurrence"] = idx          # 0 = first/canonical, 1+ = repeated
        inst["occurrence_total"] = occ_counts[key]  # total times this component appears
        if occ_counts[key] > 1:
            inst["is_list_item"] = True   # component repeats → likely list/carousel item
        occ_seen[key] = idx + 1

    # Keep ALL instances — callers filter by occurrence=0 for canonical view if needed.
    # Previously only the first occurrence was kept; now all are preserved with counters.
    unique_instances = raw_instances  # renamed for backward compat — now contains all

    raw_texts: list = []
    collect_texts(node, depth=0, max_depth=depth, results=raw_texts, path="")
    seen_contents: set = set()
    unique_texts = [
        t for t in raw_texts
        if t["content"] not in seen_contents and not seen_contents.add(t["content"])  # type: ignore[func-returns-value]
    ]

    layouts: list = []
    collect_layouts(node, depth=0, max_depth=depth, results=layouts)

    hidden_layers: list = []
    collect_hidden_layers(node, depth=0, max_depth=depth, results=hidden_layers)

    interactions: list = []
    collect_interactions(node, depth=0, max_depth=depth, results=interactions)

    raw_fill_nodes: list = []
    collect_image_fills(node, depth=0, max_depth=depth, results=raw_fill_nodes)

    return {
        "raw_instances":    raw_instances,
        "unique_instances": unique_instances,
        "raw_texts":        raw_texts,
        "unique_texts":     unique_texts,
        "layouts":          layouts,
        "hidden_layers":    hidden_layers,
        "interactions":     interactions,
        "raw_fill_nodes":   raw_fill_nodes,
    }


def _download_assets(
    file_key: str,
    node_id: str,
    raw_fill_nodes: list,
    output_dir: Path,
    json_dir: Path,
    take_screenshot: bool,
    scale: int,
    fmt: str,
    token: str,
    take_image_fills: bool = True,
) -> tuple[list, str | None]:
    """Download image fills and the root screenshot. Mutates fill entries with local_path.

    Returns:
        raw_fill_nodes:      same list, now with local_path set on each entry
        screenshot_path_rel: path relative to json_dir, or None on failure
    """
    fills_dir    = output_dir / "images" / "fills"
    previews_dir = output_dir / "images" / "previews"

    unique_refs   = list(dict.fromkeys(fill["imageRef"] for fill in raw_fill_nodes))
    fill_paths    = fetch_raw_image_fills(file_key, unique_refs, token, fills_dir) if (unique_refs and take_image_fills) else {}

    for fill in raw_fill_nodes:
        local = fill_paths.get(fill["imageRef"])
        if local:
            # Store just the filename — verify.mjs resolves against WORKING_DIR/images/fills/
            fill["local_path"] = Path(local).name

    screenshot_path_rel = None
    if take_screenshot:
        try:
            previews_dir.mkdir(parents=True, exist_ok=True)
            p = fetch_image(file_key, node_id, token, previews_dir, scale=scale, fmt=fmt)
            if p:
                try:
                    screenshot_path_rel = str(p.relative_to(json_dir))
                except ValueError:
                    screenshot_path_rel = str(p)
                tree_png = json_dir / "images" / "previews" / "tree.png"
                tree_png.parent.mkdir(parents=True, exist_ok=True)
                if p != tree_png:
                    shutil.copy2(str(p), str(tree_png))
        except Exception:
            pass  # null in JSON — callers must handle missing screenshot

    return raw_fill_nodes, screenshot_path_rel


def _enrich_instances_with_variants(
    unique_instances: list,
    variants_map: dict,
) -> None:
    """Mutate instances in-place to attach variants_available from the enrichment map."""
    for inst in unique_instances:
        cid   = inst.get("component_id")
        vdata = variants_map.get(cid) if cid else None
        if not vdata:
            continue
        entry: dict = {}
        if vdata.get("properties"):
            entry["properties"]  = vdata["properties"]
        if vdata.get("all_members"):
            entry["all_members"] = vdata["all_members"]
        combo = _parse_variant_combination(inst.get("variant", ""))
        if combo:
            entry["current_combination"] = combo
        if vdata.get("visual_signatures"):
            entry["visual_signatures"] = vdata["visual_signatures"]
        if entry:
            inst["variants_available"] = entry


def _fetch_root_description(node_id: str, file_key: str, token: str) -> str | None:
    """Fetch the designer description of the root COMPONENT node from /files/{key}/components.

    The Figma /nodes API does not return the description field — it only lives in the
    component registry endpoint. This is a targeted lookup for the root node only.
    """
    try:
        resp = api_get(f"/files/{file_key}/components", token)
        for entry in resp.get("meta", {}).get("components", []):
            nid = entry.get("node_id", "").replace("-", ":")
            if nid == node_id:
                desc = entry.get("description", "").strip()
                return desc or None
    except Exception:
        pass
    return None


def _enrich_instances_with_descriptions(
    unique_instances: list,
    comp_description: dict,
) -> None:
    """Attach designer description from the master component to each instance."""
    for inst in unique_instances:
        cid  = inst.get("component_id")
        desc = comp_description.get(cid) if cid else None
        if desc:
            inst["designer_notes"] = desc


def _merge_master_interactions(
    page_interactions: list,
    master_interactions: list,
) -> list:
    """Return page interactions extended with master interactions, deduplicated by (node_id, trigger)."""
    existing = {
        (ia["node_id"], (ia.get("triggers") or [""])[0])
        for ia in page_interactions
    }
    merged = list(page_interactions)
    for ia in master_interactions:
        key = (ia["node_id"], (ia.get("triggers") or [""])[0])
        if key not in existing:
            merged.append(ia)
            existing.add(key)
    return merged


def _build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Figma node inspector — outputs structured JSON with semantic hints.",
        epilog="Output schema is documented in the module docstring.",
    )
    parser.add_argument("url", help="Figma URL (design, make, board, file)")
    parser.add_argument("--output-dir",  default=".figma/screenshots",
                        help="Directory for screenshots and image fills.")
    parser.add_argument("--depth",       type=int,         default=10)
    parser.add_argument("--screenshot",           type=str_to_bool, default=True,  metavar="true|false")
    parser.add_argument("--instance-screenshots", type=str_to_bool, default=True,  metavar="true|false",
                        help="Export one PNG per unique instance (used by figma-forge). "
                             "Set false to skip and only keep the root screenshot — faster for DRD.")
    parser.add_argument("--image-fills",          type=str_to_bool, default=True,  metavar="true|false",
                        help="Download image fill PNGs to images/fills/. "
                             "Set false to skip downloads — image_fills[] metadata is still present in JSON.")
    parser.add_argument("--format",      choices=["png", "svg"], default="png")
    parser.add_argument("--scale",       type=int,         default=2)
    parser.add_argument("--output-json", default=None, metavar="PATH")
    return parser


def main() -> None:
    args        = _build_cli_parser().parse_args()
    token       = resolve_token()
    output_dir  = Path(args.output_dir)
    json_dir    = Path(args.output_json).parent.resolve() if args.output_json else output_dir.resolve()

    if not token:
        print(json.dumps({"error": "FIGMA_TOKEN not set"}))
        sys.exit(1)

    try:
        file_key, node_id = parse_figma_url(args.url)
    except ValueError as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    if not node_id:
        print(json.dumps({"error": "No node-id in URL — select a node in Figma then use Copy link to selection"}))
        sys.exit(1)

    try:
        data = api_get(
            f"/files/{file_key}/nodes?ids={urllib.parse.quote(node_id)}&depth={args.depth}",
            token,
        )
    except RuntimeError as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    nodes       = data.get("nodes", {})
    node_wrapper = nodes.get(node_id) or next(iter(nodes.values()), None)
    if not node_wrapper:
        print(json.dumps({"error": f"Node {node_id} not found in response"}))
        sys.exit(1)

    node = node_wrapper.get("document")
    if not node:
        print(json.dumps({"error": f"Node {node_id}: no 'document' key"}))
        sys.exit(1)

    # ── Pass 1: Collect ───────────────────────────────────────────────────────
    extracted = _collect_pass1(node, args.depth)
    variables = extract_variables(node, file_key, token, max_depth=args.depth)

    # Remove fills inherited from master components (instance override artifact).
    # Only fires an API call when nodes with 2+ distinct imageRefs are found.
    extracted["raw_fill_nodes"] = strip_master_fills(
        extracted["raw_fill_nodes"], file_key, token
    )

    extracted["raw_fill_nodes"], screenshot_path = _download_assets(
        file_key, node_id,
        extracted["raw_fill_nodes"],
        output_dir, json_dir,
        args.screenshot, args.scale, args.format,
        token,
        take_image_fills=args.image_fills,
    )

    variants_map, master_ias, comp_description = fetch_component_enrichments(file_key, extracted["raw_instances"], token, root_node_id=node_id)
    _enrich_instances_with_variants(extracted["unique_instances"], variants_map)
    _enrich_instances_with_descriptions(extracted["unique_instances"], comp_description)

    interactions = _merge_master_interactions(extracted["interactions"], master_ias)

    # Batch-export one screenshot per unique instance — reference images for forge verification
    instance_ids = [
        inst["id"] for inst in extracted["unique_instances"]
        if inst.get("id") and inst["id"] != node_id  # root already in tree.png
    ]
    previews_dir = output_dir / "images" / "previews"
    fills_dir    = output_dir / "images" / "fills"

    fetch_instances = args.screenshot and args.instance_screenshots
    instance_screenshots = batch_fetch_instance_screenshots(
        file_key, instance_ids, token, previews_dir, json_dir, scale=args.scale,
    ) if fetch_instances else {}

    icon_instances = fetch_icon_svgs(
        extracted["unique_instances"], file_key, token, fills_dir, json_dir,
    ) if fetch_instances else []

    result = {
        "file_key":           file_key,
        "node_id":            node_id,
        "name":               node.get("name", ""),
        "type":               node.get("type", ""),
        # /nodes API does not return description — look it up from comp_description (already fetched)
        # comp_description is keyed by node_id for COMPONENT nodes
        "description":        comp_description.get(node_id) or node.get("description") or None,
        "dimensions":         extract_dimensions(node),
        "corner_radius":      node.get("cornerRadius") or None,
        "layout":             extract_auto_layout(node),
        "screenshot_path":    screenshot_path,
        "screenshots":        instance_screenshots,
        "layouts":            extracted["layouts"],
        "instances":          extracted["unique_instances"],
        "texts":              extracted["unique_texts"],
        "variables":          variables,
        "image_fills":        extracted["raw_fill_nodes"],
        "hidden_layers":      extracted["hidden_layers"],
        "icon_instances":     icon_instances,
        "carousel_signals":   compute_carousel_signals(extracted["raw_fill_nodes"]),
        "list_items_shape":   compute_list_items_shape(
            extracted["raw_instances"], extracted["raw_fill_nodes"],
            extracted["raw_texts"],    extracted["layouts"],
        ),
        "interactions":       interactions,
        # Designer-authored descriptions from master components — keyed by component name.
        # Each instance also carries designer_notes inline (see instances[].designer_notes).
        "component_descriptions": {
            name: desc
            for name, desc in (
                (inst.get("component_name", ""), inst.get("designer_notes", ""))
                for inst in extracted["unique_instances"]
                if inst.get("designer_notes")
            )
            if name
        },
    }

    # ── Pass 2a: Structural interpretation ───────────────────────────────────
    hints, mock = interpret_structural(
        node,
        extracted["raw_instances"], extracted["unique_instances"],
        extracted["layouts"],       extracted["unique_texts"],
        extracted["hidden_layers"], interactions,
        extracted["raw_fill_nodes"], variables,
    )
    result["semantic_hints"] = hints
    result["mock_data"]      = mock

    # Pass 2b (LLM vision) is handled by the calling skill — enriches semantic_hints in-place.
    # The LLM reads tree.json["description"] + tree.json["component_descriptions"] directly.

    output = json.dumps(result, indent=2, ensure_ascii=False)
    print(output)

    if args.output_json:
        dest = Path(args.output_json)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(output, encoding="utf-8")


if __name__ == "__main__":
    main()
