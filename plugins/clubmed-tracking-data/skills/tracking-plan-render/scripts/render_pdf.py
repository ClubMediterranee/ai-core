#!/usr/bin/env python3
"""
PDF renderer for plan.json via reportlab.
- Description callout (rationale) at top of each event block
- Styled code block for Push dataLayer
- Params table with description + example from variable-dictionary
- KeepTogether prevents event blocks from splitting across pages
"""

import json
import sys
from pathlib import Path

LABELS = {
    "en": {
        "title":         "Tracking Plan",
        "section":       "Section",
        "tms":           "TMS",
        "analytics":     "Analytics",
        "data_layer":    "Data layer",
        "generated":     "Generated",
        "approved":      "Approved events",
        "description":   "Description",
        "trigger":       "Trigger",
        "payload":       "Data layer push",
        "params":        "Parameters",
        "param":         "Parameter",
        "param_desc":    "Description",
        "param_example": "Example",
        "open_q":        "Open Questions",
        "open_q_sub":    "Events proposed but not included in this run.",
        "event":         "Event",
        "page":          "Page",
        "confidential":  "Confidential — GA4 tracking plan",
    },
    "fr": {
        "title":         "Plan de marquage",
        "section":       "Section",
        "tms":           "TMS",
        "analytics":     "Analytics",
        "data_layer":    "Data layer",
        "generated":     "Généré le",
        "approved":      "Events approuvés",
        "description":   "Description",
        "trigger":       "Déclencheur",
        "payload":       "Push dataLayer",
        "params":        "Paramètres",
        "param":         "Paramètre",
        "param_desc":    "Description",
        "param_example": "Exemple",
        "open_q":        "Open Questions",
        "open_q_sub":    "Events proposés mais non inclus dans ce run.",
        "event":         "Événement",
        "page":          "Page",
        "confidential":  "Plan de marquage GA4 — Confidentiel",
    },
}

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph,
                                     SimpleDocTemplate, Spacer, Table, TableStyle)
    from reportlab.lib.enums import TA_CENTER
except ImportError:
    print("ERROR: reportlab not installed — run: pip3 install reportlab")
    sys.exit(1)

NAVY   = colors.HexColor("#1E2643")
NAVY_S = colors.HexColor("#2D3F6B")
BLUE   = colors.HexColor("#EBF2FB")
GREY   = colors.HexColor("#F7F8FA")
CODE_BG= colors.HexColor("#F0F4F8")
CODE_BD= colors.HexColor("#CBD5E0")
DESC_BG= colors.HexColor("#FFF8E1")
DESC_BD= colors.HexColor("#F6D860")
WHITE  = colors.white
BLACK  = colors.HexColor("#1A1A2E")
DARK_G = colors.HexColor("#4A5568")


def make_styles():
    s = getSampleStyleSheet()
    b = {"fontName": "Helvetica", "fontSize": 10, "textColor": BLACK, "leading": 14}
    for name, kwargs in [
        ("TRTitle",  {**b, "fontSize": 16, "textColor": WHITE, "fontName": "Helvetica-Bold", "alignment": TA_CENTER}),
        ("TRSect",   {**b, "fontSize": 12, "textColor": NAVY,  "fontName": "Helvetica-Bold", "spaceBefore": 10}),
        ("TREvt",    {**b, "fontSize": 11, "textColor": NAVY,  "fontName": "Helvetica-Bold"}),
        ("TRBody",   {**b, "fontSize": 9,  "leading": 13}),
        ("TRSmall",  {**b, "fontSize": 8,  "textColor": DARK_G, "leading": 11}),
        ("TRLabel",  {**b, "fontSize": 8,  "fontName": "Helvetica-Bold", "textColor": DARK_G}),
        ("TRCode",   {**b, "fontSize": 7.5,"fontName": "Courier", "leading": 11, "textColor": BLACK}),
        ("TRDesc",   {**b, "fontSize": 9,  "textColor": colors.HexColor("#7B5E00"), "leading": 13,
                      "fontName": "Helvetica-Oblique"}),
    ]:
        s.add(ParagraphStyle(name, **kwargs))
    return s


def load_param_lookup(skill_dir: str) -> dict:
    """Load variable descriptions from variable-dictionary.json + hardcoded supplements."""
    lookup = {}
    vd_path = Path(skill_dir) / "data" / "variable-dictionary.json"
    if vd_path.exists():
        vd = json.loads(vd_path.read_text(encoding="utf-8"))
        for v in vd.get("variables", []):
            lookup[v["name"]] = {
                "description": v.get("description", ""),
                "examples":    str(v.get("examples", "") or ""),
            }
    # Supplement with domain knowledge for params not in the dictionary
    supplements = {
        "resort_code":                 ("Resort identifier code",             "MPAC"),
        "resort_name":                 ("Resort display name",                 "Marrakech la Palmeraie"),
        "resort_exclusive_collection": ("Exclusive Collection tier",           "no | exclusive_collection | villas_and_chalets"),
        "room_type":                   ("Room comfort category",               "superior | deluxe | suite | villa"),
        "detail_click":                ("Stable action slug — language-neutral","change_comfort | media_photos | see_details"),
    }
    for k, (desc, ex) in supplements.items():
        if k not in lookup or not lookup[k].get("description"):
            lookup[k] = {"description": desc, "examples": ex}
    return lookup


def build_payload_text(entry: dict) -> str:
    event   = entry.get("event", "")
    payload = entry.get("payload", {})
    ec      = payload.get("event_click")
    if ec is not None:
        null_p = json.dumps({"event": event, "event_click": None}, ensure_ascii=False, indent=2)
        data_p = json.dumps({"event": event, "event_click": ec},   ensure_ascii=False, indent=2)
        return f"// 1. Reset\nclubMedLayer.push({null_p});\n\n// 2. Push\nclubMedLayer.push({data_p});"
    elif "ecommerce" in payload:
        p = {"event": event, "ecommerce": payload["ecommerce"]}
        return f"clubMedLayer.push({json.dumps(p, ensure_ascii=False, indent=2)});"
    else:
        p = {"event": event, **{k: v for k, v in payload.items() if k != "event"}}
        return f"clubMedLayer.push({json.dumps(p, ensure_ascii=False, indent=2)});"


def code_block(text: str, s) -> Table:
    safe = (text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
               .replace(" ","&#160;").replace("\n","<br/>"))
    p = Paragraph(safe, s["TRCode"])
    tbl = Table([[p]], colWidths=[170*mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), CODE_BG),
        ("BOX",           (0,0),(-1,-1), 1, CODE_BD),
        ("TOPPADDING",    (0,0),(-1,-1), 7),
        ("BOTTOMPADDING", (0,0),(-1,-1), 7),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
        ("RIGHTPADDING",  (0,0),(-1,-1), 10),
    ]))
    return tbl


def description_block(label: str, text: str, s) -> Table:
    tbl = Table(
        [[Paragraph(label, s["TRLabel"])],
         [Paragraph(text,  s["TRDesc"])]],
        colWidths=[170*mm]
    )
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), DESC_BG),
        ("BOX",           (0,0),(-1,-1), 1, DESC_BD),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("RIGHTPADDING",  (0,0),(-1,-1), 8),
    ]))
    return tbl


def params_table(params: list, param_lookup: dict, L: dict, s) -> Table:
    """Four-column params table: Parameter | Type | Description | Example."""
    hdr = [L["param"], "Type", L["param_desc"], L["param_example"]]
    rows = [hdr]
    for p in params:
        rows.append([
            p.get("name", ""),
            p.get("type", "string"),
            p.get("description", "—"),
            p.get("example", "—"),
        ])
    tbl = Table(rows, colWidths=[40*mm, 22*mm, 74*mm, 34*mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",     (0,0),(-1,0),  NAVY_S),
        ("TEXTCOLOR",      (0,0),(-1,0),  WHITE),
        ("FONTNAME",       (0,0),(-1,0),  "Helvetica-Bold"),
        ("FONTNAME",       (0,1),(-1,-1), "Courier"),
        ("FONTSIZE",       (0,0),(-1,-1), 8),
        ("ROWBACKGROUNDS", (0,1),(-1,-1), [WHITE, GREY]),
        ("GRID",           (0,0),(-1,-1), 0.3, CODE_BD),
        ("TOPPADDING",     (0,0),(-1,-1), 3),
        ("BOTTOMPADDING",  (0,0),(-1,-1), 3),
        ("LEFTPADDING",    (0,0),(-1,-1), 6),
        ("VALIGN",         (0,0),(-1,-1), "TOP"),
    ]))
    return tbl


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, A4[1]-18*mm, A4[0], 18*mm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(15*mm, A4[1]-12*mm, doc.title)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(A4[0]-15*mm, A4[1]-12*mm, f"Page {doc.page}")
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, A4[0], 7*mm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(15*mm, 2.5*mm, doc.confidential_label)
    canvas.restoreState()


def render(plan_file: str, output_dir: str, lang: str = "en", skill_dir: str = None):
    plan         = json.load(open(plan_file, encoding="utf-8"))
    meta         = plan["meta"]
    name         = meta["name"]
    s            = make_styles()
    L            = LABELS.get(lang, LABELS["en"])
    approved     = [e for e in plan["entries"] if e.get("_status") == "approved"]
    rejected     = [e for e in plan["entries"] if e.get("_status") == "rejected"]
    param_lookup = load_param_lookup(skill_dir or str(Path(__file__).parent.parent))

    out_path = Path(output_dir) / f"{name}.pdf"
    doc = SimpleDocTemplate(
        str(out_path), pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=26*mm, bottomMargin=16*mm,
    )
    doc.title             = f"{L['title']} — {name}"
    doc.confidential_label = L["confidential"]
    story = []

    # ── Cover ─────────────────────────────────────────────────────────────────
    story.append(Table(
        [[Paragraph(L["title"], s["TRTitle"])],
         [Paragraph(f"<b>{name.upper()}</b>", s["TRTitle"])]],
        colWidths=[180*mm],
        style=TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), NAVY),
            ("TOPPADDING",    (0,0),(0,0),   14),
            ("BOTTOMPADDING", (0,0),(0,0),   2),
            ("TOPPADDING",    (0,1),(0,1),   2),
            ("BOTTOMPADDING", (0,1),(0,1),   14),
        ])
    ))
    story.append(Spacer(1, 6*mm))

    mt = Table([
        [L["section"],    meta.get("site_section","")],
        [L["tms"],        meta.get("tms","GTM")],
        [L["analytics"],  meta.get("analytics","GA4")],
        [L["data_layer"], meta.get("data_layer","clubMedLayer")],
        [L["generated"],  meta.get("generated_at","")],
        [L["approved"],   str(len(approved))],
    ], colWidths=[40*mm, 140*mm])
    mt.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(0,-1), NAVY_S),
        ("TEXTCOLOR",     (0,0),(0,-1), WHITE),
        ("FONTNAME",      (0,0),(0,-1), "Helvetica-Bold"),
        ("BACKGROUND",    (1,0),(1,-1), BLUE),
        ("FONTSIZE",      (0,0),(-1,-1), 9),
        ("GRID",          (0,0),(-1,-1), 0.3, WHITE),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
    ]))
    story.append(mt)
    story.append(PageBreak())

    # ── Events — wrapped in KeepTogether to prevent mid-block page breaks ─────
    pages = {}
    for e in approved:
        page = e.get("page") or e.get("section") or "global"
        pages.setdefault(page, []).append(e)

    for page, entries in pages.items():
        story.append(Paragraph(page, s["TRSect"]))
        story.append(Spacer(1, 2*mm))

        for e in entries:
            block = []   # all elements for this event — kept together

            # Title
            title = f"<b>{e['event']}</b>"
            if e.get("description"):
                title += f" — {e['description']}"
            block.append(Paragraph(title, s["TREvt"]))
            block.append(Spacer(1, 1.5*mm))

            # Description callout (rationale)
            if e.get("rationale"):
                block.append(description_block(L["description"], e["rationale"], s))
                block.append(Spacer(1, 2*mm))

            # Trigger
            block.append(Paragraph(
                f"<b>{L['trigger']} :</b> {e.get('trigger','')}",
                s["TRBody"]
            ))
            block.append(Spacer(1, 1.5*mm))

            # Screenshot
            if e.get("screenshot"):
                img_path = Path(output_dir) / e["screenshot"]
                if img_path.exists():
                    try:
                        block.append(Image(str(img_path), width=55*mm, height=36*mm))
                        block.append(Spacer(1, 1.5*mm))
                    except Exception:
                        pass

            # Push dataLayer
            block.append(Paragraph(f"{L['payload']} :", s["TRLabel"]))
            block.append(Spacer(1, 1*mm))
            block.append(code_block(build_payload_text(e), s))

            # Params — enriched with description + example
            if e.get("params"):
                block.append(Spacer(1, 1.5*mm))
                block.append(params_table(e["params"], param_lookup, L, s))

            block.append(Spacer(1, 6*mm))
            story.append(KeepTogether(block))

    # ── Open Questions ────────────────────────────────────────────────────────
    if rejected:
        story.append(PageBreak())
        story.append(Paragraph(L["open_q"], s["TRSect"]))
        story.append(Spacer(1, 3*mm))
        oq_rows = [[L["event"], L["trigger"], L["description"]]]
        for e in rejected:
            oq_rows.append([e.get("event",""), e.get("trigger",""), e.get("rationale","")])
        oq = Table(oq_rows, colWidths=[38*mm, 60*mm, 82*mm])
        oq.setStyle(TableStyle([
            ("BACKGROUND",     (0,0),(-1,0),  NAVY),
            ("TEXTCOLOR",      (0,0),(-1,0),  WHITE),
            ("FONTNAME",       (0,0),(-1,0),  "Helvetica-Bold"),
            ("FONTSIZE",       (0,0),(-1,-1), 8),
            ("ROWBACKGROUNDS", (0,1),(-1,-1), [WHITE, GREY]),
            ("GRID",           (0,0),(-1,-1), 0.3, CODE_BD),
            ("TOPPADDING",     (0,0),(-1,-1), 4),
            ("BOTTOMPADDING",  (0,0),(-1,-1), 4),
            ("LEFTPADDING",    (0,0),(-1,-1), 5),
            ("VALIGN",         (0,0),(-1,-1), "TOP"),
        ]))
        story.append(oq)

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"✓ PDF written: {out_path}")
    return str(out_path)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: render_pdf.py <plan.json> <output_dir> [lang=en|fr] [skill_dir]")
        sys.exit(1)
    lang      = sys.argv[3] if len(sys.argv) > 3 else "en"
    skill_dir = sys.argv[4] if len(sys.argv) > 4 else None
    render(sys.argv[1], sys.argv[2], lang, skill_dir)
