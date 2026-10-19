"""
ECVR-forensics v2 — Step A: code-computed decomposition + model-vs-GA4 cross-check.

The explicability model only proposes LEADS (which variables / markets / channels to look at).
This script turns the facts into numbers, with no LLM involved:

  1. For every scope (Global, each Business Unit, each BU-focus market) it pulls live GA4
     sessions and BE confirmations by Custom Channel Group and by device, current vs prior year.
  2. It splits the change in that scope's ECVR BE into a MIX effect (traffic share moved) and a
     RATE effect (the group's own conversion moved), per channel and per device, in basis points.
     Components add up exactly to the scope's total change.
  3. It cross-checks every model lead against that GA4 result and FLAGS any discrepancy:
       - BU / market: sign (and size gap) of the model's ECVR YoY vs GA4's.
       - channel_<slug> variable rows: the model's impact direction vs the sign of that channel's
         GA4 contribution in that market.

Nothing in here names a market, channel or month: scopes, groups and leads all come from
analysis_input.json and GA4. Output: forensics_output.json (+ a console summary).
"""
import json
import os
import sys
from pathlib import Path

from google.analytics.data_v1beta.types import (
    Dimension, Filter, FilterExpression, FilterExpressionList, Metric, RunReportRequest,
)

import deepdive as dd   # reuses the GA4 client, credentials and query helpers (same folder)

DOWNLOADS = Path(os.environ.get("ECVR_DOWNLOADS_DIR", r"/mnt/c/Users/xxxxx/Downloads"))
INPUT_JSON = DOWNLOADS / "analysis_input.json"
OUTPUT_JSON = DOWNLOADS / "forensics_output.json"

# Structural thresholds (not tied to any month):
MIN_COMPONENT_BP = 0.05     # a channel/device contribution below this is "negligible", not a direction
GAP_REL_PTS = 10.0          # model vs GA4 ECVR YoY differing by more than this many points is flagged
                            # (variables and resorts use twice this, their YoYs are noisier)
MIN_CONFIRMATIONS = 50      # GA4 confirmations under this on either side => rate is fragile (flagged)
TOP_COMPONENTS = 6          # components kept per scope in the console summary
CTX_TOP = 8                 # model variables (by weight) that get their market's sessions / confirmations as context

# INTENTIONAL watch item (user decision, 2026-10-14): tracked every month whatever the model proposes. It is the one
# thing in v2 that is named in code on purpose; the report labels it as such. Event / detail value as defined in deepdive.py.
STANDING_ERROR = {"label": "NO_TRANSPORT", "event": "click_price_remote", "detail": "NO_TRANSPORT"}


def _tot(groups: dict, key: str) -> float:
    return sum(v.get(key, 0) or 0 for v in groups.values())


def _decompose(cur: dict, pri: dict, key_s="sessions", key_c="be_confirmation") -> dict:
    """Mix/rate split of the change in blended ECVR across the keys of cur/pri.
      rate_g = share1_g * (e1_g - e0_g)                  the group's OWN conversion moved
      mix_g  = (share1_g - share0_g) * (e0_g - E0)       its traffic share moved, CENTRED on the
                                                         scope's prior blended ECVR (E0)
    Centring matters: shares sum to 1, so traffic a group loses goes to the others. A group that
    converts BELOW the scope average and loses share therefore RAISES the blended rate (positive
    mix), and one that converts above the average and loses share lowers it. Without centring a
    group's share loss is charged at its own full rate, which overstates drags for high-converting
    groups and hides gains for low-converting ones. The components still add up exactly to the
    scope's total change (sum of share changes is zero)."""
    S1, S0 = _tot(cur, key_s), _tot(pri, key_s)
    C1, C0 = _tot(cur, key_c), _tot(pri, key_c)
    if not S1 or not S0:
        return {}
    E0_ALL = C0 / S0
    rows = []
    for g in set(cur) | set(pri):
        s1 = (cur.get(g, {}).get(key_s, 0) or 0)
        s0 = (pri.get(g, {}).get(key_s, 0) or 0)
        c1 = (cur.get(g, {}).get(key_c, 0) or 0)
        c0 = (pri.get(g, {}).get(key_c, 0) or 0)
        sh1, sh0 = s1 / S1, s0 / S0
        e1 = c1 / s1 if s1 else 0.0
        e0 = c0 / s0 if s0 else 0.0
        mix = (sh1 - sh0) * (e0 - E0_ALL)
        rate = sh1 * (e1 - e0)
        rows.append({
            "group": g,
            "sessions": [s0, s1], "confirmations": [c0, c1],
            "share": [sh0, sh1], "ecvr": [e0, e1],
            "mix_bp": mix * 1e4, "rate_bp": rate * 1e4, "total_bp": (mix + rate) * 1e4,
            "thin_base": min(c0, c1) < MIN_CONFIRMATIONS,
        })
    rows.sort(key=lambda r: -abs(r["total_bp"]))
    e0_all, e1_all = C0 / S0, C1 / S1
    return {
        "totals": {
            "sessions": [S0, S1], "confirmations": [C0, C1], "ecvr": [e0_all, e1_all],
            "ecvr_yoy_pct": ((e1_all / e0_all - 1) * 100) if e0_all else None,
            "delta_bp": (e1_all - e0_all) * 1e4,
        },
        "components": rows,
        "sum_check_bp": sum(r["total_bp"] for r in rows),
    }


def _device_view(dev: dict, totals: dict) -> list:
    """Device decomposition. Only analysed devices are returned by GA4 (others excluded), so the
    remainder (other devices) is reported as its own component to keep the sum exact."""
    cur = {d: {"sessions": v.get("sessions", 0), "be_confirmation": v.get("be_confirmation", 0)}
           for d, v in dev.get("current", {}).items()}
    pri = {d: {"sessions": v.get("sessions", 0), "be_confirmation": v.get("be_confirmation", 0)}
           for d, v in dev.get("prior", {}).items()}
    # The channel-group totals and the device totals come from two separate GA4 queries and can
    # differ slightly (a few sessions) in either direction. The device view is decomposed on the
    # DEVICE totals themselves, with other devices as the remainder when the channel total is
    # larger, so its components always add up to the device-based total change. When the two
    # totals differ, that device-based change is reported in "device_total_bp" for transparency.
    S1, S0 = totals["sessions"][1], totals["sessions"][0]
    C1, C0 = totals["confirmations"][1], totals["confirmations"][0]
    rem_s1, rem_s0 = S1 - _tot(cur, "sessions"), S0 - _tot(pri, "sessions")
    rem_c1, rem_c0 = C1 - _tot(cur, "be_confirmation"), C0 - _tot(pri, "be_confirmation")
    if min(rem_s1, rem_s0, rem_c1, rem_c0) >= 0:
        cur["other devices"] = {"sessions": rem_s1, "be_confirmation": rem_c1}
        pri["other devices"] = {"sessions": rem_s0, "be_confirmation": rem_c0}
    return _decompose(cur, pri).get("components", [])


def analyse_scope(client, label: str, level: str, countries) -> dict:
    ch = dd.query_channel_group_breakdown(client, countries=countries)
    if "error" in ch.get("current", {}) or "error" in ch.get("prior", {}):
        return {"scope": label, "level": level, "error": str(ch)}
    # Sessions summed over (channel group x country) rows overcount: a session counted under several rows is counted
    # several times (+0.6% / +3.0% property-wide this period). The scope's sessions are the deduplicated GA4 total for that
    # scope; every group's sessions are scaled by the same factor so shares add up to 1 and totals match GA4.
    tot = ga4_scope_sessions(client, countries)
    scale = {}
    for key, i in (("prior", 0), ("current", 1)):
        rs = sum(v["sessions"] for v in ch[key].values())
        scale[key] = (tot[i] / rs) if rs and tot[i] else 1.0
        for v in ch[key].values():
            v["sessions"] = round(v["sessions"] * scale[key])
            v["ecvr_be"] = v["be_confirmation"] / v["sessions"] if v["sessions"] else None
    dec = _decompose(ch["current"], ch["prior"])
    if not dec:
        return {"scope": label, "level": level, "error": "no sessions in one period"}
    dev = dd.query_device_split(client, countries=countries)
    for key in ("prior", "current"):
        for v in (dev.get(key) or {}).values():
            if isinstance(v, dict) and "sessions" in v:
                v["sessions"] = round(v["sessions"] * scale[key])
    by_dev = [] if ("error" in dev.get("current", {}) or "error" in dev.get("prior", {})) else _device_view(dev, dec["totals"])
    return {"scope": label, "level": level, "totals": dec["totals"], "by_channel": dec["components"],
            "by_device": by_dev, "sum_check_bp": dec["sum_check_bp"],
            # change implied by the device query's own totals; differs from totals.delta_bp only
            # when the two GA4 queries disagree by a few sessions
            "device_total_bp": sum(c["total_bp"] for c in by_dev) if by_dev else None,
            "session_scale": scale}


def _sf(field: str, value: str, contains: bool = False) -> FilterExpression:
    mt = Filter.StringFilter.MatchType.CONTAINS if contains else Filter.StringFilter.MatchType.EXACT
    return FilterExpression(filter=Filter(field_name=field, string_filter=Filter.StringFilter(value=value, match_type=mt)))


def _and(*exprs) -> FilterExpression:
    exprs = [e for e in exprs if e is not None]
    return exprs[0] if len(exprs) == 1 else FilterExpression(and_group=FilterExpressionList(expressions=exprs))


def ga4_scope_sessions(client, countries, event=None, detail=None) -> list:
    """[prior, current] DEDUPLICATED GA4 sessions of a scope (a list of GA4 country names, or None = whole property),
    optionally only the sessions in which `event` fired (with a detail_click value containing `detail`)."""
    exprs = []
    if countries:
        exprs.append(FilterExpression(filter=Filter(field_name="country",
                                                    in_list_filter=Filter.InListFilter(values=list(countries)))))
    if event:
        exprs.append(_sf("eventName", event))
    if detail:
        exprs.append(_sf("customEvent:detail_click", detail, contains=True))
    flt = (_and(*exprs) if exprs else None)
    out = []
    for dr in (dd.DATE_RANGE_PRIOR, dd.DATE_RANGE_CURRENT):
        resp = client.run_report(RunReportRequest(property=f"properties/{dd.GA4_PROPERTY_ID}", metrics=[Metric(name="sessions")],
                                                  date_ranges=[dr], dimension_filter=flt))
        out.append(int(float(resp.rows[0].metric_values[0].value)) if resp.rows else 0)
        dd.time.sleep(dd.GA4_REQUEST_DELAY_S)
    return out


def ga4_scope_events(client, countries, event) -> list:
    """[prior, current] GA4 event count of `event` for a scope (GA4 country names, or None = whole property)."""
    exprs = [_sf("eventName", event)]
    if countries:
        exprs.append(FilterExpression(filter=Filter(field_name="country",
                                                    in_list_filter=Filter.InListFilter(values=list(countries)))))
    out = []
    for dr in (dd.DATE_RANGE_PRIOR, dd.DATE_RANGE_CURRENT):
        resp = client.run_report(RunReportRequest(property=f"properties/{dd.GA4_PROPERTY_ID}", metrics=[Metric(name="eventCount")],
                                                  date_ranges=[dr], dimension_filter=_and(*exprs)))
        out.append(int(float(resp.rows[0].metric_values[0].value)) if resp.rows else 0)
        dd.time.sleep(dd.GA4_REQUEST_DELAY_S)
    return out


def ga4_by_resort(client, event_name: str) -> dict:
    """{period: {resort_code: eventCount}} for one event, one request per period."""
    out = {}
    for key, dr in (("current", dd.DATE_RANGE_CURRENT), ("prior", dd.DATE_RANGE_PRIOR)):
        resp = client.run_report(RunReportRequest(
            property=f"properties/{dd.GA4_PROPERTY_ID}", dimensions=[Dimension(name="customEvent:resort_code")],
            metrics=[Metric(name="eventCount")], date_ranges=[dr], limit=100000,
            dimension_filter=_sf("eventName", event_name)))
        out[key] = {r.dimension_values[0].value: int(float(r.metric_values[0].value)) for r in resp.rows}
    return out


def ga4_sessions_with_event(client, event_name: str) -> list:
    """[prior, current] number of SESSIONS in which `event_name` fired (property-wide)."""
    out = []
    for dr in (dd.DATE_RANGE_PRIOR, dd.DATE_RANGE_CURRENT):
        resp = client.run_report(RunReportRequest(
            property=f"properties/{dd.GA4_PROPERTY_ID}", metrics=[Metric(name="sessions")],
            date_ranges=[dr], dimension_filter=_sf("eventName", event_name)))
        out.append(int(float(resp.rows[0].metric_values[0].value)) if resp.rows else 0)
        dd.time.sleep(dd.GA4_REQUEST_DELAY_S)
    return out


def resort_total(by: dict, code: str, period: str) -> int:
    """Sum GA4 rows of a resort including season-suffixed variants (<CODE>_<SEASON>)."""
    return sum(v for k, v in by[period].items() if k == code or k.startswith(code + "_"))


def ga4_variable_counts(client, variable: str, site: str):
    """(prior, current) GA4 event counts for a model variable, using deepdive's own
    variable->GA4 mapping; None when the variable has no usable mapping or site is a rollup."""
    if site.lower() in ("asia", "other"):
        return None
    mapping = dd.variable_to_dimension(variable)
    if not mapping or mapping.get("metric") or (mapping.get("dimension") is None):
        return None
    if mapping["dimension"] == "eventName":
        event, custom = mapping["value"], None
    else:
        event, custom = mapping.get("event_filter"), (mapping["dimension"], mapping["value"])
    if not event:
        return None
    vals = []
    for dr in (dd.DATE_RANGE_PRIOR, dd.DATE_RANGE_CURRENT):
        flt = _and(_sf("eventName", event),
                   _sf(custom[0], custom[1], contains=True) if custom else None,
                   _sf("country", dd.to_ga4_country(site)) if site.lower() != "global" else None)
        resp = client.run_report(RunReportRequest(
            property=f"properties/{dd.GA4_PROPERTY_ID}", metrics=[Metric(name="eventCount")],
            date_ranges=[dr], dimension_filter=flt))
        vals.append(int(float(resp.rows[0].metric_values[0].value)) if resp.rows else 0)
        dd.time.sleep(dd.GA4_REQUEST_DELAY_S)
    return vals[0], vals[1]


def slug_to_group(slug: str, groups) -> str | None:
    for g in groups:
        if g.lower().replace(" ", "_") == slug:
            return g
    return None


def main():
    if not INPUT_JSON.exists():
        sys.exit(f"{INPUT_JSON} not found — run filter_results.py first.")
    data = json.load(open(INPUT_JSON, encoding="utf-8"))
    dd.DATE_RANGE_CURRENT, dd.DATE_RANGE_PRIOR, lab_c, lab_p = dd.derive_date_ranges(data)
    client = dd.BetaAnalyticsDataClient(credentials=dd.get_ga4_credentials())
    meta = data["meta"]
    bu_map = meta.get("bu_markets_map", {})

    scopes = []
    print("Global...")
    scopes.append(analyse_scope(client, "Global", "global", None))
    for bu_row in data.get("bu_breakdown", []):
        bu = bu_row["business_unit"]
        print(f"BU {bu}...")
        s = analyse_scope(client, bu, "bu", sorted({dd.to_ga4_country(m) for m in bu_map.get(bu, [])}))
        s["model"] = {"ecvr_yoy_pct": (bu_row.get("pct_change") or 0) * 100, "impact": bu_row.get("impact_on_ECVR_BE")}
        scopes.append(s)
    seen_markets = set()
    for bu, markets in data.get("top_countries_per_bu", {}).items():
        for m in markets:
            site = m["site"]
            print(f"Market {site} ({bu})...")
            s = analyse_scope(client, site, "market", [dd.to_ga4_country(site)])
            s["business_unit"] = bu
            s["model"] = {"ecvr_yoy_pct": (m.get("pct_change") or 0) * 100 if m.get("pct_change") is not None else None,
                          "impact": None}
            scopes.append(s)
            seen_markets.add(site)

    # ---- BU contribution to the GLOBAL change (BUs + the residual of unmapped markets = exact)
    g_scope = scopes[0]
    bu_contribution = []
    if "totals" in g_scope:
        cur, pri = {}, {}
        for s in scopes:
            if s["level"] == "bu" and "totals" in s:
                cur[s["scope"]] = {"sessions": s["totals"]["sessions"][1], "be_confirmation": s["totals"]["confirmations"][1]}
                pri[s["scope"]] = {"sessions": s["totals"]["sessions"][0], "be_confirmation": s["totals"]["confirmations"][0]}
        gt = g_scope["totals"]
        rs1, rs0 = gt["sessions"][1] - _tot(cur, "sessions"), gt["sessions"][0] - _tot(pri, "sessions")
        rc1, rc0 = gt["confirmations"][1] - _tot(cur, "be_confirmation"), gt["confirmations"][0] - _tot(pri, "be_confirmation")
        if min(rs1, rs0, rc1, rc0) >= 0:
            cur["Unmapped markets"] = {"sessions": rs1, "be_confirmation": rc1}
            pri["Unmapped markets"] = {"sessions": rs0, "be_confirmation": rc0}
        bu_contribution = _decompose(cur, pri).get("components", [])

    # ---- resorts: GA4 views / BE entries / BE confirmations per resort (prefix-matched)
    print("Resorts (GA4)...")
    resort_checks = []
    res_views, res_entry, res_conf = (ga4_by_resort(client, e) for e in ("Resort", "BE_Entry", "BE_Confirmation"))
    for r in data.get("top_resorts_positive", []) + data.get("top_resorts_negative", []):
        code = r["variable"][len("resort_view_"):]
        v = [resort_total(res_views, code, p) for p in ("prior", "current")]
        e = [resort_total(res_entry, code, p) for p in ("prior", "current")]
        c = [resort_total(res_conf, code, p) for p in ("prior", "current")]
        g_yoy = (v[1] / v[0] - 1) * 100 if v[0] else None
        m_yoy = (r.get("variation") * 100) if r.get("variation") is not None else None
        status = "not comparable"
        if g_yoy is not None and m_yoy is not None:
            status = ("DISCREPANCY" if ((g_yoy > 0) != (m_yoy > 0) and abs(g_yoy) > 5 and abs(m_yoy) > 5)
                      or abs(g_yoy - m_yoy) > GAP_REL_PTS * 2 else "confirmed")
        resort_checks.append({"variable": r["variable"], "views": v, "entries": e, "confirmations": c,
                              "ga4_views_yoy_pct": g_yoy, "model_views_yoy_pct": m_yoy, "status": status})

    # ---- model generic variables (non-channel) vs GA4 event counts
    print("Model variables (GA4)...")
    variable_checks = []
    for r in data.get("bucket_1_top_ranked", []):
        if r["variable"].startswith("channel_"):
            continue
        res = ga4_variable_counts(client, r["variable"], r["site"])
        chk = {"variable": r["variable"], "site": r["site"], "model_yoy_pct": (r["variation"] or 0) * 100,
               "model_impact": r.get("impact_on_ECVR_BE"), "model_abs_weight": r.get("absolute_weighted_importance")}
        if res is None or res[0] == 0:
            chk["status"] = "not checkable"
        else:
            g = (res[1] / res[0] - 1) * 100
            chk.update({"ga4_counts": [res[0], res[1]], "ga4_yoy_pct": g})
            m = chk["model_yoy_pct"]
            chk["status"] = ("DISCREPANCY" if ((g > 0) != (m > 0) and abs(g) > 10 and abs(m) > 10)
                             or abs(g - m) > GAP_REL_PTS * 2 else "confirmed")
        variable_checks.append(chk)
        if chk["status"] == "DISCREPANCY":
            discrepancies.append({"scope": r["site"], "level": "variable", "flag":
                                  f"{r['variable']}: model {chk['model_yoy_pct']:+.0f}% vs GA4 {chk['ga4_yoy_pct']:+.0f}%"})

    # ---- market context for the strongest model variables: what the market's own sessions / confirmations did, so a
    # signal ("offer-page views +45%") can be read against its outcome
    ctx_cache = {s_["scope"]: {"sessions": s_["totals"]["sessions"], "confirmations": s_["totals"]["confirmations"]}
                 for s_ in scopes if "totals" in s_}
    ranked_vars = sorted((c for c in variable_checks if c["status"] != "not checkable"),
                         key=lambda c: -(c.get("model_abs_weight") or 0))
    for chk in ranked_vars[:CTX_TOP]:
        site = chk["site"]
        if site.lower() in ("asia", "other"):
            continue
        if site not in ctx_cache:
            ctry = None if site.lower() == "global" else [dd.to_ga4_country(site)]
            ctx_cache[site] = {"sessions": ga4_scope_sessions(client, ctry),
                               "confirmations": ga4_scope_events(client, ctry, "BE_Confirmation")}
        chk["ctx"] = ctx_cache[site]

    # ---- cross-check 1: model ECVR YoY vs GA4 ECVR YoY per BU / market
    discrepancies = []
    for s in scopes:
        if "model" not in s or "totals" not in s:
            continue
        m, g = s["model"]["ecvr_yoy_pct"], s["totals"]["ecvr_yoy_pct"]
        fl = []
        if m is not None and g is not None:
            if (m > 0) != (g > 0) and abs(m) > 0.5 and abs(g) > 0.5:
                fl.append(f"DIRECTION: model {m:+.1f}% vs GA4 {g:+.1f}%")
            elif abs(m - g) > GAP_REL_PTS:
                fl.append(f"SIZE: model {m:+.1f}% vs GA4 {g:+.1f}% (gap {abs(m - g):.1f} pts)")
        if min(s["totals"]["confirmations"]) < MIN_CONFIRMATIONS:
            fl.append(f"THIN BASE: GA4 confirmations {s['totals']['confirmations'][0]:,.0f} -> {s['totals']['confirmations'][1]:,.0f}")
        s["flags"] = fl
        for f in fl:
            discrepancies.append({"scope": s["scope"], "level": s["level"], "flag": f})

    # ---- cross-check 2: each model channel_<slug> lead vs the GA4 contribution of that channel
    cache = {s["scope"]: s for s in scopes}
    lead_checks = []
    leads = [r for k in ("bucket_1_top_ranked", "bucket_3_emerging") for r in data.get(k, [])
             if r["variable"].startswith("channel_")]
    for r in leads:
        site = r["site"]
        if site.lower() in ("asia", "other"):
            lead_checks.append({"variable": r["variable"], "site": site, "status": "not checkable (rollup site)"})
            continue
        if site not in cache:
            print(f"Lead scope {site}...")
            cache[site] = analyse_scope(client, site, "market", None if site.lower() == "global" else [dd.to_ga4_country(site)])
        sc = cache[site]
        if "by_channel" not in sc:
            lead_checks.append({"variable": r["variable"], "site": site, "status": "not checkable (no GA4 data)"})
            continue
        grp = slug_to_group(r["variable"][len("channel_"):], [c["group"] for c in sc["by_channel"]])
        comp = next((c for c in sc["by_channel"] if c["group"] == grp), None)
        if not comp:
            lead_checks.append({"variable": r["variable"], "site": site, "status": "not checkable (channel absent in GA4)"})
            continue
        model_dir = (r.get("impact_on_ECVR_BE") or "").lower()
        bp = comp["total_bp"]
        if abs(bp) < MIN_COMPONENT_BP:
            status = "GA4 contribution negligible"
        elif (bp > 0) == (model_dir == "positive"):
            status = "confirmed"
        elif comp["thin_base"]:
            status = "DISCREPANCY (thin GA4 base - likely noise)"
        else:
            status = "DISCREPANCY"
        chk = {"variable": r["variable"], "site": site, "model_direction": model_dir,
               "model_abs_weight": r.get("absolute_weighted_importance"),
               "ga4_contribution_bp": bp, "ga4_mix_bp": comp["mix_bp"], "ga4_rate_bp": comp["rate_bp"],
               "ga4_confirmations": comp["confirmations"], "thin_base": comp["thin_base"],
               "ga4_share": comp["share"], "ga4_sessions": comp["sessions"], "ga4_ecvr": comp["ecvr"],
               "extreme_yoy_in_model": bool(r.get("extreme_yoy")), "status": status}
        lead_checks.append(chk)
        if status == "DISCREPANCY":
            discrepancies.append({"scope": site, "level": "lead", "flag":
                                  f"{r['variable']}: model says {model_dir}, GA4 contribution {bp:+.2f} bp"})

    # ---- headline KPIs from GA4 (what the KPI bars show): sessions, BE entry rate, ECVR BE
    print("Headline KPIs (GA4)...")
    kpis = {}
    if "totals" in g_scope:
        gt = g_scope["totals"]
        entry = ga4_sessions_with_event(client, "BE_Entry")
        kpis = {"sessions": gt["sessions"], "confirmations": gt["confirmations"], "be_entry_sessions": entry,
                "be_entry_rate": [entry[0] / gt["sessions"][0] if gt["sessions"][0] else None,
                                  entry[1] / gt["sessions"][1] if gt["sessions"][1] else None],
                "ecvr": gt["ecvr"]}

    # ---- intentional watch item: sessions with the STANDING_ERROR, global and per Business Unit
    print(f"Standing watch item ({STANDING_ERROR['label']})...")
    st = {"label": STANDING_ERROR["label"], "event": STANDING_ERROR["event"], "scopes": []}
    by_scope = {s_["scope"]: s_ for s_ in scopes if "totals" in s_}
    targets = [("Global", None)] + [(r["business_unit"], sorted({dd.to_ga4_country(m) for m in bu_map.get(r["business_unit"], [])}))
                                    for r in data.get("bu_breakdown", [])]
    for name, ctry in targets:
        if name not in by_scope:
            continue
        with_err = ga4_scope_sessions(client, ctry, STANDING_ERROR["event"], STANDING_ERROR["detail"])
        st["scopes"].append({"scope": name, "sessions": by_scope[name]["totals"]["sessions"], "with_error": with_err})

    out = {"period": f"{lab_c} vs {lab_p}", "kpis": kpis, "standing": st, "scopes": scopes, "bu_contribution": bu_contribution,
           "resort_checks": resort_checks, "variable_checks": variable_checks,
           "lead_checks": lead_checks, "discrepancies": discrepancies}
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False, default=str)

    # ---- console summary
    print(f"\n=== {out['period']} ===")
    for s in scopes:
        if "totals" not in s:
            print(f"{s['scope']}: {s.get('error')}")
            continue
        t = s["totals"]
        print(f"\n[{s['level']}] {s['scope']}: ECVR {t['ecvr'][0]*100:.3f}% -> {t['ecvr'][1]*100:.3f}% "
              f"({t['ecvr_yoy_pct']:+.1f}%, {t['delta_bp']:+.2f} bp) | sessions {t['sessions'][0]:,.0f} -> {t['sessions'][1]:,.0f}"
              + (f" | model {s['model']['ecvr_yoy_pct']:+.1f}%" if s.get('model') and s['model']['ecvr_yoy_pct'] is not None else ""))
        if s["level"] in ("global", "bu"):
            for c in s["by_channel"][:TOP_COMPONENTS]:
                print(f"    {c['group']:<24} mix {c['mix_bp']:+7.2f}  rate {c['rate_bp']:+7.2f}  total {c['total_bp']:+7.2f} bp"
                      f"{'  (thin base)' if c['thin_base'] else ''}")
            for c in s["by_device"]:
                print(f"    device {c['group']:<17} mix {c['mix_bp']:+7.2f}  rate {c['rate_bp']:+7.2f}  total {c['total_bp']:+7.2f} bp")
        for f in s.get("flags", []):
            print(f"    ⚑ {f}")
    print("\n=== channel leads (model vs GA4) ===")
    for c in lead_checks:
        extra = (f"model {c['model_direction']} | GA4 {c['ga4_contribution_bp']:+.2f} bp (mix {c['ga4_mix_bp']:+.2f}, rate {c['ga4_rate_bp']:+.2f})"
                 f"{' | thin base' if c.get('thin_base') else ''}{' | extreme YoY in model' if c.get('extreme_yoy_in_model') else ''}") if "model_direction" in c else ""
        print(f"  {c['status']:<28} {c['variable']:<36} {c['site']:<14} {extra}")
    print(f"\n{len(discrepancies)} discrepancy flag(s). Output: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
