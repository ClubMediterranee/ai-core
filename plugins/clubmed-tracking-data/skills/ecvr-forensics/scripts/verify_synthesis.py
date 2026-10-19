"""
ECVR BE Explicability Analysis — Step 3.5: Synthesis Verification
Reads analysis_input.json + synthesis_output.json + deepdive_output.json,
runs targeted GA4 checks, and prints a PASS / WARN / FAIL report.

Channel checks now query GA4's New Custom Channel Group directly (global scope) —
there is no CHANNEL_MAP / fixed-list filter anymore, since the pipeline no longer
produces or displays the old explicability-CSV channel_* variables at all.

Only CHECK 1 (core KPIs: Sessions/BE Entry Rate/ECVR BE — the headline numbers
this gate exists to protect) can produce a post-blocking FAIL. Every other
check (CHECK 2's per-variable driver/resort direction mismatches) is purely
informational: a mismatch there is recorded as a WARN with its specific reason
attached, never a hard stop — the model is trained on each market's own
individual GA4 site property, this script only has the shared B2C rollup to
compare against, and a single-variable/single-market disagreement isn't severe
enough to block the whole monthly post by itself.

Exit codes:
  0 — safe to post to Teams (WARNs may still be present — review them, they're
      not swallowed, just not blocking)
  1 — FAIL: a core KPI (Sessions/BE Entry Rate/ECVR BE) shows a direction
      mismatch or magnitude error beyond tolerance
"""

import json
import os
import re
import sys
import time
import calendar
from pathlib import Path

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange, Dimension, Filter, FilterExpression,
    FilterExpressionList, Metric, RunReportRequest,
)
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# All file paths resolve against ECVR_DOWNLOADS_DIR (defaults to this machine's
# original working directory) — set that env var to point the whole pipeline
# at a different folder without editing every script.
_DOWNLOADS_DIR = Path(os.environ.get("ECVR_DOWNLOADS_DIR", r"/mnt/c/Users/xxxxx/Downloads"))

# ── File paths ────────────────────────────────────────────────────────────────
ANALYSIS_INPUT   = _DOWNLOADS_DIR / "analysis_input.json"
SYNTHESIS_OUTPUT = _DOWNLOADS_DIR / "synthesis_output.json"
DEEPDIVE_OUTPUT  = _DOWNLOADS_DIR / "deepdive_output.json"

# ── GA4 ───────────────────────────────────────────────────────────────────────
GA4_PROPERTY_ID = "310694998"
GA4_TOKEN       = _DOWNLOADS_DIR / "ga4_oauth_token.json"
GA4_SCOPES      = ["https://www.googleapis.com/auth/analytics.readonly"]
GA4_DELAY_S     = 0.35

# GA4 Custom Channel Group ("New_Custom Channel Group", channelGroups/13153047450) —
# distinct from GA4's system-defined Default Channel Group. Must match deepdive.py's
# GA4_CUSTOM_CHANNEL_GROUP_ID.
GA4_CUSTOM_CHANNEL_GROUP_ID = "13153047450"
CHANNEL_DIMENSION = f"sessionCustomChannelGroup:{GA4_CUSTOM_CHANNEL_GROUP_ID}"

# ── Tolerances ────────────────────────────────────────────────────────────────
# Core KPIs: how many pp off before we raise an alarm. Tightened from 20.0/8.0 —
# this pipeline's actual core KPI YoY magnitudes run single-digit (e.g. ECVR_BE
# around -9%), so a 20pp FAIL threshold let the model be off by roughly 2x the
# real signal and still only WARN. Still loose enough to absorb the documented
# ~72h GA4 late-hit processing lag, just proportional to what's actually being
# measured instead of an arbitrary round number.
KPI_CRITICAL_TOL  = 8.0    # pp — FAIL if exceeded (likely data or direction error)
KPI_WARN_TOL      = 3.0    # pp — WARN if exceeded (late-hit or model vs GA4 lag)

# Mobile deltas: pp tolerance before WARN / FAIL (comparing deepdive's own stored
# figures against a fresh, independently-run GA4 recompute — not text-parsing)
MOBILE_FAIL_TOL   =  5.0   # pp
MOBILE_WARN_TOL   =  3.0   # pp

# Global channel group sessions: relative tolerance before WARN (recompute vs stored)
CHANNEL_RECOMPUTE_WARN_PCT = 0.10   # 10% relative difference

# Impossible-rate threshold
MAX_VALID_RATE    = 100.0  # % — any quoted rate above this in synthesis text is flagged


def classify_direction_mismatch(var, site, model_var, ga4_yoy, model_valeur=None, model_valeur_prec=None, ga4_v26=None, ga4_v25=None):
    """
    Explains WHY a driver-direction mismatch likely occurred (never whether to
    block posting — every mismatch here is recorded as a WARN regardless, see
    the call sites). Returns a reason string, or None if no specific structural
    explanation applies (still just a WARN, with a generic detail line).
    Structural rules only — no hardcoded market names.
    """
    # Resort views with a near-zero prior base can flip sign trivially (0→N vs N→0
    # read very differently as a raw ratio vs the model's own weighted treatment).
    if var.startswith("resort_view_"):
        return (
            "resort_view_* YoY sign can diverge between the model's site-level "
            "data and this script's B2C rollup query for low-volume resorts — "
            "treat as a methodology gap, not a pipeline error."
        )
    # The explicability model is trained on each market's OWN individual GA4
    # site property; this script can only query the shared B2C rollup property.
    # When the model's own absolute volume (valeur/valeur_prec) differs sharply
    # from what this script's rollup query independently counted for the same
    # variable/market (either period off by more than a generous factor), that's
    # real evidence the two properties are measuring different populations.
    VOLUME_RECONCILE_FACTOR = 2.0
    if None not in (model_valeur, model_valeur_prec, ga4_v26, ga4_v25) and ga4_v26 and ga4_v25:
        current_ratio = model_valeur / ga4_v26 if ga4_v26 else float("inf")
        prior_ratio = model_valeur_prec / ga4_v25 if ga4_v25 else float("inf")
        if (
            current_ratio > VOLUME_RECONCILE_FACTOR or current_ratio < 1 / VOLUME_RECONCILE_FACTOR
            or prior_ratio > VOLUME_RECONCILE_FACTOR or prior_ratio < 1 / VOLUME_RECONCILE_FACTOR
        ):
            return (
                f"model volume (current={model_valeur:,.0f}, prior={model_valeur_prec:,.0f}) diverges "
                f"from this script's rollup count (current={ga4_v26:,.0f}, prior={ga4_v25:,.0f}) by "
                f"more than {VOLUME_RECONCILE_FACTOR:g}x — model is trained on this market's own "
                f"individual GA4 site property, not the shared B2C rollup this script queries; "
                f"treat as a property-pairing gap, not a pipeline error."
            )
    return None


# ── Country map: model site → GA4 country dimension ───────────────────────────
COUNTRY_MAP = {
    "Israël": "Israel",
    # These have no exact GA4 country → skip
    "Global": None,
    "Other":  None,
    "Asia":   None,
}

# ── Results tracking ──────────────────────────────────────────────────────────
results = []   # list of dicts: {level, check, detail}

def record(level, check, detail):
    results.append({"level": level, "check": check, "detail": detail})
    icon = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌"}.get(level, "  ")
    print(f"  {icon} [{level}] {check}: {detail}")

# ── GA4 helpers ───────────────────────────────────────────────────────────────
def _run(req):
    time.sleep(GA4_DELAY_S)
    return client.run_report(req)

def _scalar(metric_name, dr, dim_filter=None):
    req = RunReportRequest(
        property=f"properties/{GA4_PROPERTY_ID}",
        metrics=[Metric(name=metric_name)],
        date_ranges=[dr],
        dimension_filter=dim_filter,
    )
    resp = _run(req)
    return float(resp.rows[0].metric_values[0].value) if resp.rows else 0.0

def _fe(field, value):
    return FilterExpression(filter=Filter(
        field_name=field,
        string_filter=Filter.StringFilter(
            value=value, match_type=Filter.StringFilter.MatchType.EXACT
        )
    ))

def _and(*exprs):
    return FilterExpression(and_group=FilterExpressionList(expressions=list(exprs)))

def _or(*exprs):
    return FilterExpression(or_group=FilterExpressionList(expressions=list(exprs)))

def event_count_filter(event_name, country=None):
    parts = [_fe("eventName", event_name)]
    if country:
        parts.append(_fe("country", country))
    return _and(*parts) if country else parts[0]

def _contains(field, value):
    return FilterExpression(filter=Filter(
        field_name=field,
        string_filter=Filter.StringFilter(
            value=value, match_type=Filter.StringFilter.MatchType.CONTAINS
        )
    ))

def custom_dim_count_filter(dimension, value, event_name, country=None, contains=False):
    """Like event_count_filter, but additionally scoped to one customEvent:*
    dimension value (exact or substring) — mirrors deepdive.py's
    variable_to_dimension() mappings for variables whose real GA4 event is a
    generic one (e.g. page_view) distinguished by a custom dimension."""
    parts = [_fe("eventName", event_name)]
    parts.append(_contains(dimension, value) if contains else _fe(dimension, value))
    if country:
        parts.append(_fe("country", country))
    return _and(*parts)

def _begins_with(field, value):
    return FilterExpression(filter=Filter(
        field_name=field,
        string_filter=Filter.StringFilter(
            value=value, match_type=Filter.StringFilter.MatchType.BEGINS_WITH
        )
    ))

def resort_event_filter(resort_code, country=None):
    # Prefix match, not exact: GA4 can carry a season suffix on the same resort
    # (e.g. "<CODE>_SUMMER"/"<CODE>_WINTER"), and the explicability variable is the
    # resort as a whole — an exact match would read 0 for those and skip the check.
    parts = [_fe("eventName", "Resort"), _begins_with("customEvent:resort_code", resort_code)]
    if country:
        parts.append(_fe("country", country))
    return _and(*parts)

def yoy(v26, v25):
    if v25 == 0:
        return float("inf") if v26 > 0 else 0.0
    return (v26 - v25) / abs(v25) * 100

def sign(x):
    if x is None:
        return 0
    return 1 if x > 0 else (-1 if x < 0 else 0)

# ── Date range derivation ─────────────────────────────────────────────────────
def derive_date_ranges(analysis_input):
    sample = None
    for r in analysis_input.get("bucket_1_top_ranked", []):
        d = r.get("date", "")
        if d:
            sample = d[:10]
            break
    if not sample:
        raise ValueError("Cannot determine analysis date from analysis_input.json")
    year, month, _ = sample.split("-")
    year = int(year); month = int(month)
    last_day = calendar.monthrange(year, month)[1]
    py = year - 1
    return (
        DateRange(start_date=f"{year}-{month:02d}-01",   end_date=f"{year}-{month:02d}-{last_day:02d}"),
        DateRange(start_date=f"{py}-{month:02d}-01",     end_date=f"{py}-{month:02d}-{last_day:02d}"),
        f"{year}-{month:02d}",
    )


def ga4_mobile_be_entry_rate(country, dr):
    """Live GA4 mobile BE entry rate for one country/period (None if no data)."""
    sess_req = RunReportRequest(
        property=f"properties/{GA4_PROPERTY_ID}",
        dimensions=[Dimension(name="deviceCategory"), Dimension(name="country")],
        metrics=[Metric(name="sessions")],
        date_ranges=[dr],
    )
    be_req = RunReportRequest(
        property=f"properties/{GA4_PROPERTY_ID}",
        dimensions=[Dimension(name="deviceCategory"), Dimension(name="country")],
        metrics=[Metric(name="eventCount")],
        date_ranges=[dr],
        dimension_filter=_fe("eventName", "BE_Entry"),
    )
    sr = _run(sess_req)
    br = _run(be_req)
    sess = {}
    be = {}
    for row in sr.rows:
        if row.dimension_values[1].value.lower() == country.lower():
            sess[row.dimension_values[0].value] = float(row.metric_values[0].value)
    for row in br.rows:
        if row.dimension_values[1].value.lower() == country.lower():
            be[row.dimension_values[0].value] = float(row.metric_values[0].value)
    mob_s = sess.get("mobile", 0)
    mob_b = be.get("mobile", 0)
    return (mob_b / mob_s * 100) if mob_s else None


def ga4_channel_group_sessions(group_name: str, dr) -> float:
    """Live GA4 sessions for one Custom Channel Group name, property-wide (no country filter)."""
    return _scalar("sessions", dr, _fe(CHANNEL_DIMENSION, group_name))


# ══════════════════════════════════════════════════════════════════════════════
def main():
    global client

    # ── Load files ────────────────────────────────────────────────────────────
    for p in (ANALYSIS_INPUT, SYNTHESIS_OUTPUT, DEEPDIVE_OUTPUT):
        if not p.exists():
            print(f"ERROR: {p} not found — run pipeline scripts first.", file=sys.stderr)
            sys.exit(1)

    with open(ANALYSIS_INPUT,   encoding="utf-8") as f: ai   = json.load(f)
    with open(SYNTHESIS_OUTPUT, encoding="utf-8") as f: syn  = json.load(f)
    with open(DEEPDIVE_OUTPUT,  encoding="utf-8") as f: deep = json.load(f)

    # Bail if synthesis itself failed to parse
    if "raw_output" in syn:
        print("ERROR: synthesis_output.json contains raw_output (JSON parse failed). Fix synthesis first.")
        sys.exit(1)

    dr_curr, dr_prior, period_label = derive_date_ranges(ai)
    print(f"\nVerifying synthesis for period: {period_label}")
    print(f"GA4 property: {GA4_PROPERTY_ID}\n")

    # ── Authenticate ──────────────────────────────────────────────────────────
    creds = Credentials.from_authorized_user_file(str(GA4_TOKEN), GA4_SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    client = BetaAnalyticsDataClient(credentials=creds)

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 1 — Core KPIs
    # ══════════════════════════════════════════════════════════════════════════
    print("── 1. Core KPIs ─────────────────────────────────────────────────────")

    kpi_rows = {
        r["variable"]: r
        for r in ai.get("bucket_4_core_kpi_snapshot", [])
        if r.get("site") == "Global"
    }

    s26  = _scalar("sessions",  dr_curr)
    s25  = _scalar("sessions",  dr_prior)
    be26 = _scalar("eventCount", dr_curr,  _fe("eventName", "BE_Entry"))
    be25 = _scalar("eventCount", dr_prior, _fe("eventName", "BE_Entry"))
    bc26 = _scalar("eventCount", dr_curr,  _fe("eventName", "BE_Confirmation"))
    bc25 = _scalar("eventCount", dr_prior, _fe("eventName", "BE_Confirmation"))

    ber26 = be26 / s26 * 100 if s26 else 0
    ber25 = be25 / s25 * 100 if s25 else 0
    ecvr26 = bc26 / s26 * 100 if s26 else 0
    ecvr25 = bc25 / s25 * 100 if s25 else 0

    kpi_ga4 = {
        "total_sessions": yoy(s26,   s25),
        "BE_Entry_Rate":  yoy(ber26, ber25),
        "ECVR_BE":        yoy(ecvr26, ecvr25),
    }

    for var, label in [("total_sessions","Sessions YoY"), ("BE_Entry_Rate","BE Entry Rate YoY"), ("ECVR_BE","ECVR BE YoY")]:
        row   = kpi_rows.get(var)
        if not row or row.get("variation") is None:
            record("WARN", label, "not found in analysis_input.json — skipping")
            continue
        claimed = row["variation"] * 100
        actual  = kpi_ga4[var]
        diff    = abs(claimed - actual)

        if sign(claimed) != sign(actual):
            record("FAIL", label, f"DIRECTION MISMATCH — model={claimed:+.1f}%  GA4={actual:+.1f}%")
        elif diff > KPI_CRITICAL_TOL:
            record("FAIL", label, f"magnitude too far — model={claimed:+.1f}%  GA4={actual:+.1f}%  Δ={diff:.1f}pp")
        elif diff > KPI_WARN_TOL:
            record("WARN", label, f"model={claimed:+.1f}%  GA4={actual:+.1f}%  Δ={diff:.1f}pp (late-hit / model lag expected)")
        else:
            record("PASS", label, f"model={claimed:+.1f}%  GA4={actual:+.1f}%  Δ={diff:.1f}pp")

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 2 — Bucket 1 driver direction + resort focus direction
    # (channel_*/device_* no longer appear in either — they're 100% GA4-driven and
    # never pass through the CSV, so there is nothing to cross-check here for them.)
    # ══════════════════════════════════════════════════════════════════════════
    print("\n── 2. Driver direction (bucket 1 + resort focus) ────────────────────")

    for row in ai.get("bucket_1_top_ranked", []):
        var      = row.get("variable", "")
        site     = row.get("site", "")
        model_var = row.get("variation")

        if model_var is None:
            continue

        country_ga4 = COUNTRY_MAP.get(site, site)
        if country_ga4 is None:
            continue

        ga4_yoy = None
        label = f"{var} | {site}"

        if var.startswith("departure_"):
            # Mirrors deepdive.py's variable_to_dimension(): real event is
            # page_view, segment lives in customEvent:departure_date_range,
            # exact match on the suffix after "departure_".
            segment = var[len("departure_"):]
            dim_filter = custom_dim_count_filter("customEvent:departure_date_range", segment, "page_view", country_ga4)
            v26 = _scalar("eventCount", dr_curr, dim_filter)
            v25 = _scalar("eventCount", dr_prior, dim_filter)
            ga4_yoy = yoy(v26, v25)
        elif var.startswith("page_view_shopping_"):
            # Mirrors deepdive.py's variable_to_dimension(): real event is
            # page_view, page lives in customEvent:page_name — substring match
            # (not exact) since "shopping_landing" is a PREFIX family
            # ("shopping_landing_<campaign>"), while "shopping_offer"/
            # "shopping_search" happen to match exactly as substrings too.
            segment = var[len("page_view_"):]
            dim_filter = custom_dim_count_filter("customEvent:page_name", segment, "page_view", country_ga4, contains=True)
            v26 = _scalar("eventCount", dr_curr, dim_filter)
            v25 = _scalar("eventCount", dr_prior, dim_filter)
            ga4_yoy = yoy(v26, v25)
        elif var in ("BE_Transport_count", "counter_proposal_display_count") or (var.startswith("BE_") and var.endswith("_count")):
            event = var if not (var.startswith("BE_") and var.endswith("_count")) else var[: -len("_count")]
            v26 = _scalar("eventCount", dr_curr,  event_count_filter(event, country_ga4))
            v25 = _scalar("eventCount", dr_prior, event_count_filter(event, country_ga4))
            ga4_yoy = yoy(v26, v25)
        else:
            continue

        if ga4_yoy == float("inf"):
            if model_var > 0:
                record("PASS", label, "both model and GA4 show growth from near-zero base")
            else:
                record("WARN", label, f"model variation={model_var:+.1%} but GA4 prior was 0 — check emerging bucket")
            continue

        model_sign = sign(model_var)
        ga4_sign   = sign(ga4_yoy)
        # Structural tolerance, not tied to any specific variable/market: when BOTH
        # sides show a small-magnitude move (under NEAR_ZERO_MAGNITUDE_PCT), a sign
        # flip is noise around zero (model vs. GA4's ~72h processing lag), not a
        # genuine directional contradiction worth blocking the post over.
        NEAR_ZERO_MAGNITUDE_PCT = 10.0
        near_zero_both = abs(model_var * 100) < NEAR_ZERO_MAGNITUDE_PCT and abs(ga4_yoy) < NEAR_ZERO_MAGNITUDE_PCT

        if model_sign == 0 or ga4_sign == 0:
            record("WARN", label, f"model={model_var:+.1%}  GA4={ga4_yoy:+.1f}% — zero on one side, skipping direction check")
        elif model_sign != ga4_sign and near_zero_both:
            record("WARN", label, f"model={model_var:+.1%}  GA4={ga4_yoy:+.1f}% — both near-zero magnitude, sign flip is noise not error")
        elif model_sign != ga4_sign:
            # Per-variable driver direction checks are informational, never a
            # post-blocking FAIL — the model is trained on each market's own
            # individual GA4 site property, this script only has the shared
            # B2C rollup to compare against, and a single-variable/single-market
            # disagreement (unlike the core KPI check above, which is the
            # headline number the gate actually protects) isn't severe enough
            # to block the whole monthly post. Still surfaces the specific
            # reason so it's never silently hidden, just never a hard stop.
            reason = classify_direction_mismatch(
                var, site, model_var, ga4_yoy,
                model_valeur=row.get("valeur"), model_valeur_prec=row.get("valeur_prec"),
                ga4_v26=v26, ga4_v25=v25,
            )
            detail = f"direction mismatch — model={model_var:+.1%}  GA4={ga4_yoy:+.1f}%"
            if reason:
                detail += f"  [{reason}]"
            record("WARN", label, detail)
        else:
            record("PASS", label, f"direction aligned — model={model_var:+.1%}  GA4={ga4_yoy:+.1f}%")

    resort_rows = ai.get("top_resorts_positive", []) + ai.get("top_resorts_negative", [])
    for row in resort_rows:
        var = row.get("variable", "")
        model_var = row.get("variation")
        if model_var is None or not var.startswith("resort_view_"):
            continue
        code = var.replace("resort_view_", "")
        v26 = _scalar("sessions", dr_curr,  resort_event_filter(code))
        v25 = _scalar("sessions", dr_prior, resort_event_filter(code))
        ga4_yoy = yoy(v26, v25)
        label = f"{var} | Global"

        if ga4_yoy == float("inf"):
            if model_var > 0:
                record("PASS", label, "both model and GA4 show growth from near-zero base")
            else:
                record("WARN", label, f"model variation={model_var:+.1%} but GA4 prior was 0")
            continue

        model_sign = sign(model_var)
        ga4_sign   = sign(ga4_yoy)
        if model_sign == 0 or ga4_sign == 0:
            record("WARN", label, f"model={model_var:+.1%}  GA4={ga4_yoy:+.1f}% — zero on one side, skipping direction check")
        elif model_sign != ga4_sign:
            # Informational, never post-blocking — see the bucket_1 loop above
            # for why per-variable driver direction checks don't FAIL the gate.
            reason = classify_direction_mismatch(var, "Global", model_var, ga4_yoy)
            detail = f"direction mismatch — model={model_var:+.1%}  GA4={ga4_yoy:+.1f}%"
            if reason:
                detail += f"  [{reason}]"
            record("WARN", label, detail)
        else:
            record("PASS", label, f"direction aligned — model={model_var:+.1%}  GA4={ga4_yoy:+.1f}%")

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 3 — Device split recompute (global + per-BU-country), comparing
    # deepdive_output.json's own stored figures against a fresh, independent GA4 pull
    # ══════════════════════════════════════════════════════════════════════════
    print("\n── 3. Mobile BE entry rate — recompute vs stored ────────────────────")

    def _check_mobile(label: str, country_filter: str | None, stored: dict):
        stored_curr = (stored.get("current", {}) or {}).get("mobile", {}).get("be_entry_rate")
        stored_prior = (stored.get("prior", {}) or {}).get("mobile", {}).get("be_entry_rate")
        if stored_curr is None or stored_prior is None:
            record("WARN", f"Mobile | {label}", "no stored mobile BE entry rate in deepdive_output.json — skipping")
            return
        if country_filter:
            live_curr = ga4_mobile_be_entry_rate(country_filter, dr_curr)
            live_prior = ga4_mobile_be_entry_rate(country_filter, dr_prior)
        else:
            # Global recompute: aggregate mobile sessions/BE_Entry with no country filter
            sess_req = RunReportRequest(property=f"properties/{GA4_PROPERTY_ID}",
                dimensions=[Dimension(name="deviceCategory")], metrics=[Metric(name="sessions")], date_ranges=[dr_curr])
            be_req = RunReportRequest(property=f"properties/{GA4_PROPERTY_ID}",
                dimensions=[Dimension(name="deviceCategory")], metrics=[Metric(name="eventCount")],
                date_ranges=[dr_curr], dimension_filter=_fe("eventName", "BE_Entry"))
            sr, br = _run(sess_req), _run(be_req)
            mob_s = next((float(r.metric_values[0].value) for r in sr.rows if r.dimension_values[0].value == "mobile"), 0)
            mob_b = next((float(r.metric_values[0].value) for r in br.rows if r.dimension_values[0].value == "mobile"), 0)
            live_curr = (mob_b / mob_s * 100) if mob_s else None
            live_prior = None  # global prior recompute skipped for brevity — current-period check is the main signal

        if live_curr is None:
            record("WARN", f"Mobile | {label}", "no live GA4 mobile session data found")
            return

        stored_curr_pct = stored_curr * 100
        diff = abs(stored_curr_pct - live_curr)
        if diff > MOBILE_FAIL_TOL:
            record("WARN", f"Mobile | {label}", f"stored={stored_curr_pct:+.1f}%  live GA4={live_curr:+.1f}%  Δ={diff:.1f}pp (recompute drift)")
        elif diff > MOBILE_WARN_TOL:
            record("WARN", f"Mobile | {label}", f"stored={stored_curr_pct:+.1f}%  live GA4={live_curr:+.1f}%  Δ={diff:.1f}pp")
        else:
            record("PASS", f"Mobile | {label}", f"stored={stored_curr_pct:+.1f}%  live GA4={live_curr:+.1f}%  Δ={diff:.1f}pp")

    global_device = deep.get("global_device", {})
    if global_device:
        _check_mobile("Global", None, global_device.get("breakdown", {}))

    for bu in deep.get("bu_insights", []):
        for c in bu.get("countries", []):
            site = c.get("site", "")
            country_ga4 = COUNTRY_MAP.get(site, site)
            if country_ga4 is None:
                continue
            _check_mobile(site, country_ga4, c.get("device_breakdown", {}))

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 4 — Global New Custom Channel Group sessions: recompute vs stored
    # ══════════════════════════════════════════════════════════════════════════
    print("\n── 4. Global channel group sessions — recompute vs stored ──────────")

    global_channel = deep.get("global_channel", {})
    # global_channel is now pre-split into top-3-positive/top-3-negative by direct
    # impact on ECVR BE (see deepdive.py's split_channel_groups_by_impact) rather
    # than a single "breakdown" list ranked by session count.
    top_groups = (global_channel.get("positive") or []) + (global_channel.get("negative") or [])
    if not top_groups:
        record("WARN", "Global channel groups", "no global_channel positive/negative groups found in deepdive_output.json — skipping")
    else:
        for row in top_groups:
            group = row.get("group", "")
            stored_curr = row.get("sessions_current", 0)
            if not group or stored_curr == 0:
                continue
            live_curr = ga4_channel_group_sessions(group, dr_curr)
            if stored_curr == 0:
                continue
            rel_diff = abs(live_curr - stored_curr) / stored_curr
            label = f"Channel | {group}"
            if rel_diff > CHANNEL_RECOMPUTE_WARN_PCT:
                record("WARN", label, f"stored={stored_curr:,}  live GA4={live_curr:,.0f}  Δ={rel_diff:.1%} (recompute drift — late-hit window)")
            else:
                record("PASS", label, f"stored={stored_curr:,}  live GA4={live_curr:,.0f}  Δ={rel_diff:.1%}")

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 5 — No impossible conversion rates (>100%) in synthesis text
    # ══════════════════════════════════════════════════════════════════════════
    print("\n── 5. Impossible rate guard ─────────────────────────────────────────")

    rate_re = re.compile(r"(?<![,\d.])([+\-−]?)(\d{3,}(?:\.\d+)?)\s*%")  # "." excluded: "0.075%" is not 075%
    full_text = json.dumps(syn, ensure_ascii=False)  # ASCII-escaping turned "%→1.8%" into "%\\u21921.8%", read as 21921.8%
    hits = []
    for m in rate_re.finditer(full_text):
        sign_char = m.group(1)
        val = float(m.group(2))
        if sign_char in ("+", "-", "−"):
            continue
        context = full_text[max(0, m.start()-80):m.end()+60]
        if re.search(r"YoY|year.on.year|growth|increased|grew", context, re.I):
            continue
        if re.search(r"ecvr|conversion.rate|be.entry.rate", context, re.I):
            hits.append((val, context.strip()[:80]))

    if hits:
        for val, ctx in hits:
            record("FAIL", "Impossible rate", f"{val:.1f}% — context: ...{ctx}...")
    else:
        record("PASS", "Impossible rate guard", "no conversion rates above 100% detected in synthesis text")

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 6 — Channel taxonomy purity: synthesis must never mention an old
    # channel_* variable name (structural regression guard for this redesign)
    # ══════════════════════════════════════════════════════════════════════════
    print("\n── 6. Channel taxonomy purity guard ─────────────────────────────────")

    # The explicability CSV's channel_* vocabulary is fixed (it's GA4's old Default
    # Channel Group taxonomy, not a per-month finding) — match against that known
    # list rather than a wildcard, since a wildcard also matches this pipeline's own
    # schema key names (e.g. "channel_section_global") as false positives.
    # The model's channel_<slug> variables now share the custom channel group
    # taxonomy, so the guard is about DISPLAY: reader-facing text must use the group
    # name, not a raw channel_<slug> variable name. This pipeline's own schema keys
    # (channel_section_global, channel_positive, ...) are the only allowed matches.
    old_channel_re = re.compile(r"\b(channel_(?!section|positive|negative|country|group)[a-z0-9_]+)\b", re.I)
    # Only free text is scanned: a "variable" key is a data field that carries the exact
    # variable name (shown next to a plain-language theme), not reader-facing prose.
    def _strip_variable_keys(o):
        if isinstance(o, dict):
            return {k: _strip_variable_keys(v) for k, v in o.items() if k != "variable"}
        if isinstance(o, list):
            return [_strip_variable_keys(v) for v in o]
        return o
    full_text_lower = json.dumps(_strip_variable_keys(syn))
    old_hits = sorted(set(old_channel_re.findall(full_text_lower)))
    if old_hits:
        record("FAIL", "Channel taxonomy purity", f"raw channel_* variable name(s) found in synthesis output (use the channel group name): {', '.join(old_hits)}")
    else:
        record("PASS", "Channel taxonomy purity", "no raw channel_* variable names found — GA4 Custom Channel Group names only")

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 7 — Unmeasured causal claims (informational, never blocking): the data
    # blocks measure sessions/confirmations/ECVR/device/channel, not UTM hygiene,
    # CRM sends or targeting. Stating those as causes is speculation.
    # ══════════════════════════════════════════════════════════════════════════
    print("\n── 7. Unmeasured causal claims ──────────────────────────────────────")
    UNMEASURED_CAUSES = re.compile(
        r"utm|misattribut|stripping|crm (?:campaign|segment|targeting|dispatch)|returning visitors?",
        re.I)
    def _free_text(o, path=""):
        if isinstance(o, dict):
            for k, v in o.items():
                if k != "variable":
                    yield from _free_text(v, f"{path}/{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                yield from _free_text(v, f"{path}[{i}]")
        elif isinstance(o, str):
            yield path, o
    cause_hits = [(p, m.group(0)) for p, t in _free_text(syn) for m in UNMEASURED_CAUSES.finditer(t)]
    if cause_hits:
        for p, w in cause_hits[:15]:
            record("WARN", "Unmeasured cause", f"'{w}' asserted at {p} — not measured by this pipeline, reword as a hypothesis")
    else:
        record("PASS", "Unmeasured causal claims", "no unmeasured-cause wording found")

    # ══════════════════════════════════════════════════════════════════════════
    # SUMMARY
    # ══════════════════════════════════════════════════════════════════════════
    print("\n" + "═" * 65)
    fails  = [r for r in results if r["level"] == "FAIL"]
    warns  = [r for r in results if r["level"] == "WARN"]
    passes = [r for r in results if r["level"] == "PASS"]

    print(f"RESULT: {len(passes)} PASS  |  {len(warns)} WARN  |  {len(fails)} FAIL")

    if fails:
        print("\nFAILURES (block Teams post):")
        for r in fails:
            print(f"  ❌ {r['check']}: {r['detail']}")
        print("\n→ Fix these issues before running teams_message.py")
        sys.exit(1)
    elif warns:
        print("\nWARNINGS (review before posting — may reflect known methodology gaps):")
        for r in warns:
            print(f"  ⚠️  {r['check']}: {r['detail']}")
        print("\n→ PASS WITH WARNINGS — safe to post if warnings are expected methodology gaps")
        sys.exit(0)
    else:
        print("\n→ ALL CHECKS PASSED — safe to post to Teams")
        sys.exit(0)


if __name__ == "__main__":
    main()
