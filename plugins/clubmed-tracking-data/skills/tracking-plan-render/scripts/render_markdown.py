#!/usr/bin/env python3
"""
Markdown renderer for plan.json. Zero dependencies.
- Justification at the top of each event block
- Per-event confidence line (colour-coded bar + tier emoji) — the user reviews the
  rendered markdown and adjusts low-confidence events
- "Rationale" → "Justification"
"""

import json
import sys
from pathlib import Path


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
        "confidence": "Confidence",
        "status_existing": "Existing", "status_existing_legacy": "Existing (legacy)",
        "status_proposed": "Proposed", "verified": "Verified",
        "recap_existing": "existing", "recap_proposed": "proposed",
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
        "confidence": "Confiance",
        "status_existing": "Existant", "status_existing_legacy": "Existant (legacy)",
        "status_proposed": "Proposé", "verified": "Vérifié",
        "recap_existing": "existant·s", "recap_proposed": "proposé·s",
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


def build_confidence_md(entry, label="Confidence"):
    """Render the confidence line: tier emoji + proportional bar + percent + origin.

    Tiers: 🟢 >= 80% · 🟡 60-79% · 🔴 < 60%. Confirmed/legacy entries (no confidence
    field, or 1.0) show as 🟢 without a bar.
    """
    origin = entry.get("origin", "inferred")
    conf   = entry.get("confidence")

    if conf is None:
        # confirmed / legacy entries carry no confidence score
        return f"**{label} :** 🟢 · {origin}"

    pct    = round(conf * 100)
    emoji  = "🟢" if conf >= 0.80 else "🟡" if conf >= 0.60 else "🔴"
    filled = round(conf * 10)
    bar    = "■" * filled + "□" * (10 - filled)
    return f"**{label} :** {emoji} {bar} {pct}% · {origin}"


def is_existing(entry):
    """An entry reflects tracking already in place (not a proposal)."""
    return entry.get("origin") in ("confirmed", "legacy")


def build_status_md(entry, L):
    """Status badge distinguishing existing tracking from proposals.

    confirmed → ✅ Existing (+ VERIFICATION note if present)
    legacy    → 📋 Existing (legacy)
    inferred  → 💡 Proposed
    """
    origin = entry.get("origin", "inferred")
    if origin == "confirmed":
        line = f"**✅ {L['status_existing']}**"
        note = entry.get("VERIFICATION")
        return f"{line} — _{note}_" if note else line
    if origin == "legacy":
        return f"**📋 {L['status_existing_legacy']}**"
    return f"**💡 {L['status_proposed']}**"


def render(plan_file: str, output_dir: str, lang: str = "en"):
    plan         = json.load(open(plan_file, encoding="utf-8"))
    meta         = plan["meta"]
    name         = meta["name"]
    L            = LABELS.get(lang, LABELS["en"])
    approved     = [e for e in plan["entries"] if e.get("_status") == "approved"]
    rejected     = [e for e in plan["entries"] if e.get("_status") == "rejected"]

    n_existing = sum(1 for e in approved if is_existing(e))
    n_proposed = len(approved) - n_existing

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
        f"| {L['approved']} | {len(approved)} — ✅ {n_existing} {L['recap_existing']} · 💡 {n_proposed} {L['recap_proposed']} |",
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

            # Status badge FIRST — existing tracking vs proposal
            lines += [build_status_md(e, L), ""]

            # Justification — before everything else
            if e.get("rationale"):
                lines += [
                    f"> **{L['justification']} :** {e['rationale']}",
                    "",
                ]

            lines += [f"**{L['trigger']} :** {e.get('trigger', '')}  "]
            lines += [build_confidence_md(e, L["confidence"]) + "  "]

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
        print("Usage: render_markdown.py <plan.json> <output_dir> [lang=en|fr]")
        sys.exit(1)
    lang      = sys.argv[3] if len(sys.argv) > 3 else "en"
    render(sys.argv[1], sys.argv[2], lang)
