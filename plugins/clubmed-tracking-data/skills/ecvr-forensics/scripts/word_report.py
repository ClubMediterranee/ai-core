"""
ECVR BE Explicability Analysis — Word Report
Reads synthesis_output.json + analysis_input.json, produces a stylized, readable
.docx report following the EXACT same structure and content rules as the Teams
card (teams_message.py) — same section order, same CARD METRIC CONVENTION,
same green/red-only color logic, same flag handling. This is an alternate output
format for the same synthesis data, not a different analysis.

Section order (identical to the 3-part Teams card, just as one continuous document):
  1. KPIs
  2. Autopsy (overall_conclusion)
  3. DEVICE — global view
  4. NEW CUSTOM CHANNEL GROUP — global view
  5. BUSINESS UNIT SPLIT (+ BU KPI bar)
  6. BUSINESS UNIT FOCUS (per-BU top-3 countries, device, channel)
  7. CHANNEL × COUNTRY HIGHLIGHTS — each BU-focus country's top 2 channels by impact
  8. RESORT FOCUS — top 5 positive / top 5 negative
  9. OTHER KEY SIGNALS
 10. TOP 3 ACTIONS + WATCH POINTS

Requires: pip install python-docx
"""

import json
import os
import sys
from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# All file paths resolve against ECVR_DOWNLOADS_DIR (defaults to this machine's
# original working directory) — set that env var to point the whole pipeline
# at a different folder without editing every script.
_DOWNLOADS_DIR = Path(os.environ.get("ECVR_DOWNLOADS_DIR", r"/mnt/c/Users/xxxxx/Downloads"))

INPUT_JSON     = _DOWNLOADS_DIR / "synthesis_output.json"
ANALYSIS_INPUT = _DOWNLOADS_DIR / "analysis_input.json"
OUTPUT_DOCX    = _DOWNLOADS_DIR / "ECVR_Forensics_Report.docx"

# Same green/red-only palette as teams_message.py — no orange/yellow for flags.
COLOR_POSITIVE = RGBColor(0x1E, 0x7D, 0x32)   # green
COLOR_NEGATIVE = RGBColor(0xC6, 0x28, 0x28)   # red
COLOR_NEUTRAL  = RGBColor(0x42, 0x42, 0x42)   # dark grey (neutral direction)
COLOR_SUBTLE   = RGBColor(0x75, 0x75, 0x75)   # grey (metric_line / narrative)
COLOR_ACCENT   = RGBColor(0x1A, 0x56, 0x8C)   # blue (headers, period)
COLOR_WARNING  = RGBColor(0xB8, 0x8A, 0x00)   # amber — WATCH POINTS heading only, never flags

FONT_BODY   = "Calibri"
FONT_HEADER = "Calibri"


# ---------------------------------------------------------------------------
# Low-level docx helpers
# ---------------------------------------------------------------------------
def set_cell_shading(cell, hex_color: str):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    cell._tc.get_or_add_tcPr().append(shd)


def add_heading(doc, text: str, level: int = 1, color: RGBColor = COLOR_ACCENT, space_before=18, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = FONT_HEADER
    run.font.bold = True
    run.font.size = Pt({1: 20, 2: 15, 3: 12.5}.get(level, 12))
    run.font.color.rgb = color
    if level == 1:
        pPr = p._p.get_or_add_pPr()
        border = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"), "single")
        bottom.set(qn("w:sz"), "8")
        bottom.set(qn("w:space"), "4")
        bottom.set(qn("w:color"), "1A568C")
        border.append(bottom)
        pPr.append(border)
    return p


def add_narrative(doc, text: str):
    if not text:
        return
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(8)
    run = p.add_run(text)
    run.font.italic = True
    run.font.size = Pt(10.5)
    run.font.color.rgb = COLOR_SUBTLE
    run.font.name = FONT_BODY


FLAG_LABELS = {"🔧": "Data quality", "🔍": "Small base", "⚑": "Model vs GA4"}


def flag_note_run(p, flag: str):
    """Flags render in RED text only (never orange), consistent with
    teams_message.py's FLAG_COLORS — both flag types map to the same red."""
    if not flag:
        return
    run = p.add_run(f"  [{flag}]")
    run.font.size = Pt(9)
    run.font.bold = True
    run.font.color.rgb = COLOR_NEGATIVE


def direction_color(direction: str) -> RGBColor:
    if direction == "positive":
        return COLOR_POSITIVE
    if direction == "negative":
        return COLOR_NEGATIVE
    return COLOR_NEUTRAL


def add_item(doc, header: str, metric_line: str, summary: str, color: RGBColor, flag: str = "", site: str = "", fixed_color: bool = False):
    """Renders one card-equivalent item: bold colored header (+ optional site),
    grey metric_line, plain summary, red flag note if present. Header color is
    forced to red whenever a flag is present, same rule as teams_message.py's
    item_card (a flagged item is an unconfirmed/artifact reading) — UNLESS
    fixed_color=True, in which case the passed color is used as-is regardless
    of flag (mirrors teams_message.py's fixed_color_item, used for resort items
    whose color is already fixed by which list — positive/negative — they're
    placed in; a flag there is a caveat, not a color override)."""
    if flag and not fixed_color:
        color = COLOR_NEGATIVE

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.keep_with_next = True
    header_text = header + (f"  —  {site}" if site else "")
    run = p.add_run(header_text)
    run.font.bold = True
    run.font.size = Pt(11)
    run.font.color.rgb = color
    run.font.name = FONT_BODY
    flag_note_run(p, flag)

    if metric_line:
        p2 = doc.add_paragraph()
        p2.paragraph_format.space_before = Pt(0)
        p2.paragraph_format.space_after = Pt(0)
        p2.paragraph_format.keep_with_next = True
        r2 = p2.add_run(metric_line)
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = COLOR_SUBTLE
        r2.font.name = FONT_BODY

    if summary:
        p3 = doc.add_paragraph()
        p3.paragraph_format.space_before = Pt(1)
        p3.paragraph_format.space_after = Pt(4)
        r3 = p3.add_run(summary)
        r3.font.size = Pt(10.5)
        r3.font.name = FONT_BODY


def add_country_channel_block(doc, country: str, business_unit: str, items: list):
    """
    Groups a country's channel×country highlight items into ONE block: a
    country sub-header with its net read (e.g. "2 channels hurting"), then one
    line per channel explicitly labelled Helping/Hurting — mirrors
    teams_message.py's build_country_channel_block. Replaces a flat list of
    individually-colored items that read as an undifferentiated wall of red
    with occasional unlabelled green. Does NOT render per-item flags (see
    module docstring above this function's call site) — flags still appear
    in full detail wherever the same finding is analysed elsewhere.
    """
    positive_n = sum(1 for it in items if it.get("direction") == "positive")
    negative_n = len(items) - positive_n
    net_color = COLOR_POSITIVE if negative_n == 0 else COLOR_NEGATIVE
    if positive_n and negative_n:
        net_label = f"{positive_n} helping, {negative_n} hurting"
    elif positive_n:
        net_label = f"{positive_n} channel{'s' if positive_n > 1 else ''} helping"
    else:
        net_label = f"{negative_n} channel{'s' if negative_n > 1 else ''} hurting"

    bu_tag = f" ({business_unit})" if business_unit else ""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(f"{country}{bu_tag} — {net_label}")
    r.font.bold = True
    r.font.size = Pt(11)
    r.font.color.rgb = net_color
    r.font.name = FONT_BODY

    read = next((it.get("market_read") for it in items if it.get("market_read")), "")
    if read:
        pr = doc.add_paragraph()
        pr.paragraph_format.space_before = Pt(0)
        pr.paragraph_format.space_after = Pt(2)
        pr.paragraph_format.keep_with_next = True
        rr = pr.add_run(read)
        rr.font.size = Pt(9.5)
        rr.font.name = FONT_BODY
    for it in items:
        is_positive = it.get("direction") == "positive"
        drv = it.get("driver")
        icon = ("Helping" if is_positive else "Hurting") + (f" via {drv}" if drv and drv != "negligible" else "")
        color = COLOR_POSITIVE if is_positive else COLOR_NEGATIVE
        p2 = doc.add_paragraph()
        p2.paragraph_format.space_before = Pt(2)
        p2.paragraph_format.space_after = Pt(0)
        p2.paragraph_format.keep_with_next = True
        r2 = p2.add_run(f"{icon} — {it.get('group', '')}: {it.get('metric_line', '')}")
        r2.font.size = Pt(9.5)
        r2.font.bold = True
        r2.font.color.rgb = color
        r2.font.name = FONT_BODY
        if it.get("summary"):
            p3 = doc.add_paragraph()
            p3.paragraph_format.space_before = Pt(0)
            p3.paragraph_format.space_after = Pt(4)
            r3 = p3.add_run(it["summary"])
            r3.font.size = Pt(9.5)
            r3.font.color.rgb = COLOR_SUBTLE
            r3.font.name = FONT_BODY
        if it.get("flag"):
            p4 = doc.add_paragraph()
            p4.paragraph_format.space_before = Pt(0)
            p4.paragraph_format.space_after = Pt(4)
            r4 = p4.add_run(it["flag"])
            r4.font.size = Pt(9)
            r4.font.bold = True
            r4.font.color.rgb = COLOR_NEGATIVE
            r4.font.name = FONT_BODY


def add_fact_table(doc, facts: list, col_widths=(Cm(4.5), Cm(9.0))):
    """A compact two-column table (name | metric_line) — used for channel
    breakdowns inside BU FOCUS, mirroring the card's FactSet."""
    if not facts:
        return
    table = doc.add_table(rows=0, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    table.autofit = False
    for name, value in facts:
        row = table.add_row()
        row.cells[0].width, row.cells[1].width = col_widths
        p0 = row.cells[0].paragraphs[0]
        r0 = p0.add_run(name)
        r0.font.bold = True
        r0.font.size = Pt(9.5)
        r0.font.name = FONT_BODY
        p1 = row.cells[1].paragraphs[0]
        r1 = p1.add_run(value)
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = COLOR_SUBTLE
        r1.font.name = FONT_BODY
        set_cell_shading(row.cells[0], "F2F2F2")
        set_cell_shading(row.cells[1], "F2F2F2")


def fmt_kpi_value(var: str, value) -> str:
    if value is None:
        return "N/A"
    if var == "total_sessions":
        return f"{int(value):,}"
    return f"{value:.2%}"


def fmt_yoy(variation) -> tuple:
    if variation is None:
        return "", "N/A", COLOR_NEUTRAL
    sign = "▲" if variation >= 0 else "▼"
    color = COLOR_POSITIVE if variation >= 0 else COLOR_NEGATIVE
    return sign, f"{abs(variation):.1%}", color


# ---------------------------------------------------------------------------
# KPI bar (top global KPIs + BU KPI bar) — rendered as tables, same 3/5-column
# layout the card uses, since Word has no native "ColumnSet"
# ---------------------------------------------------------------------------
def _forensics_path():
    return _DOWNLOADS_DIR / "forensics_output.json"


def extract_kpis(analysis_input: dict) -> dict:
    """Headline KPIs from GA4 (forensics_output.json); explicability-model snapshot only as a fallback."""
    fp = _forensics_path()
    if fp.exists():
        k = json.load(open(fp, encoding="utf-8")).get("kpis") or {}
        if k:
            rel = lambda a: ((a[1] / a[0] - 1) if a and a[0] else None)
            return {
                "total_sessions": {"current": k["sessions"][1], "yoy": rel(k["sessions"])},
                "BE_Entry_Rate": {"current": k["be_entry_rate"][1], "yoy": rel(k["be_entry_rate"])},
                "ECVR_BE": {"current": k["ecvr"][1], "yoy": rel(k["ecvr"])},
            }
    kpis = {}
    for row in analysis_input.get("bucket_4_core_kpi_snapshot", []):
        if row.get("site") == "Global":
            var = row.get("variable")
            if var in ("total_sessions", "BE_Entry_Rate", "ECVR_BE"):
                kpis[var] = {"current": row.get("valeur"), "yoy": row.get("variation")}
    return kpis


def extract_bu_kpis(analysis_input: dict) -> list:
    rows = [dict(r) for r in analysis_input.get("bu_breakdown", [])]
    fp = _forensics_path()
    if fp.exists():
        fx = json.load(open(fp, encoding="utf-8"))
        bu = {s["scope"]: s for s in fx.get("scopes", []) if s.get("level") == "bu" and "totals" in s}
        g = next((s for s in fx.get("scopes", []) if s.get("level") == "global" and "totals" in s), None)
        for r in rows:
            s = bu.get(r.get("business_unit"))
            if s and g:
                t = s["totals"]
                r["ecvr_be"] = t["ecvr"][1]
                r["pct_change"] = (t["ecvr_yoy_pct"] / 100) if t["ecvr_yoy_pct"] is not None else None
                r["poids"] = t["sessions"][1] / g["totals"]["sessions"][1]
    return rows


def extract_country_bu_lookup(analysis_input: dict) -> dict:
    """Builds {country_name: business_unit} from analysis_input.json's
    top_countries_per_bu — reliable fallback for crossover_section items, since
    the LLM-filled business_unit field there is occasionally left blank."""
    lookup = {}
    for bu, countries in analysis_input.get("top_countries_per_bu", {}).items():
        for c in countries:
            site = c.get("site")
            if site:
                lookup[site] = bu
    return lookup


def add_kpi_bar(doc, columns: list):
    """columns: list of (label, big_value_str, yoy_sign, yoy_pct_str, yoy_color)."""
    if not columns:
        return
    table = doc.add_table(rows=3, cols=len(columns))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for col_idx, (label, value_str, sign, pct, color) in enumerate(columns):
        for row_idx, (text, size, bold, txt_color) in enumerate([
            (label, 9.5, True, COLOR_NEUTRAL),
            (value_str, 18, True, COLOR_ACCENT),
            (f"{sign} {pct} vs N-1", 9.5, False, color),
        ]):
            cell = table.cell(row_idx, col_idx)
            set_cell_shading(cell, "F2F2F2")
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(text)
            run.font.size = Pt(size)
            run.font.bold = bold
            run.font.color.rgb = txt_color
            run.font.name = FONT_BODY
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


# ---------------------------------------------------------------------------
# Section builders — each mirrors the equivalent teams_message.py section
# ---------------------------------------------------------------------------
def add_device_section(doc, device_global: dict):
    d_narrative = device_global.get("narrative", "")
    d_items = device_global.get("items", [])[:3]
    if not (d_narrative or d_items):
        return
    add_heading(doc, "📱  DEVICE — Global", level=2)
    add_narrative(doc, d_narrative)
    for item in d_items:
        add_item(
            doc, item.get("label", ""), item.get("metric_line", ""), item.get("summary", ""),
            direction_color(item.get("direction", "")), item.get("flag", ""),
        )


def add_channel_section(doc, channel_global: dict):
    ch_narrative = channel_global.get("narrative", "")
    # Up to 3 positive + 3 negative = 6 items max (see the synthesis_output.json schema) — [:5]
    # here previously silently dropped the 6th item off the end.
    ch_items = channel_global.get("items", [])[:6]
    if not (ch_narrative or ch_items):
        return
    add_heading(doc, "📡  NEW CUSTOM CHANNEL GROUP — Global", level=2)
    add_narrative(doc, ch_narrative)
    for item in ch_items:
        add_item(
            doc, item.get("group", ""), item.get("metric_line", ""), item.get("summary", ""),
            direction_color(item.get("direction", "")), item.get("flag", ""),
        )


def add_bu_split_section(doc, bu_section: dict, bu_kpis: list):
    bu_narrative = bu_section.get("narrative", "")
    bu_items = bu_section.get("items", [])
    if not (bu_narrative or bu_items or bu_kpis):
        return
    add_heading(doc, "🧭  BUSINESS UNIT SPLIT", level=2)

    if bu_kpis:
        columns = []
        for row in bu_kpis:
            bu = row.get("business_unit", "")
            ecvr_be = row.get("ecvr_be")
            pct_change = row.get("pct_change")
            poids = row.get("poids")
            ecvr_str = f"{ecvr_be:.2%}" if ecvr_be is not None else "N/A"
            sign, pct, color = fmt_yoy(pct_change)
            label = f"{bu} ({poids:.1%} of sessions)" if poids is not None else bu
            columns.append((label, ecvr_str, sign, pct, color))
        add_kpi_bar(doc, columns)

    add_narrative(doc, bu_narrative)
    for item in bu_items:
        add_item(
            doc, item.get("business_unit", ""), item.get("metric_line", ""), item.get("summary", ""),
            direction_color(item.get("direction", "")), item.get("flag", ""),
        )


def add_bu_focus_section(doc, bu_focus: list):
    if not bu_focus:
        return
    add_heading(doc, "🔎  BUSINESS UNIT FOCUS", level=1)
    add_narrative(doc, "Top 3 countries, device and New Custom Channel Group breakdown, per Business Unit.")

    for bu in bu_focus:
        name = bu.get("business_unit", "")
        narrative = bu.get("narrative", "")
        countries = bu.get("top_countries", [])
        device = bu.get("device", {})
        channel = bu.get("channel", {})

        add_heading(doc, f"── {name} ──", level=3, color=COLOR_ACCENT, space_before=14, space_after=2)
        add_narrative(doc, narrative)

        for c in countries[:3]:
            add_item(
                doc, c.get("market", ""), c.get("metric_line", ""), c.get("summary", ""),
                direction_color(c.get("direction", "")), c.get("flag", ""),
            )

        if device.get("metric_line") or device.get("summary"):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            r = p.add_run("📱 Device")
            r.font.bold = True
            r.font.size = Pt(10)
            r.font.name = FONT_BODY
            if device.get("metric_line"):
                p2 = doc.add_paragraph()
                p2.paragraph_format.space_before = Pt(0)
                p2.paragraph_format.space_after = Pt(0)
                r2 = p2.add_run(device["metric_line"])
                r2.font.size = Pt(9.5)
                r2.font.color.rgb = COLOR_SUBTLE
                r2.font.name = FONT_BODY
            if device.get("summary"):
                p3 = doc.add_paragraph()
                p3.paragraph_format.space_after = Pt(4)
                r3 = p3.add_run(device["summary"])
                r3.font.size = Pt(10)
                r3.font.name = FONT_BODY

        channel_items = channel.get("items", [])
        if channel_items or channel.get("summary"):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            r = p.add_run("📡 New Custom Channel Group")
            r.font.bold = True
            r.font.size = Pt(10)
            r.font.name = FONT_BODY
            facts = [(row.get("group", "?"), row.get("metric_line", "")) for row in channel_items[:4]]
            add_fact_table(doc, facts)
            if channel.get("summary"):
                p3 = doc.add_paragraph()
                p3.paragraph_format.space_after = Pt(6)
                r3 = p3.add_run(channel["summary"])
                r3.font.size = Pt(10)
                r3.font.name = FONT_BODY


def add_crossover_section(doc, crossover: dict, country_bu_lookup: dict | None = None):
    """CHANNEL × COUNTRY HIGHLIGHTS — grouped by COUNTRY (mirrors
    teams_message.py's build_country_channel_block), not a flat list of 26
    individually-colored items — that flat layout read as an undifferentiated
    wall of red with occasional unlabelled green. Shows every BU-focus country
    (no size constraint here, unlike the Teams payload), ranked by urgency
    (most negative channels first, then flagged ones). Per-item data-quality
    flags are deliberately not rendered here (see add_country_channel_block) —
    this section is a fast country-by-country skim, not where flags get
    litigated; the same finding still carries its flag in bu_focus/other_signals.

    country_bu_lookup ({country: BU}) backstops the LLM-filled business_unit
    field, which is occasionally left blank."""
    country_bu_lookup = country_bu_lookup or {}
    x_narrative = crossover.get("narrative", "")
    x_items_all = crossover.get("items", [])
    if not (x_narrative or x_items_all):
        return

    countries_ordered = []
    seen = set()
    for it in x_items_all:
        c = it.get("country", "")
        if c not in seen:
            seen.add(c)
            countries_ordered.append(c)
    by_country = {c: [it for it in x_items_all if it.get("country") == c] for c in countries_ordered}

    def _country_urgency(c: str) -> tuple:
        items = by_country[c]
        negative_n = sum(1 for it in items if it.get("direction") != "positive")
        flagged_n = sum(1 for it in items if it.get("flag"))
        return (-negative_n, -flagged_n)
    countries_ranked = sorted(countries_ordered, key=_country_urgency)

    add_heading(doc, "🔀  CHANNEL × COUNTRY HIGHLIGHTS", level=2)
    add_narrative(doc, x_narrative)
    for c in countries_ranked:
        items = by_country[c]
        bu = items[0].get("business_unit") or country_bu_lookup.get(c, "")
        add_country_channel_block(doc, c, bu, items)


def add_resort_section(doc, resort: dict):
    """RESORT FOCUS — top 5 positive / top 5 negative. Color is FIXED by list
    membership (fixed_color=True) — a flag never flips a positive-list item to
    red or vice versa (item 8 fix); it only adds a caveat note below."""
    r_pos = resort.get("positive", {})
    r_neg = resort.get("negative", {})
    r_pos_items = r_pos.get("items", [])[:5]
    r_neg_items = r_neg.get("items", [])[:5]
    if not (r_pos_items or r_neg_items or r_pos.get("narrative") or r_neg.get("narrative")):
        return
    add_heading(doc, "🏖️  RESORT FOCUS", level=2)
    if r_pos.get("narrative"):
        add_narrative(doc, "Model credits these positively: " + r_pos["narrative"])
    for item in r_pos_items:
        add_item(doc, item.get("variable", ""), item.get("metric_line", ""), item.get("summary", ""),
                  COLOR_POSITIVE, item.get("flag", ""), fixed_color=True)
    if r_neg.get("narrative"):
        add_narrative(doc, "Model credits these negatively: " + r_neg["narrative"])
    for item in r_neg_items:
        add_item(doc, item.get("variable", ""), item.get("metric_line", ""), item.get("summary", ""),
                  COLOR_NEGATIVE, item.get("flag", ""), fixed_color=True)


def add_other_signals_section(doc, other: dict):
    # Every header stays grey regardless of direction OR flag (fixed_color=True
    # bypasses add_item's flag-override) — the flag itself already renders as
    # its own red note below the summary via flag_note_run; also coloring the
    # header red on top of that, with everything else in this mixed-direction
    # grab-bag section randomly blue, was too much visual noise.
    o_narrative = other.get("narrative", "")
    o_items = other.get("items", [])[:16]
    if not (o_narrative or o_items):
        return
    add_heading(doc, "🧩  OTHER KEY SIGNALS", level=2)
    add_narrative(doc, o_narrative)
    for item in o_items:
        label = f"{item.get('theme', '')} ({item.get('variable', '')})" if item.get("variable") else item.get("theme", "")
        add_item(
            doc, label, item.get("metric_line", ""), item.get("summary", ""),
            COLOR_NEUTRAL, item.get("flag", ""), site=item.get("site", ""), fixed_color=True,
        )


def add_top_actions_and_watch_points(doc, top_actions: list, watch_points: list):
    if top_actions:
        add_heading(doc, "🎯  TOP 3 ACTIONS THIS MONTH", level=2)
        for i, action in enumerate(top_actions[:3], 1):
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(6)
            r1 = p.add_run(f"{i}. ")
            r1.font.bold = True
            r1.font.size = Pt(11)
            r1.font.name = FONT_BODY
            r2 = p.add_run(action)
            r2.font.size = Pt(11)
            r2.font.name = FONT_BODY

    if watch_points:
        add_heading(doc, "⚠️  WATCH POINTS", level=2, color=COLOR_WARNING)
        add_narrative(doc, "Actionable flags for the next sprint — data quality issues, anomalies to investigate, or risks that could distort future analyses.")
        for wp in watch_points[:10]:
            p = doc.add_paragraph(style="List Bullet")
            r = p.add_run(wp)
            r.font.size = Pt(10.5)
            r.font.name = FONT_BODY


def add_legend_and_footer(doc, summary: dict):
    all_flags = []
    sections = [
        summary.get("device_section_global", {}),
        summary.get("channel_section_global", {}),
        summary.get("bu_section", {}),
        summary.get("crossover_section", {}),
        summary.get("resort_section", {}).get("positive", {}),
        summary.get("resort_section", {}).get("negative", {}),
        summary.get("other_signals_section", {}),
    ]
    for section in sections:
        for item in section.get("items", []):
            f = item.get("flag", "")
            if f and f[:1] not in all_flags:
                all_flags.append(f[:1])
    for bu in summary.get("bu_focus", []):
        for c in bu.get("top_countries", []):
            f = c.get("flag", "")
            if f and f[:1] not in all_flags:
                all_flags.append(f[:1])

    legend_text = {
        "🔧": "🔧 Data quality = probable tracking/tagging fault, not a genuine business signal until validated.",
        "🔍": "🔍 Small base = % built on very few booking confirmations (or a near-zero prior base), directional read only.",
        "⚑": "⚑ Model vs GA4 = the explicability model and GA4 disagree on direction or size; the figure shown is GA4.",
    }

    doc.add_paragraph().paragraph_format.space_before = Pt(12)
    if all_flags:
        p = doc.add_paragraph()
        r = p.add_run(" ".join(legend_text[f] for f in all_flags if f in legend_text)
                       + " Header color is switched to red whenever a flag is present, overriding the direction-based green/red.")
        r.font.size = Pt(8.5)
        r.font.italic = True
        r.font.color.rgb = COLOR_SUBTLE
        r.font.name = FONT_BODY

    p2 = doc.add_paragraph()
    r2 = p2.add_run(
        "Generated automatically · Club Med Digital Analytics · "
        "Channel figures use GA4's New Custom Channel Group exclusively. "
        "Figures are live GA4 (ECVR-forensics v2); the explicability model only proposes what to look at, and where it "
        "disagrees with GA4 the item is flagged ⚑. GA4 can differ slightly due to late-arriving sessions (~72h processing "
        "window). Low-volume markets should be treated as approximate."
    )
    r2.font.size = Pt(8.5)
    r2.font.italic = True
    r2.font.color.rgb = COLOR_SUBTLE
    r2.font.name = FONT_BODY


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def build_report(summary: dict, kpis: dict, bu_kpis: list, country_bu_lookup: dict | None = None) -> Document:
    doc = Document()

    # Base style
    normal = doc.styles["Normal"]
    normal.font.name = FONT_BODY
    normal.font.size = Pt(10.5)
    for section in doc.sections:
        section.left_margin = Cm(2.0)
        section.right_margin = Cm(2.0)
        section.top_margin = Cm(1.5)
        section.bottom_margin = Cm(1.5)

    period = summary.get("analysis_period", "Monthly Analysis")

    # --- Title + period ---
    title = doc.add_paragraph()
    title.paragraph_format.space_after = Pt(2)
    tr = title.add_run("📊 ECVR BE Monthly Analysis")
    tr.font.size = Pt(24)
    tr.font.bold = True
    tr.font.color.rgb = COLOR_ACCENT
    tr.font.name = FONT_HEADER

    period_p = doc.add_paragraph()
    period_p.paragraph_format.space_after = Pt(10)
    pr = period_p.add_run(period)
    pr.font.size = Pt(13)
    pr.font.color.rgb = COLOR_NEUTRAL
    pr.font.name = FONT_BODY

    # Discreet model footnote — small, grey, not competing with the period line.
    model_name = summary.get("generated_by_model", "")
    if model_name:
        model_p = doc.add_paragraph()
        model_p.paragraph_format.space_after = Pt(10)
        mr = model_p.add_run(f"Generated using {model_name}")
        mr.font.size = Pt(8.5)
        mr.font.color.rgb = COLOR_SUBTLE
        mr.font.name = FONT_BODY

    # --- 1. KPI bar ---
    kpi_columns = []
    for var, label in (("total_sessions", "Sessions"), ("BE_Entry_Rate", "BE Entry Rate"), ("ECVR_BE", "ECVR BE")):
        data = kpis.get(var, {})
        val_str = fmt_kpi_value(var, data.get("current"))
        sign, pct, color = fmt_yoy(data.get("yoy"))
        kpi_columns.append((label, val_str, sign, pct, color))
    add_kpi_bar(doc, kpi_columns)

    if summary.get("funnel_summary"):
        add_narrative(doc, summary["funnel_summary"])

    # --- 2. Autopsy ---
    add_heading(doc, "🩺  FUNNEL AUTOPSY", level=1)
    conclusion = summary.get("overall_conclusion", "")
    if conclusion:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(10)
        r = p.add_run(conclusion)
        r.font.size = Pt(11)
        r.font.name = FONT_BODY

    # --- 3-5: Device / Channel / BU Split ---
    add_device_section(doc, summary.get("device_section_global", {}))
    add_channel_section(doc, summary.get("channel_section_global", {}))
    add_bu_split_section(doc, summary.get("bu_section", {}), bu_kpis)

    # --- 6: BU Focus ---
    add_bu_focus_section(doc, summary.get("bu_focus", []))

    # --- 7-9: Crossovers / Resort / Other Signals ---
    add_crossover_section(doc, summary.get("crossover_section", {}), country_bu_lookup)
    add_resort_section(doc, summary.get("resort_section", {}))
    add_other_signals_section(doc, summary.get("other_signals_section", {}))

    # --- 10: Top Actions + Watch Points ---
    add_top_actions_and_watch_points(doc, summary.get("top_actions", []), summary.get("watch_points", []))

    # --- Legend + footer ---
    add_legend_and_footer(doc, summary)

    return doc


def main():
    if not INPUT_JSON.exists():
        print(f"ERROR: {INPUT_JSON} not found. Run compose.py first.", file=sys.stderr)
        sys.exit(1)

    print("Loading synthesis_output.json...")
    with open(INPUT_JSON, encoding="utf-8") as f:
        summary = json.load(f)

    kpis = {}
    bu_kpis = []
    country_bu_lookup = {}
    if ANALYSIS_INPUT.exists():
        with open(ANALYSIS_INPUT, encoding="utf-8") as f:
            analysis_data = json.load(f)
        kpis = extract_kpis(analysis_data)
        bu_kpis = extract_bu_kpis(analysis_data)
        country_bu_lookup = extract_country_bu_lookup(analysis_data)
    else:
        print("Warning: analysis_input.json not found — KPI bars will be empty.")

    print("Building Word document...")
    doc = build_report(summary, kpis, bu_kpis, country_bu_lookup)

    doc.save(OUTPUT_DOCX)
    print(f"Report saved to: {OUTPUT_DOCX}")


if __name__ == "__main__":
    main()
