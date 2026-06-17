#!/usr/bin/env python3
"""
Markdown renderer for plan.json. Zero dependencies.
- Justification at the top of each event block
- "Source: Inféré · X%" removed — irrelevant for final user
- "Rationale" → "Justification"
"""

import json
import sys
from pathlib import Path

PARAM_SUPPLEMENT = {
    "resort_code":                 {"description": "Resort identifier code",              "format": "string",  "examples": "MPAC"},
    "resort_name":                 {"description": "Resort display name",                  "format": "string",  "examples": "Marrakech la Palmeraie"},
    "resort_exclusive_collection": {"description": "Exclusive Collection tier",            "format": "enum",    "examples": "no | exclusive_collection | villas_and_chalets"},
    "room_type":                   {"description": "Room comfort category",                "format": "enum",    "examples": "superior | deluxe | suite | villa"},
    "detail_click":                {"description": "Stable action slug — language-neutral","format": "string",  "examples": "change_comfort | media_photos | see_details"},
}

def load_param_lookup(skill_dir=None):
    lookup = {}
    if skill_dir:
        vd_path = Path(skill_dir) / "data" / "variable-dictionary.json"
        if vd_path.exists():
            vd = json.loads(vd_path.read_text(encoding="utf-8"))
            for v in vd.get("variables", []):
                lookup[v["name"]] = {
                    "description": v.get("description",""),
                    "format":      v.get("format","string"),
                    "examples":    str(v.get("examples","") or ""),
                }
    for k, v in PARAM_SUPPLEMENT.items():
        if k not in lookup or not lookup[k].get("description"):
            lookup[k] = v
    return lookup

LABELS = {
    "en": {
        "title": "Tracking Plan", "approved": "Approved events",
        "section": "Section", "tms": "TMS", "analytics": "Analytics",
        "data_layer": "Data layer", "generated": "Generated",
        "trigger": "Trigger", "screenshot": "Element",
        "payload": "Data layer push", "params": "Parameters",
        "justification": "Description", "open_q": "Open Questions",
        "open_q_sub": "_Events proposed but not included in this run._",
        "event": "Event", "rationale_col": "Description",
    },
    "fr": {
        "title": "Plan de marquage", "approved": "Events approuvés",
        "section": "Section", "tms": "TMS", "analytics": "Analytics",
        "data_layer": "Data layer", "generated": "Généré le",
        "trigger": "Déclencheur", "screenshot": "Capture",
        "payload": "Push dataLayer", "params": "Paramètres",
        "justification": "Description", "open_q": "Open Questions",
        "open_q_sub": "_Events proposés mais non inclus dans ce run._",
        "event": "Événement", "rationale_col": "Description",
    },
}


def build_payload_md(entry):
    event   = entry.get("event", "")
    payload = entry.get("payload", {})
    ec      = payload.get("event_click")

    if ec is not None:
        null_push = json.dumps({"event": event, "event_click": None},
                               ensure_ascii=False, indent=2)
        data_push = json.dumps({"event": event, "event_click": ec},
                               ensure_ascii=False, indent=2)
        return (f"```js\n// 1. Reset\nclubMedLayer.push({null_push});\n\n"
                f"// 2. Push\nclubMedLayer.push({data_push});\n```")
    elif "ecommerce" in payload:
        p = {"event": event, "ecommerce": payload["ecommerce"]}
        return f"```js\nclubMedLayer.push({json.dumps(p, ensure_ascii=False, indent=2)});\n```"
    else:
        p = {"event": event, **{k: v for k, v in payload.items() if k != "event"}}
        return f"```js\nclubMedLayer.push({json.dumps(p, ensure_ascii=False, indent=2)});\n```"


def render(plan_file: str, output_dir: str, lang: str = "en", skill_dir: str = None):
    plan         = json.load(open(plan_file, encoding="utf-8"))
    meta         = plan["meta"]
    name         = meta["name"]
    L            = LABELS.get(lang, LABELS["en"])
    param_lookup = load_param_lookup(skill_dir)
    approved     = [e for e in plan["entries"] if e.get("_status") == "approved"]
    rejected     = [e for e in plan["entries"] if e.get("_status") == "rejected"]

    lines = []

    # ── Header ────────────────────────────────────────────────────────────────
    lines += [
        f"# {L['title']} — {name}",
        "",
        f"| Field | Value |",
        f"|---|---|",
        f"| {L['section']} | `{meta.get('site_section', '')}` |",
        f"| {L['tms']} | {meta.get('tms', 'GTM')} |",
        f"| {L['analytics']} | {meta.get('analytics', 'GA4')} |",
        f"| {L['data_layer']} | `{meta.get('data_layer', 'clubMedLayer')}` |",
        f"| {L['generated']} | {meta.get('generated_at', '')} |",
        f"| {L['approved']} | {len(approved)} |",
        "",
        "---",
        "",
    ]

    # ── Events grouped by page ────────────────────────────────────────────────
    pages = {}
    for e in approved:
        page = e.get("page") or e.get("section") or "global"
        pages.setdefault(page, []).append(e)

    for page, entries in pages.items():
        lines += [f"## {page}", ""]

        for e in entries:
            title = f"### `{e['event']}`"
            if e.get("description"):
                title += f" — {e['description']}"
            lines += [title, ""]

            # Justification FIRST — before everything else
            if e.get("rationale"):
                lines += [
                    f"> **{L['justification']} :** {e['rationale']}",
                    "",
                ]

            lines += [f"**{L['trigger']} :** {e.get('trigger', '')}  "]

            if e.get("screenshot"):
                lines += [f"**{L['screenshot']} :** `{e['screenshot']}`  "]

            lines += ["", f"**{L['payload']} :**", "", build_payload_md(e), ""]

            if e.get("params"):
                lines += [
                    f"**{L['params']} :**",
                    "",
                    f"| {L['params']} | Type | Description | Exemple |",
                    "|---|---|---|---|",
                ]
                for p in e["params"]:
                    pname = p.get("name", "")
                    pfmt  = f"`{p.get('type','string')}`"
                    pdesc = p.get("description","—")
                    pex   = p.get("example","—")
                    lines.append(f"| `{pname}` | {pfmt} | {pdesc} | {pex} |")
                lines.append("")

            lines += ["---", ""]

    # ── Open Questions ────────────────────────────────────────────────────────
    if rejected:
        lines += [
            f"## {L['open_q']}",
            "",
            L["open_q_sub"],
            "",
            f"| {L['event']} | {L['trigger']} | {L['justification']} |",
            "|---|---|---|",
        ]
        for e in rejected:
            ev  = f"`{e['event']}`"
            tr  = e.get("trigger", "").replace("|", "\\|")
            rat = e.get("rationale", "").replace("|", "\\|")
            lines.append(f"| {ev} | {tr} | {rat} |")
        lines.append("")

    out_path = Path(output_dir) / f"{name}.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"✓ Markdown written: {out_path}")
    return str(out_path)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: render_markdown.py <plan.json> <output_dir> [lang=en|fr] [skill_dir]")
        sys.exit(1)
    lang      = sys.argv[3] if len(sys.argv) > 3 else "en"
    skill_dir = sys.argv[4] if len(sys.argv) > 4 else None
    render(sys.argv[1], sys.argv[2], lang, skill_dir)
