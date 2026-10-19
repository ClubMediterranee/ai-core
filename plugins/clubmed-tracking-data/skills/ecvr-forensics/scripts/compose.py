"""
ECVR-forensics v2 — Step B: compose synthesis_output.json from forensics_output.json.

Same JSON shape the v1 renderers (teams_message.py / word_report.py) already read, so cards and
the Word report are unchanged. The difference is WHO writes what:

  * CODE writes every number, direction, metric line, flag, ranking and per-item sentence, all
    computed from forensics_output.json (GA4) + analysis_input.json (the model's leads).
  * The LLM only words the narrative layer (conclusion, section narratives, 3 actions, watch
    points) from a fact sheet. Each text it returns is CHECKED IN CODE: every number it contains
    must exist in the fact sheet, and it may not state a cause nothing measures. A text that
    fails the check is replaced by a deterministic sentence built from the same facts — so a
    wrong figure can never reach a card.
  * Model-vs-GA4 discrepancies are simply FLAGGED (⚑) on the item they concern. No other
    arbitration.

Nothing here names a market, channel, resort or month.
"""
import json
import os
import re
import sys
from pathlib import Path

import anthropic

import claims as CL

DOWNLOADS = Path(os.environ.get("ECVR_DOWNLOADS_DIR", r"/mnt/c/Users/xxxxx/Downloads"))
FORENSICS = DOWNLOADS / "forensics_output.json"
ANALYSIS = DOWNLOADS / "analysis_input.json"
OUTPUT = DOWNLOADS / "synthesis_output.json"

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-6-swc-gmdt"
# Low sampling temperature on EVERY model call in v2: the wording should stay close to the cited claims,
# not wander. Retries use the same value (they are corrections, not new drafts).
TEMPERATURE = 0.2

# Structural parameters (not tied to any month)
CHANNELS_PER_SIDE = 3        # global / BU channel rows per direction
CROSS_PER_MARKET = 2         # channel rows per BU-focus market
OTHER_PER_KIND = 5           # other-signal rows per kind (model variables / channel leads)
NEGLIGIBLE_BP = 0.05         # |bp| under this is "roughly unchanged"
MIN_CONFIRMATIONS = 50       # small-base threshold (matches forensics.py)
SURGE_MIN = 1.0              # +100% views counts as a surge in the resort narrative

PAIRING = re.compile(r"offset|counterweight|counterbalanc|counter(?:ed|ing|s|acted|acting)\b|balanc(?:ed|ing) (?:by|out)|cushion|compensat|partial(?:ly)? (?:mix )?(?:gain|offset)|"
                     r"in exchange|at the expense of|replac|swap|"
                     r"reallocat|cannibali[sz]|instead of", re.I)

UNMEASURED_CAUSES = re.compile(
    r"utm|tagging|tracking (?:fault|break|gap)|misattribut|stripping|crm|returning visitors?|"
    r"classif|attribution|engagement quality|intent|landing[- ]page (?:quality|relevance)", re.I)


# ------------------------------------------------------------------ formatting helpers
def f2(x):
    """Signed 2-decimal figure that never prints a negative zero ("-0.00")."""
    t = f"{x:+.2f}"
    return "+0.00" if t == "-0.00" else t


def pct(x, d=1, sign=True):
    if x is None:
        return "N/A"
    t = f"{x:+.{d}f}%" if sign else f"{x:.{d}f}%"
    return t.replace("-0.0%", "+0.0%") if t in ("-0.0%", "-0%") else t


def rate(e):
    return "N/A" if e is None else f"{e * 100:.2f}%"


def yoy_of(e0, e1):
    return None if not e0 else (e1 / e0 - 1) * 100


def thin_flag(conf):
    return f"🔍 Small base — {conf[0]:,.0f} vs {conf[1]:,.0f} confirmations" if min(conf) < MIN_CONFIRMATIONS else ""


def comp_metric_line(c, scope_sessions=None):
    """'Session Weight X% · ECVR BE Y% · Z.Z% YoY' from a decomposition component."""
    return (f"Session Weight {c['share'][1] * 100:.1f}% · ECVR BE {rate(c['ecvr'][1])} · "
            f"{pct(yoy_of(c['ecvr'][0], c['ecvr'][1]))} YoY")


SHARE_STEADY_PTS = 0.01      # a traffic-share change under 1 point reads as "steady"


def comp_sentence(c, label=None):
    """One deterministic sentence from a component's own mix/rate numbers. 'Steady' describes the
    SHARE (under SHARE_STEADY_PTS of movement), never a small mix effect."""
    r, m = c["rate_bp"], c["mix_bp"]
    sh0, sh1 = c["share"]
    below_avg = abs(m) >= NEGLIGIBLE_BP and ((m > 0) != (sh1 > sh0))   # share and mix move opposite ways
    if abs(r) < NEGLIGIBLE_BP:
        own = "its own conversion is roughly unchanged"
    else:
        own = f"its own conversion {'fell' if r < 0 else 'rose'} ({f2(r)} bp)"
    if abs(sh1 - sh0) < SHARE_STEADY_PTS:
        share = f"traffic share is steady ({sh0:.1%} to {sh1:.1%})"
    elif abs(m) < NEGLIGIBLE_BP:
        share = (f"traffic share {'rose' if sh1 > sh0 else 'fell'} from {sh0:.1%} to {sh1:.1%} "
                 f"(negligible effect on the blended rate, {f2(m)} bp mix)")
    else:
        share = (f"traffic share {'rose' if sh1 > sh0 else 'fell'} from {sh0:.1%} to {sh1:.1%}, "
                 f"which {'raised' if m > 0 else 'lowered'} the blended rate by {abs(m):.2f} bp"
                 + (" because it converts below the scope average" if below_avg else ""))
    return f"{own[0].upper() + own[1:]}; {share}."


def _mech(c):
    """One channel/device effect in plain words from its own rate/mix figures (what moved and how, never why)."""
    r, m = c["rate_bp"], c["mix_bp"]
    sh0, sh1 = c["share"]
    bits = []
    if abs(m) >= NEGLIGIBLE_BP and abs(sh1 - sh0) >= SHARE_STEADY_PTS:
        bits.append(f"its traffic share {'rose' if sh1 > sh0 else 'fell'} from {sh0:.1%} to {sh1:.1%} (mix {f2(m)} bp)")
    if abs(r) >= NEGLIGIBLE_BP:
        bits.append(f"its own conversion {'rose' if r > 0 else 'fell'} (rate {f2(r)} bp)")
    return " and ".join(bits) if bits else "it was roughly unchanged"


def scope_prose(s, n_channels=2):
    """Deterministic two-sentence reading of a BU / market from its own decomposition. Same facts as the
    model-written sentence, used when that sentence is rejected."""
    t = s["totals"]
    chans = sorted(s["by_channel"], key=lambda c: -abs(c["total_bp"]))[:n_channels]
    devs = [d for d in sorted(s["by_device"], key=lambda c: -abs(c["total_bp"])) if d["group"] != "other devices"][:2]
    verb = "fell" if t["delta_bp"] < 0 else "rose"
    first = f"{s['scope']}'s ECVR {verb} {abs(t['delta_bp']):.2f} bp"
    if chans:
        first += ", with " + "; ".join(f"{c['group']} {'lowering' if c['total_bp'] < 0 else 'raising'} it by {abs(c['total_bp']):.2f} bp ({_mech(c)})"
                                      for c in chans)
    first += "."
    if min(t["confirmations"]) < MIN_CONFIRMATIONS:
        first += f" The base is thin ({t['confirmations'][0]:,.0f} vs {t['confirmations'][1]:,.0f} confirmations)."
    second = (" On devices, " + "; ".join(f"{d['group']} {'lost' if d['total_bp'] < 0 else 'gained'} {abs(d['total_bp']):.2f} bp ({_mech(d)})"
                                          for d in devs) + ".") if devs else ""
    return first + second


def direction_of(bp):
    return "positive" if bp > 0 else "negative"


# ------------------------------------------------------------------ section builders
def top_by_sign(components, n=CHANNELS_PER_SIDE):
    pos = sorted([c for c in components if c["total_bp"] > 0], key=lambda c: -c["total_bp"])[:n]
    neg = sorted([c for c in components if c["total_bp"] < 0], key=lambda c: c["total_bp"])[:n]
    return pos, neg


def channel_items(components, with_summary=True):
    pos, neg = top_by_sign(components)
    items = []
    for c in sorted(pos, key=lambda c: -c["share"][1]) + sorted(neg, key=lambda c: -c["share"][1]):
        it = {"group": c["group"], "direction": direction_of(c["total_bp"]),
              "metric_line": comp_metric_line(c), "flag": thin_flag(c["confirmations"])}
        if with_summary:
            it["summary"] = ISENT.get(f"chan:global:{c['group']}") or comp_sentence(c)
        items.append(it)
    return items


def property_wide_items(fx, ai):
    """One global-channel line per property-wide recurring model variable (see claims.property_wide): the GA4
    global figures of that channel group, how many markets the model flags it in, and what GA4 says in each.
    Added to the global channel section even when the channel is outside the top-3-per-direction by bp, because
    a pattern the model flags in many markets is worth stating once at global level."""
    items = []
    for pw in CL.property_wide(fx, ai):
        c = pw["comp"]
        s_yoy = yoy_of(*c["sessions"])
        parts = [f"GA4 globally: sessions {c['sessions'][0]:,.0f} to {c['sessions'][1]:,.0f} ({pct(s_yoy)}), BE confirmations "
                 f"{c['confirmations'][0]:,.0f} to {c['confirmations'][1]:,.0f}; effect on global ECVR {f2(c['total_bp'])} bp "
                 f"(rate {f2(c['rate_bp'])} bp, mix {f2(c['mix_bp'])} bp)."]
        parts.append(f"The model flags this channel in {pw['listing']} markets, {len(pw['similar'])} of which move like the global "
                     f"figure ({pct(pw['global_variation'] * 100)})" + (f"; outliers: {', '.join(pw['outliers'])}" if pw["outliers"] else "") + ".")
        checkable = len(pw["confirmed"]) + len(pw["negligible"]) + len(pw["contradict"])
        if checkable:
            parts.append(f"GA4 confirms the model's direction in {len(pw['confirmed'])} of {checkable} checkable markets"
                         + (f" ({', '.join(m for m, _ in pw['confirmed'])})" if pw["confirmed"] else "")
                         + (f", is negligible in {', '.join(pw['negligible'])}" if pw["negligible"] else "")
                         + (f" and contradicts it in {', '.join(m for m, _ in pw['contradict'])}" if pw["contradict"] else "") + ".")
        items.append({"group": f"{pw['group']} (flagged by the model in {pw['listing']} markets)",
                      "direction": direction_of(c["total_bp"]), "metric_line": comp_metric_line(c),
                      "summary": " ".join(parts), "flag": thin_flag(c["confirmations"])})
    return items


def device_items(by_device):
    items = []
    for label in ("mobile", "desktop"):
        c = next((x for x in by_device if x["group"] == label), None)
        if not c:
            continue
        items.append({"label": label.capitalize(), "direction": direction_of(c["total_bp"]),
                      "metric_line": comp_metric_line(c), "summary": ISENT.get(f"dev:global:{label}") or comp_sentence(c),
                      "flag": thin_flag(c["confirmations"])})
    return items


def scope_flags(scope):
    fl = []
    for f in scope.get("flags", []):
        if f.startswith("DIRECTION") or f.startswith("SIZE"):
            fl.append("⚑ Model vs GA4 — " + f.split(": ", 1)[1])
        elif f.startswith("THIN BASE"):
            fl.append(thin_flag(scope["totals"]["confirmations"]))
    return fl[0] if fl else ""


def bu_items(fx, model_by_bu, msent=None):
    msent = msent or {}
    items = []
    for s in fx["scopes"]:
        if s["level"] != "bu" or "totals" not in s:
            continue
        t = s["totals"]
        items.append({
            "business_unit": s["scope"], "direction": direction_of(t["delta_bp"]),
            "metric_line": f"ECVR BE {rate(t['ecvr'][1])} · {pct(t['ecvr_yoy_pct'])} YoY",
            "summary": ISENT.get(f"buspl:{s['scope']}") or msent.get(s["scope"]) or bu_sentence(s), "flag": scope_flags(s)})
    return items


def bu_sentence(s):
    return scope_prose(s)


def country_items(scopes_by_name, markets, bu_sessions, msent=None):
    msent = msent or {}
    items = []
    for m in markets:
        s = scopes_by_name.get(m["site"])
        if not s or "totals" not in s:
            continue
        t = s["totals"]
        weight = t["sessions"][1] / bu_sessions if bu_sessions else None
        top = sorted(s["by_channel"], key=lambda c: -abs(c["total_bp"]))[:1]
        dv = sorted(s["by_device"], key=lambda c: -abs(c["total_bp"]))[:1]
        sent = f"{f2(t['delta_bp'])} bp in total"
        if top:
            sent += f"; largest channel effect: {top[0]['group']} ({f2(top[0]['total_bp'])} bp)"
        if dv:
            sent += f"; largest device effect: {dv[0]['group']} ({f2(dv[0]['total_bp'])} bp)"
        items.append({
            "market": m["site"], "direction": direction_of(t["delta_bp"]),
            "metric_line": f"Session Weight {weight * 100:.1f}% · ECVR BE {rate(t['ecvr'][1])} · {pct(t['ecvr_yoy_pct'])} YoY"
                           if weight is not None else f"ECVR BE {rate(t['ecvr'][1])} · {pct(t['ecvr_yoy_pct'])} YoY",
            "summary": ISENT.get(f"mkt:{m['site']}") or msent.get(m["site"]) or scope_prose(s), "flag": scope_flags(s)})
    return items


def bu_focus(fx, ai, msent=None):
    msent = msent or {}
    scopes = {s["scope"]: s for s in fx["scopes"] if "totals" in s}
    out = []
    for s in fx["scopes"]:
        if s["level"] != "bu" or "totals" not in s:
            continue
        bu = s["scope"]
        markets = ai.get("top_countries_per_bu", {}).get(bu, [])
        dv = s["by_device"]
        dl = []
        for label in ("mobile", "desktop"):
            c = next((x for x in dv if x["group"] == label), None)
            if c:
                dl.append(f"{label.capitalize()}: {comp_metric_line(c)}")
        ch = channel_items(s["by_channel"], with_summary=False)
        pos, neg = top_by_sign(s["by_channel"])
        out.append({
            "business_unit": bu, "narrative": ISENT.get(f"bunar:{bu}") or msent.get(bu) or bu_sentence(s),
            "top_countries": country_items(scopes, markets, s["totals"]["sessions"][1], msent),
            "device": {"metric_line": " · ".join(dl),
                       "summary": ISENT.get(f"budev:{bu}") or " ".join(f"{x['group'].capitalize()} {f2(x['total_bp'])} bp (rate {f2(x['rate_bp'])} bp, mix {f2(x['mix_bp'])} bp)."
                                           for x in dv if x["group"] != "other devices")},
            "channel": {"items": [{"group": i["group"], "metric_line": i["metric_line"]} for i in ch],
                        "summary": ISENT.get(f"buchan:{bu}") or "; ".join(f"{c['group']} {f2(c['total_bp'])} bp" for c in sorted(neg + pos, key=lambda c: -abs(c["total_bp"]))[:3]) + "."}})
    return out


def driver_label(c):
    """What the item's net effect comes from: 'rate' (its own conversion), 'mix' (its traffic share)
    or 'both' — used for crossover headers instead of a bare helping/hurting."""
    r, m = abs(c["rate_bp"]), abs(c["mix_bp"])
    if r < NEGLIGIBLE_BP and m < NEGLIGIBLE_BP:
        return "negligible"
    if r >= 2 * m:
        return "own conversion"
    if m >= 2 * r:
        return "traffic share"
    return "conversion and share"


def crossover_items(fx, ai, msent=None):
    msent = msent or {}
    scopes = {s["scope"]: s for s in fx["scopes"] if "totals" in s}
    items = []
    for bu, markets in ai.get("top_countries_per_bu", {}).items():
        for m in markets:
            s = scopes.get(m["site"])
            if not s:
                continue
            for k, c in enumerate(sorted(s["by_channel"], key=lambda c: -abs(c["total_bp"]))[:CROSS_PER_MARKET]):
                items.append({"country": m["site"], "business_unit": bu, "group": c["group"],
                              "driver": driver_label(c),
                              "direction": direction_of(c["total_bp"]),
                              "metric_line": comp_metric_line(c), "summary": ISENT.get(f"cross:{m['site']}:{c['group']}") or comp_sentence(c),
                              "flag": thin_flag(c["confirmations"])})
    return items


def resort_block(fx, ai):
    ga4 = {r["variable"]: r for r in fx.get("resort_checks", [])}

    def item(r):
        g = ga4.get(r["variable"], {})
        v, c = g.get("views", [0, 0]), g.get("confirmations", [0, 0])
        code = r["variable"][len("resort_view_"):]
        sent = ISENT.get(f"resort:{code}") or (f"Views {v[0]:,} to {v[1]:,} ({pct(g.get('ga4_views_yoy_pct'), 0)}) and BE confirmations "
                                               f"{c[0]:,} to {c[1]:,}.")
        flag = ""
        if g.get("status") == "DISCREPANCY":
            flag = (f"⚑ Model vs GA4 — views model {pct(g['model_views_yoy_pct'], 0)}, GA4 {pct(g['ga4_views_yoy_pct'], 0)}")
        elif min(c) < MIN_CONFIRMATIONS:
            flag = thin_flag(c)
        yo = g.get("ga4_views_yoy_pct")
        return {"variable": r["variable"],
                "metric_line": f"{pct(yo if yo is not None else (r.get('variation') or 0) * 100, 1)} YoY · Impact {r['absolute_weighted_importance'] * 100:.2f}% of global ECVR BE change",
                "summary": sent, "flag": flag}

    def narrative(rows):
        recs = [(r, ga4.get(r["variable"], {})) for r in rows]
        code = lambda r: r["variable"][len("resort_view_"):]
        surged = [code(r) for r, g in recs if (g.get("ga4_views_yoy_pct") or 0) >= SURGE_MIN * 100]
        fell = [code(r) for r, g in recs if (g.get("ga4_views_yoy_pct") or 0) < 0]
        parts = []
        if surged:
            parts.append(f"{len(surged)} saw views surge ({', '.join(surged)})")
        if fell:
            parts.append(f"{len(fell)} saw views fall ({', '.join(fell)})")
        text = f"Of {len(rows)} resorts, " + "; ".join(parts) if parts else f"{len(rows)} resorts"
        return text + "."

    pos, neg = ai.get("top_resorts_positive", []), ai.get("top_resorts_negative", [])
    return {"positive": {"narrative": narrative(pos), "items": [item(r) for r in pos]},
            "negative": {"narrative": narrative(neg), "items": [item(r) for r in neg]}}


def _other_selection(fx):
    gen = sorted(fx.get("variable_checks", []), key=lambda c: -(c.get("model_abs_weight") or 0))[:OTHER_PER_KIND]
    leads = sorted([c for c in fx.get("lead_checks", []) if "model_direction" in c and c["status"] != "GA4 contribution negligible"],
                   key=lambda c: -(c.get("model_abs_weight") or 0))[:OTHER_PER_KIND]
    return gen, leads


def other_items(fx, ai):
    """Model signals and channel leads that GA4 confirms or contradicts, each with a short reading written from the card's own
    verified claims (ISENT); the plain GA4 figures are only the fallback. Leads whose GA4 contribution is negligible are not
    listed; they are counted in the section narrative."""
    items = []
    gen, leads = _other_selection(fx)
    for c in gen:
        key = f"sig:{c['variable']}:{c['site']}"
        if c["status"] == "not checkable":
            sent = ISENT.get(key) or "Model signal with no usable GA4 mapping, so it could not be cross-checked."
            ml = f"Model {pct(c['model_yoy_pct'], 0)}"
            flag = ""
        else:
            sent = ISENT.get(key) or f"GA4 counts {c['ga4_counts'][0]:,} to {c['ga4_counts'][1]:,} events ({pct(c['ga4_yoy_pct'], 0)})."
            ml = f"GA4 {pct(c['ga4_yoy_pct'], 0)} · {c['ga4_counts'][0]:,} to {c['ga4_counts'][1]:,} events"
            flag = (f"⚑ Model vs GA4 — model {pct(c['model_yoy_pct'], 0)}, GA4 {pct(c['ga4_yoy_pct'], 0)}" if c["status"] == "DISCREPANCY" else "")
        items.append({"theme": c["variable"].replace("_", " "), "variable": c["variable"], "site": c["site"],
                      "direction": (c.get("model_impact") or "negative"), "metric_line": ml, "summary": sent, "flag": flag})
    for c in leads:
        key = f"lead:{c['variable'].replace('channel_', '')}:{c['site']}"
        sent = ISENT.get(key) or (f"GA4: this channel moved ECVR {f2(c['ga4_contribution_bp'])} bp here "
                                  f"(mix {f2(c['ga4_mix_bp'])} bp, rate {f2(c['ga4_rate_bp'])} bp).")
        if c["status"].startswith("DISCREPANCY"):
            flag = "⚑ Model vs GA4 — model says " + c["model_direction"] + ", GA4 opposite" + (" (thin base)" if c.get("thin_base") else "")
        else:
            flag = thin_flag(c["ga4_confirmations"])
        items.append({"theme": c["variable"].replace("channel_", "").replace("_", " ") + " channel", "variable": c["variable"],
                      "site": c["site"], "direction": c["model_direction"],
                      "metric_line": f"GA4 effect {f2(c['ga4_contribution_bp'])} bp on {c['site']}'s ECVR",
                      "summary": sent, "flag": flag})
    return items


# ------------------------------------------------------------------ fact sheet + checked wording
def fact_sheet(fx, ai):
    L = []
    g = next(s for s in fx["scopes"] if s["level"] == "global")
    t = g["totals"]
    L.append(f"GLOBAL: ECVR {rate(t['ecvr'][0])} -> {rate(t['ecvr'][1])} ({pct(t['ecvr_yoy_pct'])}, {f2(t['delta_bp'])} bp); "
             f"sessions {t['sessions'][0]:,.0f} -> {t['sessions'][1]:,.0f} ({pct(yoy_of(*t['sessions']))}); "
             f"confirmations {t['confirmations'][0]:,.0f} -> {t['confirmations'][1]:,.0f}")
    for c in g["by_device"]:
        L.append(f"GLOBAL DEVICE {c['group']}: total {f2(c['total_bp'])} bp (rate {f2(c['rate_bp'])} bp, mix {f2(c['mix_bp'])} bp); "
                 f"share {c['share'][0]:.1%} -> {c['share'][1]:.1%}")
    for c in sorted(g["by_channel"], key=lambda c: -abs(c["total_bp"]))[:8]:
        L.append(f"GLOBAL CHANNEL {c['group']}: total {f2(c['total_bp'])} bp (rate {f2(c['rate_bp'])} bp, mix {f2(c['mix_bp'])} bp); "
                 f"share {c['share'][0]:.1%} -> {c['share'][1]:.1%}; confirmations {c['confirmations'][0]:,.0f} -> {c['confirmations'][1]:,.0f}")
    # cross-scope table for the largest global channels and both devices: how the same group
    # behaved in every Business Unit, so any "where is it largest" claim has the figures to rest on
    bus = [s for s in fx["scopes"] if s["level"] == "bu" and "totals" in s]
    for gname in [c["group"] for c in sorted(g["by_channel"], key=lambda c: -abs(c["total_bp"]))[:4]]:
        cells = []
        for b in bus:
            c = next((x for x in b["by_channel"] if x["group"] == gname), None)
            if c:
                cells.append(f"{b['scope']} total {f2(c['total_bp'])} (rate {f2(c['rate_bp'])} bp, mix {f2(c['mix_bp'])} bp)")
        L.append(f"CHANNEL {gname} ACROSS BUSINESS UNITS, bp: " + "; ".join(cells))
    for dname in ("mobile", "desktop"):
        cells = []
        for b in bus:
            c = next((x for x in b["by_device"] if x["group"] == dname), None)
            if c:
                cells.append(f"{b['scope']} total {f2(c['total_bp'])} (rate {f2(c['rate_bp'])} bp, mix {f2(c['mix_bp'])} bp)")
        L.append(f"DEVICE {dname} ACROSS BUSINESS UNITS, bp: " + "; ".join(cells))
    for c in fx.get("bu_contribution", []):
        L.append(f"BU CONTRIBUTION TO GLOBAL {c['group']}: total {f2(c['total_bp'])} bp (rate {f2(c['rate_bp'])} bp, mix {f2(c['mix_bp'])} bp)")
    for s in fx["scopes"]:
        if s["level"] not in ("bu", "market") or "totals" not in s:
            continue
        tt = s["totals"]
        L.append(f"{s['level'].upper()} {s['scope']} [bp in this block are of THIS scope's own ECVR; not additive across scopes or with global]: ECVR {pct(tt['ecvr_yoy_pct'])} ({f2(tt['delta_bp'])} bp); sessions "
                 f"{tt['sessions'][0]:,.0f} -> {tt['sessions'][1]:,.0f} ({pct(yoy_of(*tt['sessions']))}); confirmations "
                 f"{tt['confirmations'][0]:,.0f} -> {tt['confirmations'][1]:,.0f}")
        for c in sorted(s["by_channel"], key=lambda c: -abs(c["total_bp"]))[:3]:
            L.append(f"  {s['scope']} channel {c['group']}: {f2(c['total_bp'])} bp (rate {f2(c['rate_bp'])} bp, mix {f2(c['mix_bp'])} bp)")
        for c in s["by_device"]:
            L.append(f"  {s['scope']} device {c['group']}: {f2(c['total_bp'])} bp (rate {f2(c['rate_bp'])} bp, mix {f2(c['mix_bp'])} bp)")
    for d in fx.get("discrepancies", []):
        L.append(f"DISCREPANCY model vs GA4 [{d['scope']}]: {friendly(d['flag'])}")
    for r in fx.get("resort_checks", []):
        L.append(f"RESORT {r['variable']}: GA4 views {r['views'][0]:,} -> {r['views'][1]:,}; confirmations {r['confirmations'][0]:,} -> {r['confirmations'][1]:,}; status {r['status']}")
    return "\n".join(L)


def numbers_in(text):
    out = set()
    for m in re.finditer(r"\d[\d,]*\.?\d*", text):
        tok = m.group(0).rstrip(".,").replace(",", "")
        if not tok:
            continue
        out.add(tok)
        if "." in tok:
            out.add(tok.rstrip("0").rstrip("."))
    return out


def text_ok(text, allowed_numbers, pairing_ok=False):
    if not isinstance(text, str) or not text.strip():
        return False
    if UNMEASURED_CAUSES.search(text) or (PAIRING.search(text) and not pairing_ok):
        return False
    return all(n in allowed_numbers or float(n) in {0.0} for n in numbers_in(text)
               if re.fullmatch(r"\d+(?:\.\d+)?", n))


def allowed_numbers(sheet):
    base = numbers_in(sheet)
    extra = set()
    for n in list(base):                       # a figure may be quoted rounded to fewer decimals
        try:
            f = float(n)
        except ValueError:
            continue
        for d in (0, 1, 2):
            extra.add(f"{f:.{d}f}")
            extra.add(f"{f:.{d}f}".rstrip("0").rstrip(".") if "." in f"{f:.{d}f}" else f"{f:.{d}f}")
    return base | extra


NUMBER_WORDS = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8}


def total_called_rate(text: str, claim_objs) -> str | None:
    """A sentence that attaches an own-conversion ('rate') label to a figure which, in the cited claims, is a
    TOTAL (rate + mix) is wrong: "desktop accounts for -0.88 bp of the own-conversion (rate) drag" when -0.88 is
    desktop's total and its rate is -1.11. Looks for '<total figure> ... (of the )?(own-conversion|rate) (drag|effect|
    decline)' within one clause and compares with the claims' labelled figures."""
    totals, rates = set(), set()
    for c in claim_objs:
        for m in re.finditer(r"moved global ECVR ([+-]\d+\.\d\d) bp.*?\(rate ([+-]\d+\.\d\d) bp", c["text"]):
            totals.add(m.group(1)); rates.add(m.group(2))
        for m in re.finditer(r"contributed ([+-]\d+\.\d\d) bp to the GLOBAL ECVR change.*?\(rate ([+-]\d+\.\d\d) bp", c["text"]):
            totals.add(m.group(1)); rates.add(m.group(2))
    for m in re.finditer(r"([+-]\d+\.\d\d) bp\b[^.;,]{0,60}?(?:own[- ]conversion|\brate\b)\s*(?:\(rate\)\s*)?(?:drag|effect|decline|deterioration|loss)(?!\s*(?:of|at|was|is|:)?\s*[+-]\d+\.\d\d)", text, re.I):
        fig = m.group(1)
        if fig in totals and fig not in rates:
            return f"{fig} bp is a total (rate + mix), not a rate effect"
    return None


def count_mismatch(text: str):
    """"Four model leads flagged ...: A in X, B in Y, C, D and E" -> the number of items listed after the colon
    must equal the number word. Returns a reason string, or None. Only fires when a count word is directly
    followed by a noun and a colon-introduced enumeration, so ordinary figures are never touched."""
    m = re.search(r"\b(two|three|four|five|six|seven|eight)\s+(?:[A-Za-z-]+\s+){0,4}?(?:flagged|listed|shown|named|identified|"
                  r"leads|signals|markets|channels|resorts|discrepancies)[^:;]{0,60}:\s*(.+?)(?:\.(?:\s|$)|$)", text, re.S | re.I)
    if not m:
        return None
    claimed = NUMBER_WORDS[m.group(1).lower()]
    listed = [x for x in re.split(r";\s*|,\s*|\s+and\s+", m.group(2)) if x.strip()]
    if ";" in m.group(2):                      # semicolon-separated enumeration: one item per segment
        listed = [x for x in re.split(r";\s*", m.group(2)) if x.strip()]
    # "Display Acquisition in Belgium and Italy" is two leads sharing one channel: count place names too
    places = re.findall(r"\bin\s+([A-Z][\w]+(?:\s+and\s+[A-Z][\w]+)*)", m.group(2))
    n = len(listed) if ";" in m.group(2) else (sum(1 + p.count(" and ") for p in places) if places else len(listed))
    return None if n == claimed else f"count word '{m.group(1)}' but {n} items are listed"


LINK_VERBS = re.compile(r"\b(?:shift(?:ed|ing)?|mov(?:ed|ing)|migrat\w+|flow(?:ed|ing)?|transferr?\w*)\s+(?:from|into|to)\b", re.I)


UP_WORDS = re.compile(r"\b(?:rose|rising|grew|growing|grown|larger|bigger|increas\w+|surg\w+|expand\w+|jump\w+|climb\w+|gain\w+|higher)\b", re.I)
DOWN_WORDS = re.compile(r"\b(?:fell|falling|shrank|shrink\w*|smaller|declin\w+|dropp\w+|collaps\w+|eas(?:ed|ing)|lower|slipp\w+|contract\w+)\b", re.I)


def share_direction_error(text: str):
    """A 'from a% to b%' figure must agree with the verb or adjective just before it ('a larger share, rising from 30.6% to
    20.8%' is wrong). Only the 70 characters before the figure are read."""
    for m in re.finditer(r"from (\d+(?:\.\d+)?)% to (\d+(?:\.\d+)?)%", text):
        a, b = float(m.group(1)), float(m.group(2))
        if a == b:
            continue
        before = text[max(0, m.start() - 70):m.start()]
        up, down = bool(UP_WORDS.search(before)), bool(DOWN_WORDS.search(before))
        if (b > a and down and not up) or (b < a and up and not down):
            return f"direction wording contradicts 'from {m.group(1)}% to {m.group(2)}%' ({'rose' if b > a else 'fell'})"
    return None


def links_two_channels(text: str, channel_names) -> bool:
    """A 'moved/shifted from X to Y' phrase is only a problem when the sentence names two different
    channel groups; the same words about one metric ('its ECVR moved from 0.05% to 0.04%') are fine."""
    if not LINK_VERBS.search(text):
        return False
    low = text.lower()
    return sum(1 for n in channel_names if n.lower() in low) >= 2


def friendly(text: str) -> str:
    """Reader-facing channel names: channel_<slug> -> 'Slug Words' (the Custom Channel Group name)."""
    return re.sub(r"channel_([a-z0-9_]+)", lambda m: m.group(1).replace("_", " ").title(), text)


def fallback_texts(fx, ai):
    g = next(s for s in fx["scopes"] if s["level"] == "global")
    t = g["totals"]
    chans = sorted(g["by_channel"], key=lambda c: -abs(c["total_bp"]))
    devs = [d for d in g["by_device"] if d["group"] != "other devices"]
    bus = sorted([s for s in fx["scopes"] if s["level"] == "bu" and "totals" in s], key=lambda s: s["totals"]["delta_bp"])
    sess = yoy_of(*t["sessions"])
    concl = (f"Global ECVR BE moved {pct(t['ecvr_yoy_pct'])} ({f2(t['delta_bp'])} bp) on GA4 while sessions moved {pct(sess)}"
             f". Largest channel effect: {chans[0]['group']} ({f2(chans[0]['total_bp'])} bp)."
             + (f" Largest device effect: {max(devs, key=lambda d: abs(d['total_bp']))['group']} ({f2(max(devs, key=lambda d: abs(d['total_bp']))['total_bp'])} bp)." if devs else "")
             + (f" Largest Business Unit drag: {bus[0]['scope']} ({f2(bus[0]['totals']['delta_bp'])} bp)." if bus else ""))
    actions = []
    chs = sorted([c for c in g["by_channel"] if c["total_bp"] < -NEGLIGIBLE_BP], key=lambda c: c["total_bp"])
    bus_all = [x for x in fx["scopes"] if x["level"] == "bu" and "totals" in x]
    for c in chs:
        if len(actions) >= 2:
            break
        if abs(c["mix_bp"]) >= 2 * abs(c["rate_bp"]):
            actions.append(f"Confirm in the source reports that the {c['group']} volume is as planned: its share of sessions went from {c['share'][0]:.1%} "
                           f"to {c['share'][1]:.1%} on {c['confirmations'][0]:,.0f} vs {c['confirmations'][1]:,.0f} BE confirmations, which cost global "
                           f"ECVR {abs(c['total_bp']):.2f} bp.")
        else:
            where = [x["scope"] for x in bus_all
                     if any(y["group"] == c["group"] and y["rate_bp"] < -NEGLIGIBLE_BP for y in x["by_channel"])]
            if where:
                actions.append(f"Review the {c['group']} booking journey step by step (entry, then confirmation) in {', '.join(where)}, where its own "
                               f"conversion fell: it cost global ECVR {abs(c['total_bp']):.2f} bp, and the step where visitors stop is the next thing to locate.")
    contrib = sorted(fx.get("bu_contribution", []), key=lambda c: c["total_bp"])
    if contrib and len(actions) < 3:
        worst = next((x for x in bus_all if x["scope"] == contrib[0]["group"]), None)
        dvs = sorted([d for d in (worst["by_device"] if worst else []) if d["group"] != "other devices" and d["total_bp"] < -NEGLIGIBLE_BP],
                     key=lambda d: d["total_bp"])
        if dvs:
            d = dvs[0]
            actions.append(f"Review the {d['group']} booking journey in {worst['scope']}: {d['group']} ECVR went from {d['ecvr'][0] * 100:.3f}% to "
                           f"{d['ecvr'][1] * 100:.3f}% ({f2(d['total_bp'])} bp in {worst['scope']}'s own units), so compare where {d['group']} visitors "
                           f"stop between entry and confirmation.")
    actions = actions[:3]
    watch = [f"Review {d['scope']}: {friendly(d['flag'])}." for d in fx.get("discrepancies", [])[:6]]
    return concl, actions, watch


def market_sentences(fx, ai, client, K, cmap, known_scopes, channel_names, allowed, validate_fn):
    """One analytic sentence per BU and per BU-focus market, written from that scope's own READ claim, with
    every comparison word and figure checked exactly like the narratives. -> {scope: sentence}. A scope whose
    sentence still fails after two corrections keeps its deterministic line (no entry returned)."""
    reads = {}
    for c in K.items:
        m = re.match(r"(MARKET|BU) READ (.+?):", c["text"])
        if m:
            reads[m.group(2)] = c
    if not reads or client is None:
        return {}

    def lic(c):
        return " {licenses: " + ", ".join(sorted(c["licenses"])) + "}" if c["licenses"] else ""

    prompt = (
        "For each scope below (a Business Unit or a market), write TWO short sentences (max 60 words in all) in plain "
        "analyst English, the way you would say it aloud to a colleague, explaining what happened to its ECVR BE and through "
        "which mechanism.\n"
        "Sentence 1: the direction and size of the scope's change, then the channel(s) that moved it, saying IN WORDS whether "
        "the channel's own conversion changed (rate) or only its share of traffic changed (mix), with its share going from a% "
        "to b% when it is a mix effect. Sentence 2: the device picture, the same way. Use at most 3 figures per sentence, copied "
        "exactly from the scope's own claim; do not list every figure.\n"
        "Write a share change as 'rose from a% to b%' or 'fell from a% to b%', never 'stood at'. Never use the verbs moved, shifted, "
        "flowed, migrated or transferred followed by from/to/into: use rose, fell, gained or lost. Do not state confirmation counts "
        "unless the base is thin. "
        "FORM (placeholders, not data): '<Scope>'s ECVR fell X bp, led by <Channel A>, whose traffic share rose from a% to b% "
        "(mix -c bp), and <Channel B>, whose own conversion fell (rate -d bp). On devices, <device 1> lost ground through its "
        "own conversion (rate -e bp), while <device 2> ...'.\n"
        "RULES (checked by code): bp figures are in the scope's OWN ECVR units; a comparison word (largest, most, only, "
        "dominated, primarily, above/below average, all) is allowed only if the claim licenses it for that entity (the claim "
        "licenses 'largest' only for its first-named channel; for devices describe each on its own figures); never say one "
        "channel offsets, replaces or compensates another unless an OFFSET claim of that scope is cited and the sentence names exactly "
        "its two channels; different names are different channels. DESCRIBE WHAT MOVED AND HOW, "
        "NEVER WHY: you know a channel or market only by its name and figures, so make no assumption about what it consists of "
        "or how it is run, and give no reason, cause or interpretation the claim does not state. Mention a thin base if the "
        "claim says so.\n"
        "'Led by X' is allowed ONLY when X's effect has the same sign as the scope's change; otherwise say 'the largest single effect was X'.\n"
        "Words that need proof are allowed ONLY when you cite the claim that proves them: 'mostly / mainly / largely / primarily' about a channel "
        "needs that channel's DETAIL claim to carry {licenses: dominant}; 'entirely / purely / almost entirely' needs {licenses: total}; "
        "'offset / partly offset / countered / cancels' needs the scope's OFFSET claim, and the sentence must then name exactly its two "
        "channels. When the claims do not carry the licence, describe the figures plainly instead. When in doubt, leave the word out.\n"
        "End every sentence with the ids of the claims it rests on, like [C45, C46]. Return ONLY a JSON object {scope: sentence}.\n\n"
        + "\n".join(f"{name}: [{c['id']}] {c['text']}{lic(c)}"
                    + "".join(f"\n    [{e['id']}] {e['text']}{lic(e)}" for e in K.items if e.get("kind") and e["scope"] == name)
                    for name, c in reads.items()))

    def call(p, max_tokens):
        m = client.messages.create(model=MODEL, max_tokens=max_tokens, temperature=TEMPERATURE,
                                   messages=[{"role": "user", "content": p}])
        r = next((b.text for b in m.content if hasattr(b, "text")), "")
        return json.loads(friendly(r[r.find("{"): r.rfind("}") + 1]))

    try:
        data = call(prompt, 6000)
    except Exception as e:
        print(f"  Market-sentence call failed ({e}) - deterministic lines kept.")
        return {}
    out, bad = {}, {}

    def judge(name, text):
        text = re.sub(r"(?<![\[\w])C\d+(?:\s*,\s*C\d+)*\s*$", "", text.strip()).strip()   # a bare trailing 'C49' is a citation the model forgot to bracket
        if not re.search(r"\[C\d+", text):
            text = text.rstrip() + f" [{reads[name]['id']}]"
        body, claims_, ok, why = validate_fn(text)
        if ok:
            sc_ = next((x for x in fx["scopes"] if x["scope"] == name and "totals" in x), None)
            if sc_:
                for c_ in sc_["by_channel"]:
                    if re.search(r"(?:led|driven|headed) by (?:the )?" + re.escape(c_["group"]) + r"\b", body, re.I) \
                            and abs(c_["total_bp"]) >= NEGLIGIBLE_BP and (c_["total_bp"] < 0) != (sc_["totals"]["delta_bp"] < 0):
                        ok, why = False, f"'led by {c_['group']}' but its effect points the opposite way to the scope's change"
        if ok and reads[name]["id"] not in [c["id"] for c in claims_]:
            return body, False, "cites a different scope's claim"
        return body, ok, why

    for name, text in data.items():
        if name not in reads or not isinstance(text, str):
            continue
        body, ok, why = judge(name, text)
        if ok:
            out[name] = body
        else:
            bad[name] = {"rejected_sentence": body, "reason": why,
                         "claim": {"id": reads[name]["id"], "text": reads[name]["text"], "licenses": sorted(reads[name]["licenses"])}}
    for _ in range(2):
        if not bad:
            break
        try:
            redo = call("Each sentence below was REJECTED by an automatic fact check, for the reason given. Rewrite it using only "
                        "the figures in its claim, drop any comparison word the claim does not license, keep plain two-sentence prose (what moved and "
                        "through which mechanism, never why), never link two channels, "
                        "state no cause, and end with the claim id. Return ONLY a JSON object {scope: sentence}.\n\n"
                        + json.dumps(bad, ensure_ascii=False, indent=1), 4000)
        except Exception:
            break
        for name in list(bad):
            t = redo.get(name)
            if isinstance(t, str):
                body, ok, why = judge(name, t)
                if ok:
                    out[name] = body
                    bad.pop(name)
                else:
                    bad[name]["rejected_sentence"], bad[name]["reason"] = body, why
    for name, b in bad.items():
        print(f"    market sentence for {name} kept deterministic - {b['reason']} | {b['rejected_sentence'][:240]}")
    return out


def item_sentences(fx, ai, K, client, validate_fn):
    """One short, varied sentence per card (global devices and channels, BU split, BU devices, BU channels, channel x market),
    written from the card's own verified claims and checked like every other sentence. -> {key: sentence}. A card whose
    sentence never passes keeps its deterministic line (no entry)."""
    if client is None:
        return {}
    g = next((s for s in fx["scopes"] if s["level"] == "global" and "totals" in s), None)
    if not g:
        return {}
    by_key = {}
    for c in K.items:
        if c.get("key"):
            by_key.setdefault(c["key"], []).append(c)
    batches = {
        "global devices": ("How the device's own conversion and its share of sessions changed, and what that did to global ECVR BE.", []),
        "global channels": ("How the channel's own conversion and its share of sessions changed, and what that did to global ECVR BE.", []),
        "BU split": ("The Business Unit's role in the GLOBAL change (what it took off or added) and how its own ECVR moved in %. No channel detail: that belongs to another card.", []),
        "BU devices": ("How mobile and desktop each moved ECVR inside this Business Unit and which one held up better.", []),
        "BU channels": ("The channels that moved this Business Unit's ECVR, named with how each moved it.", []),
        "channel in market": ("How this one channel moved this one market's ECVR.", []),
        "market": ("What happened to this market's ECVR BE and through which channel(s) and devices, written as a short paragraph.", []),
        "BU narrative": ("What happened to this Business Unit's own ECVR BE and through which channel(s) and devices, written as a short paragraph.", []),
        "other signals": ("What this model signal did in GA4 in this market, read against what the market's own sessions and BE confirmations did: say plainly whether the signal and the booking outcome moved the same way or not. Observation only, no cause.", []),
        "model channel leads": ("What this channel did in this market (its share of sessions, its BE confirmations, its effect on the market's ECVR) and whether GA4 bears out the model's direction.", []),
        "resorts": ("What happened to this resort's views and to its bookings (BE confirmations), saying plainly whether bookings followed the views; mention a small base when the claim says so.", []),
    }
    LIMITS = {"market": (2, 62), "BU narrative": (2, 62)}      # (max sentences, max words)

    def add(batch, key, claims):
        if claims:
            batches[batch][1].append((key, claims))

    for d in g["by_device"]:
        if d["group"] in ("mobile", "desktop"):
            add("global devices", f"dev:global:{d['group']}", by_key.get(f"dev:global:{d['group']}", []))
    pos, neg = top_by_sign(g["by_channel"])
    for c in pos + neg:
        add("global channels", f"chan:global:{c['group']}", by_key.get(f"chan:global:{c['group']}", []))
    scopes = {s["scope"]: s for s in fx["scopes"] if "totals" in s}
    for s in fx["scopes"]:
        if s["level"] == "bu" and "totals" in s:
            bu = s["scope"]
            add("BU split", f"buspl:{bu}", by_key.get(f"buspl:{bu}", []) + by_key.get(f"buread:{bu}", []))
            add("BU devices", f"budev:{bu}", by_key.get(f"dev:{bu}:mobile", []) + by_key.get(f"dev:{bu}:desktop", []))
            add("BU channels", f"buchan:{bu}", [c for k, v in by_key.items() if k.startswith(f"cross:{bu}:") for c in v])
    def device_story(sc):
        """Devices are worth a sentence only when they differ in a way a reader would care about: they moved in opposite
        directions, or one moved at least twice as much as the other, on a base that is not thin."""
        if not sc or min(sc["totals"]["confirmations"]) < MIN_CONFIRMATIONS:
            return False
        dv = [d["total_bp"] for d in sc["by_device"] if d["group"] in ("mobile", "desktop")]
        if len(dv) < 2 or max(abs(x) for x in dv) < NEGLIGIBLE_BP:
            return False
        a, b = sorted(dv, key=abs)
        return (a * b < 0 and abs(a) >= NEGLIGIBLE_BP) or abs(b) >= 2 * abs(a)

    def scope_claims(name):
        sc = scopes.get(name)
        story = device_story(sc)
        return [c for c in K.items if c["scope"] == name and (c.get("key") or c.get("kind"))
                and not str(c.get("key") or "").startswith(("lead:", "sig:", "resort:"))
                and (story or not str(c.get("key") or "").startswith("dev:"))]

    gen_sel, lead_sel = _other_selection(fx)
    for c in gen_sel:
        add("other signals", f"sig:{c['variable']}:{c['site']}", by_key.get(f"sig:{c['variable']}:{c['site']}", []))
    for c in lead_sel:
        add("model channel leads", f"lead:{c['variable'].replace('channel_', '')}:{c['site']}", by_key.get(f"lead:{c['variable'].replace('channel_', '')}:{c['site']}", []))
    for r in ai.get("top_resorts_positive", []) + ai.get("top_resorts_negative", []):
        code = r["variable"][len("resort_view_"):]
        add("resorts", f"resort:{code}", by_key.get(f"resort:{code}", []))
    for s in fx["scopes"]:
        if s["level"] == "bu" and "totals" in s:
            add("BU narrative", f"bunar:{s['scope']}", scope_claims(s["scope"]))
    for bu, markets in ai.get("top_countries_per_bu", {}).items():
        for m in markets:
            if m["site"] in scopes:
                add("market", f"mkt:{m['site']}", scope_claims(m["site"]))
    for bu, markets in ai.get("top_countries_per_bu", {}).items():
        for m in markets:
            s = scopes.get(m["site"])
            if not s:
                continue
            for c in sorted(s["by_channel"], key=lambda c: -abs(c["total_bp"]))[:CROSS_PER_MARKET]:
                add("channel in market", f"cross:{m['site']}:{c['group']}", by_key.get(f"cross:{m['site']}:{c['group']}", []))

    rules = (
        "You write ONE short sentence per card for a monthly ECVR BE (booking-engine conversion rate) report, in plain analyst "
        "English, the way a person would say it aloud, e.g. 'Mobile carries three quarters of sessions but converts at a thinner "
        "rate than a year ago.' Max 28 words (40 for a card with several claims), ONE sentence, at most 3 figures copied EXACTLY from the card's claims (bp figures are in "
        "the scope's OWN ECVR units). Say what happened and through which mechanism IN WORDS (its own conversion changed, or only its "
        "share of traffic changed); do not write '(rate -x, mix -y)' brackets and do not list figures.\n"
        "'mostly / mainly / largely' at most ONCE per sentence, and only to contrast with something that moved through both effects; "
        "otherwise just say what moved.\n"
        "For resort and model-signal cards the mechanism is simply what moved and whether the bookings followed it. "
        "Never put a points figure right after a % or a '% to %' range (no '0.834% to 0.287%, -0.069 points'): one or the other.\n"
        "VARY the sentences: inside this batch no two sentences may open with the same two words or share a skeleton; open some with "
        "the scope, some with the mechanism, some with a figure.\n"
        "Never explain WHY: you know a channel, market or device only by its name and its figures; no cause, and no assumption about "
        "what it consists of or how it is run. Proof words (largest, mostly, mainly, entirely, above/below average, all, only) are "
        "allowed ONLY when a cited claim carries that licence for that entity; when in doubt leave them out. Never link two channels "
        "(no offset, swap, replaced). Mention a thin base if the claim says so.\n"
        "End each sentence with the id(s) of the claim(s) it rests on, like [C12] or [C12, C13]. Do all reasoning silently: your reply must "
        "START with the opening brace and contain nothing but the JSON object. Return ONLY a JSON object with EXACTLY one "
        "entry per KEY given (use the KEY text as the JSON key, never a claim id or a sub-key).\n\n")

    def lic(c):
        return " {licenses: " + ", ".join(sorted(c["licenses"])) + "}" if c["licenses"] else ""

    def call(p):
        m = client.messages.create(model=MODEL, max_tokens=9000, temperature=TEMPERATURE, messages=[{"role": "user", "content": p}])
        r = friendly(next((b.text for b in m.content if hasattr(b, "text")), ""))
        end = r.rfind("}") + 1
        for st in [i for i, ch in enumerate(r) if ch == "{"]:
            try:
                out = json.loads(r[st:end])
                if isinstance(out, dict):
                    return out
            except ValueError:
                continue
        raise ValueError(f"no JSON object in the reply (stop_reason={m.stop_reason}, {len(r)} chars)")

    out = {}
    for name, (angle, reqs) in batches.items():
        if not reqs:
            continue
        todo, notes, good = dict(reqs), {}, {}
        for rnd in range(4):
            if not todo:
                break
            listing = "\n\n".join(f"KEY \"{k}\" (write exactly ONE sentence for this key, covering all the claims under it):\n"
                                  + "\n".join(f"   [{c['id']}] {c['text']}{lic(c)}" for c in cl) for k, cl in todo.items())
            ms, mw = LIMITS.get(name, (1, 34))
            para = (f"\nFOR THIS BATCH write {ms} sentences (max {mw - 8} words in all) instead of one: sentence 1 = the change in the scope's own "
                    f"ECVR BE (say it in % when the claim gives one) and the channel(s) that moved it, with the mechanism in words; sentence 2 = the "
                    f"two devices, but ONLY if DEVICE claims are listed for the card (they are listed only when the devices tell a story: "
                    f"opposite directions, or one far larger than the other); otherwise write a single sentence and say nothing about devices. NO bracketed '(rate x, mix y)' figures, at most 4 figures in all, and 'led by X' only when X pushed the same way "
                    f"as the scope's change. If an OFFSET claim is listed you may say the two named channels partly offset each other, "
                    f"naming exactly those two. Start sentence 1 with something other than the scope's name in about half the cards.\n"
                    if name in LIMITS else "")
            fb = ("\nREJECTED earlier (fix each, using only its claims):\n" + json.dumps(notes, ensure_ascii=False, indent=1) + "\n") if notes else ""
            try:
                data = call(rules + f"BATCH: {name}. {angle}\n" + para + fb + "\n" + listing)
            except Exception as e:
                print(f"  Item-sentence call for {name} failed ({e}) - retrying." if rnd < 3 else f"  Item-sentence call failed for {name} ({e}) - deterministic lines kept.")
                continue
            notes = {}
            taken = {" ".join(v.lower().split()[:2]) for v in good.values()}
            for k, text in data.items():
                if k not in todo or not isinstance(text, str):
                    continue
                cl = todo[k]
                text = re.sub(r"(?<![\[\w])C\d+(?:\s*,\s*C\d+)*\s*$", "", text.strip()).strip()
                if not re.search(r"\[C\d+", text):
                    text = text.rstrip() + f" [{cl[0]['id']}]"
                body, used, ok, why = validate_fn(text)
                if ok and not ({c["id"] for c in cl} & {c["id"] for c in used}):
                    ok, why = False, "cites a claim of a different card"
                ms, mw = LIMITS.get(name, (1, 44 if len(cl) > 1 else 34))
                if ok and (len(re.findall(r"[.!?](?:\s|$)", body)) > ms or len(body.split()) > mw):
                    ok, why = False, f"must be at most {ms} sentence(s) and {mw - 6} words"
                if ok and len(re.findall(r"\b(?:mostly|mainly|largely|primarily|predominantly)\b", body, re.I)) > 1:
                    ok, why = False, "'mostly/mainly' at most once per line, and only where it contrasts with a channel that moved through both effects"
                if ok and re.search(r"\((?:rate|mix)\b", body):
                    ok, why = False, "no bracketed (rate .., mix ..) figures: say it in words"
                if ok and k.split(":")[0] in ("mkt", "bunar"):
                    sc_ = next((x for x in fx["scopes"] if x["scope"] == k.split(":", 1)[1] and "totals" in x), None)
                    for c_ in (sc_["by_channel"] if sc_ else []):
                        if re.search(r"(?:led|driven|headed) by (?:the )?" + re.escape(c_["group"]) + r"\b", body, re.I) \
                                and abs(c_["total_bp"]) >= NEGLIGIBLE_BP and (c_["total_bp"] < 0) != (sc_["totals"]["delta_bp"] < 0):
                            ok, why = False, f"'led by {c_['group']}' but it pushed the opposite way to the scope's change"
                opening = " ".join(body.lower().split()[:2])
                if ok and opening in taken:
                    ok, why = False, f"opens with '{opening}' like another card in this batch: restructure it"
                if ok:
                    good[k] = body
                    taken.add(opening)
                    todo.pop(k)
                else:
                    notes[k] = {"rejected_sentence": body, "reason": why}
        for k, v in good.items():
            out[k] = v
        for k, v in notes.items():
            print(f"      reject {k}: {v['reason']} | {v['rejected_sentence'][:200]}")
        miss = [k for k, _ in reqs if k not in good]
        if miss and not notes:
            print(f"      {name}: model returned no sentence for {miss[:3]} (returned keys: {list(data)[:3] if 'data' in dir() else '?'})")
        if miss:
            print(f"    {name}: {len(miss)} card(s) kept deterministic ({', '.join(miss[:4])}{'...' if len(miss) > 4 else ''})")
    return out


def wording(fx, ai):
    """LLM wording of the narrative layer, written FROM numbered verified claims (claims.py).

    The model writes full analytical sentences but must cite the claim ids each sentence rests on
    ("[C7,C11]"). Code then checks every sentence: (1) every figure in it exists in the cited claims or
    the fact sheet, (2) no unmeasured cause or channel pairing, (3) every comparison word ("largest",
    "only", "dominated", "above average", "all", "most" ...) is licensed by a cited claim about the same
    entity. A sentence that fails is REPLACED by the text of its cited claims, so what reaches a card is
    either verified analysis or verified fact, never an unsupported statement."""
    concl_fb, actions_fb, watch_fb = fallback_texts(fx, ai)
    K = CL.build(fx, ai)
    cmap = K.by_id()
    channel_names = sorted({c["group"] for s in fx["scopes"] for c in s.get("by_channel", [])})
    known_scopes = sorted({s["scope"] for s in fx["scopes"] if s["level"] in ("bu", "market")}
                          | {c["group"] for c in fx.get("bu_contribution", [])})
    sheet = fact_sheet(fx, ai) + "\n" + K.listing()
    allowed = allowed_numbers(sheet)
    result = {"overall_conclusion": concl_fb, "top_actions": actions_fb, "watch_points": watch_fb, "narratives": {}}
    stats = {"ok": 0, "replaced": 0, "fails": []}
    if not API_KEY:
        print("  No ANTHROPIC_API_KEY — deterministic wording only.")
        return result, 0, 0
    client = anthropic.Anthropic(api_key=API_KEY)
    prompt = (
        "You write the analytical narrative of a monthly ECVR BE (booking-engine conversion rate) report for "
        "senior analysts. It must be a COMPREHENSIVE explanation, not generic statements: say what moved, by how "
        "much, through which mechanism (a group's own conversion = 'rate', or its traffic share = 'mix'), where "
        "else the same pattern appears, and which figure or scope is worth verifying.\n\n"
        "You are given NUMBERED VERIFIED CLAIMS computed by code from GA4. EVERY SINGLE SENTENCE you write, in every "
        "text, MUST end with the ids of the claims it rests on, immediately after its full stop, like \"... -1.87 bp. [C7]\" "
        "or \"... in 4 of 5 BUs. [C7,C11]\" — one citation per sentence, never one per paragraph, never omitted. "
        "A sentence without its own citation is rejected. Hard rules, checked by code:\n"
        "1. Use only figures that appear in the cited claims, copied exactly. Never compute or round new numbers.\n"
        "2. A comparison word (largest, most, only, dominated, primarily, mainly, above/below average, all, every, "
        "most BUs) may be used ONLY if a cited claim carries that licence for the SAME entity you name "
        "(claims show {licenses: ...}). The strongest words (entirely, purely, wholly, exclusively, 'almost entirely') need "
        "the licence 'total', which a claim carries only when one effect is at least 95% of rate plus mix. Otherwise describe "
        "the figures without the comparison.\n"
        "3. Channels with different names are different channels: never link two channels (no offset, "
        "counterweight, swap, replaced, 'moved in the opposite direction'), even if one grew while another "
        "shrank; give each its own figures.\n"
        "4. Business Unit and market bp figures are in that scope's OWN ECVR units: never add them to each "
        "other or to a global figure, and never compare them with global bp.\n"
        "5. State no cause the claims do not measure (no tagging, attribution, CRM, intent, quality, campaign or "
        "targeting claims). Make NO assumption about what a channel group, market, variable or metric consists of or how it "
        "is run: you know only its name and the figures in the claims. This applies to actions and watch points as much as to "
        "the narrative: a recommended follow-up must name what to check (the figure, scope or data in the claims) and never a "
        "hypothesised reason or mechanism. Write 'verify the <figure/scope>', never 'verify whether <guessed cause>'.\n"
        "6. Mention model-vs-GA4 discrepancies and thin bases (small base) where they matter.\n"
        "7. If a claim lists several model leads that disagree with GA4, ONE watch point must name ALL of them (the claim states the "
        "count): never name only some.\n"
        "7b. Do NOT write watch points about claims starting 'RECURRING CHANNEL EFFECT': code adds one watch point per recurring "
        "channel after yours.\n"
        "7c. Every claim that says 'is a property-wide pattern' must get its own watch point (figures from the claim, "
        "worded 'worth verifying' if you suggest a follow-up, and with no guess about the cause).\n"
        "8. A scope's TOTAL effect (rate + mix) is not its rate effect: never call a total 'the own-conversion drag' or "
        "'the rate drag'. Quote the total as the total and the rate figure as the rate. When you list items under a count "
        "('four leads', 'five markets') the count must equal the number of items you list.\n"
        "9. Never put a points figure next to a % change or a '% to %' range, in brackets or after a comma: give the % figures, and give a points "
        "figure only on its own, for an effect on ECVR (e.g. 'cost the scope 0.043 points of ECVR').\n\n"
        "Return ONLY a JSON object with keys:\n"
        '  "overall_conclusion": 5-6 sentences, max 170 words: headline change; volume vs conversion; device; '
        "channel; BU; discrepancies/caveats,\n"
        '  "top_actions": exactly 3 ACTIVABLE actions, each one finding plus the concrete operational step it calls for, verb-first, max 50 words: '
        "state the finding (the scope, the channel or device, and the verified figure) and then the step a team would take: verify in the source "
        "reports that the volume or set-up of that channel in that market is as planned, review the booking journey step by step for that device "
        "or market, compare that channel's journey between the Business Units where it fell and where it held, or confirm whether a traffic change "
        "was planned. NEVER propose re-running, excluding data from, re-weighting or otherwise modifying the explicability model or the ECVR "
        "computation, and never propose analyses of the report itself. Do not assume what a channel consists of or why it moved: the step is a "
        "check, not a diagnosis. In actions never use largest, most, only, all, every or second-largest. No owners,\n"
        '  "watch_points": up to 5 items, max 30 words each,\n'
        '  "narratives": {"device": ..., "channel": ..., "bu": ..., "crossover": ..., "resort_positive": ..., '
        '"resort_negative": ..., "other": ...} each 2-3 sentences, max 60 words. FORMS: "crossover" is a comment on the state of things across markets and channels (which patterns recur across Business Units, which stay local to one market, whether the weakness is about conversion or about traffic mix), in plain words, at most 3 figures, NEVER an enumeration of per-BU figures; "resort_positive" and "resort_negative" say what views and confirmations tell together (whether bookings followed views, which resorts have a small base), at most 3 figures, no ratios per 1,000 views; "other" is not used.\n\n'
        "=== VERIFIED CLAIMS ===\n" + K.listing())
    try:
        msg = client.messages.create(model=MODEL, max_tokens=8000, temperature=TEMPERATURE, messages=[{"role": "user", "content": prompt}])
        raw = next((b.text for b in msg.content if hasattr(b, "text")), "")
        data = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
    except Exception as e:
        print(f"  Wording call failed ({e}) — deterministic wording only.")
        return result, 0, 0
    data = json.loads(friendly(json.dumps(data, ensure_ascii=False)))

    def validate(sent):
        """-> (body, claim_objs, ok, reason) for one sentence ending in its [C..] citations."""
        cites = re.findall(r"\[((?:C\d+)(?:\s*,\s*C\d+)*)\]", sent)
        ids = [i.strip() for grp in cites for i in grp.split(",")]
        body = re.sub(r"\s*\[(?:C\d+)(?:\s*,\s*C\d+)*\]", "", sent).strip()
        claim_objs = [cmap[i] for i in ids if i in cmap]
        if not claim_objs:
            return body, claim_objs, False, "no valid claim cited"
        sd = share_direction_error(body)
        if sd:
            return body, claim_objs, False, sd
        cm = count_mismatch(body) or total_called_rate(body, claim_objs)
        if cm:
            return body, claim_objs, False, cm
        if links_two_channels(body, channel_names):
            return body, claim_objs, False, "links two channels with a movement verb (shifted/moved from X to Y)"
        pm = PAIRING.search(body)
        if pm:
            low = body.lower()
            licensed = any("offset" in c["licenses"] and c.get("pair") and all(g.lower() in low for g in c["pair"]) for c in claim_objs)
            if not licensed:
                return body, claim_objs, False, (f"forbidden wording '{pm.group(0)}': only allowed when an OFFSET claim is cited "
                                                 f"and the sentence names exactly its two channels")
        if not text_ok(body, allowed, pairing_ok=bool(pm)):
            m1 = UNMEASURED_CAUSES.search(body) or (None if pm else PAIRING.search(body))
            if m1:
                return body, claim_objs, False, f"forbidden wording '{m1.group(0)}' (a cause nothing measures, or linking two channels)"
            miss = ", ".join(sorted(n for n in numbers_in(body) if re.fullmatch(r"\d+(?:\.\d+)?", n) and n not in allowed))[:60]
            return body, claim_objs, False, f"figure(s) not in the claims: {miss}"
        ok, why = CL.sentence_supported(body, claim_objs, known_scopes)
        return body, claim_objs, ok, why

    def split(text):
        # keep each sentence's citation attached, whether the model wrote "text. [C1]" or "text [C1]."
        return [m.group(0).strip() for m in re.finditer(
            r".+?[.!?](?:\s*\[[^\]]+\])?(?=\s+[A-Z0-9]|\s*$)|.+?(?:\s*\[[^\]]+\])(?=\s+[A-Z0-9]|\s*$)", text.strip(), re.S)]

    def rewrite(failed):
        """One retry for the rejected sentences: the model is shown why each was rejected and the claims
        it cited, and must write a supported version (or a plainer one). -> {index: new sentence}."""
        if not failed:
            return {}
        payload = {str(k): {"rejected_sentence": v["body"], "reason": v["why"],
                            "cited_claims": [{"id": c["id"], "text": c["text"], "licenses": sorted(c["licenses"])}
                                             for c in v["claims"]]}
                   for k, v in failed.items()}
        try:
            m = client.messages.create(model=MODEL, max_tokens=5000, temperature=TEMPERATURE, messages=[{"role": "user", "content": (
                "Each sentence below was REJECTED by an automatic fact check, for the reason given. Rewrite it so it "
                "passes: keep the analytical point, but use only the figures in the cited claims, drop any comparison "
                "word (largest, only, dominated, above/below average, all, most...) the cited claims do not license for "
                "the entity named, never link two channels, and state no unmeasured cause. Keep its role (an action stays "
                "a verb-first action). End each rewritten sentence with the claim ids it rests on, like [C7]. Return ONLY "
                "a JSON object with the same keys and the rewritten sentences as values.\n\n"
                + json.dumps(payload, ensure_ascii=False, indent=1))}])
            r = next((b.text for b in m.content if hasattr(b, "text")), "")
            return json.loads(friendly(r[r.find("{"): r.rfind("}") + 1]))
        except Exception as e:
            print(f"  Rewrite call failed ({e}).")
            return {}

    def inherit_citations(text):
        """A model sometimes cites once at the end of a group of sentences. Give every uncited sentence
        the citation of the next cited sentence in the same text, so the checker can still validate it."""
        sents = split(text)
        cited = [bool(re.search(r"\[C\d+", x)) for x in sents]
        out = []
        for i, x in enumerate(sents):
            if not cited[i]:
                nxt = next((sents[j] for j in range(i + 1, len(sents)) if cited[j]), None)
                m = re.search(r"\[((?:C\d+)(?:\s*,\s*C\d+)*)\]", nxt) if nxt else None
                if m:
                    x = x.rstrip() + f" [{m.group(1)}]"
            out.append(x)
        return " ".join(out)

    def process(texts, rounds=2):
        """texts: {key: raw text}. Validate sentence by sentence; send rejected ones back up to `rounds`
        times with the reason; whatever still fails is replaced by its cited claim text.
        -> ({key: clean text}, ok, replaced, {key: replaced_count})."""
        parts = {k: [list(validate(x)) + [x] for x in split(inherit_citations(v))] for k, v in texts.items() if isinstance(v, str) and v.strip()}
        for _ in range(rounds):
            failed = {}
            for k, lst in parts.items():
                for idx, (body, cl, ok, why, raw) in enumerate(lst):
                    if not ok and cl:
                        failed[f"{k}#{idx}"] = {"body": body, "why": why, "claims": cl[:3]}
            if not failed:
                break
            redo = rewrite(failed)
            for k, lst in parts.items():
                for idx, item in enumerate(lst):
                    new = redo.get(f"{k}#{idx}")
                    if not item[2] and isinstance(new, str):
                        b2, c2, ok2, w2 = validate(new)
                        if ok2 or c2:
                            lst[idx] = [b2, c2, ok2, w2, new]
        out, ok_n, rep_n, per_key = {}, 0, 0, {}
        for k, lst in parts.items():
            sents, bad = [], 0
            for body, cl, ok, why, raw in lst:
                if ok:
                    sents.append(body); ok_n += 1
                else:
                    rep_n += 1; bad += 1
                    stats["fails"].append((why, body[:130]))
                    if cl:
                        sents.append(" ".join(c["text"] for c in cl[:2]))
            out[k] = " ".join(sents).strip()
            per_key[k] = bad
        return out, ok_n, rep_n, per_key

    texts = {"conclusion": data.get("overall_conclusion"), **{f"nar_{k}": v for k, v in (data.get("narratives") or {}).items()}}
    for i, a in enumerate(data.get("top_actions") or []):
        texts[f"action_{i}"] = a
    for i, w in enumerate(data.get("watch_points") or []):
        texts[f"watch_{i}"] = w
    cleaned, ok_n, rep_n, bad_by_key = process(texts)
    stats["ok"], stats["replaced"] = ok_n, rep_n
    if cleaned.get("conclusion"):
        result["overall_conclusion"] = cleaned["conclusion"]
    VERBS = ("Confirm", "Review", "Check", "Verify", "Compare", "Validate", "Investigate", "Examine", "Audit", "Diagnose", "Assess",
             "Monitor", "Track", "Reconcile", "Break down", "Segment", "Isolate", "Quantify")
    ACTION_BAN = re.compile(r"re-?run|exclud|explicabilit|\bthe model\b|recomput|re-?weight|dedup", re.I)
    model_actions = []
    for i in range(len(data.get("top_actions") or [])):
        t = cleaned.get(f"action_{i}")
        if t and bad_by_key.get(f"action_{i}", 0) == 0 and t.startswith(VERBS) and not ACTION_BAN.search(t):
            model_actions.append(t)
    # each action is judged on its own: a rejected one does not sink the others
    final_actions, spare = list(model_actions[:3]), [a for a in actions_fb]
    while len(final_actions) < 3 and spare:
        final_actions.append(spare.pop(0))
    if final_actions:
        result["top_actions"] = final_actions[:3]
        print(f"  Actions: {len(model_actions[:3])} written by the model and verified, {max(0, len(final_actions[:3]) - len(model_actions[:3]))} from data-built fallbacks.")
    wps = [cleaned.get(f"watch_{i}") for i in range(len(data.get("watch_points") or []))]
    wps = [w for w in wps if w and "moved global ECVR" not in w]

    def tidy_watch(w):
        """A watch point the verifier replaced by raw claim text is rewritten deterministically from the data."""
        m = re.match(r"(MARKET|BU) READ ([^:]+):", w)
        if m:
            sc = next((x for x in fx["scopes"] if x["scope"] == m.group(2) and "totals" in x), None)
            if not sc:
                return w
            t = sc["totals"]
            return (f"{sc['scope']} ECVR moved {t['ecvr_yoy_pct']:+.1f}% on {t['confirmations'][0]:,.0f} to "
                    f"{t['confirmations'][1]:,.0f} BE confirmations"
                    + (": a thin base, read as directional only." if min(t["confirmations"]) < MIN_CONFIRMATIONS else "."))
        m = re.match(r"Model vs GA4 \[([^\]]+)\]: (DIRECTION|SIZE): model ([^ ]+) vs GA4 ([^ .]+(?:\.\d+)?%)", w)
        if m:
            return (f"Model and GA4 disagree on {m.group(1)} {m.group(2).lower()}: model {m.group(3)} vs GA4 {m.group(4)}; "
                    f"worth verifying before relying on either figure.")
        return w
    seen_w, tidy = set(), []
    for w in map(tidy_watch, wps):
        if w not in seen_w:
            seen_w.add(w); tidy.append(w)
    wps = tidy
    rec_wps = [c["short"] for c in K.items if c["scope"] == "recurring" and c.get("short")]
    if wps or rec_wps:
        result["watch_points"] = (wps[:5] if wps else result.get("watch_points", [])[:5]) + rec_wps
    for k in (data.get("narratives") or {}):
        if cleaned.get(f"nar_{k}"):
            result["narratives"][k] = cleaned[f"nar_{k}"]
    for why, body in stats["fails"]:
        print(f"    still replaced after retry — {why} | {body}")
    result["market_sentences"] = market_sentences(fx, ai, client, K, cmap, known_scopes, channel_names, allowed, lambda t: validate(t))
    result["item_sentences"] = item_sentences(fx, ai, K, client, lambda t: validate(t))
    return result, stats["ok"], stats["replaced"]


# ------------------------------------------------------------------ main
BP_RE = re.compile(r"([+\-\u2212]?)(\d+(?:\.\d+)?) ?bp\b")


def bp_to_points(obj):
    """Reader-facing unit: basis points -> percentage points (1 bp = 0.01 pt). Applied ONLY to the finished text, after every
    check has run on the bp figures, so the verification stays exact. Three decimals (a 0.05 bp effect is 0.0005 pt)."""
    if isinstance(obj, str):
        def conv(m):
            v = float(m.group(2)) / 100
            sign = "-" if m.group(1) in ("-", "\u2212") and v else ("+" if m.group(1) == "+" else "")
            return f"{sign}{v:.3f} points"
        return re.sub(r"\bzero bp\b", "zero points", BP_RE.sub(conv, obj))
    if isinstance(obj, list):
        return [bp_to_points(x) for x in obj]
    if isinstance(obj, dict):
        return {k: bp_to_points(v) for k, v in obj.items()}
    return obj


ISENT = {}      # {card key: model-written sentence}, filled in main()


POINTS_AFTER_PCT = re.compile(r"(\d%)\s*\([+\-\u2212]?\d+(?:\.\d+)? points(?: in [^)]*)?\)")
POINTS_AFTER_RANGE = re.compile(r"(\d%) to (\d+(?:\.\d+)?%)\s*[,;]\s*[+\-\u2212]?\d+(?:\.\d+)? points(?: in [A-Za-z\u00c0-\u017f' ]+? (?:own )?(?:ECVR )?units)?")
INTERNAL_NOTE_RE = re.compile(r"\s*\((?:an? )?arithmetic[^()]*\)", re.I)


def strip_internal(obj):
    """Remove the checker's internal notes (e.g. '(arithmetic on the two figures)') from reader-facing text."""
    if isinstance(obj, str):
        return POINTS_AFTER_RANGE.sub(r"\1 to \2", POINTS_AFTER_PCT.sub(r"\1", INTERNAL_NOTE_RE.sub("", obj)))
    if isinstance(obj, list):
        return [strip_internal(x) for x in obj]
    if isinstance(obj, dict):
        return {k: strip_internal(v) for k, v in obj.items()}
    return obj


def funnel_text(fx):
    """One plain sentence on the booking funnel (sessions -> BE entries -> BE confirmations), % changes only, from GA4.
    It says where the weakening is larger (entering the booking engine or inside it) and nothing about causes."""
    k = fx.get("kpis") or {}
    if not (k.get("sessions") and k.get("be_entry_sessions") and k.get("confirmations")):
        return ""
    S, E, C = k["sessions"], k["be_entry_sessions"], k["confirmations"]
    if not (S[0] and E[0] and C[0] and S[1] and E[1]):
        return ""
    rel = lambda a: (a[1] / a[0] - 1) * 100
    entry_step = (E[1] / S[1]) / (E[0] / S[0]) - 1          # entries per session
    inside_step = (C[1] / E[1]) / (C[0] / E[0]) - 1         # confirmations per entry
    grows = rel(E) < rel(S) and rel(C) < rel(E)
    lead = "The loss grows at each step of the funnel" if grows else "Down the funnel"
    where = "inside the booking engine" if inside_step < entry_step else "at the entrance to the booking engine"
    return (f"{lead} (sessions {pct(rel(S))}, booking-engine entries {pct(rel(E))}, confirmations {pct(rel(C))}), "
            f"and the weakening is larger {where}.")


def standing_watch(fx):
    """INTENTIONAL watch point (user decision): the standing error is reported every month, whatever the model proposes."""
    st = fx.get("standing") or {}
    g = next((x for x in st.get("scopes", []) if x["scope"] == "Global"), None)
    if not g:
        return None
    e, S = g["with_error"], g["sessions"]
    r0, r1 = e[0] / S[0], e[1] / S[1]
    bus = [x for x in st["scopes"] if x["scope"] != "Global" and x["sessions"][0] and x["sessions"][1] and x["with_error"][0]]
    bus.sort(key=lambda x: x["with_error"][1] / x["sessions"][1], reverse=True)
    detail = ""
    if bus:
        top = bus[0]
        detail = (f" It is highest in {top['scope']}, where {top['with_error'][1] / top['sessions'][1]:.2%} of sessions "
                  f"saw it ({top['with_error'][0] / top['sessions'][0]:.2%} a year earlier).")
    return (f"Intentional watch point: {st['label']} errors on the price check appeared in {e[1]:,.0f} sessions against {e[0]:,.0f} a year earlier "
            f"({pct((e[1] / e[0] - 1) * 100)}), i.e. {r1:.2%} of sessions against {r0:.2%}.{detail} This item is tracked every month by design, "
            f"independently of the explicability model; its link to the ECVR change is not measured here.")


def main():
    for p in (FORENSICS, ANALYSIS):
        if not p.exists():
            sys.exit(f"{p} not found — run filter_results.py and forensics.py first.")
    fx = json.load(open(FORENSICS, encoding="utf-8"))
    ai = json.load(open(ANALYSIS, encoding="utf-8"))
    g = next(s for s in fx["scopes"] if s["level"] == "global")
    global ISENT
    words, ok, bad = wording(fx, ai)
    ISENT = words.get("item_sentences", {})
    print(f"  Wording: {ok} sentence(s) verified against their cited claims, {bad} replaced by the claim text.")
    nar = words["narratives"]
    msent = words.get("market_sentences", {})
    negl = [c for c in fx.get("lead_checks", []) if c.get("status") == "GA4 contribution negligible"]
    unchk = [c for c in fx.get("lead_checks", []) if str(c.get("status", "")).startswith("not checkable")]
    other_note = (f"{len(negl)} further model channel lead(s) have a negligible GA4 contribution "
                  f"(under {NEGLIGIBLE_BP / 100:.4f} points) and {len(unchk)} could not be checked; they are not listed.")
    rs = resort_block(fx, ai)
    bu_sec = bu_items(fx, None, msent)
    out = {
        "analysis_period": fx["period"].replace(" vs ", " vs "),
        "funnel_summary": funnel_text(fx),
        "top_actions": words["top_actions"],
        "overall_conclusion": words["overall_conclusion"],
        "device_section_global": {"narrative": nar.get("device") or "Device effects below split each device's change into its own conversion (rate) and its traffic share (mix), in basis points.",
                                  "items": device_items(g["by_device"])},
        "channel_section_global": {"narrative": nar.get("channel") or "Channels ranked by their effect on global ECVR BE, in basis points.",
                                   "items": channel_items(g["by_channel"]) + property_wide_items(fx, ai)},
        "bu_section": {"narrative": nar.get("bu") or "Each Business Unit's change in ECVR BE on GA4; discrepancies with the explicability model are flagged.",
                       "items": bu_sec},
        "bu_focus": bu_focus(fx, ai, msent),
        "crossover_section": {"narrative": nar.get("crossover") or "Each focus market's own largest channel effects on its ECVR BE.",
                              "items": crossover_items(fx, ai, msent)},
        "resort_section": {"positive": {"narrative": nar.get("resort_positive") or rs["positive"]["narrative"], "items": rs["positive"]["items"]},
                           "negative": {"narrative": nar.get("resort_negative") or rs["negative"]["narrative"], "items": rs["negative"]["items"]}},
        "other_signals_section": {"narrative": "Model signals and channel leads that GA4 confirms or contradicts. " + other_note,
                                  "items": other_items(fx, ai)},
        "watch_points": words["watch_points"] + ([standing_watch(fx)] if standing_watch(fx) else []),
        "generated_by_model": "ECVR-forensics v2 (figures: code + GA4; wording: Sonnet 4.6, checked)",
    }
    out = strip_internal(bp_to_points(out))
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"Composed: {OUTPUT}")


if __name__ == "__main__":
    main()
