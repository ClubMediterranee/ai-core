"""
ECVR BE Explicability Analysis — Step 1: Filter & Bucket
Reads explicability CSV + country weights CSV + BU-level CSV, produces analysis_input.json
"""

import csv
import json
import math
import os
import sys
import io
from collections import Counter
from pathlib import Path

# --- Configuration ---
VARIATION_THRESHOLD = 0.05          # 5% — movers threshold for zero-importance variables
EMERGING_BASE_RATIO = 0.20          # base < 20% of current → emerging
MOVERS_MIN_VOLUME = 50              # prior value must be ≥ 50 to qualify as a mover
TOP_N_VARIABLES = 30
TOP_N_COUNTRIES_PER_BU = 3          # per-BU country focus (item 6 of the card redesign)
TOP_N_EMERGING = 10             # top emerging by absolute current value
TOP_N_MOVERS = 10               # top zero-imp movers by volume × variation score
TOP_N_RESORTS = 5               # top positive / top negative resort_view_* rows

# All file paths resolve against ECVR_DOWNLOADS_DIR (defaults to this machine's
# original working directory) — set that env var to point the whole pipeline
# at a different folder without editing every script.
_DOWNLOADS_DIR = Path(os.environ.get("ECVR_DOWNLOADS_DIR", r"/mnt/c/Users/xxxxx/Downloads"))

# These two filenames change every month (new CSV export) — update here.
EXPLICABILITY_CSV = _DOWNLOADS_DIR / "job_9fN6eXhUPVbE0XXtBkGI4I5ItUjU.csv"
COUNTRIES_CSV  = _DOWNLOADS_DIR / "job_eQEwOhTqO5eyePFtPlPxS3P6UjLk.csv"
BU_CSV = _DOWNLOADS_DIR / "job_Ae4cO-YBJMqhymTHn1gTOZiYknpZ.csv"
OUTPUT_JSON = _DOWNLOADS_DIR / "analysis_input.json"

CORE_KPIS = {
    "BE_CR", "ECVR", "ECVR_BE", "BE_Confirmation_count",
    "BE_Entry_count", "BE_Entry_Rate", "purchase_count", "total_sessions"
}

# Variables excluded from every bucket — never treated as an analysable signal:
# - nights_1_5_real_price_display: legacy/unused field
# - avg_session_duration: GA4's averageSessionDuration is not trustworthy for this
#   property (flagged by the user — do not surface it anywhere in the analysis)
EXCLUDED = {"nights_1_5_real_price_display", "avg_session_duration"}

# Business Unit reference — Club Med market organisation (see memory: reference_bu_market_list).
# Maps the country names as they appear in the "top contributing sites" CSV to their BU.
# "Other" and "Asia" are rollup/residual buckets in the source data, not real single markets.
BU_MAP = {
    "South Africa": "EMEA", "Switzerland": "EMEA", "France": "EMEA",
    "United Kingdom": "EMEA", "Netherlands": "EMEA", "Italy": "EMEA",
    "Belgium": "EMEA", "Germany": "EMEA", "Israël": "EMEA", "Israel": "EMEA",
    "Ukraine": "EMEA", "Russia": "EMEA", "Portugal": "EMEA", "Spain": "EMEA",
    "Turkey": "EMEA", "Sweden": "EMEA", "Denmark": "EMEA", "Ireland": "EMEA",
    "Japan": "NEA", "Taiwan": "NEA", "South Korea": "NEA", "Korea": "NEA",
    "Hong Kong": "NEA", "China": "NEA",
    "Thailand": "SEAP", "Malaysia": "SEAP", "India": "SEAP", "Australia": "SEAP",
    "New Zealand": "SEAP", "Indonesia": "SEAP", "Singapore": "SEAP",
    "Mexico": "NAM", "United States": "NAM", "Panama": "NAM", "Canada": "NAM",
    "Dominican Republic": "NAM",
    "Brazil": "SAM", "Chile": "SAM", "Argentina": "SAM", "Uruguay": "SAM",
}


def get_bu(site: str) -> str:
    """Business Unit for a market/site name, or 'Other' for rollup/unmapped entries."""
    return BU_MAP.get(site.strip(), "Other")


def get_bu_markets_map() -> dict:
    """Inverts BU_MAP into {business_unit: [market names]} — the single source of
    truth for which GA4 country values belong to each BU. Downstream scripts
    (deepdive.py) consume this from analysis_input.json's meta rather than keeping
    their own copy of the market/BU mapping."""
    out: dict = {}
    for market, bu in BU_MAP.items():
        out.setdefault(bu, []).append(market)
    return out


def parse_float(val):
    try:
        f = float(val)
        return f
    except (ValueError, TypeError):
        return None


def is_infinite_or_nan(val):
    if val is None:
        return True
    if isinstance(val, float) and (math.isinf(val) or math.isnan(val)):
        return True
    if isinstance(val, str) and val.strip().lower() in ("infinity", "inf", "nan", ""):
        return True
    return False


def is_emerging(valeur, valeur_prec, variation_raw):
    """True if the prior base was near-zero or variation is infinite/NaN."""
    if is_infinite_or_nan(variation_raw):
        return True
    vp = parse_float(valeur_prec)
    v = parse_float(valeur)
    if vp is None or v is None:
        return True
    if vp == 0:
        return True
    if v != 0 and abs(vp) < EMERGING_BASE_RATIO * abs(v):
        return True
    return False


def read_delimited_csv(path):
    """Generic reader — auto-detects ';' vs ',' delimiter, strips whitespace from
    keys/values. Used for all three source CSVs (explicability, countries, BU)."""
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        sample = f.read(2048)
        f.seek(0)
        sep = ";" if sample.count(";") > sample.count(",") else ","
        reader = csv.DictReader(f, delimiter=sep)
        for row in reader:
            if any(v.strip() for v in row.values()):
                rows.append({k.strip(): v.strip() for k, v in row.items()})
    return rows


# Backward-compatible aliases (same generic reader, kept for clarity at call sites)
read_explicability_csv = read_delimited_csv
read_countries_csv = read_delimited_csv
read_bu_csv = read_delimited_csv


def bucket_variables(rows):
    """
    Buckets explicability-model rows by importance/behaviour. device_* and
    resort_view_* variables are EXCLUDED here entirely (bucket 1 through 5):
    - device_*: this analysis is driven 100% by live GA4 deviceCategory queries
      (see deepdive.py), never by these CSV variables.
    - channel_*: NOT excluded. The model's channel_<slug> variables are now built on
      the same GA4 Custom Channel Group taxonomy the pipeline uses, so they flow
      through like any other variable (deepdive.py maps them to that dimension).
    - resort_view_*: handled by its own dedicated top-5-positive / top-5-negative
      selection (see get_top_resorts), not by generic importance-based bucketing —
      so it never double-counts into bucket_1/2/3 or "other signals".
    """
    top_ranked = []
    zero_movers = []
    emerging = []
    core_kpis = []
    set_aside = []

    for row in rows:
        variable = row.get("variable", "").strip()
        if not variable:
            continue
        if variable in EXCLUDED:
            continue
        if variable.startswith(("device_", "resort_view_")):
            continue

        importance_raw = row.get("importance", "0")
        abs_wi_raw = row.get("absolute_weighted_importance", "0")
        variation_raw = row.get("variation", "")
        valeur = row.get("valeur", "")
        valeur_prec = row.get("valeur_prec", "")
        impact = row.get("impact_on_ECVR_BE", "").strip()

        importance = parse_float(importance_raw) or 0.0
        abs_wi = parse_float(abs_wi_raw) or 0.0
        variation = parse_float(variation_raw)

        record = {
            "site": row.get("site", "").strip(),
            "date": row.get("date", "").strip(),
            "variable": variable,
            "valeur": parse_float(valeur),
            "importance": importance,
            "date_prec": row.get("date_prec", "").strip(),
            "valeur_prec": parse_float(valeur_prec),
            "variation": variation,
            "weighted_importance": parse_float(row.get("weighted_importance", "")) or 0.0,
            "absolute_weighted_importance": abs_wi,
            "impact_on_ECVR_BE": impact,
        }

        # Core KPIs go to their own bucket regardless of importance
        if variable in CORE_KPIS:
            core_kpis.append(record)
            continue

        if importance != 0.0 and is_emerging(valeur, valeur_prec, variation_raw):
            # Non-zero importance, but the YoY is built on a near-zero or tiny prior base, so the
            # row's weight comes from the SIZE OF THE MOVE, not from the model's coefficient.
            # It goes to the emerging bucket (context for the follow-up), never the ranked one.
            record["extreme_yoy"] = True
            emerging.append(record)
        elif importance != 0.0:
            top_ranked.append(record)
        else:
            # Zero-importance: check emerging first
            if is_emerging(valeur, valeur_prec, variation_raw):
                emerging.append(record)
            elif (variation is not None and abs(variation) > VARIATION_THRESHOLD
                  and record["valeur_prec"] is not None and abs(record["valeur_prec"]) >= MOVERS_MIN_VOLUME):
                zero_movers.append(record)
            else:
                set_aside.append(record)

    # Sort top_ranked and take top N
    top_ranked.sort(key=lambda r: r["absolute_weighted_importance"], reverse=True)
    top_ranked = top_ranked[:TOP_N_VARIABLES]

    # Sort zero_movers by volume × variation score, keep top N
    zero_movers.sort(
        key=lambda r: abs(r["variation"] or 0) * abs(r["valeur_prec"] or 0),
        reverse=True
    )
    zero_movers = zero_movers[:TOP_N_MOVERS]

    # Sort emerging by absolute current value, keep top N, drop zero-value rows
    emerging = [r for r in emerging if r["valeur"] is not None and r["valeur"] != 0]
    emerging.sort(key=lambda r: (not r.get("extreme_yoy"), -(r.get("absolute_weighted_importance") or 0), -abs(r["valeur"])))
    emerging = emerging[:TOP_N_EMERGING]

    return top_ranked, zero_movers, emerging, core_kpis, set_aside


def _get(row, *keys):
    """Case-insensitive multi-key dict lookup."""
    row_lower = {k.lower(): v for k, v in row.items()}
    for k in keys:
        v = row_lower.get(k.lower())
        if v is not None:
            return v
    return ""


def get_all_countries(rows):
    """All markets with BU tags and parsed metrics (unbounded, unsorted-by-contribution)."""
    country_rows = []
    for row in rows:
        # Accepts both known export schemas (legacy Looker-style headers and the
        # job_*.csv headers) — the first matching header name wins.
        site = _get(row, "Site").strip()
        contrib_raw = _get(row, "Absolute weighted contribution", "absolute_weighted_importance") or "0"
        ecvr_y = parse_float(_get(row, "ECVR_BE y", "ECVR_BE"))
        ecvr_y1 = parse_float(_get(row, "ECVR_BE y-1", "ECVR_BE_prec"))
        pct_change = parse_float(_get(row, "% change", "variation"))
        contrib = parse_float(contrib_raw) or 0.0
        if not site:
            continue
        if ecvr_y is None and ecvr_y1 is None and contrib == 0.0:
            # Unrecognised schema — fail loudly instead of silently producing
            # empty rows that make the BU-focus selection fall back to file order.
            raise ValueError(
                f"Country CSV row for '{site}' has no recognisable ECVR/contribution "
                f"columns (headers seen: {sorted(row.keys())})"
            )
        country_rows.append({
            "site": site,
            "business_unit": get_bu(site),
            "ecvr_be_y": ecvr_y,
            "ecvr_be_y1": ecvr_y1,
            "pct_change": pct_change,
            "absolute_weighted_contribution": contrib,
        })
    return country_rows


def get_top_countries_per_bu(all_countries, top_n=TOP_N_COUNTRIES_PER_BU):
    """
    Groups all markets by Business Unit and returns each BU's top N markets by
    absolute weighted contribution to the global ECVR BE change — generic to
    whichever markets/BUs are present in the data, not a fixed market list.
    'Other' (rollup/residual sites with no real BU) is excluded from BU-level focus.
    """
    by_bu: dict = {}
    for c in all_countries:
        if c["business_unit"] == "Other":
            continue
        by_bu.setdefault(c["business_unit"], []).append(c)

    result = {}
    for bu, markets in by_bu.items():
        ranked = sorted(markets, key=lambda r: r["absolute_weighted_contribution"], reverse=True)
        result[bu] = ranked[:top_n]
    return result


def get_bu_breakdown(bu_rows):
    """
    Parses the BU-level explicability CSV (one row per Business Unit) into a ranked
    list — the BU-equivalent of the country-level weighted-contribution table.
    'poids' is the BU's share of global traffic/weight; absolute_weighted_importance
    is its normalised share of the global ECVR BE movement this period.
    """
    out = []
    for row in bu_rows:
        bu = _get(row, "BU").strip()
        if not bu:
            continue
        out.append({
            "business_unit": bu,
            "ecvr_be": parse_float(_get(row, "ECVR_BE")),
            "ecvr_be_prior": parse_float(_get(row, "ECVR_BE_prec")),
            "pct_change": parse_float(_get(row, "variation")),
            "poids": parse_float(_get(row, "poids")) or 0.0,
            "absolute_weighted_importance": parse_float(_get(row, "absolute_weighted_importance")) or 0.0,
            "impact_on_ECVR_BE": _get(row, "impact_on_ECVR_BE").strip(),
        })
    out.sort(key=lambda r: r["absolute_weighted_importance"], reverse=True)
    return out


def get_top_resorts(rows, top_n=TOP_N_RESORTS):
    """
    Top N resort_view_* variables by absolute weighted importance, split into
    positive-impact and negative-impact groups. Resort performance is read at
    Global (property-wide) scope — a resort's viewing trend is a genuine
    property-wide signal, not something to slice per market. Generic ranking
    rule (impact direction + magnitude), no hardcoded resort codes.
    """
    # Per-resort booking-engine funnel counts (Global rows): be_entry_<CODE> /
    # be_conf_<CODE> let the text check a resort's conversion against what the
    # model's direction implies, instead of inferring it from the view count alone.
    global_vals = {}
    for row in rows:
        if row.get("site", "").strip() == "Global":
            global_vals[row.get("variable", "").strip()] = (
                parse_float(row.get("valeur", "")), parse_float(row.get("valeur_prec", "")))

    candidates = []
    for row in rows:
        variable = row.get("variable", "").strip()
        if not variable.startswith("resort_view_"):
            continue
        if row.get("site", "").strip() != "Global":
            continue
        variation_raw = row.get("variation", "")
        if is_infinite_or_nan(variation_raw):
            continue
        abs_wi = parse_float(row.get("absolute_weighted_importance", "0")) or 0.0
        code = variable[len("resort_view_"):]
        be_entry = global_vals.get(f"be_entry_{code}", (None, None))
        be_conf = global_vals.get(f"be_conf_{code}", (None, None))
        candidates.append({
            "variable": variable,
            "site": "Global",
            "be_entry_current": be_entry[0],
            "be_entry_prior": be_entry[1],
            "be_conf_current": be_conf[0],
            "be_conf_prior": be_conf[1],
            "valeur": parse_float(row.get("valeur", "")),
            "valeur_prec": parse_float(row.get("valeur_prec", "")),
            "variation": parse_float(variation_raw),
            "importance": parse_float(row.get("importance", "")),
            "absolute_weighted_importance": abs_wi,
            "impact_on_ECVR_BE": row.get("impact_on_ECVR_BE", "").strip(),
        })

    positive = sorted(
        [c for c in candidates if c["impact_on_ECVR_BE"] == "positive"],
        key=lambda r: r["absolute_weighted_importance"], reverse=True
    )[:top_n]
    negative = sorted(
        [c for c in candidates if c["impact_on_ECVR_BE"] == "negative"],
        key=lambda r: r["absolute_weighted_importance"], reverse=True
    )[:top_n]
    return positive, negative


def detect_bu_clusters(all_countries, zero_thresh=0.001, pct_thresh=-0.5, min_markets=2, min_share=0.5):
    """
    Flag Business Units where a majority of markets simultaneously show near-zero
    ECVR BE — a much stronger tracking/technical-bug signal than scattered individual
    markets, since it implies a shared BU-level cause (e.g. a regional tag/domain issue)
    rather than independent market-level noise.
    """
    by_bu = {}
    for c in all_countries:
        by_bu.setdefault(c["business_unit"], []).append(c)

    clusters = []
    for bu, markets in by_bu.items():
        if bu == "Other" or len(markets) < min_markets:
            continue
        affected = [
            m for m in markets
            if (m.get("ecvr_be_y") is not None and m["ecvr_be_y"] < zero_thresh
                and m.get("pct_change") is not None and m["pct_change"] < pct_thresh)
        ]
        if len(affected) >= min_markets and len(affected) / len(markets) >= min_share:
            # Severity tiering: membership in the cluster is binary (same trigger threshold
            # for all), but the actual magnitude of collapse can vary a lot between members.
            # Expose each member's own pct_change so downstream text can distinguish
            # "near-total collapse" from "borderline" instead of treating the whole
            # cluster as uniformly severe — generic ranking, not tied to any market name.
            affected_sorted = sorted(affected, key=lambda m: m["pct_change"])
            most_severe_pct = affected_sorted[0]["pct_change"]
            least_severe_pct = affected_sorted[-1]["pct_change"]
            clusters.append({
                "business_unit": bu,
                "affected_markets": [m["site"] for m in affected_sorted],
                "affected_markets_detail": [
                    {"site": m["site"], "pct_change": m["pct_change"], "ecvr_be_y": m["ecvr_be_y"]}
                    for m in affected_sorted
                ],
                "total_markets_in_bu": len(markets),
                "severity_spread": abs(most_severe_pct - least_severe_pct) > 0.15,
            })
    return clusters


def main():
    print("Reading explicability data...")
    rows = read_explicability_csv(EXPLICABILITY_CSV)
    print(f"  {len(rows)} rows loaded")

    print("Bucketing variables (device_*/resort_view_*/avg_session_duration excluded)...")
    top_ranked, zero_movers, emerging, core_kpis, set_aside = bucket_variables(rows)
    print(f"  Bucket 1 — Top {TOP_N_VARIABLES} ranked:  {len(top_ranked)}")
    print(f"  Bucket 2 — Zero-imp movers:       {len(zero_movers)}")
    print(f"  Bucket 3 — Emerging:               {len(emerging)}")
    print(f"  Bucket 4 — Core KPI snapshot:      {len(core_kpis)}")
    print(f"  Bucket 5 — Set aside:              {len(set_aside)}")

    print("Reading country weights...")
    country_rows = read_countries_csv(COUNTRIES_CSV)
    all_countries = get_all_countries(country_rows)
    top_countries_per_bu = get_top_countries_per_bu(all_countries)
    for bu, markets in top_countries_per_bu.items():
        print(f"  {bu} top {len(markets)}: {', '.join(m['site'] for m in markets)}")

    print("Reading BU-level explicability data...")
    bu_rows = read_bu_csv(BU_CSV)
    bu_breakdown = get_bu_breakdown(bu_rows)
    print(f"  {len(bu_breakdown)} Business Units loaded")

    print("Selecting top/bottom resorts (Global scope)...")
    top_resorts_positive, top_resorts_negative = get_top_resorts(rows)
    print(f"  Top {len(top_resorts_positive)} positive / top {len(top_resorts_negative)} negative resort_view_* rows")

    # --- Data quality flags ---
    # Dominant variables: same variable appearing 3+ times in bucket_1.
    # When prior values are near-zero, this is a new launch inflating YoY artificially.
    var_counts = Counter(r["variable"] for r in top_ranked)
    dominant_variables = []
    for var, count in var_counts.items():
        if count < 3:
            continue
        instances = [r for r in top_ranked if r["variable"] == var]
        near_zero_prior = sum(
            1 for r in instances
            if r.get("valeur_prec") is None or (r.get("valeur_prec") or 0) < 10
        )
        global_row = next((r for r in rows
                           if r.get("site", "").strip() == "Global" and r.get("variable", "").strip() == var), None)
        dominant_variables.append({
            "variable": var,
            "count_in_bucket_1": count,
            "is_new_launch": near_zero_prior >= (count // 2 + 1),
            "global_variation": parse_float(global_row.get("variation", "")) if global_row else None,
            "global_abs_wi": parse_float(global_row.get("absolute_weighted_importance", "")) if global_row else None,
            "global_impact": global_row.get("impact_on_ECVR_BE", "").strip() if global_row else None,
            "instances": [
                {"site": r["site"], "impact_on_ECVR_BE": r["impact_on_ECVR_BE"], "variation": r["variation"]}
                for r in instances
            ],
        })
    dominant_variables.sort(key=lambda x: x["count_in_bucket_1"], reverse=True)

    # Near-zero conversion markets: likely tracking / technical bug when multiple hit zero.
    # Threshold: ECVR_BE y < 0.001 (0.1%) AND pct_change < -0.5 (-50%)
    zero_conversion_markets = [
        c["site"] for c in all_countries
        if (c.get("ecvr_be_y") is not None and c["ecvr_be_y"] < 0.001
            and c.get("pct_change") is not None and c["pct_change"] < -0.5)
    ]

    # BU-level clusters: majority of a Business Unit's markets simultaneously near-zero.
    bu_clusters = detect_bu_clusters(all_countries)

    if dominant_variables:
        print(f"  ⚠ Dominant variables in bucket_1: "
              + ", ".join(f"{d['variable']} ×{d['count_in_bucket_1']}" for d in dominant_variables))
    if zero_conversion_markets:
        print(f"  ⚠ Near-zero conversion markets: {', '.join(zero_conversion_markets)}")
    if bu_clusters:
        print("  ⚠ BU-level clusters (probable regional tracking bug): " + ", ".join(
            f"{c['business_unit']} ({len(c['affected_markets'])}/{c['total_markets_in_bu']}: {', '.join(c['affected_markets'])})"
            for c in bu_clusters
        ))

    output = {
        "meta": {
            "source_file": str(EXPLICABILITY_CSV.name),
            "countries_file": str(COUNTRIES_CSV.name),
            "bu_file": str(BU_CSV.name),
            "variation_threshold": VARIATION_THRESHOLD,
            "emerging_base_ratio": EMERGING_BASE_RATIO,
            "top_n_variables": TOP_N_VARIABLES,
            "top_n_countries_per_bu": TOP_N_COUNTRIES_PER_BU,
            "dominant_variables": dominant_variables,
            "zero_conversion_markets": zero_conversion_markets,
            "bu_clusters": bu_clusters,
            "bu_markets_map": get_bu_markets_map(),
        },
        "bucket_1_top_ranked": top_ranked,
        "bucket_2_zero_imp_movers": zero_movers,
        "bucket_3_emerging": emerging,
        "bucket_4_core_kpi_snapshot": core_kpis,
        "bucket_5_set_aside_count": len(set_aside),
        "bu_breakdown": bu_breakdown,
        "top_countries_per_bu": top_countries_per_bu,
        "top_resorts_positive": top_resorts_positive,
        "top_resorts_negative": top_resorts_negative,
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)

    print(f"\nOutput written to: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
