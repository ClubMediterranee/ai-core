"""
ECVR BE Explicability Analysis — Step 4: Teams Message
Reads synthesis_output.json, builds FOUR Adaptive Card payloads, and posts them
as separate messages to a Microsoft Teams channel via Incoming Webhook.

Posted as 4 messages (not 1) because a single combined card exceeded the payload
size the Teams/Power Automate relay will actually deliver — a ~50KB single card,
a ~38KB two-way split, and later a ~28KB "Part 3/3" (once the country-grouped
CHANNEL × COUNTRY HIGHLIGHTS redesign added more content per country) all returned
HTTP 202 but never appeared in the channel. Splitting the old Part 3/3 further —
CHANNEL × COUNTRY HIGHLIGHTS + RESORT FOCUS in Part 3/4, OTHER KEY SIGNALS +
TOP 3 ACTIONS + WATCH POINTS in Part 4/4 — keeps each message safely small
without cutting any content.

Card order (top-down funnel, per the redesigned pipeline):
  Part 1/4:
    1. KPIs
    2. Autopsy (~5-sentence overall_conclusion)
    3. DEVICE — global view
    4. NEW CUSTOM CHANNEL GROUP — global view (concise)
    5. BU SPLIT — weight/change per Business Unit
  Part 2/4:
    6. BU FOCUS — per-BU top-3 countries, device, channel
  Part 3/4:
    7. CHANNEL × COUNTRY HIGHLIGHTS — each BU-focus country's top 2 channels by impact
    8. RESORT FOCUS — top 5 positive / top 5 negative
  Part 4/4:
    9. OTHER KEY SIGNALS — up to 16 items (model signals + channel signals)
   10. TOP 3 ACTIONS + Watch points — read last, as the call to action

Setup:
  In Teams: channel → ··· → Connectors → Incoming Webhook → create → copy URL
  Set that URL as TEAMS_WEBHOOK_URL below (or via env var TEAMS_WEBHOOK_URL)
"""

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
INPUT_JSON        = Path(os.environ.get("ECVR_DOWNLOADS_DIR", r"/mnt/c/Users/xxxxx/Downloads")) / "synthesis_output.json"
ANALYSIS_INPUT    = Path(os.environ.get("ECVR_DOWNLOADS_DIR", r"/mnt/c/Users/xxxxx/Downloads")) / "analysis_input.json"
# Hardcoded on purpose — this pipeline runs unattended on a schedule, so it
# can't depend on an env var being set in whatever environment triggers it.
# TEAMS_WEBHOOK_URL still overrides this if set (e.g. for pointing at a
# different channel without editing the script).
TEAMS_WEBHOOK_URL = os.environ.get(
    "TEAMS_WEBHOOK_URL",
    "https://defaulte0921cd58a3d4e51a56f176998dbcf.5c.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/00/workflows/d34c7970d5a442d39b9c08c07aea5ac4/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=l7kxLBoRUoUtv6gkGJRyKoPyy3MhyFWmqC27yr2na7A"
)

# Color palette for Adaptive Cards (Teams hex format)
COLOR_POSITIVE = "good"     # green
COLOR_NEGATIVE = "attention" # red
COLOR_NEUTRAL  = "accent"    # blue
COLOR_WARNING  = "warning"   # yellow


# ---------------------------------------------------------------------------
# Adaptive Card builders
# ---------------------------------------------------------------------------

def text_block(text: str, size="default", weight="default", color=None, wrap=True, subtle=False) -> dict:
    block = {"type": "TextBlock", "text": text, "wrap": wrap}
    if size != "default":
        block["size"] = size
    if weight != "default":
        block["weight"] = weight
    if color:
        block["color"] = color
    if subtle:
        block["isSubtle"] = True
    return block


def container(items: list, style=None) -> dict:
    c = {"type": "Container", "items": items}
    if style:
        c["style"] = style
    return c


def fact_set(facts: list) -> dict:
    return {"type": "FactSet", "facts": [{"title": k, "value": v} for k, v in facts]}


def toggle_container(title: str, items: list, icon: str = "▶", description: str = "") -> dict:
    """Collapsible section via Action.ShowCard — used for WATCH POINTS so a 6-item
    next-sprint list doesn't add to the single-scroll length of the main card."""
    body = []
    if description:
        body.append({"type": "TextBlock", "text": description, "isSubtle": True, "size": "Small", "wrap": True, "spacing": "None"})
    body.extend(items)
    return {
        "type": "ActionSet",
        "actions": [
            {
                "type": "Action.ShowCard",
                "title": f"{icon} {title}",
                "card": {
                    "type": "AdaptiveCard",
                    "body": body,
                },
            }
        ],
    }


def _forensics_path():
    return INPUT_JSON.parent / "forensics_output.json"


def extract_kpis(analysis_input: dict) -> dict:
    """Headline KPIs from GA4 (forensics_output.json), in the same shape the cards already read:
    {var: {current, prior, yoy}} for total_sessions, BE_Entry_Rate, ECVR_BE. Falls back to the
    explicability model's snapshot only if forensics_output.json is missing."""
    fp = _forensics_path()
    if fp.exists():
        k = json.load(open(fp, encoding="utf-8")).get("kpis") or {}
        if k:
            rel = lambda a: ((a[1] / a[0] - 1) if a and a[0] else None)
            return {
                "total_sessions": {"current": k["sessions"][1], "prior": k["sessions"][0], "yoy": rel(k["sessions"])},
                "BE_Entry_Rate": {"current": k["be_entry_rate"][1], "prior": k["be_entry_rate"][0], "yoy": rel(k["be_entry_rate"])},
                "ECVR_BE": {"current": k["ecvr"][1], "prior": k["ecvr"][0], "yoy": rel(k["ecvr"])},
            }
    kpis = {}
    for row in analysis_input.get("bucket_4_core_kpi_snapshot", []):
        if row.get("site") == "Global":
            var = row.get("variable")
            if var in ("total_sessions", "BE_Entry_Rate", "ECVR_BE"):
                kpis[var] = {"current": row.get("valeur"), "prior": row.get("valeur_prec"), "yoy": row.get("variation")}
    return kpis


def fmt_kpi_value(var: str, value) -> str:
    if value is None:
        return "N/A"
    if var == "total_sessions":
        return f"{int(value):,}"
    return f"{value:.2%}"


def fmt_yoy(variation) -> str:
    if variation is None:
        return "", "", "default"
    sign = "▲" if variation >= 0 else "▼"
    color_word = "good" if variation >= 0 else "attention"
    return sign, f"{abs(variation):.1%}", color_word


def kpi_column(label: str, value_str: str, yoy_sign: str, yoy_pct: str, yoy_color: str) -> dict:
    return {
        "type": "Column",
        "width": "stretch",
        "items": [
            {"type": "TextBlock", "text": label, "weight": "Bolder", "wrap": True, "horizontalAlignment": "Center"},
            {"type": "TextBlock", "text": value_str, "size": "Large", "weight": "Bolder", "horizontalAlignment": "Center", "wrap": True},
            {"type": "TextBlock", "text": f"{yoy_sign} {yoy_pct} vs N-1", "color": yoy_color, "size": "Small", "horizontalAlignment": "Center", "wrap": True},
        ],
    }


def extract_bu_kpis(analysis_input: dict) -> list:
    """Pull the BU-level breakdown (ECVR BE + its YoY evolution per Business Unit)
    from analysis_input.json's bu_breakdown — the BU-equivalent of extract_kpis'
    Global KPI row, used to render a KPI-bar-style column set for BUSINESS UNIT
    SPLIT, one column per BU, sorted by absolute weighted importance (already the
    sort order bu_breakdown is produced in by filter_results.py)."""
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
    top_countries_per_bu — the authoritative source for which BU a country
    belongs to. Used as a reliable fallback for crossover_section items, since
    the LLM-filled business_unit field there is occasionally left blank."""
    lookup = {}
    for bu, countries in analysis_input.get("top_countries_per_bu", {}).items():
        for c in countries:
            site = c.get("site")
            if site:
                lookup[site] = bu
    return lookup


def bu_kpi_column(bu_row: dict) -> dict:
    """Same visual shape as kpi_column (label / big value / YoY line) but for one
    Business Unit: label = BU code (with its session weight — poids, each BU's
    share of total SESSIONS — alongside it), big value = its own ECVR BE, YoY
    line = its ECVR BE evolution — so BU SPLIT reads exactly like the top KPI
    bar does for the global ECVR BE figure, just broken out by BU."""
    bu = bu_row.get("business_unit", "")
    ecvr_be = bu_row.get("ecvr_be")
    pct_change = bu_row.get("pct_change")
    poids = bu_row.get("poids")
    ecvr_be_str = f"{ecvr_be:.2%}" if ecvr_be is not None else "N/A"
    sign, pct, color = fmt_yoy(pct_change) if pct_change is not None else ("", "N/A", "default")
    label_text = f"{bu} ({poids:.1%} of sessions)" if poids is not None else bu
    return {
        "type": "Column",
        "width": "stretch",
        "items": [
            {"type": "TextBlock", "text": label_text, "weight": "Bolder", "size": "Small", "wrap": True, "horizontalAlignment": "Center"},
            {"type": "TextBlock", "text": ecvr_be_str, "size": "Large", "weight": "Bolder", "horizontalAlignment": "Center", "wrap": True},
            {"type": "TextBlock", "text": f"{sign} {pct} vs N-1", "color": color, "size": "Small", "horizontalAlignment": "Center", "wrap": True},
        ],
    }


def build_bu_kpi_bar(bu_kpis: list) -> dict | None:
    """A KPI-bar-style ColumnSet for Business Units — one column per BU showing its
    own ECVR BE and its YoY evolution, the same visual pattern as the Sessions/BE
    Entry Rate/ECVR BE bar at the top of the card."""
    if not bu_kpis:
        return None
    cols = [bu_kpi_column(row) for row in bu_kpis]
    return {
        "type": "ColumnSet",
        "columns": cols,
        "style": "emphasis",
        "bleed": True,
    }


# v2: market / BU reads are one long, deliberately complete line of figures. Cutting it mid-sentence with "…"
# drops figures, so item summaries are only shortened beyond this generous cap (still under the card size limit).
ITEM_SUMMARY_MAX = 700


def first_sentence(text: str, max_chars: int = 120) -> str:
    """Returns the first sentence, capped at max_chars. A sentence is only split at a real sentence end
    (". " followed by a capital letter), never inside a figure such as "0.0% to 27.3%"."""
    import re as _re
    m = _re.search(r"[.!?](?=\s+[A-Z])", text)
    if m and m.end() <= max_chars:
        return text[:m.end()]
    return text[:max_chars].rsplit(" ", 1)[0] + "…" if len(text) > max_chars else text


def expandable_item(header: str, site: str, summary: str, header_color: str) -> dict:
    items = []
    if header:
        header_text = f"{header} — {site}" if site else header
        items.append({"type": "TextBlock", "text": header_text, "weight": "Bolder", "color": header_color, "wrap": True})
    items.append({"type": "TextBlock", "text": summary, "wrap": True, "spacing": "Small"})
    return {"type": "Container", "style": "emphasis", "items": items, "spacing": "Small"}


def fmt_variation(variation) -> str:
    if variation is None:
        return "N/A"
    sign = "+" if variation >= 0 else ""
    return f"{sign}{variation:.1%}"


# Both flag types render as red (COLOR_NEGATIVE) — the card intentionally stays
# to a strict green/red palette (direction good/bad) with no orange/yellow
# "warning" color for flagged items; yellow is reserved for Watch Points only
# (see COLOR_WARNING's other use site), which are a different kind of marker.
FLAG_COLORS = {"🔧": COLOR_NEGATIVE, "🔍": COLOR_NEGATIVE, "⚑": COLOR_NEGATIVE}


def flag_block(flag: str) -> dict | None:
    if not flag:
        return None
    color = FLAG_COLORS.get(flag[:1], COLOR_NEGATIVE)
    return {"type": "TextBlock", "text": flag, "size": "Small", "weight": "Bolder", "color": color, "wrap": True, "spacing": "Small"}


def direction_color(direction: str) -> str:
    if direction == "positive":
        return COLOR_POSITIVE
    if direction == "negative":
        return COLOR_NEGATIVE
    return COLOR_NEUTRAL


def item_card(header_text: str, metric_line: str, summary: str, color: str, flag: str = "") -> dict:
    """Shared item-card shape — header, metric line, one-cause summary, optional
    data-quality/small-base flag. Same structure across every section so scanning
    rhythm doesn't break section to section.

    Header color is forced to red whenever a flag is present, overriding the
    direction-based good/attention color — a flagged item is by definition an
    unconfirmed/artifact reading. The card stays strictly green/red; no orange."""
    if flag:
        color = FLAG_COLORS.get(flag[:1], COLOR_NEGATIVE)
    short_summary = first_sentence(summary, max_chars=ITEM_SUMMARY_MAX)
    items = [
        {"type": "TextBlock", "text": header_text, "weight": "Bolder", "color": color, "wrap": True},
    ]
    if metric_line:
        items.append({"type": "TextBlock", "text": metric_line, "size": "Small", "isSubtle": True, "wrap": True, "spacing": "Small"})
    items.append({"type": "TextBlock", "text": short_summary, "wrap": True, "spacing": "Small"})
    fb = flag_block(flag)
    if fb:
        items.append(fb)
    return {"type": "Container", "style": "emphasis", "items": items, "spacing": "Small"}


def section_item_simple(label: str, site: str, summary: str, color: str, flag: str = "", metric_line: str = "", rank: int | None = None) -> dict:
    """Generic item card — header (+ optional site/rank), metric line, summary, flag.
    `rank` is a purely cosmetic prefix (e.g. "1.") — pass it only when the section's
    order is actually enforced by a stated criterion."""
    prefix = f"{rank}. " if rank is not None else ""
    header_text = f"**{prefix}{label}**" + (f"  —  {site}" if site else "")
    return item_card(header_text, metric_line, summary, color, flag)


def channel_group_item(group: str, summary: str, color: str, flag: str = "", metric_line: str = "") -> dict:
    """Item card for a real GA4 Custom Channel Group row (global channel section,
    BU-focus channel breakdown, crossover section). Header is always the real GA4
    group name — never an old channel_* variable name."""
    header_text = f"**{group}**"
    return item_card(header_text, metric_line, summary, color, flag)


def build_country_channel_block(country: str, business_unit: str, items: list) -> dict:
    """
    Groups a country's channel×country highlight items (already restricted to
    that one country by the caller) into ONE card: a country sub-header stating
    its net read (e.g. "2 channels hurting" / "1 helping, 1 hurting"), followed
    by one line per channel explicitly labelled ✅ Helping / ⚠️ Hurting — never a
    bare colored header with no verbal cue, which is what made this section hard
    to parse (a wall of red cards with an occasional unlabelled green one).
    Net-read color: green only if EVERY item for this country is positive, red
    otherwise (mixed or all-negative) — a country with one bright spot amid
    mostly bad news should still read as a country needing attention overall.

    v2: each row states WHAT drives its net effect ("via own conversion" / "via traffic share" /
    "via conversion and share") and carries its small-base / model-vs-GA4 flag, so a channel that
    "hurts" only through a share change on a thin base is visible as such."""
    positive_n = sum(1 for it in items if it.get("direction") == "positive")
    negative_n = len(items) - positive_n
    if negative_n == 0:
        net_color = COLOR_POSITIVE
    else:
        net_color = COLOR_NEGATIVE

    if positive_n and negative_n:
        net_label = f"{positive_n} helping, {negative_n} hurting"
    elif positive_n:
        net_label = f"{positive_n} channel{'s' if positive_n > 1 else ''} helping"
    else:
        net_label = f"{negative_n} channel{'s' if negative_n > 1 else ''} hurting"

    bu_tag = f" ({business_unit})" if business_unit else ""
    header = {
        "type": "TextBlock",
        "text": f"**{country}**{bu_tag} — {net_label}",
        "weight": "Bolder",
        "color": net_color,
        "wrap": True,
    }
    lines = [header]
    read = next((it.get("market_read") for it in items if it.get("market_read")), "")
    if read:
        lines.append({"type": "TextBlock", "text": read, "size": "Small", "wrap": True, "spacing": "Small"})
    for it in items:
        is_positive = it.get("direction") == "positive"
        drv = it.get("driver")
        via = f" via {drv}" if drv and drv != "negligible" else ""
        icon = ("✅ Helping" if is_positive else "⚠️ Hurting") + via
        color = COLOR_POSITIVE if is_positive else COLOR_NEGATIVE
        lines.append({
            "type": "TextBlock",
            "text": f"{icon} — **{it.get('group', '')}**: {it.get('metric_line', '')}",
            "size": "Small",
            "color": color,
            "wrap": True,
            "spacing": "Small",
        })
        if it.get("summary"):
            lines.append({
                "type": "TextBlock",
                "text": first_sentence(it["summary"], max_chars=200),
                "size": "Small",
                "isSubtle": True,
                "wrap": True,
                "spacing": "None",
            })
        fb = flag_block(it.get("flag", ""))
        if fb:
            lines.append(fb)
    return {"type": "Container", "style": "emphasis", "items": lines, "spacing": "Small"}


def fixed_color_item(label: str, summary: str, color: str, flag: str = "", metric_line: str = "") -> dict:
    """Like section_item_simple, but the header color is FIXED (by list
    membership — e.g. resort_section.positive vs .negative) and is NEVER
    overridden by a flag, unlike item_card's default behaviour. Use this
    wherever an item's color is already determined by which bucket it was
    placed in (a resort in the top-5-POSITIVE list is a positive item, full
    stop) — a small-base/data-quality flag still shows as a caveat note below
    the summary, it just doesn't flip the header to red. This avoids a red
    header appearing inside a section titled "Top performing" (item 8)."""
    short_summary = first_sentence(summary, max_chars=280)
    items = [
        {"type": "TextBlock", "text": f"**{label}**", "weight": "Bolder", "color": color, "wrap": True},
    ]
    if metric_line:
        items.append({"type": "TextBlock", "text": metric_line, "size": "Small", "isSubtle": True, "wrap": True, "spacing": "Small"})
    items.append({"type": "TextBlock", "text": short_summary, "wrap": True, "spacing": "Small"})
    fb = flag_block(flag)
    if fb:
        items.append(fb)
    return {"type": "Container", "style": "emphasis", "items": items, "spacing": "Small"}


def top_actions_section(actions: list) -> dict:
    """Renders the TOP ACTIONS list — no ownership tags, most urgent first. Placed
    right after the autopsy per the card redesign (surfaced early, not buried at
    the bottom alongside watch points)."""
    items = [
        {"type": "TextBlock", "text": "🎯 TOP 3 ACTIONS THIS MONTH", "weight": "Bolder", "size": "Medium", "wrap": True},
    ]
    for i, action in enumerate(actions[:3], 1):
        items.append({
            "type": "Container",
            "style": "emphasis",
            "spacing": "Small",
            "items": [{"type": "TextBlock", "text": f"**{i}.** {action}", "wrap": True}],
        })
    return {"type": "Container", "spacing": "Large", "items": items}


def build_section(icon: str, title: str, narrative: str, items: list, caption: str = "") -> dict:
    """Renders a named category section: header + optional rank-order caption +
    narrative paragraph + item cards."""
    body_items = [
        {"type": "TextBlock", "text": f"{icon} {title}", "weight": "Bolder", "size": "Medium", "wrap": True},
    ]
    if caption:
        body_items.append({
            "type": "TextBlock",
            "text": caption,
            "wrap": True,
            "isSubtle": True,
            "size": "Small",
            "spacing": "None",
        })
    if narrative:
        body_items.append({
            "type": "TextBlock",
            "text": narrative,
            "wrap": True,
            "isSubtle": True,
            "spacing": "Small",
        })
    body_items.extend(items)
    return {"type": "Container", "spacing": "Large", "items": body_items}


def build_bu_focus_block(bu_entry: dict) -> dict:
    """Renders one Business Unit's drill-down: narrative + top-3 countries +
    device summary + channel breakdown, nested under one BU sub-heading."""
    bu = bu_entry.get("business_unit", "")
    narrative = bu_entry.get("narrative", "")
    countries = bu_entry.get("top_countries", [])
    device = bu_entry.get("device", {})
    channel = bu_entry.get("channel", {})

    items = [
        {"type": "TextBlock", "text": f"── {bu} ──", "weight": "Bolder", "wrap": True, "spacing": "Medium"},
    ]
    if narrative:
        items.append({"type": "TextBlock", "text": narrative, "wrap": True, "isSubtle": True, "spacing": "Small"})

    for c in countries[:3]:
        items.append(section_item_simple(
            c.get("market", ""), "", c.get("summary", ""),
            direction_color(c.get("direction", "")),
            c.get("flag", ""), c.get("metric_line", ""),
        ))

    if device.get("metric_line") or device.get("summary"):
        items.append({
            "type": "Container", "style": "emphasis", "spacing": "Small",
            "items": [
                {"type": "TextBlock", "text": "📱 Device", "weight": "Bolder", "size": "Small", "wrap": True},
                {"type": "TextBlock", "text": device.get("metric_line", ""), "size": "Small", "isSubtle": True, "wrap": True, "spacing": "Small"},
                {"type": "TextBlock", "text": device.get("summary", ""), "wrap": True, "spacing": "Small"},
            ],
        })

    channel_items = channel.get("items", [])
    if channel_items or channel.get("summary"):
        facts = [{"title": r.get("group", "?"), "value": r.get("metric_line", "")} for r in channel_items[:4]]
        chan_body = [
            {"type": "TextBlock", "text": "📡 New Custom Channel Group", "weight": "Bolder", "size": "Small", "wrap": True},
        ]
        if facts:
            chan_body.append({"type": "FactSet", "facts": facts, "spacing": "Small"})
        if channel.get("summary"):
            chan_body.append({"type": "TextBlock", "text": channel["summary"], "wrap": True, "spacing": "Small"})
        items.append({"type": "Container", "style": "emphasis", "spacing": "Small", "items": chan_body})

    return {"type": "Container", "spacing": "Medium", "items": items}


def wrap_card(body: list) -> dict:
    """Wraps a body list into a postable Teams message envelope. Split into its own
    function because the card is now posted as THREE separate messages (see
    build_card_part1/part2/part3) — a single AdaptiveCard body containing every
    section (KPIs through watch points) exceeded ~50KB, past the practical size limit
    for a card nested this deeply with Action.ShowCard (BU FOCUS alone was ~18KB) —
    large payloads can be silently dropped by the Teams/Power Automate relay even
    when the initial HTTP call returns 202 (confirmed: a combined ~38KB "part 2"
    was accepted with 202 but never appeared in the channel). BU FOCUS gets its own
    message (part 2) since it's the single biggest section; everything else splits
    across part 1 and part 3 without cutting any content."""
    return {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "contentUrl": None,
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": body,
                    "msteams": {"width": "full"},
                },
            }
        ],
    }


def build_card_part1(summary: dict, kpis: dict, bu_kpis: list) -> dict:
    """Message 1/4: KPIs, Autopsy, DEVICE (global), NEW CUSTOM CHANNEL GROUP (global),
    BU SPLIT (with its own KPI-style weight/ECVR-BE bar) — the headline/summary
    portion of the analysis. Top 3 Actions moved to part 4, alongside Watch Points
    (both are action-oriented, read last)."""
    period = summary.get("analysis_period", "Monthly Analysis")
    conclusion = summary.get("overall_conclusion", "")
    device_global = summary.get("device_section_global", {})
    channel_global = summary.get("channel_section_global", {})
    bu_section = summary.get("bu_section", {})
    model_name = summary.get("generated_by_model", "")

    body = []

    # --- 1. Header + KPI bar ---
    header_items = [
        text_block("📊 ECVR BE Monthly Analysis", size="large", weight="bolder"),
        text_block(period, size="medium", color=COLOR_NEUTRAL),
    ]
    if model_name:
        # Discreet, small, grey — a footnote on which model ran this analysis,
        # not something that should compete with the period for attention.
        header_items.append(text_block(f"Generated using {model_name}", size="small", subtle=True))
    body.append(container(header_items, style="emphasis"))

    kpi_cols = []
    for var, label in (
        ("total_sessions", "Sessions"),
        ("BE_Entry_Rate",  "BE Entry Rate"),
        ("ECVR_BE",        "ECVR BE"),
    ):
        data = kpis.get(var, {})
        val_str = fmt_kpi_value(var, data.get("current"))
        yoy = data.get("yoy")
        sign, pct, color = fmt_yoy(yoy) if yoy is not None else ("", "N/A", "default")
        kpi_cols.append(kpi_column(label, val_str, sign, pct, color))

    if kpi_cols:
        body.append({
            "type": "ColumnSet",
            "columns": kpi_cols,
            "style": "emphasis",
            "bleed": True,
        })

    if summary.get("funnel_summary"):
        body.append(text_block(summary["funnel_summary"], wrap=True))

    # --- 2. Autopsy (~5 sentences) ---
    sentences = [s.strip() for s in conclusion.replace("\n", " ").split(". ") if s.strip()]
    sentences = [s if s.endswith(".") else s + "." for s in sentences]
    n = len(sentences)
    if n >= 3:
        para1 = sentences[0]
        para2 = " ".join(sentences[1:max(2, n - 1)])
        para3 = " ".join(sentences[max(2, n - 1):])
    elif n == 2:
        para1, para2, para3 = sentences[0], sentences[1], ""
    else:
        para1, para2, para3 = conclusion, "", ""

    autopsy_items = [
        {"type": "TextBlock", "text": "🩺 FUNNEL AUTOPSY", "weight": "Bolder", "size": "Medium", "wrap": True},
        {"type": "TextBlock", "text": para1, "wrap": True, "spacing": "Medium", "weight": "Bolder", "isSubtle": False},
    ]
    if para2:
        autopsy_items.append({"type": "TextBlock", "text": para2, "wrap": True, "spacing": "Medium"})
    if para3:
        autopsy_items.append({"type": "TextBlock", "text": para3, "wrap": True, "spacing": "Medium", "isSubtle": True})
    body.append({"type": "Container", "spacing": "Large", "items": autopsy_items})

    # --- 3. DEVICE — global view ---
    d_narrative = device_global.get("narrative", "")
    d_items = device_global.get("items", [])[:3]
    if d_narrative or d_items:
        section_items = [
            section_item_simple(
                item.get("label", ""), "", item.get("summary", ""),
                direction_color(item.get("direction", "")),
                item.get("flag", ""), item.get("metric_line", ""),
            )
            for item in d_items
        ]
        body.append(build_section("📱", "DEVICE — Global", d_narrative, section_items))

    # --- 4. NEW CUSTOM CHANNEL GROUP — global view (concise) ---
    ch_narrative = channel_global.get("narrative", "")
    # Up to 3 positive + 3 negative = 6 items max (see the synthesis_output.json schema) — [:5]
    # here previously silently dropped the 6th item off the end.
    ch_items = channel_global.get("items", [])[:6]
    if ch_narrative or ch_items:
        section_items = [
            channel_group_item(
                item.get("group", ""), item.get("summary", ""),
                direction_color(item.get("direction", "")),
                item.get("flag", ""), item.get("metric_line", ""),
            )
            for item in ch_items
        ]
        body.append(build_section("📡", "NEW CUSTOM CHANNEL GROUP — Global", ch_narrative, section_items))

    # --- 5. BU SPLIT — KPI-style weight/ECVR-BE bar, then per-BU cause items ---
    bu_narrative = bu_section.get("narrative", "")
    bu_items = bu_section.get("items", [])
    bu_kpi_bar = build_bu_kpi_bar(bu_kpis)
    if bu_narrative or bu_items or bu_kpi_bar:
        section_items = [
            section_item_simple(
                item.get("business_unit", ""), "", item.get("summary", ""),
                direction_color(item.get("direction", "")),
                item.get("flag", ""), item.get("metric_line", ""),
            )
            for item in bu_items
        ]
        header_block = {"type": "Container", "spacing": "Large", "items": [
            {"type": "TextBlock", "text": "🧭 BUSINESS UNIT SPLIT", "weight": "Bolder", "size": "Medium", "wrap": True},
        ]}
        body.append(header_block)
        if bu_kpi_bar:
            body.append(bu_kpi_bar)
        if bu_narrative:
            body.append({"type": "TextBlock", "text": bu_narrative, "wrap": True, "isSubtle": True, "spacing": "Small"})
        body.extend(section_items)

    body.append(text_block(
        "📨 Continued in the next message: BU Focus.",
        subtle=True, size="small"
    ))

    return wrap_card(body)


def build_card_part2(summary: dict, period: str) -> dict:
    """Message 2/3: BU FOCUS only — the single largest section (per-BU top-3
    countries + device + channel breakdown), isolated into its own message since
    combined with everything else it pushed part 2 past the size that Teams/Power
    Automate would actually deliver (confirmed: a ~38KB combined message returned
    202 but never appeared in the channel)."""
    bu_focus = summary.get("bu_focus", [])

    body = [
        container([
            text_block("📊 ECVR BE Monthly Analysis — Part 2/4", size="large", weight="bolder"),
            text_block(period, size="medium", color=COLOR_NEUTRAL),
        ], style="emphasis"),
    ]

    if bu_focus:
        focus_blocks = [build_bu_focus_block(bu) for bu in bu_focus]
        body.append({
            "type": "Container", "spacing": "Large",
            "items": [
                {"type": "TextBlock", "text": "🔎 BUSINESS UNIT FOCUS", "weight": "Bolder", "size": "Medium", "wrap": True},
                {"type": "TextBlock", "text": "Top 3 countries, device and New Custom Channel Group breakdown, per Business Unit.",
                 "wrap": True, "isSubtle": True, "size": "Small", "spacing": "None"},
            ] + focus_blocks,
        })

    body.append(text_block(
        "📨 Continued in the next message: Channel × Country Crossovers, Resort Focus, Other Key Signals, Top 3 Actions, Watch Points.",
        subtle=True, size="small"
    ))

    return wrap_card(body)


def build_card_part3(summary: dict, period: str, country_bu_lookup: dict | None = None) -> dict:
    """Message 3/4: CHANNEL × COUNTRY HIGHLIGHTS, RESORT FOCUS. Split off from
    what used to be a single "Part 3/3" (with Other Key Signals + Top Actions +
    Watch Points also crammed in) because that combined message grew to ~28KB
    as the country-grouped crossover redesign added more content per country —
    confirmed to return HTTP 202 but never actually appear in the Teams channel
    (the exact silent-drop failure mode seen before with oversized payloads).
    Now 4 parts total, each comfortably smaller.

    country_bu_lookup ({country: BU}, from analysis_input.json's
    top_countries_per_bu) backstops crossover_section's LLM-filled
    business_unit field, which is occasionally left blank — never show an
    empty "()" in the country header."""
    country_bu_lookup = country_bu_lookup or {}
    crossover = summary.get("crossover_section", {})
    resort = summary.get("resort_section", {})

    body = [
        container([
            text_block("📊 ECVR BE Monthly Analysis — Part 3/4", size="large", weight="bolder"),
            text_block(period, size="medium", color=COLOR_NEUTRAL),
        ], style="emphasis"),
    ]

    # --- CHANNEL × COUNTRY HIGHLIGHTS ---
    # Grouped by COUNTRY (one card per market, both its channels named as
    # "Helping"/"Hurting" inside it) rather than 26 flat item cards with no
    # grouping — the flat layout read as a wall of red with occasional
    # unlabelled green, since most countries here have 2 negative channels and
    # only a few have any positive one. Shows every BU-focus country (this
    # section is always the SAME country roster as bu_focus's top-3-per-BU —
    # never a re-selected or filtered subset) — a prior all-negative-first
    # urgency sort combined with a hard [:8] cap had the side effect of
    # silently dropping every country with any positive channel this month
    # (confirmed: all 5 mixed/all-positive countries — South Africa, Israël,
    # Italy, Brazil, Australia — fell after the cutoff). Verified the full
    # 13-country payload stays at ~24KB, comfortably under the ~28KB failure
    # threshold, so the cap is no longer needed. Still sorted by urgency
    # (all-negative countries first) so the most concerning markets read
    # first, just without truncating anyone off the bottom.
    x_narrative = crossover.get("narrative", "")
    x_items_all = crossover.get("items", [])
    countries_ordered = []
    seen = set()
    for it in x_items_all:
        c = it.get("country", "")
        if c not in seen:
            seen.add(c)
            countries_ordered.append(c)
    by_country = {c: [it for it in x_items_all if it.get("country") == c] for c in countries_ordered}
    # synthesis_output.json's crossover items don't carry a numeric impact_score
    # (that's deepdive-internal only) — rank by how many of a country's channels
    # are hurting it (all-negative countries are the most urgent), tie-broken by
    # whether any item carries a data-quality/small-base flag (still material,
    # just caveated) ahead of ones with none.
    def _country_urgency(c: str) -> tuple:
        items = by_country[c]
        negative_n = sum(1 for it in items if it.get("direction") != "positive")
        flagged_n = sum(1 for it in items if it.get("flag"))
        return (-negative_n, -flagged_n)
    countries_ranked = sorted(countries_ordered, key=_country_urgency)
    if x_narrative or countries_ranked:
        section_items = [
            build_country_channel_block(
                c,
                by_country[c][0].get("business_unit") or country_bu_lookup.get(c, ""),
                by_country[c],
            )
            for c in countries_ranked
        ]
        body.append(build_section("🔀", "CHANNEL × COUNTRY HIGHLIGHTS", x_narrative, section_items))

    # Resort Focus has its own message (Part 3b) so this one stays under the size the Teams relay delivers.
    body.append(text_block(
        "Continued in Part 4/4: Resort Focus, Other Key Signals, Top 3 Actions, Watch Points.",
        subtle=True, size="small"
    ))

    return wrap_card(body)


def build_card_part4(summary: dict, period: str) -> dict:
    """Message 4/4: OTHER KEY SIGNALS, TOP 3 ACTIONS, WATCH POINTS — the final,
    most action-oriented part of the analysis. Split out from the old "Part
    3/3" (see build_card_part3's docstring) to keep every message safely under
    the payload size that the Teams/Power Automate relay will actually deliver.
    Note: this function does not accept country_bu_lookup — it has no
    country-grouped content of its own (that lives in Part 3/4)."""
    other = summary.get("other_signals_section", {})
    resort = summary.get("resort_section", {})
    top_actions = summary.get("top_actions", [])
    watch_points = summary.get("watch_points", [])[:10]

    body = [
        container([
            text_block("📊 ECVR BE Monthly Analysis — Part 4/4", size="large", weight="bolder"),
            text_block(period, size="medium", color=COLOR_NEUTRAL),
        ], style="emphasis"),
    ]

    # --- RESORT FOCUS — top 5 positive / top 5 negative ---
    # Color is FIXED by list membership (fixed_color_item) — a flag never flips a
    # positive-list item to red or vice versa (item 8 fix); it only adds a caveat.
    r_pos = resort.get("positive", {})
    r_neg = resort.get("negative", {})
    r_pos_items = r_pos.get("items", [])[:5]
    r_neg_items = r_neg.get("items", [])[:5]
    if r_pos_items or r_neg_items or r_pos.get("narrative") or r_neg.get("narrative"):
        resort_body = [
            {"type": "TextBlock", "text": "🏖️ RESORT FOCUS", "weight": "Bolder", "size": "Medium", "wrap": True},
        ]
        if r_pos.get("narrative"):
            resort_body.append({"type": "TextBlock", "text": "Model credits these positively: " + r_pos["narrative"], "wrap": True, "isSubtle": True, "spacing": "Small"})
        for item in r_pos_items:
            resort_body.append(fixed_color_item(
                item.get("variable", ""), item.get("summary", ""),
                COLOR_POSITIVE, item.get("flag", ""), item.get("metric_line", ""),
            ))
        if r_neg.get("narrative"):
            resort_body.append({"type": "TextBlock", "text": "Model credits these negatively: " + r_neg["narrative"], "wrap": True, "isSubtle": True, "spacing": "Medium"})
        for item in r_neg_items:
            resort_body.append(fixed_color_item(
                item.get("variable", ""), item.get("summary", ""),
                COLOR_NEGATIVE, item.get("flag", ""), item.get("metric_line", ""),
            ))
        body.append({"type": "Container", "spacing": "Large", "items": resort_body})


    # --- OTHER KEY SIGNALS — up to 16 items ---
    # Every header stays grey regardless of direction OR flag — using
    # fixed_color_item (not section_item_simple) so a flag never overrides the
    # header to red. The flag itself already renders as its own red line below
    # the summary (flag_block) — having the header ALSO turn red on top of
    # that, with everything else in this mixed-direction grab-bag section
    # randomly blue, was too much visual noise for what's meant to be a calm,
    # uniform list.
    o_narrative = other.get("narrative", "")
    o_items = other.get("items", [])[:16]
    if o_narrative or o_items:
        section_items = [
            fixed_color_item(
                (f"{item.get('theme', '')} ({item.get('variable', '')})" if item.get("variable") else item.get("theme", ""))
                + (f"  —  {item.get('site', '')}" if item.get("site") else ""),
                item.get("summary", ""),
                # "default" (not COLOR_NEUTRAL/"accent") — Adaptive Cards renders
                # "accent" as blue, which read as a color-coded signal even
                # though it isn't one here. "default" is the card's ordinary
                # body-text color (dark grey/black depending on theme), with no
                # blue tint — truly neutral for this section specifically.
                "default",
                item.get("flag", ""), item.get("metric_line", ""),
            )
            for item in o_items
        ]
        body.append(build_section("🧩", "OTHER KEY SIGNALS", o_narrative, section_items))

    # --- TOP 3 ACTIONS + WATCH POINTS — read last, together, as the call to action ---
    if top_actions:
        body.append(top_actions_section(top_actions))

    if watch_points:
        watch_items = [
            expandable_item("⚠️ Watch point", "", wp, COLOR_WARNING)
            for wp in watch_points
        ]
        body.append(toggle_container("WATCH POINTS", watch_items, icon="⚠️",
            description="Actionable flags for the next sprint — data quality issues, anomalies to investigate, or risks that could distort future analyses."))

    # --- Flags used anywhere in this message, collected dynamically ---
    all_flags = []
    for item in (list(r_pos.get("items", [])[:5]) + list(r_neg.get("items", [])[:5]) + list(other.get("items", []))):
        f = item.get("flag", "")
        if f:
            prefix = f[:1]
            if prefix not in all_flags:
                all_flags.append(prefix)

    legend_text = {
        "🔧": "🔧 Data quality = probable tracking/tagging fault, not a genuine business signal until validated.",
        "🔍": "🔍 Small base = % built on very few booking confirmations (or a near-zero prior base), directional read only.",
        "⚑": "⚑ Model vs GA4 = the explicability model and GA4 disagree on direction or size; the figure shown is GA4.",
    }

    # --- Footer ---
    if all_flags:
        color_note = "Header color shows YoY direction (green = up, red = down); it is switched to the flag's own color whenever a flag is present."
        body.append(text_block(
            " ".join(legend_text[f] for f in all_flags if f in legend_text) + " " + color_note,
            subtle=True, size="small"
        ))
    body.append(text_block(
        "Generated automatically · Club Med Digital Analytics · "
        "Channel figures use GA4's New Custom Channel Group exclusively. "
        "Figures are live GA4 (ECVR-forensics v2); the explicability model only proposes what to look at, and where it disagrees with GA4 the item is flagged ⚑. GA4 can differ slightly due to late-arriving sessions (~72h processing window). Low-volume markets should be treated as approximate.",
        subtle=True, size="small"
    ))

    return wrap_card(body)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if "--dry-run" not in sys.argv and TEAMS_WEBHOOK_URL == "REPLACE_WITH_YOUR_WEBHOOK_URL":
        print("ERROR: Set TEAMS_WEBHOOK_URL in the script or as an environment variable.", file=sys.stderr)
        sys.exit(1)

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
        print("Warning: analysis_input.json not found — KPI bar will be empty.")

    period = summary.get("analysis_period", "Monthly Analysis")

    print("Building Adaptive Cards (4 parts — kept under the Teams payload size limit)...")
    card1 = build_card_part1(summary, kpis, bu_kpis)
    card2 = build_card_part2(summary, period)
    card3 = build_card_part3(summary, period, country_bu_lookup)
    card4 = build_card_part4(summary, period)

    # Save card payloads for inspection/debugging
    parts = [
        ("part1", card1, "Part 1/4 (KPIs, Autopsy, Device, Channel, BU Split + BU KPI bar)"),
        ("part2", card2, "Part 2/4 (BU Focus)"),
        ("part3", card3, "Part 3/4 (Crossovers)"),
        ("part4", card4, "Part 4/4 (Resort Focus, Other Key Signals, Top Actions, Watch Points)"),
    ]
    for name, card, _ in parts:
        path = INPUT_JSON.parent / f"teams_card_payload_{name}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(card, f, indent=2, ensure_ascii=False)
        print(f"Card payload saved to: {path}")

    def post(card: dict, label: str):
        size_kb = len(json.dumps(card).encode("utf-8")) / 1024
        if "--dry-run" in sys.argv:
            # Same behaviour as v1 (posts automatically, user decision 2026-10-15); --dry-run only builds and saves the cards.
            print(f"[DRY RUN] {label} built ({size_kb:.1f} KB) — NOT posted.")
            return
        print(f"Posting {label} to Teams ({size_kb:.1f} KB)...")
        payload = json.dumps(card).encode("utf-8")
        req = urllib.request.Request(
            TEAMS_WEBHOOK_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                body = resp.read().decode("utf-8")
                print(f"  Teams response: {resp.status} — {body}")
        except urllib.error.HTTPError as e:
            print(f"ERROR posting {label} to Teams: {e.code} — {e.read().decode('utf-8')}", file=sys.stderr)
            sys.exit(1)

    # POST_GAP_S is deliberately generous: the webhook is a Power Automate HTTP
    # trigger, not a direct Teams webhook — its underlying flow processes runs
    # sequentially, and firing the next trigger before a run has actually finished
    # posting to Teams can cause that run to be silently dropped (confirmed:
    # 3 posts fired ~2s apart all returned 202, but the first message never
    # appeared in the channel). Wait for each flow run to fully complete before
    # firing the next.
    POST_GAP_S = 15
    publishing = "--dry-run" not in sys.argv
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
    to_post = [(n, c, l) for n, c, l in parts if only is None or n in only]
    for i, (_, card, label) in enumerate(to_post):
        post(card, label)
        if publishing and i < len(to_post) - 1:
            print(f"  Waiting {POST_GAP_S}s before the next post (let the Power Automate flow finish this run)...")
            time.sleep(POST_GAP_S)

    if publishing:
        print("Done — all 4 messages posted to Teams. Please confirm in the channel that all 4 actually appeared, "
              "in order (a 202 response only confirms the trigger fired, not that the flow finished posting to Teams).")
    else:
        print("Dry run complete — 4 card payloads saved locally, nothing was posted.")


if __name__ == "__main__":
    main()
