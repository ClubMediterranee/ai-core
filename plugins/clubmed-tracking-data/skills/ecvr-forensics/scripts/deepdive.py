"""
ECVR BE Explicability Analysis — Step 2: GA4 Deep-Dive
Queries GA4 at multiple scopes (global, per-Business-Unit, per-market) and asks
Claude for diagnostic insights at each level. Outputs deepdive_output.json.

Channel and device analysis are driven ENTIRELY by live GA4 queries — never by the
explicability CSV's old channel_*/device_* variables, which filter_results.py
excludes upstream. The only channel taxonomy ever surfaced is GA4's New Custom
Channel Group.

Requires before first run:
  pip install google-analytics-data google-auth-oauthlib anthropic

OAuth credentials: download OAuth 2.0 client credentials JSON from
  Google Cloud Console → APIs & Services → Credentials → Create OAuth client ID
  (Desktop app type) and place at the path set in OAUTH_CREDENTIALS_FILE.
"""

import json
import os
import sys
import time
from pathlib import Path

import anthropic
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Filter,
    FilterExpression,
    Metric,
    RunReportRequest,
)
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# ---------------------------------------------------------------------------
# Configuration — fill in GA4_PROPERTY_ID before first run
# ---------------------------------------------------------------------------
GA4_PROPERTY_ID = "310694998"   # e.g. "123456789"

# GA4 Custom Channel Group ("New_Custom Channel Group", channelGroups/13153047450) —
# distinct from GA4's system-defined Default Channel Group. Queried via the
# "sessionCustomChannelGroup:<id>" dimension syntax. This is the ONLY channel
# taxonomy this pipeline ever surfaces — update this ID if the channel group is
# ever recreated under a new ID in GA4 Admin.
GA4_CUSTOM_CHANNEL_GROUP_ID = "13153047450"

# All file paths resolve against ECVR_DOWNLOADS_DIR (defaults to this machine's
# original working directory) — set that env var to point the whole pipeline
# at a different folder without editing every script.
_DOWNLOADS_DIR = Path(os.environ.get("ECVR_DOWNLOADS_DIR", r"/mnt/c/Users/xxxxx/Downloads"))

# OAuth client secret JSON downloaded from Google Cloud Console (APIs & Services
# -> Credentials -> OAuth 2.0 Client -> Download JSON) — NEVER commit this file
# itself; only its path is configured here. Set OAUTH_CREDENTIALS_FILENAME to
# whatever your own downloaded file is actually named.
OAUTH_CREDENTIALS_FILE = _DOWNLOADS_DIR / os.environ.get(
    "OAUTH_CREDENTIALS_FILENAME", "client_secret.json"
)
OAUTH_TOKEN_FILE       = _DOWNLOADS_DIR / "ga4_oauth_token.json"

INPUT_JSON   = _DOWNLOADS_DIR / "analysis_input.json"
OUTPUT_JSON  = _DOWNLOADS_DIR / "deepdive_output.json"
CONTEXT_FILE = Path(__file__).parent / "data" / "context.md"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

CLAUDE_MODEL = "claude-sonnet-4-6-swc-gmdt"

# GA4 date range — auto-derived from analysis_input.json's own date column at
# run time (see derive_date_ranges() / main()), never edited by hand. These
# module-level names stay as the single source every query/prompt in this file
# reads from — main() reassigns them via `global` right after loading the data,
# before any GA4 call or prompt is built.
DATE_RANGE_CURRENT = None
DATE_RANGE_PRIOR   = None
PERIOD_LABEL_CURRENT = None
PERIOD_LABEL_PRIOR   = None

GA4_SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]

# Rate limiting — GA4 API quota is generous but we respect it
GA4_REQUEST_DELAY_S = 0.3
LLM_REQUEST_DELAY_S = 0.5

# ---------------------------------------------------------------------------
# GA4 full-funnel metrics to pull for every variable
# ---------------------------------------------------------------------------
FUNNEL_METRICS = [
    Metric(name="sessions"),
    Metric(name="engagedSessions"),
    Metric(name="engagementRate"),
]

# Rollup/residual site buckets from the explicability model's source data — these
# are not real, single GA4 "country" dimension values, so a strict country-match
# filter against them matches zero rows and silently returns a false 0/0. Any site
# name in this set skips the country filter instead (unfiltered/global-scope pull)
# rather than asserting a fabricated zero. Keyed on the general "not a real GA4
# country" property, not on any specific month's finding — extend this set if a
# future period introduces another rollup bucket, never hardcode a market fix.
NON_COUNTRY_SITES = {"global", "other", "asia"}


# ---------------------------------------------------------------------------
# Variable → GA4 dimension mapping (generic variables only — channel_*, device_*
# and resort_view_* variables from the CSV never reach this function: channel and
# device are 100% GA4-driven, and resort views are handled by their own dedicated
# top-5-positive/top-5-negative loop, which still uses this map's resort branch).
# ---------------------------------------------------------------------------
def variable_to_dimension(variable: str) -> dict | None:
    """
    Returns {"dimension": <ga4_dim_name>, "value": <filter_value>} or None
    if no meaningful GA4 dimension maps to this variable.
    """
    if variable.startswith("resort_view_"):
        resort_code = variable.replace("resort_view_", "")
        # Resort views tracked via Resort event with customEvent:resort_code dimension
        return {"dimension": "customEvent:resort_code", "value": resort_code, "event_filter": "Resort"}

    if variable in (
        "BE_CR", "ECVR", "ECVR_BE", "BE_Confirmation_count",
        "BE_Entry_count", "BE_Entry_Rate", "purchase_count", "total_sessions",
        "resort_views_count",
    ):
        # Core KPIs — no dimension filter, pull global funnel
        return {"dimension": None, "value": None}

    if variable == "click_price_remote_error_check_prices_count":
        # Real GA4 event is "click_price_remote", not a literal eventName match on
        # the full variable string (which returns 0/0). The specific failure reason
        # lives in customEvent:detail_click as "error_check_prices_<REASON>" (e.g.
        # NO_TRANSPORT, NO_ACCOMMODATION, NOT_ON_SALE_FOR_THE_PERIOD, NO_PRICE,
        # PRODUCT_CLOSE, ...) — confirmed live against GA4 property 310694998, Aug
        # 2026: NO_TRANSPORT is the single largest reason (356K of ~1.06M total
        # global "check prices" errors). The CSV variable is the aggregate across
        # ALL error_check_prices_* reasons, so match on the "error_check_prices"
        # substring (not an exact reason) via query_ga4_funnel's existing
        # substring-containment dimension match.
        return {
            "dimension": "customEvent:detail_click",
            "value": "error_check_prices",
            "event_filter": "click_price_remote",
        }

    if variable.startswith("click_price_remote_") and variable.endswith("_count"):
        # click_price_remote_<detail>_count -> real GA4 event "click_price_remote",
        # with <detail> carried in customEvent:detail_click (exact value, e.g.
        # "validate_participants"). Without this the generic click_ rule below
        # looks for an eventName of the full variable string and reads 0/0.
        detail = variable[len("click_price_remote_"):-len("_count")]
        return {
            "dimension": "customEvent:detail_click",
            "value": detail,
            "event_filter": "click_price_remote",
        }

    for prefix, event in (("be_entry_", "BE_Entry"), ("be_conf_", "BE_Confirmation")):
        if variable.startswith(prefix):
            # Per-resort booking-engine funnel counts: the GA4 event carries the
            # resort code in customEvent:resort_code (same dimension as resort views).
            # Generic prefix rule — any be_entry_<CODE>/be_conf_<CODE> maps the same way.
            return {
                "dimension": "customEvent:resort_code",
                "value": variable[len(prefix):],
                "event_filter": event,
            }

    if variable.startswith("channel_"):
        # The model's channel_<slug> variables are the GA4 Custom Channel Groups
        # (slug = group name lower-cased, spaces -> underscores). Match on the group
        # name via the same custom-channel-group dimension the channel sections use.
        return {
            "dimension": f"sessionCustomChannelGroup:{GA4_CUSTOM_CHANNEL_GROUP_ID}",
            "value": variable[len("channel_"):].replace("_", " "),
        }

    if variable.startswith("departure_"):
        # Real GA4 event is "page_view", not a literal eventName match on the
        # full variable string (which returns 0/0 both periods). The booking-
        # window segment lives in customEvent:departure_date_range with values
        # EXACTLY matching the suffix after "departure_" (early_booking,
        # middle_booking, late_booking) — confirmed live against GA4 property
        # 310694998, Sep 2026: all three values present with real, substantial
        # volume (e.g. late_booking: 395K occurrences). Generic suffix rule,
        # not a hardcoded list of the three current values — any future
        # departure_<segment> variable maps the same way.
        segment = variable[len("departure_"):]
        return {
            "dimension": "customEvent:departure_date_range",
            "value": segment,
            "event_filter": "page_view",
        }

    if variable.startswith("page_view_shopping_"):
        # Real GA4 event is "page_view", not a literal eventName match (returns
        # 0/0 both periods). The specific shopping page lives in
        # customEvent:page_name, which for most pages matches the suffix after
        # "page_view_" EXACTLY (page_name="shopping_offer", "shopping_search")
        # but for landing pages is a PREFIX family — "shopping_landing_<campaign>"
        # (e.g. "shopping_landing_sun_holidays", "shopping_landing_all_inclusive")
        # — confirmed live against GA4 property 310694998, Sep 2026. Matching on
        # the "shopping_<X>" substring (not an exact value) via query_ga4_funnel's
        # existing substring-containment dimension match handles both shapes with
        # one rule, without hardcoding every landing-page campaign name.
        shopping_segment = variable[len("page_view_"):]
        return {
            "dimension": "customEvent:page_name",
            "value": shopping_segment,
            "event_filter": "page_view",
        }

    if variable.startswith("click_") or variable.startswith("counter_proposal_"):
        # Event-level variables — dimension is eventName
        return {"dimension": "eventName", "value": variable}

    if variable.startswith("nights_"):
        return None  # excluded

    # GA4 native metrics that aren't event names at all — query by metric, not eventName.
    # Extend this dict if a future month surfaces another metric-shaped variable
    # (e.g. bounce_rate -> bounceRate); never patch the fallback branch below instead.
    # NOTE: avg_session_duration is deliberately absent — GA4's averageSessionDuration
    # is not trustworthy for this property and is excluded upstream in filter_results.py.
    METRIC_NAME_MAP = {
        "new_users": "newUsers",
    }
    if variable in METRIC_NAME_MAP:
        return {"dimension": None, "value": None, "metric": METRIC_NAME_MAP[variable]}

    # BE_*_count variables track a GA4 event of the same name minus the "_count" suffix
    # (same pattern already used for BE_Entry_count -> event "BE_Entry" in
    # query_device_split). Generic rule, not a hardcoded name list.
    if variable.startswith("BE_") and variable.endswith("_count"):
        event_name = variable[: -len("_count")]
        return {"dimension": "eventName", "value": event_name}

    # Default: try to match by eventName
    return {"dimension": "eventName", "value": variable}


def derive_date_ranges(data: dict) -> tuple[DateRange, DateRange, str, str]:
    """Reads the analysis month straight off analysis_input.json's own data
    (the first dated row in any bucket) rather than a hardcoded constant —
    this is what lets the pipeline "run on whatever month's CSV you dropped in"
    with zero manual editing. Mirrors verify_synthesis.py's derive_date_ranges,
    extended to also return the human-readable period labels this file's
    prompts need (PERIOD_LABEL_CURRENT/PRIOR).

    Current-period month/year come from the CSV; the prior period is always
    the same calendar month one year earlier (YoY), matching the explicability
    model's own current/date_prec convention — never computed any other way.
    """
    sample = None
    for bucket_key in ("bucket_1_top_ranked", "bucket_2_zero_imp_movers", "bucket_3_emerging"):
        for row in data.get(bucket_key, []):
            d = row.get("date", "")
            if d:
                sample = d[:10]
                break
        if sample:
            break
    if not sample:
        raise ValueError(
            "Cannot determine analysis month from analysis_input.json — no dated "
            "row found in bucket_1_top_ranked/bucket_2_zero_imp_movers/bucket_3_emerging."
        )

    year, month, _ = sample.split("-")
    year, month = int(year), int(month)
    import calendar as _calendar
    last_day = _calendar.monthrange(year, month)[1]
    prior_year = year - 1

    date_range_current = DateRange(start_date=f"{year}-{month:02d}-01", end_date=f"{year}-{month:02d}-{last_day:02d}")
    date_range_prior   = DateRange(start_date=f"{prior_year}-{month:02d}-01", end_date=f"{prior_year}-{month:02d}-{last_day:02d}")

    month_name = _calendar.month_abbr[month]
    period_label_current = f"{month_name} {year}"
    period_label_prior   = f"{month_name} {prior_year}"

    return date_range_current, date_range_prior, period_label_current, period_label_prior


# ---------------------------------------------------------------------------
# OAuth helpers
# ---------------------------------------------------------------------------
def get_ga4_credentials() -> Credentials:
    creds = None

    if OAUTH_TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(OAUTH_TOKEN_FILE), GA4_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not OAUTH_CREDENTIALS_FILE.exists():
                print(
                    f"\nERROR: OAuth credentials file not found at:\n  {OAUTH_CREDENTIALS_FILE}\n"
                    "Download it from Google Cloud Console → APIs & Services → Credentials\n"
                    "(Create OAuth 2.0 Client ID, Desktop app type, download JSON)\n",
                    file=sys.stderr,
                )
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(
                str(OAUTH_CREDENTIALS_FILE), GA4_SCOPES
            )
            # WSL2: manually build auth URL with explicit redirect_uri, listen on localhost:8080
            import webbrowser
            _original_open = webbrowser.open
            def _print_url(url, new=0, autoraise=True):
                print(f"\nOpen this URL in your Windows browser:\n\n{url}\n")
                print("Waiting for authorisation on http://localhost:8080/ ...")
                return True
            webbrowser.open = _print_url
            creds = flow.run_local_server(port=8080)
            webbrowser.open = _original_open

        with open(OAUTH_TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        print("  OAuth token saved.")

    return creds


# ---------------------------------------------------------------------------
# GA4 query — generic per-variable funnel (bucket 1/2/3 + resorts + core KPIs)
# ---------------------------------------------------------------------------
# Normalise country names from explicability model to GA4 format
COUNTRY_NAME_MAP = {
    "Israël": "Israel",
}


def to_ga4_country(name: str) -> str:
    return COUNTRY_NAME_MAP.get(name, name)


def query_ga4_funnel(
    client: BetaAnalyticsDataClient,
    dimension_name: str | None,
    dimension_value: str | list[str] | None,
    site: str,
    event_filter: str | None = None,
    metric_name: str | None = None,
) -> dict:
    """
    Pulls full-funnel metrics for both current and prior year periods.
    Filters by dimension_value (if provided) and by country (site).
    event_filter: if set, adds a dimension_filter on eventName.
    metric_name: if set, additionally requests this GA4 metric and surfaces it under
    result["metric_value"].
    Returns a dict with current/prior metrics.
    """
    ga4_country = to_ga4_country(site)

    dimensions = []
    if dimension_name:
        dimensions.append(Dimension(name=dimension_name))
    dimensions.append(Dimension(name="country"))

    def run_for_period(date_range: DateRange) -> dict:
        try:
            dim_filter = None
            if event_filter:
                dim_filter = FilterExpression(
                    filter=Filter(
                        field_name="eventName",
                        string_filter=Filter.StringFilter(
                            value=event_filter,
                            match_type=Filter.StringFilter.MatchType.EXACT
                        )
                    )
                )

            metrics = list(FUNNEL_METRICS)
            if metric_name:
                metrics.append(Metric(name=metric_name))

            request = RunReportRequest(
                property=f"properties/{GA4_PROPERTY_ID}",
                dimensions=dimensions,
                metrics=metrics,
                date_ranges=[date_range],
                dimension_filter=dim_filter,
            )
            response = client.run_report(request)
            time.sleep(GA4_REQUEST_DELAY_S)

            result = {
                "sessions": 0,
                "engaged_sessions": 0,
                "engagement_rate": None,
            }
            if metric_name:
                result["metric_name"] = metric_name
                result["metric_value"] = 0.0

            country_idx = len(dimensions) - 1

            for row in response.rows:
                dim_values = [d.value for d in row.dimension_values]

                row_country = dim_values[country_idx] if len(dim_values) > country_idx else ""
                if ga4_country.lower() not in NON_COUNTRY_SITES and ga4_country.lower() != "" and row_country.lower() != ga4_country.lower():
                    continue

                if dimension_name and dimension_value:
                    row_dim = dim_values[0] if dim_values else ""
                    values = dimension_value if isinstance(dimension_value, list) else [dimension_value]
                    if not any(v.upper() in row_dim.upper() for v in values):
                        continue

                m = row.metric_values
                result["sessions"]         += int(float(m[0].value or 0))
                result["engaged_sessions"] += int(float(m[1].value or 0))
                if metric_name:
                    result["metric_value"] += float(m[3].value or 0)

            if result["sessions"] > 0:
                if not event_filter:
                    result["engagement_rate"] = result["engaged_sessions"] / result["sessions"]

            if event_filter:
                result["engagement_rate_note"] = (
                    "Omitted — event-filtered query returns only sessions where the event fired, "
                    "making engagement rate circular. See site_engagement for the real site-wide figure."
                )

            return result

        except Exception as e:
            return {"error": str(e)}

    current = run_for_period(DATE_RANGE_CURRENT)
    prior   = run_for_period(DATE_RANGE_PRIOR)
    return {"current": current, "prior": prior}


def query_site_engagement(
    client: BetaAnalyticsDataClient,
    site: str,
) -> dict:
    """
    Unfiltered site-wide sessions + engagement rate for a given country.
    Used alongside event-filtered queries to provide meaningful site context.
    """
    ga4_country = to_ga4_country(site)

    def run_for_period(date_range: DateRange) -> dict:
        try:
            request = RunReportRequest(
                property=f"properties/{GA4_PROPERTY_ID}",
                dimensions=[Dimension(name="country")],
                metrics=[Metric(name="sessions"), Metric(name="engagedSessions")],
                date_ranges=[date_range],
            )
            response = client.run_report(request)
            time.sleep(GA4_REQUEST_DELAY_S)

            sessions, engaged = 0, 0
            for row in response.rows:
                country = row.dimension_values[0].value
                if ga4_country.lower() not in NON_COUNTRY_SITES and ga4_country.lower() != "" and country.lower() != ga4_country.lower():
                    continue
                sessions += int(float(row.metric_values[0].value or 0))
                engaged  += int(float(row.metric_values[1].value or 0))

            return {
                "sessions": sessions,
                "engaged_sessions": engaged,
                "engagement_rate": engaged / sessions if sessions > 0 else None,
            }
        except Exception as e:
            return {"error": str(e)}

    return {
        "current": run_for_period(DATE_RANGE_CURRENT),
        "prior":   run_for_period(DATE_RANGE_PRIOR),
    }


# ---------------------------------------------------------------------------
# GA4 query — Custom Channel Group breakdown, at ANY scope (global / BU / country)
# ---------------------------------------------------------------------------
def query_channel_group_breakdown(client: BetaAnalyticsDataClient, countries: list[str] | None = None) -> dict:
    """
    Pulls the FULL, unfiltered GA4 Custom Channel Group breakdown (every group GA4
    actually returns, including "Unassigned"), aggregated over `countries` — a list
    of real GA4 country dimension values. Pass None (or an empty list) for a
    property-wide, GLOBAL pull with no country filter at all. This single function
    covers every scope this pipeline needs: global (countries=None), a Business
    Unit (countries=<that BU's market list>), or a single market (countries=[site]).
    Never filters to a fixed list of channel-group NAMES — only ever a country
    scope filter — so every real group GA4 returns stays visible, "Unassigned"
    included.

    Per group, pulls sessions AND BE_Confirmation event count, so a real per-channel
    ECVR BE (BE_Confirmation / sessions) can be computed — this is the metric used
    everywhere in the card's grey line (see CARD METRIC CONVENTION), replacing the
    old "engagement rate" (GA4's generic engagedSessions/sessions, which most
    readers don't have an intuition for and doesn't reflect booking behaviour).
    Returns {"current": {group_name: {sessions, be_confirmation, ecvr_be}}, "prior": {...}}.
    """
    wanted = {c.lower() for c in countries} if countries else None
    dimension_name = f"sessionCustomChannelGroup:{GA4_CUSTOM_CHANNEL_GROUP_ID}"

    be_confirmation_filter = FilterExpression(
        filter=Filter(
            field_name="eventName",
            string_filter=Filter.StringFilter(
                value="BE_Confirmation",
                match_type=Filter.StringFilter.MatchType.EXACT,
            )
        )
    )

    def run_for_period(date_range: DateRange) -> dict:
        try:
            sessions_req = RunReportRequest(
                property=f"properties/{GA4_PROPERTY_ID}",
                dimensions=[
                    Dimension(name=dimension_name),
                    Dimension(name="country"),
                ],
                metrics=[Metric(name="sessions")],
                date_ranges=[date_range],
            )
            sessions_resp = client.run_report(sessions_req)
            time.sleep(GA4_REQUEST_DELAY_S)

            be_conf_req = RunReportRequest(
                property=f"properties/{GA4_PROPERTY_ID}",
                dimensions=[
                    Dimension(name=dimension_name),
                    Dimension(name="country"),
                ],
                metrics=[Metric(name="eventCount")],
                date_ranges=[date_range],
                dimension_filter=be_confirmation_filter,
            )
            be_conf_resp = client.run_report(be_conf_req)
            time.sleep(GA4_REQUEST_DELAY_S)

            sessions_by_group: dict = {}
            for row in sessions_resp.rows:
                group   = row.dimension_values[0].value
                country = row.dimension_values[1].value
                if wanted is not None and country.lower() not in wanted:
                    continue
                sessions_by_group[group] = sessions_by_group.get(group, 0) + int(float(row.metric_values[0].value or 0))

            be_conf_by_group: dict = {}
            for row in be_conf_resp.rows:
                group   = row.dimension_values[0].value
                country = row.dimension_values[1].value
                if wanted is not None and country.lower() not in wanted:
                    continue
                be_conf_by_group[group] = be_conf_by_group.get(group, 0) + int(float(row.metric_values[0].value or 0))

            buckets: dict = {}
            for group in set(list(sessions_by_group.keys()) + list(be_conf_by_group.keys())):
                s = sessions_by_group.get(group, 0)
                bc = be_conf_by_group.get(group, 0)
                buckets[group] = {
                    "sessions": s,
                    "be_confirmation": bc,
                    "ecvr_be": bc / s if s > 0 else None,
                }

            return buckets

        except Exception as e:
            return {"error": str(e)}

    return {
        "current": run_for_period(DATE_RANGE_CURRENT),
        "prior":   run_for_period(DATE_RANGE_PRIOR),
    }


def _yoy_relative_pct(current: float | None, prior: float | None) -> float | None:
    """Relative YoY % change between two rates (e.g. two ECVR BE values), as used
    everywhere else in this pipeline's YoY figures (BU section, top KPI bar) —
    NOT a percentage-point difference. Returns None if prior is 0/None (no
    baseline to express a relative change against)."""
    if current is None or prior is None or prior == 0:
        return None
    return (current - prior) / abs(prior) * 100.0


def _impact_score(session_share: float | None, ecvr_be_current: float | None, ecvr_be_prior: float | None) -> float | None:
    """A group's approximate DIRECT IMPACT on the overall ECVR BE: its session
    share times its own ECVR BE change (current - prior), i.e. how much this
    group's own conversion-rate movement, weighted by how much traffic it
    carries, likely moved the blended ECVR BE. This is what channel rankings
    are sorted by now (item 2 of the redesign) — NOT raw session volume, which
    only measures traffic weight and can rank a high-traffic/flat-conversion
    channel above a lower-traffic channel whose conversion rate collapsed.
    Returns None when session_share or either ECVR BE value is unavailable.
    """
    if session_share is None or ecvr_be_current is None or ecvr_be_prior is None:
        return None
    return session_share * (ecvr_be_current - ecvr_be_prior)


def top_channel_groups(breakdown: dict, top_n: int = 8, rank_by: str = "impact") -> list[dict]:
    """
    Returns a flat list of {group, sessions_current, sessions_prior,
    session_share_current, ecvr_be_current, ecvr_be_prior, ecvr_be_yoy_pct,
    impact_score} for every GA4 Custom Channel Group in the breakdown, ranked
    per `rank_by`:
      - "impact" (default): by impact_score's ABSOLUTE value, descending — the
        groups whose own ECVR BE movement (weighted by session share) most
        moved the blended rate, positive or negative. This is the ranking used
        for channel_section_global and BU-focus channel breakdowns (item 2).
      - "sessions": by current-period session count, descending (unchanged
        legacy behaviour — still used where raw traffic volume is the point,
        e.g. crossover detection's candidate pool).
    session_share_current is each group's share of TOTAL current-period sessions
    across every group GA4 returned (not just the top_n kept) — "Unassigned" is
    never excluded from ranking eligibility, hiding it would recreate the exact
    blind spot this design fixes. ecvr_be_yoy_pct is a RELATIVE percent change
    (matching every other YoY figure in this pipeline), not a pp difference.
    """
    current = breakdown.get("current", {})
    prior = breakdown.get("prior", {})
    if "error" in current or "error" in prior:
        return []
    total_current_sessions = sum(v.get("sessions", 0) for v in current.values())
    total_prior_sessions = sum(v.get("sessions", 0) for v in prior.values())
    all_groups = set(current.keys()) | set(prior.keys())
    rows = []
    for g in all_groups:
        c = current.get(g, {})
        p = prior.get(g, {})
        c_sessions = c.get("sessions", 0)
        c_ecvr = c.get("ecvr_be")
        p_ecvr = p.get("ecvr_be")
        share = c_sessions / total_current_sessions if total_current_sessions > 0 else None
        rows.append({
            "group": g,
            "sessions_current": c_sessions,
            "sessions_prior": p.get("sessions", 0),
            "confirmations_current": c.get("be_confirmation", 0),
            "confirmations_prior": p.get("be_confirmation", 0),
            "session_share_current": share,
            "session_share_prior": (p.get("sessions", 0) / total_prior_sessions) if total_prior_sessions > 0 else None,
            "sessions_yoy_pct": _yoy_relative_pct(c_sessions, p.get("sessions", 0)),
            "ecvr_be_current": c_ecvr,
            "ecvr_be_prior": p_ecvr,
            "ecvr_be_yoy_pct": _yoy_relative_pct(c_ecvr, p_ecvr),
            "impact_score": _impact_score(share, c_ecvr, p_ecvr),
        })
    if rank_by == "sessions":
        rows.sort(key=lambda r: -r["sessions_current"])
    else:
        rows.sort(key=lambda r: -abs(r["impact_score"] or 0))
    return rows[:top_n]


def _breakdown_totals(breakdown: dict) -> tuple[int, int, int, int]:
    """(sessions_current, sessions_prior, confirmations_current, confirmations_prior) summed
    over every channel group of a channel-group breakdown, i.e. the scope's own totals."""
    def tot(period: str, key: str) -> int:
        groups = breakdown.get(period, {})
        if "error" in groups:
            return 0
        return sum(v.get(key, 0) for v in groups.values())
    return tot("current", "sessions"), tot("prior", "sessions"), tot("current", "be_confirmation"), tot("prior", "be_confirmation")


def top_session_volume_shifts(breakdown: dict, top_n: int = 3) -> list[dict]:
    """
    The top_n channel groups with the largest absolute change in SESSION SHARE
    between the two periods, regardless of their ECVR BE movement. Complements
    split_channel_groups_by_impact, which ranks on ECVR BE movement and so can
    never surface a group whose volume moved a lot while its conversion stayed
    ~0 on both sides (impact_score ~ 0). Selection only — no group is excluded
    from anywhere else, and no judgement is made about whether the shift is
    campaign-driven, a relabel, or something else.
    """
    current = breakdown.get("current", {})
    prior = breakdown.get("prior", {})
    if "error" in current or "error" in prior:
        return []
    tot_c = sum(v.get("sessions", 0) for v in current.values())
    tot_p = sum(v.get("sessions", 0) for v in prior.values())
    rows = []
    for g in set(current) | set(prior):
        c_s = current.get(g, {}).get("sessions", 0)
        p_s = prior.get(g, {}).get("sessions", 0)
        share_c = c_s / tot_c if tot_c else 0.0
        share_p = p_s / tot_p if tot_p else 0.0
        rows.append({
            "group": g,
            "sessions_current": c_s,
            "sessions_prior": p_s,
            "session_share_current": share_c,
            "session_share_prior": share_p,
            "share_shift": share_c - share_p,
        })
    rows.sort(key=lambda r: -abs(r["share_shift"]))
    return rows[:top_n]


def split_channel_groups_by_impact(breakdown: dict, top_n_each: int = 3) -> tuple[list[dict], list[dict]]:
    """
    Splits ALL channel groups in the breakdown (no top_n cap on the candidate
    pool) into two SELECTED lists: the top_n_each groups whose impact_score is
    POSITIVE (helped ECVR BE) and the top_n_each whose impact_score is NEGATIVE
    (hurt ECVR BE) — selection is by impact_score magnitude (which channels
    matter most), same as before. Groups with no computable impact_score
    (missing prior/current ECVR BE) are excluded from both lists rather than
    silently sorted to one end.

    DISPLAY ORDER (within each already-selected list) is by session Weight
    descending, not by impact_score — once impact_score has done its job of
    picking which channels are worth showing, the reader wants to see them
    ranked by how much traffic each one represents, not re-sorted by a number
    that isn't itself shown on the card. Used for the 'top 3 positive / top 3
    negative' channel display (items 2-3 of the redesign).
    """
    all_rows = top_channel_groups(breakdown, top_n=10_000, rank_by="impact")
    positive = [r for r in all_rows if r["impact_score"] is not None and r["impact_score"] > 0]
    negative = [r for r in all_rows if r["impact_score"] is not None and r["impact_score"] < 0]
    positive.sort(key=lambda r: -r["impact_score"])
    negative.sort(key=lambda r: r["impact_score"])
    positive = positive[:top_n_each]
    negative = negative[:top_n_each]
    # Re-sort the SELECTED groups by session weight (descending) for display.
    positive.sort(key=lambda r: -(r["session_share_current"] or 0))
    negative.sort(key=lambda r: -(r["session_share_current"] or 0))
    return positive, negative


def _fmt_channel_rows(rows: list[dict]) -> str:
    """Renders channel rows per the CARD METRIC CONVENTION: Weight (session share) ·
    ECVR BE · Evolution (relative % YoY) — plus raw session counts for context."""
    if not rows:
        return "  (no data)"
    lines = []
    for r in rows:
        c, p = r["sessions_current"], r["sessions_prior"]
        share = r.get("session_share_current")
        share_fmt = f"{share:.1%}" if share is not None else "N/A"
        ecvr = r.get("ecvr_be_current")
        ecvr_fmt = f"{ecvr:.2%}" if ecvr is not None else "N/A"
        yoy = r.get("ecvr_be_yoy_pct")
        yoy_fmt = f"{yoy:+.1f}% YoY" if yoy is not None else "N/A YoY"
        s_yoy = r.get("sessions_yoy_pct")
        s_yoy_fmt = f", {s_yoy:+.0f}% sessions YoY" if s_yoy is not None else ""
        lines.append(
            f"  {r['group']}: Weight {share_fmt} · ECVR BE {ecvr_fmt} · {yoy_fmt} "
            f"(sessions {c:,} vs {p:,}{s_yoy_fmt}; BE confirmations "
            f"{r.get('confirmations_current', 0):,} vs {r.get('confirmations_prior', 0):,})"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# GA4 query — device split, at ANY scope (global / BU / country)
# ---------------------------------------------------------------------------
# Device categories surfaced anywhere in this pipeline. Tablet (and any other GA4
# deviceCategory value, e.g. "smart tv") is deliberately excluded — too low-volume
# to warrant its own analysis slot; mobile/desktop are the only two device types
# this pipeline reports on. Structural allowlist, not a per-month decision.
ANALYSED_DEVICES = ("mobile", "desktop")


def query_device_split(client: BetaAnalyticsDataClient, countries: list[str] | None = None) -> dict:
    """
    Queries sessions, BE_Entry and BE_Confirmation event counts split by
    deviceCategory, aggregated over `countries` (real GA4 country values), or
    property-wide when countries is None/empty. Same single-function-covers-
    every-scope design as query_channel_group_breakdown. Result is filtered to
    ANALYSED_DEVICES only (mobile/desktop) — tablet and other minor categories
    are dropped here, at the query boundary, so every downstream consumer
    (prompts, synthesis, card) never sees them.

    ecvr_be (BE_Confirmation/sessions) is the headline metric per the CARD METRIC
    CONVENTION; be_entry_rate (BE_Entry/sessions, funnel-entry only) is kept
    alongside it as supporting funnel-health detail, not the headline number.
    """
    wanted = {c.lower() for c in countries} if countries else None

    def _event_filter(event_name: str) -> FilterExpression:
        return FilterExpression(
            filter=Filter(
                field_name="eventName",
                string_filter=Filter.StringFilter(
                    value=event_name,
                    match_type=Filter.StringFilter.MatchType.EXACT,
                )
            )
        )

    def run_for_period(date_range: DateRange) -> dict:
        try:
            sessions_req = RunReportRequest(
                property=f"properties/{GA4_PROPERTY_ID}",
                dimensions=[Dimension(name="deviceCategory"), Dimension(name="country")],
                metrics=[Metric(name="sessions")],
                date_ranges=[date_range],
            )
            sessions_resp = client.run_report(sessions_req)
            time.sleep(GA4_REQUEST_DELAY_S)

            be_entry_req = RunReportRequest(
                property=f"properties/{GA4_PROPERTY_ID}",
                dimensions=[Dimension(name="deviceCategory"), Dimension(name="country")],
                metrics=[Metric(name="eventCount")],
                date_ranges=[date_range],
                dimension_filter=_event_filter("BE_Entry"),
            )
            be_entry_resp = client.run_report(be_entry_req)
            time.sleep(GA4_REQUEST_DELAY_S)

            be_conf_req = RunReportRequest(
                property=f"properties/{GA4_PROPERTY_ID}",
                dimensions=[Dimension(name="deviceCategory"), Dimension(name="country")],
                metrics=[Metric(name="eventCount")],
                date_ranges=[date_range],
                dimension_filter=_event_filter("BE_Confirmation"),
            )
            be_conf_resp = client.run_report(be_conf_req)
            time.sleep(GA4_REQUEST_DELAY_S)

            def _agg(resp) -> dict:
                out: dict = {}
                for row in resp.rows:
                    device = row.dimension_values[0].value
                    country = row.dimension_values[1].value
                    if wanted is not None and country.lower() not in wanted:
                        continue
                    out[device] = out.get(device, 0) + int(float(row.metric_values[0].value or 0))
                return out

            sessions_by_device = _agg(sessions_resp)
            be_entry_by_device = _agg(be_entry_resp)
            be_conf_by_device = _agg(be_conf_resp)

            # Total across EVERY device GA4 returns (mobile/desktop/tablet/smart tv/...)
            # so session_share below reflects each analysed device's real share of all
            # traffic, not just its share among the devices we choose to report on.
            total_sessions_all_devices = sum(sessions_by_device.values())

            result = {}
            for device in ANALYSED_DEVICES:
                s = sessions_by_device.get(device, 0)
                be = be_entry_by_device.get(device, 0)
                bc = be_conf_by_device.get(device, 0)
                result[device] = {
                    "sessions": s,
                    "be_entry": be,
                    "be_entry_rate": be / s if s > 0 else None,
                    "be_confirmation": bc,
                    "ecvr_be": bc / s if s > 0 else None,
                    "session_share": s / total_sessions_all_devices if total_sessions_all_devices > 0 else None,
                }
            return result

        except Exception as e:
            return {"error": str(e)}

    return {
        "current": run_for_period(DATE_RANGE_CURRENT),
        "prior": run_for_period(DATE_RANGE_PRIOR),
    }


def _fmt_device_rows(device_breakdown: dict) -> str:
    """Renders device rows per the CARD METRIC CONVENTION: Weight (session share) ·
    ECVR BE · Evolution (relative % YoY) — plus BE entry rate as supporting funnel
    detail. Takes the full {"current": ..., "prior": ...} breakdown (not a single
    period) so the YoY change can be computed here, consistently with
    _fmt_channel_rows."""
    curr = device_breakdown.get("current", {})
    prev = device_breakdown.get("prior", {})
    if "error" in curr or "error" in prev:
        return f"  (GA4 error: {curr.get('error') or prev.get('error')})"
    lines = []
    for device in ANALYSED_DEVICES:
        c = curr.get(device, {})
        p = prev.get(device, {})
        s = c.get("sessions", 0)
        share = c.get("session_share")
        ecvr_c = c.get("ecvr_be")
        ecvr_p = p.get("ecvr_be")
        yoy = _yoy_relative_pct(ecvr_c, ecvr_p)
        entry_rate = c.get("be_entry_rate")

        share_fmt = f"{share:.1%}" if share is not None else "N/A"
        share_p = p.get("session_share")
        share_p_fmt = f" (was {share_p:.1%})" if share_p is not None else ""
        ecvr_fmt = f"{ecvr_c:.2%}" if ecvr_c is not None else "N/A"
        yoy_fmt = f"{yoy:+.1f}% YoY" if yoy is not None else "N/A YoY"
        entry_fmt = f"{entry_rate:.1%}" if entry_rate is not None else "N/A"
        s_yoy = _yoy_relative_pct(s, p.get("sessions", 0))
        s_yoy_fmt = f", {s_yoy:+.0f}% sessions YoY" if s_yoy is not None else ""

        lines.append(
            f"  {device}: Weight {share_fmt}{share_p_fmt} · ECVR BE {ecvr_fmt} · {yoy_fmt} "
            f"(sessions {s:,}{s_yoy_fmt}, BE entry rate {entry_fmt})"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Channel × Country highlights (no new GA4 calls — reuses the per-country
# channel breakdowns already collected during the BU-focus pass). Redesigned
# rule (item 6): rather than searching for any (country, channel) pair whose
# YoY diverges from the global trend, this takes the SAME countries already
# featured in BU FOCUS (the top-3-per-BU list) and, for each, surfaces its own
# top 2 real GA4 Custom Channel Groups by DIRECT IMPACT on that country's ECVR
# BE — i.e. exactly the country roster the reader has already seen, drilled
# one level deeper into its channel mix, instead of an open-ended search that
# could surface a country never mentioned anywhere else in the report.
# ---------------------------------------------------------------------------
def compute_country_channel_highlights(
    top_countries_per_bu: dict,
    per_country_channel_rows: dict,
    top_n_per_country: int = 2,
) -> list[dict]:
    """
    For every country already listed under each BU in top_countries_per_bu,
    SELECTS that country's own top_n_per_country channels by absolute
    impact_score (which channels matter most to that country's ECVR BE), then
    re-orders those selected channels by session Weight descending for display
    — same selection-then-reorder split as split_channel_groups_by_impact.
    Returns a flat list of {country, business_unit, rank, group,
    sessions_current, sessions_prior, session_share_current, ecvr_be_current,
    ecvr_be_prior, ecvr_be_yoy_pct, impact_score}, ordered by (business_unit,
    country, rank) — a deterministic, fully-accounted-for roster (every
    BU-focus country appears, each with its own top N channels), not a
    magnitude-trimmed subset that could silently drop an entire market.
    """
    results = []
    for bu, countries in top_countries_per_bu.items():
        for country_row in countries:
            site = country_row.get("site", "")
            rows = per_country_channel_rows.get(site, [])
            selected = sorted(
                [r for r in rows if r.get("impact_score") is not None],
                key=lambda r: -abs(r["impact_score"]),
            )[:top_n_per_country]
            ranked = sorted(selected, key=lambda r: -(r.get("session_share_current") or 0))
            for rank, r in enumerate(ranked, 1):
                results.append({
                    "country": site,
                    "business_unit": bu,
                    "rank": rank,
                    **r,
                })
    return results


# ---------------------------------------------------------------------------
# LLM diagnostic prompt builders
# ---------------------------------------------------------------------------
def _load_context() -> str:
    if CONTEXT_FILE.exists():
        return CONTEXT_FILE.read_text(encoding="utf-8")
    return (
        "You are analysing data for Club Med, a premium all-inclusive resort brand operating globally. "
        "ECVR BE (Booking Engine Conversion Rate) = BE Confirmation count / total sessions. "
        "The explicability model performs a Year-on-Year monthly comparison to identify which variables "
        "most impacted the ECVR BE change."
    )

CLUBMED_CONTEXT = _load_context() + """

EVIDENCE RULE (applies to every diagnostic you write): you only have the numbers printed in
this prompt (sessions, BE confirmations, ECVR BE, device split, channel group, model
variables). Describe what moved and by how much; never state as a cause anything those numbers
do not measure — UTM/tagging/attribution faults, "stripping", "misattribution",
CRM/campaign/targeting changes, returning visitors, reclassification. If you want to suggest a
cause, phrase it as something to verify ("worth checking whether ..."), never as a finding.
"""


def build_prompt_standard(record: dict, ga4_data: dict, bucket_label: str, site_engagement: dict | None = None) -> str:
    var = record["variable"]
    site = record["site"]
    variation = record.get("variation")
    impact = record.get("impact_on_ECVR_BE", "")
    abs_wi = record.get("absolute_weighted_importance", 0)

    var_pct = f"{variation:.1%}" if variation is not None else "N/A"

    ga4_curr = ga4_data.get("current", {})
    ga4_prev = ga4_data.get("prior", {})

    def fmt(d: dict, hide_engagement: bool = False) -> str:
        if "error" in d:
            return f"  (GA4 error: {d['error']})"
        if d.get("unavailable"):
            return ("  (GA4 comparison UNAVAILABLE for this variable — no usable GA4 mapping. "
                    "This is NOT zero sessions: do not infer a dead tag, a tracking fault or "
                    "missing traffic from it.)")
        parts = [
            f"Sessions: {d.get('sessions', 0):,}",
            f"Engaged: {d.get('engaged_sessions', 0):,}",
        ]
        if d.get("be_confirmation") is not None:
            parts.append(f"BE confirmations: {d['be_confirmation']:,}")
        if d.get("ecvr_be") is not None:
            parts.append(f"ECVR BE: {d['ecvr_be']:.3%}")
        if d.get("session_share") is not None:
            parts.append(f"Share of all sessions: {d['session_share']:.1%}")
        if not hide_engagement:
            er = f"{d['engagement_rate']:.1%}" if d.get("engagement_rate") is not None else "N/A"
            parts.append(f"Engagement rate: {er}")
        if d.get("metric_name"):
            parts.append(f"{d['metric_name']}: {d.get('metric_value', 0):,.2f}")
        return "  " + " | ".join(parts)

    def fmt_site_eng(d: dict) -> str:
        if not d or "error" in d:
            return "  (unavailable)"
        er = f"{d['engagement_rate']:.1%}" if d.get("engagement_rate") is not None else "N/A"
        return f"  Sessions: {d.get('sessions', 0):,} | Engaged: {d.get('engaged_sessions', 0):,} | Engagement rate: {er}"

    is_event_filtered = ga4_curr.get("engagement_rate_note") is not None
    site_eng_block = ""
    if is_event_filtered and site_engagement:
        site_eng_block = f"""
NOTE: Engagement rate is omitted from the event-filtered data above — it would be
near 100% by definition (only sessions where the event fired are returned).
The real site-wide engagement rate for {site} is shown below instead:

  Site-wide engagement — Current period:
{fmt_site_eng(site_engagement.get("current", {}))}
  Site-wide engagement — Prior period:
{fmt_site_eng(site_engagement.get("prior", {}))}
"""

    return f"""{CLUBMED_CONTEXT}

VARIABLE ANALYSIS REQUEST
--------------------------
Variable: {var}
Site (country): {site}
Bucket: {bucket_label}
YoY variation: {var_pct}
Impact direction on ECVR BE: {impact}
Absolute weighted importance (0-100 normalised): {abs_wi:.4f}

GA4 Event-scoped Data (sessions where this variable's event fired)
  Current period:
{fmt(ga4_curr, hide_engagement=is_event_filtered)}
  Prior period:
{fmt(ga4_prev, hide_engagement=is_event_filtered)}
{site_eng_block}
Based on the above, provide a concise diagnostic (3-5 sentences) that:
1. States what changed and whether it represents a volume, quality, or funnel problem
2. Proposes the most likely root cause given the Club Med context
3. Flags any anomaly or data gap worth investigating further
Do not repeat raw numbers already visible above. Be specific and actionable.
"""


def build_prompt_emerging(record: dict, ga4_data: dict) -> str:
    var = record["variable"]
    site = record["site"]
    valeur = record.get("valeur")
    valeur_prec = record.get("valeur_prec")

    ga4_curr = ga4_data.get("current", {})

    def fmt(d: dict) -> str:
        if "error" in d:
            return f"  (GA4 error: {d['error']})"
        if d.get("unavailable"):
            return "  (GA4 comparison UNAVAILABLE — no usable GA4 mapping; this is NOT zero sessions)"
        extra = f" | BE confirmations: {d['be_confirmation']:,}" if d.get("be_confirmation") is not None else ""
        return f"  Sessions: {d.get('sessions', 0):,} | Engaged: {d.get('engaged_sessions', 0):,}{extra}"

    return f"""{CLUBMED_CONTEXT}

EMERGING VARIABLE ANALYSIS REQUEST
------------------------------------
Variable: {var}
Site (country): {site}
Prior year value: {valeur_prec} (near-zero or unavailable — likely new/in development last year)
Current year value: {valeur}
Model weight (absolute weighted importance): {record.get("absolute_weighted_importance", 0):.4f}{" — NOTE: this weight is driven by the SIZE of the YoY move on a tiny prior base, not by the model's own coefficient (" + format(record.get("importance", 0), "+.4f") + "); treat it as context, not as a driver." if record.get("extreme_yoy") else ""}

GA4 Current Period ({PERIOD_LABEL_CURRENT}):
{fmt(ga4_curr)}

This variable had little or no data in the prior year. Please assess:
1. Whether this appears to be a new feature, a new resort, or a newly tracked element
2. Whether its current volume is significant enough to warrant inclusion in the main analysis
3. Any early signals (positive or negative) visible in the GA4 data
Keep the response to 3-4 sentences.
"""


def build_prompt_device(scope_label: str, device_breakdown: dict) -> str:
    """
    Generic device-split prompt for ANY scope: global, a Business Unit, or a single
    country. scope_label names the scope in plain language (e.g. "Global (property-wide)",
    "EMEA Business Unit", "Japan").
    """
    return f"""{CLUBMED_CONTEXT}

DEVICE SPLIT ANALYSIS — {scope_label}
------------------------------------------------
GA4 device split for {scope_label} ({PERIOD_LABEL_CURRENT} vs {PERIOD_LABEL_PRIOR}):
{_fmt_device_rows(device_breakdown)}

Assess in 3-4 sentences:
1. Whether mobile ECVR BE declined more than −0.5pp YoY (flag as CRO priority if so)
2. Whether the device session mix (weight/share by device) shifted meaningfully
3. Which device is under the most pressure and what that implies for {scope_label}
Be specific and actionable. Do not repeat raw numbers already visible above.
"""


def build_prompt_channel(scope_label: str, positive_rows: list[dict], negative_rows: list[dict]) -> str:
    """
    Generic channel-breakdown prompt for ANY scope. Only ever names GA4's New
    Custom Channel Group values — never the old explicability-CSV channel_*
    variable names, which this pipeline no longer surfaces anywhere. Rows are
    pre-split by direct impact on ECVR BE (positive vs negative), matching the
    top-3-positive/top-3-negative structure the card displays (items 2-3).
    """
    return f"""{CLUBMED_CONTEXT}

NEW CUSTOM CHANNEL GROUP ANALYSIS — {scope_label}
------------------------------------------------------
Real GA4 Custom Channel Group breakdown for {scope_label}, ranked by DIRECT IMPACT on
ECVR BE (session weight x conversion-rate movement) — NOT by raw session volume.
"Unassigned" is included if it ranks, since it reflects sessions GA4's configured
rules don't currently classify into any named group.

Top channels HELPING ECVR BE:
{_fmt_channel_rows(positive_rows)}

Top channels HURTING ECVR BE:
{_fmt_channel_rows(negative_rows)}

Assess in 3-4 sentences:
1. Which channel group(s) are most responsible for the {scope_label} ECVR BE change — name them explicitly
2. Whether a meaningful share of traffic falls under "Unassigned" (a GA4 rule coverage
   gap, not a genuine behavioural signal) — call this out if so
3. Whether the dominant driver is a volume/mix shift (session weight) or a genuine
   conversion-quality change (ECVR BE itself moving)
Only ever refer to these real GA4 Custom Channel Group names. Do not invent or reference
any other channel taxonomy.
"""


def build_prompt_bu(bu_row: dict, device_breakdown: dict, channel_positive: list[dict], channel_negative: list[dict]) -> str:
    bu = bu_row["business_unit"]
    pct = bu_row.get("pct_change")
    impact = bu_row.get("impact_on_ECVR_BE", "")
    ecvr = bu_row.get("ecvr_be")
    ecvr_prior = bu_row.get("ecvr_be_prior")

    pct_fmt = f"{pct:+.1%}" if pct is not None else "N/A"
    ecvr_fmt = f"{ecvr:.4%}" if ecvr is not None else "N/A"
    ecvr_prior_fmt = f"{ecvr_prior:.4%}" if ecvr_prior is not None else "N/A"

    return f"""{CLUBMED_CONTEXT}

BUSINESS UNIT ANALYSIS — {bu}
--------------------------------
ECVR BE {PERIOD_LABEL_CURRENT}: {ecvr_fmt}  |  {PERIOD_LABEL_PRIOR}: {ecvr_prior_fmt}  |  YoY: {pct_fmt}
Impact direction on global ECVR BE: {impact}

GA4 Device split for {bu} ({PERIOD_LABEL_CURRENT} vs {PERIOD_LABEL_PRIOR}):
{_fmt_device_rows(device_breakdown)}

GA4 New Custom Channel Group breakdown for {bu}, ranked by DIRECT IMPACT on {bu}'s ECVR BE:
Top channels HELPING {bu}'s ECVR BE:
{_fmt_channel_rows(channel_positive)}
Top channels HURTING {bu}'s ECVR BE:
{_fmt_channel_rows(channel_negative)}

In 3-5 sentences, assess:
1. Whether {bu} is a net positive or negative contributor to the global ECVR BE change, and by how much
2. The device pattern within {bu} — you MUST discuss BOTH Mobile AND Desktop explicitly, even when one
   device's ECVR BE moved more than the other. Mobile typically carries most of {bu}'s session WEIGHT
   even when Desktop's own rate moved more — a device carrying 70-80% of sessions is never a footnote,
   state its own ECVR BE and trend explicitly, not just "mobile is flat" as an aside to the desktop story.
3. The channel pattern within {bu} — name real GA4 Custom Channel Group(s) only
Be specific and actionable.
"""


def build_prompt_country_focus(
    country_row: dict,
    session_weight_in_bu: float | None,
    device_breakdown: dict,
    channel_top_rows: list[dict],
) -> str:
    site = country_row["site"]
    bu = country_row.get("business_unit", "")
    pct_change = country_row.get("pct_change")
    ecvr_y = country_row.get("ecvr_be_y")
    ecvr_y1 = country_row.get("ecvr_be_y1")

    pct_fmt = f"{pct_change:.1%}" if pct_change is not None else "N/A"
    ecvr_fmt = f"{ecvr_y:.2%}" if ecvr_y is not None else "N/A"
    ecvr1_fmt = f"{ecvr_y1:.2%}" if ecvr_y1 is not None else "N/A"
    weight_fmt = f"{session_weight_in_bu:.1%}" if session_weight_in_bu is not None else "N/A"

    return f"""{CLUBMED_CONTEXT}

COUNTRY FOCUS — {site} ({bu} Business Unit)
----------------------------------------------
Weight (share of {bu}'s sessions): {weight_fmt}
ECVR BE {PERIOD_LABEL_CURRENT}: {ecvr_fmt}  |  {PERIOD_LABEL_PRIOR}: {ecvr1_fmt}  |  YoY: {pct_fmt}

GA4 Device split for {site} ({PERIOD_LABEL_CURRENT} vs {PERIOD_LABEL_PRIOR}):
{_fmt_device_rows(device_breakdown)}

GA4 New Custom Channel Group breakdown for {site} (ranked by current sessions):
{_fmt_channel_rows(channel_top_rows)}

Provide a concise market diagnostic (3-4 sentences):
1. Whether {site} is a net positive or negative contributor to the {bu} / global ECVR BE shift
2. Whether the driver is volume, device mix, channel mix, or conversion quality
3. Name the specific real GA4 Custom Channel Group(s) or device most responsible, if any stand out
Be specific and actionable. Do not repeat raw numbers already visible above.
"""


def build_prompt_crossover(highlight: dict) -> str:
    """
    Prompt for one (country, channel group) highlight — the country's own
    top-2-by-impact real GA4 Custom Channel Group, for a country already
    featured in BU FOCUS. Grounded entirely in that country's own numbers, no
    cross-country/global comparison (see compute_country_channel_highlights).
    """
    country = highlight["country"]
    bu = highlight["business_unit"]
    group = highlight["group"]
    c, p = highlight["sessions_current"], highlight["sessions_prior"]
    share = highlight.get("session_share_current")
    ecvr = highlight.get("ecvr_be_current")
    yoy = highlight.get("ecvr_be_yoy_pct")

    share_fmt = f"{share:.1%}" if share is not None else "N/A"
    ecvr_fmt = f"{ecvr:.2%}" if ecvr is not None else "N/A"
    yoy_fmt = f"{yoy:+.1f}%" if yoy is not None else "N/A"

    return f"""{CLUBMED_CONTEXT}

CHANNEL × COUNTRY HIGHLIGHT — {group} in {country} ({bu})
------------------------------------------------------------
This is one of {country}'s top real GA4 Custom Channel Groups by direct impact on
its own ECVR BE this period (session weight × ECVR BE movement).

{group} in {country}: {c:,} sessions ({PERIOD_LABEL_CURRENT}) vs {p:,} ({PERIOD_LABEL_PRIOR})
Weight: {share_fmt} of {country}'s sessions | ECVR BE: {ecvr_fmt} | YoY: {yoy_fmt}

In 2-3 sentences:
1. Whether this channel's movement in {country} is driving that market's ECVR BE up or down
2. The most likely cause (campaign change, budget shift, seasonal pattern, tracking gap)
Be specific to {country} — do not generalise to other markets.
"""


def build_prompt_resort(record: dict, ga4_data: dict, direction_label: str, site_engagement: dict | None = None) -> str:
    """Thin wrapper around build_prompt_standard with resort-appropriate framing."""
    return build_prompt_standard(record, ga4_data, f"Top {direction_label} resort view (Global, property-wide)", site_engagement)


def build_prompt_core_kpi(records: list) -> str:
    lines = []
    for r in records:
        if r.get("site") == "Global":
            v = r.get("valeur")
            vp = r.get("valeur_prec")
            var_pct = f"{r['variation']:.1%}" if r.get("variation") is not None else "N/A"
            lines.append(f"  {r['variable']}: {v} (prior: {vp}, YoY: {var_pct})")

    kpi_block = "\n".join(lines) if lines else "  (no global rows found)"

    return f"""{CLUBMED_CONTEXT}

CORE KPI SUMMARY REQUEST
--------------------------
The following KPIs are provided as context for the monthly summary.
They are not individually analysed (importance set to 0 by design — too directly correlated).

{kpi_block}

In 2-3 sentences, summarise the overall KPI health for {PERIOD_LABEL_CURRENT} vs {PERIOD_LABEL_PRIOR}.
Flag any KPI showing an unusually large move that stakeholders should be aware of.
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if GA4_PROPERTY_ID == "REPLACE_WITH_YOUR_PROPERTY_ID":
        print("ERROR: Set GA4_PROPERTY_ID in the script before running.", file=sys.stderr)
        sys.exit(1)

    if not ANTHROPIC_API_KEY:
        print("ERROR: Set ANTHROPIC_API_KEY environment variable before running.", file=sys.stderr)
        sys.exit(1)

    print("Loading analysis_input.json...")
    with open(INPUT_JSON, encoding="utf-8") as f:
        data = json.load(f)

    global DATE_RANGE_CURRENT, DATE_RANGE_PRIOR, PERIOD_LABEL_CURRENT, PERIOD_LABEL_PRIOR
    DATE_RANGE_CURRENT, DATE_RANGE_PRIOR, PERIOD_LABEL_CURRENT, PERIOD_LABEL_PRIOR = derive_date_ranges(data)
    print(f"Analysis period detected from data: {PERIOD_LABEL_CURRENT} vs {PERIOD_LABEL_PRIOR}")

    print("Authenticating with GA4 (browser window will open if first run)...")
    creds = get_ga4_credentials()
    ga4_client = BetaAnalyticsDataClient(credentials=creds)

    llm_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def ask_llm(prompt: str, max_tokens: int = 400) -> str:
        time.sleep(LLM_REQUEST_DELAY_S)
        try:
            msg = llm_client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text.strip()
        except Exception as e:
            return f"LLM error: {e}"

    output = {
        "meta": {
            **data["meta"],
            # Structured period info derived above — lets the later steps build an
            # accurate "analysis_month" without guessing from source_file (a raw
            # CSV filename, not a human-readable month).
            "analysis_month": f"{PERIOD_LABEL_CURRENT} vs {PERIOD_LABEL_PRIOR}",
            "period_label_current": PERIOD_LABEL_CURRENT,
            "period_label_prior": PERIOD_LABEL_PRIOR,
        },
        "bucket_1_insights": [],
        "bucket_2_insights": [],
        "bucket_3_insights": [],
        "bucket_4_core_kpi_summary": None,
        "global_device": None,
        "global_channel": None,
        "bu_insights": [],
        "channel_country_crossovers": [],
        "resort_insights_positive": [],
        "resort_insights_negative": [],
    }

    import threading
    _channel_cache: dict = {}
    _channel_lock = threading.Lock()

    def _enrich_channel_row(var: str, site: str, ga4_data: dict) -> None:
        """channel_<slug> variables are Custom Channel Groups. query_ga4_funnel only returns
        sessions/engagement for them, which let the text talk about 'quality' with no
        conversion data. Add the group's own BE confirmations, ECVR BE and share of sessions
        from the channel-group breakdown (same scope: the row's market, or global)."""
        if site.lower() in NON_COUNTRY_SITES and site.lower() != "global":
            return
        slug = var[len("channel_"):]
        with _channel_lock:
            if site not in _channel_cache:
                countries = None if site.lower() == "global" else [to_ga4_country(site)]
                _channel_cache[site] = query_channel_group_breakdown(ga4_client, countries=countries)
            bd = _channel_cache[site]
        for period in ("current", "prior"):
            groups = bd.get(period, {})
            if "error" in groups or "error" in ga4_data.get(period, {}):
                continue
            total = sum(v.get("sessions", 0) for v in groups.values())
            for gname, gv in groups.items():
                if gname.lower().replace(" ", "_") == slug:
                    ga4_data[period]["be_confirmation"] = gv.get("be_confirmation", 0)
                    ga4_data[period]["ecvr_be"] = gv.get("ecvr_be")
                    ga4_data[period]["session_share"] = (gv.get("sessions", 0) / total) if total else None
                    break

    def analyse_record(record: dict, bucket_label: str, prompt_fn) -> dict:
        var = record["variable"]
        site = record["site"]
        print(f"    [{bucket_label}] {var} | {site}")

        dim = variable_to_dimension(var)
        if dim is None:
            # No GA4 mapping at all: say so explicitly. An empty dict would print as
            # "Sessions: 0" and read as a dead tag.
            ga4_data = {"current": {"unavailable": True}, "prior": {"unavailable": True}}
        else:
            ga4_data = query_ga4_funnel(
                ga4_client, dim["dimension"], dim["value"], site,
                event_filter=dim.get("event_filter"),
                metric_name=dim.get("metric"),
            )
            gc, gp = ga4_data.get("current", {}), ga4_data.get("prior", {})
            if ("error" not in gc and "error" not in gp
                    and gc.get("sessions", 0) == 0 and gp.get("sessions", 0) == 0
                    and ((record.get("valeur") or 0) != 0 or (record.get("valeur_prec") or 0) != 0)):
                # The model has volume for this variable but GA4 returns nothing in either
                # period: the mapping does not resolve, which is a gap in this pipeline,
                # not evidence about the site.
                ga4_data = {"current": {"unavailable": True}, "prior": {"unavailable": True}}
            elif var.startswith("channel_"):
                _enrich_channel_row(var, site, ga4_data)

        site_engagement = None
        if dim and dim.get("event_filter"):
            site_engagement = query_site_engagement(ga4_client, site)

        prompt = prompt_fn(record, ga4_data, site_engagement) if site_engagement else prompt_fn(record, ga4_data)
        insight = ask_llm(prompt, max_tokens=400)

        return {
            **record,
            "ga4_data": ga4_data,
            "site_engagement": site_engagement,
            "insight": insight,
        }

    # Records are independent (one GA4 query + one LLM call each), so the three
    # bucket loops run through a small thread pool. executor.map preserves input
    # order, so the output lists are identical to the sequential version. Workers
    # are capped well below GA4's concurrent-request limit.
    from concurrent.futures import ThreadPoolExecutor
    RECORD_WORKERS = 4

    def _run_bucket(title, records, label, prompt_fn):
        print(f"\n{title} ({len(records)} records)...")
        with ThreadPoolExecutor(max_workers=RECORD_WORKERS) as pool:
            return list(pool.map(lambda rec: analyse_record(rec, label, prompt_fn), records))

    output["bucket_1_insights"] = _run_bucket(
        "Bucket 1 — Top ranked", data["bucket_1_top_ranked"], "ranked",
        lambda r, g, se=None: build_prompt_standard(r, g, "Top ranked (non-zero importance)", se))
    output["bucket_2_insights"] = _run_bucket(
        "Bucket 2 — Zero-imp movers", data["bucket_2_zero_imp_movers"], "mover",
        lambda r, g, se=None: build_prompt_standard(r, g, "Zero-importance mover (|variation| > 5%)", se))
    output["bucket_3_insights"] = _run_bucket(
        "Bucket 3 — Emerging", data["bucket_3_emerging"], "emerging",
        lambda r, g, se=None: build_prompt_emerging(r, g))

    # --- GLOBAL device split ---
    print("\nGlobal device split...")
    global_device_breakdown = query_device_split(ga4_client, countries=None)
    global_device_insight = ask_llm(build_prompt_device("Global (property-wide)", global_device_breakdown), max_tokens=400)
    output["global_device"] = {"breakdown": global_device_breakdown, "insight": global_device_insight}

    # --- GLOBAL New Custom Channel Group breakdown ---
    # Ranked by DIRECT IMPACT on ECVR BE (session weight x rate movement), split
    # into top-3 positive / top-3 negative (item 2+3 of this redesign) — replaces
    # the previous single list ranked by raw session volume, which could surface
    # a high-traffic/flat-conversion channel ahead of a lower-traffic channel
    # whose conversion rate actually moved the needle.
    print("Global New Custom Channel Group breakdown...")
    global_channel_breakdown = query_channel_group_breakdown(ga4_client, countries=None)
    global_channel_positive, global_channel_negative = split_channel_groups_by_impact(global_channel_breakdown, top_n_each=3)
    global_channel_insight = ask_llm(
        build_prompt_channel("Global (property-wide)", global_channel_positive, global_channel_negative),
        max_tokens=400,
    )
    output["global_channel"] = {
        "positive": global_channel_positive,
        "negative": global_channel_negative,
        "volume_shifts": top_session_volume_shifts(global_channel_breakdown, top_n=3),
        "insight": global_channel_insight,
    }

    # --- BU-level focus: weight/change + device + channel + top-3 countries each ---
    bu_markets_map = data["meta"].get("bu_markets_map", {})
    bu_breakdown = data.get("bu_breakdown", [])
    top_countries_per_bu = data.get("top_countries_per_bu", {})

    per_country_channel_rows = {}  # for country-channel-highlight lookup: {country: [group rows]}

    print(f"\nBU focus — {len(bu_breakdown)} Business Units...")
    for bu_row in bu_breakdown:
        bu = bu_row["business_unit"]
        print(f"  [BU] {bu}")
        raw_markets = bu_markets_map.get(bu, [])
        ga4_markets = list({to_ga4_country(m) for m in raw_markets})

        bu_device = query_device_split(ga4_client, countries=ga4_markets)
        bu_channel_breakdown = query_channel_group_breakdown(ga4_client, countries=ga4_markets)
        bu_channel_positive, bu_channel_negative = split_channel_groups_by_impact(bu_channel_breakdown, top_n_each=3)
        bu_insight = ask_llm(
            build_prompt_bu(bu_row, bu_device, bu_channel_positive, bu_channel_negative),
            max_tokens=500,
        )

        # Total current-period sessions for the whole BU (across ANALYSED_DEVICES),
        # used below to compute each of its countries' session_weight_in_bu — no
        # extra GA4 call needed, reuses bu_device already fetched above.
        bu_total_sessions = sum(
            bu_device.get("current", {}).get(d, {}).get("sessions", 0) for d in ANALYSED_DEVICES
        )

        bu_sess_c, bu_sess_p, bu_conf_c, bu_conf_p = _breakdown_totals(bu_channel_breakdown)

        country_entries = []
        for country_row in top_countries_per_bu.get(bu, []):
            site = country_row["site"]
            print(f"    [country] {site}")
            ga4_country = to_ga4_country(site)

            country_device = query_device_split(ga4_client, countries=[ga4_country])
            country_channel_breakdown = query_channel_group_breakdown(ga4_client, countries=[ga4_country])
            # Full impact-ranked pool (uncapped) — used ONLY for the country-
            # channel-highlight lookup below (item 6); kept out of country_entries
            # so it never bloats the per-country data block.
            country_channel_full = top_channel_groups(country_channel_breakdown, top_n=50, rank_by="impact")
            per_country_channel_rows[site] = country_channel_full
            # Trimmed top-6-by-impact view — this is what actually gets displayed
            # in this country's own channel_breakdown field.
            country_channel_top = country_channel_full[:6]

            country_total_sessions = sum(
                country_device.get("current", {}).get(d, {}).get("sessions", 0) for d in ANALYSED_DEVICES
            )
            session_weight_in_bu = country_total_sessions / bu_total_sessions if bu_total_sessions > 0 else None

            country_insight = ask_llm(
                build_prompt_country_focus(country_row, session_weight_in_bu, country_device, country_channel_top),
                max_tokens=400,
            )

            c_sess_c, c_sess_p, c_conf_c, c_conf_p = _breakdown_totals(country_channel_breakdown)
            country_entries.append({
                **country_row,
                "sessions_current": c_sess_c, "sessions_prior": c_sess_p,
                "confirmations_current": c_conf_c, "confirmations_prior": c_conf_p,
                "session_weight_in_bu": session_weight_in_bu,
                "device_breakdown": country_device,
                "channel_breakdown": country_channel_top,
                "insight": country_insight,
            })

        output["bu_insights"].append({
            **bu_row,
            "sessions_current": bu_sess_c, "sessions_prior": bu_sess_p,
            "confirmations_current": bu_conf_c, "confirmations_prior": bu_conf_p,
            "device_breakdown": bu_device,
            "channel_positive": bu_channel_positive,
            "channel_negative": bu_channel_negative,
            "insight": bu_insight,
            "countries": country_entries,
        })

    # --- Channel × Country highlights (no new GA4 calls) ---
    # Item 6 redesign: reuses the SAME country roster already featured in BU FOCUS
    # (top_countries_per_bu) rather than an open-ended search across all markets —
    # for each of those countries, its own top 2 real GA4 Custom Channel Groups by
    # direct impact on that country's ECVR BE.
    print("\nChannel × Country highlights (top 2 per BU-focus country)...")
    highlights = compute_country_channel_highlights(top_countries_per_bu, per_country_channel_rows, top_n_per_country=2)
    print(f"  {len(highlights)} highlight(s) found")
    for h in highlights:
        insight = ask_llm(build_prompt_crossover(h), max_tokens=300)
        output["channel_country_crossovers"].append({**h, "insight": insight})

    # --- Resort focus: top 5 positive / top 5 negative (Global scope) ---
    top_resorts_positive = data.get("top_resorts_positive", [])
    top_resorts_negative = data.get("top_resorts_negative", [])

    print(f"\nResort focus — top {len(top_resorts_positive)} positive...")
    for rec in top_resorts_positive:
        result = analyse_record(rec, "resort-positive", lambda r, g, se=None: build_prompt_resort(r, g, "positive", se))
        output["resort_insights_positive"].append(result)

    print(f"Resort focus — top {len(top_resorts_negative)} negative...")
    for rec in top_resorts_negative:
        result = analyse_record(rec, "resort-negative", lambda r, g, se=None: build_prompt_resort(r, g, "negative", se))
        output["resort_insights_negative"].append(result)

    # --- Bucket 4: Core KPI summary (single LLM call) ---
    print("\nBucket 4 — Core KPI summary...")
    core_records = data["bucket_4_core_kpi_snapshot"]
    output["bucket_4_core_kpi_summary"] = ask_llm(build_prompt_core_kpi(core_records), max_tokens=300)

    # --- Write output ---
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)

    total = (
        len(output["bucket_1_insights"])
        + len(output["bucket_2_insights"])
        + len(output["bucket_3_insights"])
        + sum(len(bu["countries"]) for bu in output["bu_insights"])
        + len(output["resort_insights_positive"])
        + len(output["resort_insights_negative"])
    )
    print(f"\nDone — {total} records analysed ({len(output['bu_insights'])} BUs, "
          f"{len(output['channel_country_crossovers'])} crossovers).")
    print(f"Output written to: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
