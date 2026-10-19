"""
ECVR-forensics v2 — verified claims.

Every comparison, ranking and "who drives it" statement in the narrative layer starts here, computed
by code from forensics_output.json (GA4). A claim is a numbered sentence with:
  * text      — the deterministic sentence, with every figure it uses;
  * subject   — the entity the claim is about (a comparison word may only be used about its subject);
  * licenses  — the comparison words the claim PROVES (e.g. "rank1" = largest/most, "only", "dominant",
                "avg_above"/"avg_below", "all", "majority"). A narrative sentence that uses such a word
                must cite a claim that licenses it for the entity it names.

The model writes the analysis; compose.py checks each sentence against the claims it cites and
replaces any sentence the claims do not support with the claim's own text. Nothing here names a
market, channel, resort or month.
"""
import re

NEGLIGIBLE_BP = 0.05       # below this a rate/mix effect is "negligible", not a direction
DOMINANT_SHARE = 2 / 3     # an effect "dominates" when it is at least this share of |rate|+|mix|
TOTAL_SHARE = 0.95         # "entirely / purely / wholly / exclusively" needs at least this share
MIN_CONFIRMATIONS = 50

# comparison words -> the license a cited claim must carry (checked in this order)
LICENSE_PATTERNS = [
    ("majority", re.compile(r"\b(majority|most (?:BUs|business units|markets|channels|devices)|several)\b", re.I)),
    ("rank1", re.compile(r"\b(largest|biggest|steepest|greatest|heaviest|deepest|most)\b", re.I)),
    ("only", re.compile(r"\b(?:only(?!\s+[-+]?\d)|sole|solely)\b", re.I)),
    ("total", re.compile(r"\b(?:almost entirely|entirely|purely|wholly|exclusively|completely|fully|solely driven|"
                         r"nothing but|pure (?:mix|rate) effect)\b", re.I)),
    ("dominant", re.compile(r"\b(dominat\w*|primar\w*|mainly|largely|predominantly|"
                            r"driven (?:mostly|mainly))\b", re.I)),
    ("avg_above", re.compile(r"above[- ](?:the )?(?:\w+ )?average|higher[- ]than[- ]average", re.I)),
    ("avg_below", re.compile(r"below[- ](?:the )?(?:\w+ )?average|lower[- ]than[- ]average", re.I)),
    ("all", re.compile(r"\b(all|every)\b", re.I)),
]


def f2(x):
    """Signed 2-decimal figure that never prints a negative zero ("-0.00")."""
    t = f"{x:+.2f}"
    return "+0.00" if t == "-0.00" else t


def _bp(x):
    return f"{f2(x)} bp"


def _pct(x, d=1):
    if x is None:
        return "N/A"
    t = f"{x:+.{d}f}%"
    return "+0.0%" if t == "-0.0%" else t


def _share(c):
    return f"{c['share'][0]:.1%} to {c['share'][1]:.1%}"


def _dominance(rate, mix):
    r, m = abs(rate), abs(mix)
    if r + m < NEGLIGIBLE_BP:
        return "negligible", "both effects are negligible"
    if r / (r + m) >= DOMINANT_SHARE:
        return "rate", "mostly its own conversion (rate)"
    if m / (r + m) >= DOMINANT_SHARE:
        return "mix", "mostly its traffic share (mix)"
    return "both", "a mix of its own conversion (rate) and its traffic share (mix)"


def dom_licenses(rate, mix):
    """Licences earned by a rate/mix split: 'dominant' at >= DOMINANT_SHARE, and the stricter 'total'
    ('entirely', 'purely'...) only at >= TOTAL_SHARE of |rate|+|mix|."""
    r, m = abs(rate), abs(mix)
    if r + m < NEGLIGIBLE_BP:
        return set()
    top = max(r, m) / (r + m)
    out = set()
    if top >= DOMINANT_SHARE:
        out.add("dominant")
    if top >= TOTAL_SHARE:
        out.add("total")
    return out


# A recurring model variable is PROPERTY-WIDE when most of the markets that list it move like the global row.
PW_TOLERANCE = 0.5        # a market "moves like global" if same sign and within this fraction of the global move
PW_MIN_SHARE = 0.75       # share of the listing markets that must move like global
PW_MIN_MARKETS = 3        # fewer listing markets is not a recurring pattern

# A channel group is RECURRING when it moves ECVR by at least RC_MIN_BP in the same direction in RC_MIN_MARKETS
# markets and is not already one of the global top RC_GLOBAL_TOP channels per direction.
RC_MIN_BP = 0.3
RC_MIN_MARKETS = 3
RC_GLOBAL_TOP = 3         # matches compose.CHANNELS_PER_SIDE
RC_MAX = 5                # recurring-channel claims kept
OFFSET_MIN_SHARE = 1 / 2   # an offset is claimed only when the smaller opposite effect cancels at least this share of the larger (half: 'partly')
RC_DOMINANCE = 2          # same-direction markets must be at least this many times the opposite-direction markets


def property_wide(fx: dict, ai: dict) -> list:
    """Recurring model CHANNEL variables whose markets mostly move like the global row, joined with the GA4
    global component of that channel group and the GA4 check of each market lead. Generic: variables, markets
    and channel groups all come from the data; nothing is named here."""
    out = []
    g = next((s for s in fx["scopes"] if s["level"] == "global" and "totals" in s), None)
    if not g:
        return out
    groups = {c["group"].lower().replace(" ", "_"): c for c in g["by_channel"]}
    for dv in ai.get("meta", {}).get("dominant_variables", []):
        var = dv["variable"]
        gv, inst = dv.get("global_variation"), dv.get("instances") or []
        if not var.startswith("channel_") or gv is None or gv == 0 or len(inst) < PW_MIN_MARKETS:
            continue
        comp = groups.get(var[len("channel_"):])
        if not comp:
            continue
        similar, outliers = [], []
        for i in inst:
            v = i.get("variation")
            ok = v is not None and (v > 0) == (gv > 0) and abs(v - gv) <= PW_TOLERANCE * abs(gv)
            (similar if ok else outliers).append(i["site"])
        if len(similar) / len(inst) < PW_MIN_SHARE:
            continue
        leads = [c for c in fx.get("lead_checks", []) if c["variable"] == var]
        confirmed = [(c["site"], c["ga4_contribution_bp"]) for c in leads if c.get("status") == "confirmed"]
        negligible = [c["site"] for c in leads if c.get("status") == "GA4 contribution negligible"]
        contradict = [(c["site"], c["ga4_contribution_bp"]) for c in leads if str(c.get("status", "")).startswith("DISCREPANCY")]
        unchecked = [c["site"] for c in leads if str(c.get("status", "")).startswith("not checkable")]
        out.append({"variable": var, "group": comp["group"], "comp": comp, "global_variation": gv,
                    "listing": len(inst), "similar": similar, "outliers": outliers, "confirmed": confirmed,
                    "negligible": negligible, "contradict": contradict, "unchecked": unchecked})
    return out


class Claims:
    def __init__(self):
        self.items = []

    def add(self, text, subject=None, licenses=(), scope="", short=None, kind=None, pair=None, key=None):
        cid = f"C{len(self.items) + 1}"
        self.items.append({"id": cid, "text": text, "subject": subject, "licenses": set(licenses), "scope": scope,
                           "short": short, "kind": kind, "pair": pair, "key": key})
        return cid

    def by_id(self):
        return {c["id"]: c for c in self.items}

    def listing(self):
        out = []
        for c in self.items:
            lic = (" {licenses: " + ", ".join(sorted(c["licenses"])) + (f" for {c['subject']}" if c["subject"] else "") + "}") if c["licenses"] else ""
            out.append(f"[{c['id']}] {c['text']}{lic}")
        return "\n".join(out)



def scope_detail_claims(K, s):
    """Per-channel DETAIL claims (dominance licences earned by that channel's own rate/mix split) and one OFFSET claim
    (the largest positive and the largest negative channel act in opposite directions: arithmetic, not interpretation)
    for a BU / market scope. These are what lets a sentence say 'mostly its own conversion' or 'partly offset by'
    about a named channel, and only when the figures prove it."""
    chans = sorted(s["by_channel"], key=lambda c: -abs(c["total_bp"]))[:3]
    for c in chans:
        dm, dwhy = _dominance(c["rate_bp"], c["mix_bp"])
        K.add(f"{s['scope']} DETAIL: {c['group']} moved {s['scope']}'s ECVR {_bp(c['total_bp'])}: {dwhy} (rate {_bp(c['rate_bp'])}, "
              f"mix {_bp(c['mix_bp'])}); traffic share {_share(c)}.",
              subject=c["group"], licenses=dom_licenses(c["rate_bp"], c["mix_bp"]), scope=s["scope"], kind="detail",
              key=f"cross:{s['scope']}:{c['group']}")
    for d in s["by_device"]:
        if d["group"] == "other devices":
            continue
        dm, dwhy = _dominance(d["rate_bp"], d["mix_bp"])
        e0, e1 = d["ecvr"]
        K.add(f"{s['scope']} DEVICE: {d['group']} moved {s['scope']}'s ECVR {_bp(d['total_bp'])}: {dwhy} (rate {_bp(d['rate_bp'])}, "
              f"mix {_bp(d['mix_bp'])}); traffic share {_share(d)}; its own ECVR {e0 * 100:.3f}% to {e1 * 100:.3f}%.",
              subject=d["group"], licenses=dom_licenses(d["rate_bp"], d["mix_bp"]), scope=s["scope"], kind="detail",
              key=f"dev:{s['scope']}:{d['group']}")
    comps = [c for c in s["by_channel"] if abs(c["total_bp"]) >= NEGLIGIBLE_BP]
    pos = max((c for c in comps if c["total_bp"] > 0), key=lambda c: c["total_bp"], default=None)
    neg = min((c for c in comps if c["total_bp"] < 0), key=lambda c: c["total_bp"], default=None)
    if pos and neg:
        big, small = (pos, neg) if pos["total_bp"] >= -neg["total_bp"] else (neg, pos)
        share = abs(small["total_bp"]) / abs(big["total_bp"])
        if share < OFFSET_MIN_SHARE:
            return
        K.add(f"{s['scope']} OFFSET: {pos['group']} ({_bp(pos['total_bp'])}) and {neg['group']} ({_bp(neg['total_bp'])}) act in "
              f"opposite directions on {s['scope']}'s ECVR and sum to {_bp(pos['total_bp'] + neg['total_bp'])}; {small['group']} cancels "
              f"{share:.0%} of {big['group']}'s effect (arithmetic on the two figures).",
              subject=s["scope"], licenses={"offset"}, scope=s["scope"], kind="offset", pair=(pos["group"], neg["group"]),
              key=f"off:{s['scope']}")


def build(fx: dict, ai: dict) -> Claims:
    K = Claims()
    scopes = {s["scope"]: s for s in fx["scopes"] if "totals" in s}
    g = next(s for s in fx["scopes"] if s["level"] == "global" and "totals" in s)
    t = g["totals"]
    bus = [s for s in fx["scopes"] if s["level"] == "bu" and "totals" in s]
    markets = [s for s in fx["scopes"] if s["level"] == "market" and "totals" in s]
    E0 = t["ecvr"][0]

    # ---------------- headline
    sess_yoy = (t["sessions"][1] / t["sessions"][0] - 1) * 100
    K.add(f"Global ECVR BE moved {_pct(t['ecvr_yoy_pct'])} ({_bp(t['delta_bp'])}), from {t['ecvr'][0] * 100:.3f}% to "
          f"{t['ecvr'][1] * 100:.3f}%; sessions {t['sessions'][0]:,.0f} to {t['sessions'][1]:,.0f} ({_pct(sess_yoy)}); "
          f"BE confirmations {t['confirmations'][0]:,.0f} to {t['confirmations'][1]:,.0f}.", scope="global")
    rate_sum = sum(c["rate_bp"] for c in g["by_channel"])
    mix_sum = sum(c["mix_bp"] for c in g["by_channel"])
    dom, why = _dominance(rate_sum, mix_sum)
    K.add(f"Across channel groups, the global change is the sum of own-conversion (rate) effects of {_bp(rate_sum)} and "
          f"traffic-mix effects of {_bp(mix_sum)}.", subject="the global change",
          licenses=dom_licenses(rate_sum, mix_sum), scope="global")
    dev_rate = sum(d["rate_bp"] for d in g["by_device"])
    dev_mix = sum(d["mix_bp"] for d in g["by_device"])
    K.add(f"Across devices, own-conversion (rate) effects total {_bp(dev_rate)} and traffic-mix effects {_bp(dev_mix)}.",
          scope="global")

    # ---------------- devices
    devs = [d for d in g["by_device"] if d["group"] != "other devices"]
    worst_dev = min(devs, key=lambda d: d["total_bp"]) if devs else None
    for d in devs:
        dm, dwhy = _dominance(d["rate_bp"], d["mix_bp"])
        lic = dom_licenses(d["rate_bp"], d["mix_bp"])
        e0, e1 = d["ecvr"]
        K.add(f"{d['group'].capitalize()} moved global ECVR {_bp(d['total_bp'])}: {dwhy} (rate {_bp(d['rate_bp'])}, mix "
              f"{_bp(d['mix_bp'])}); its traffic share went {_share(d)} and its own ECVR {e0 * 100:.3f}% to {e1 * 100:.3f}%.",
              subject=d["group"], licenses=lic, scope="global", key=f"dev:global:{d['group']}")
    if worst_dev and worst_dev["total_bp"] < -NEGLIGIBLE_BP:
        K.add(f"{worst_dev['group'].capitalize()} is the largest device drag on global ECVR ({_bp(worst_dev['total_bp'])}).",
              subject=worst_dev["group"], licenses={"rank1"}, scope="global")

    # ---------------- channels (global)
    chans = sorted(g["by_channel"], key=lambda c: c["total_bp"])
    neg = [c for c in chans if c["total_bp"] < -NEGLIGIBLE_BP]
    pos = [c for c in reversed(chans) if c["total_bp"] > NEGLIGIBLE_BP]

    def chan_claim(c, label):
        dm, dwhy = _dominance(c["rate_bp"], c["mix_bp"])
        lic = dom_licenses(c["rate_bp"], c["mix_bp"])
        e0, e1 = c["ecvr"]
        avg = ""
        if c["confirmations"][0] > 0 and c["share"][0] > 0:
            if e0 > E0:
                avg, lic = " It converted ABOVE the global average a year ago.", lic | {"avg_above"}
            elif e0 < E0:
                avg, lic = " It converted BELOW the global average a year ago.", lic | {"avg_below"}
        thin = (f" Small base: {c['confirmations'][0]:,.0f} vs {c['confirmations'][1]:,.0f} confirmations."
                if min(c["confirmations"]) < MIN_CONFIRMATIONS else "")
        K.add(f"{c['group']} moved global ECVR {_bp(c['total_bp'])} ({label}): {dwhy} (rate {_bp(c['rate_bp'])}, mix "
              f"{_bp(c['mix_bp'])}); traffic share {_share(c)}; sessions {c['sessions'][0]:,.0f} to {c['sessions'][1]:,.0f}; "
              f"confirmations {c['confirmations'][0]:,.0f} to {c['confirmations'][1]:,.0f}.{avg}{thin}",
              subject=c["group"], licenses=lic, scope="global", key=f"chan:global:{c['group']}")

    for i, c in enumerate(neg[:4]):
        chan_claim(c, "largest negative channel effect" if i == 0 else f"negative channel effect #{i + 1}")
        if i == 0:
            K.items[-1]["licenses"].add("rank1")
    for i, c in enumerate(pos[:3]):
        chan_claim(c, "largest positive channel effect" if i == 0 else f"positive channel effect #{i + 1}")
        if i == 0:
            K.items[-1]["licenses"].add("rank1")

    # ---------------- BU contribution to the global change
    contrib = fx.get("bu_contribution", [])
    if contrib:
        ranked = sorted(contrib, key=lambda c: c["total_bp"])
        for c in ranked:
            dm, dwhy = _dominance(c["rate_bp"], c["mix_bp"])
            K.add(f"{c['group']} contributed {_bp(c['total_bp'])} to the GLOBAL ECVR change: {dwhy} (rate {_bp(c['rate_bp'])}, "
                  f"mix {_bp(c['mix_bp'])}).", subject=c["group"],
                  licenses=dom_licenses(c["rate_bp"], c["mix_bp"]), scope="global", key=f"buspl:{c['group']}")
        if ranked[0]["total_bp"] < -NEGLIGIBLE_BP:
            K.add(f"{ranked[0]['group']} is the largest negative contributor to the global change ({_bp(ranked[0]['total_bp'])}).",
                  subject=ranked[0]["group"], licenses={"rank1"}, scope="global")
        positives = [c for c in contrib if c["total_bp"] > NEGLIGIBLE_BP]
        K.add("Business Units with a positive contribution to the global change: "
              + (", ".join(f"{c['group']} ({_bp(c['total_bp'])})" for c in positives) or "none") + ".",
              subject=positives[0]["group"] if len(positives) == 1 else None,
              licenses={"only"} if len(positives) == 1 else (), scope="global")

    # ---------------- each BU in its own units
    for s in bus:
        tt = s["totals"]
        ch = sorted(s["by_channel"], key=lambda c: -abs(c["total_bp"]))[:1]
        dv = sorted([d for d in s["by_device"] if d["group"] != "other devices"], key=lambda d: -abs(d["total_bp"]))[:1]
        extra = ""
        lic = set()
        subj = None
        if ch:
            extra += f" Largest channel effect there: {ch[0]['group']} ({_bp(ch[0]['total_bp'])} in {s['scope']}'s own ECVR)."
            subj = ch[0]["group"]; lic.add("rank1")
        if dv:
            extra += f" Largest device effect there: {dv[0]['group']} ({_bp(dv[0]['total_bp'])} in {s['scope']}'s own ECVR)."
        K.add(f"{s['scope']}'s own ECVR moved {_pct(tt['ecvr_yoy_pct'])} ({_bp(tt['delta_bp'])} in its own units); sessions "
              f"{tt['sessions'][0]:,.0f} to {tt['sessions'][1]:,.0f}; confirmations {tt['confirmations'][0]:,.0f} to "
              f"{tt['confirmations'][1]:,.0f}.{extra}", subject=subj, licenses=lic, scope=s["scope"])

    # ---------------- cross-BU patterns (does the same group behave the same way everywhere?)
    def pattern(kind, name, getter, field):
        cells = []
        for s in bus:
            c = getter(s)
            if c:
                cells.append((s["scope"], c[field], c["total_bp"]))
        if not cells:
            return
        neg_b = [(b, v) for b, v, _ in cells if v < -NEGLIGIBLE_BP]
        pos_b = [(b, v) for b, v, _ in cells if v > NEGLIGIBLE_BP]
        label = "own-conversion (rate)" if field == "rate_bp" else "traffic-mix"
        if len(neg_b) == len(cells):
            lic = {"all", "majority"}
        elif len(neg_b) * 2 > len(cells):
            lic = {"majority"}
        else:
            lic = set()
        txt = (f"{name}'s {label} effect is negative in {len(neg_b)} of {len(cells)} Business Units "
               f"({', '.join(f'{b} {_bp(v)}' for b, v in neg_b) or 'none'}) and positive in "
               f"{', '.join(f'{b} {_bp(v)}' for b, v in pos_b) or 'none'}; figures are in each BU's own ECVR units.")
        K.add(txt, subject=name, licenses=lic, scope="cross-BU")

    for c in (neg[:3] + pos[:1]):
        pattern("channel", c["group"], lambda s, n=c["group"]: next((x for x in s["by_channel"] if x["group"] == n), None), "rate_bp")
    for d in devs:
        pattern("device", d["group"].capitalize(), lambda s, n=d["group"]: next((x for x in s["by_device"] if x["group"] == n), None), "rate_bp")

    # ---------------- markets
    for s in markets:
        tt = s["totals"]
        ch = sorted(s["by_channel"], key=lambda c: -abs(c["total_bp"]))[:2]
        dv = sorted([d for d in s["by_device"] if d["group"] != "other devices"], key=lambda d: -abs(d["total_bp"]))[:1]
        bits = [f"{c['group']} {_bp(c['total_bp'])} (rate {_bp(c['rate_bp'])}, mix {_bp(c['mix_bp'])})" for c in ch]
        thin = (f" Small base: {tt['confirmations'][0]:,.0f} vs {tt['confirmations'][1]:,.0f} confirmations."
                if min(tt["confirmations"]) < MIN_CONFIRMATIONS else "")
        K.add(f"{s['scope']} ({s.get('business_unit', '')}): own ECVR {_pct(tt['ecvr_yoy_pct'])} ({_bp(tt['delta_bp'])} in its own "
              f"units); sessions {tt['sessions'][0]:,.0f} to {tt['sessions'][1]:,.0f}. Largest channel effects: " + "; ".join(bits)
              + (f". Largest device effect: {dv[0]['group']} ({_bp(dv[0]['total_bp'])})" if dv else "") + f".{thin}",
              subject=ch[0]["group"] if ch else None, licenses={"rank1"} if ch else (), scope=s["scope"])

    # ---------------- per-market detail claims (one per market) used for the one-sentence market reads
    for s in markets:
        tt = s["totals"]
        chs = sorted(s["by_channel"], key=lambda c: -abs(c["total_bp"]))[:3]
        dvs = [d for d in s["by_device"] if d["group"] != "other devices"]
        parts = []
        for c in chs:
            dm, dwhy = _dominance(c["rate_bp"], c["mix_bp"])
            parts.append(f"{c['group']} {_bp(c['total_bp'])} (rate {_bp(c['rate_bp'])}, mix {_bp(c['mix_bp'])}; traffic share {_share(c)}; "
                         f"confirmations {c['confirmations'][0]:,.0f} to {c['confirmations'][1]:,.0f})")
        dparts = [f"{d['group']} {_bp(d['total_bp'])} (rate {_bp(d['rate_bp'])}, mix {_bp(d['mix_bp'])})" for d in dvs]
        thin = (f" Whole-market base is small: {tt['confirmations'][0]:,.0f} vs {tt['confirmations'][1]:,.0f} confirmations."
                if min(tt["confirmations"]) < MIN_CONFIRMATIONS else "")
        lic = {"rank1"} if chs else set()
        K.add(f"MARKET READ {s['scope']}: own ECVR {_pct(tt['ecvr_yoy_pct'])} ({_bp(tt['delta_bp'])} in its own units), sessions "
              f"{tt['sessions'][0]:,.0f} to {tt['sessions'][1]:,.0f}, confirmations {tt['confirmations'][0]:,.0f} to {tt['confirmations'][1]:,.0f}. "
              f"Largest channel effects: " + "; ".join(parts) + ". Devices: " + "; ".join(dparts) + f".{thin}",
              subject=chs[0]["group"] if chs else None, licenses=lic, scope=s["scope"], key=f"mktread:{s['scope']}")
        scope_detail_claims(K, s)
    for s in bus:
        tt = s["totals"]
        chs = sorted(s["by_channel"], key=lambda c: -abs(c["total_bp"]))[:3]
        dvs = [d for d in s["by_device"] if d["group"] != "other devices"]
        parts = [f"{c['group']} {_bp(c['total_bp'])} (rate {_bp(c['rate_bp'])}, mix {_bp(c['mix_bp'])})" for c in chs]
        dparts = [f"{d['group']} {_bp(d['total_bp'])} (rate {_bp(d['rate_bp'])}, mix {_bp(d['mix_bp'])})" for d in dvs]
        K.add(f"BU READ {s['scope']}: own ECVR {_pct(tt['ecvr_yoy_pct'])} ({_bp(tt['delta_bp'])} in its own units), sessions "
              f"{tt['sessions'][0]:,.0f} to {tt['sessions'][1]:,.0f}, confirmations {tt['confirmations'][0]:,.0f} to {tt['confirmations'][1]:,.0f}. "
              f"Largest channel effects: " + "; ".join(parts) + ". Devices: " + "; ".join(dparts) + ".",
              subject=chs[0]["group"] if chs else None, licenses={"rank1"} if chs else set(), scope=s["scope"],
              key=f"buread:{s['scope']}")
        scope_detail_claims(K, s)

    # ---------------- property-wide recurring model variables (one claim each)
    for pw in property_wide(fx, ai):
        c = pw["comp"]
        s_yoy = (c["sessions"][1] / c["sessions"][0] - 1) * 100 if c["sessions"][0] else None
        checkable = len(pw["confirmed"]) + len(pw["negligible"]) + len(pw["contradict"])
        conf_txt = ""
        if checkable:
            conf_txt = (f" GA4 confirms a contribution in the model's direction in {len(pw['confirmed'])} of {checkable} checkable markets"
                        + (" (" + ", ".join(f"{m} {_bp(v)}" for m, v in pw["confirmed"]) + " in each market's own ECVR units)" if pw["confirmed"] else "")
                        + (f"; negligible in {', '.join(pw['negligible'])}" if pw["negligible"] else "")
                        + (f"; contradicted in {', '.join(m for m, _ in pw['contradict'])}" if pw["contradict"] else "") + ".")
        out_txt = f" Outliers vs the global move: {', '.join(pw['outliers'])}." if pw["outliers"] else ""
        thin = (f" Small base: {c['confirmations'][0]:,.0f} vs {c['confirmations'][1]:,.0f} confirmations."
                if min(c["confirmations"]) < MIN_CONFIRMATIONS else "")
        K.add(f"{pw['group']} is a property-wide pattern: the model variable moves {_pct(pw['global_variation'] * 100)} globally and is flagged in "
              f"{pw['listing']} markets, {len(pw['similar'])} of which move like the global figure. GA4 globally: sessions "
              f"{c['sessions'][0]:,.0f} to {c['sessions'][1]:,.0f} ({_pct(s_yoy)}), BE confirmations {c['confirmations'][0]:,.0f} to "
              f"{c['confirmations'][1]:,.0f}; effect on global ECVR {_bp(c['total_bp'])} (rate {_bp(c['rate_bp'])}, mix {_bp(c['mix_bp'])}).{conf_txt}{out_txt}{thin}",
              subject=pw["group"], licenses={"majority"} if len(pw["similar"]) * 2 > pw["listing"] else (), scope="global")

    # ---------------- recurring channel effects: the same channel group moves ECVR materially, in the same
    # direction, in several markets, but is not among the global top channels (so no other card covers it)
    gch = sorted(g["by_channel"], key=lambda c: c["total_bp"])
    covered = {c["group"] for c in gch[:RC_GLOBAL_TOP] + gch[-RC_GLOBAL_TOP:]}
    rec = {}
    for s in markets:
        for c in s["by_channel"]:
            if abs(c["total_bp"]) >= RC_MIN_BP and c["group"] not in covered:
                rec.setdefault((c["group"], c["total_bp"] < 0), []).append((s["scope"], c))
    ranked = sorted(((k, v) for k, v in rec.items()
                     if len(v) >= RC_MIN_MARKETS and len(v) >= RC_DOMINANCE * len(rec.get((k[0], not k[1]), []))),
                    key=lambda kv: (-len(kv[1]), -sum(abs(c["total_bp"]) for _, c in kv[1])))
    for (group, neg), rows in ranked[:RC_MAX]:
        rows = sorted(rows, key=lambda r: abs(r[1]["total_bp"]), reverse=True)
        thin = [m for m, c in rows if min(c["confirmations"]) < MIN_CONFIRMATIONS]
        K.add(f"RECURRING CHANNEL EFFECT: {group} {'lowered' if neg else 'raised'} ECVR by at least {RC_MIN_BP} bp in "
              f"{len(rows)} of {len(markets)} analysed markets: "
              + "; ".join(f"{m} {_bp(c['total_bp'])} (rate {_bp(c['rate_bp'])}, mix {_bp(c['mix_bp'])})" for m, c in rows)
              + " (each market's own ECVR units). Global GA4 effect of this channel group: "
              + _bp(next((c["total_bp"] for c in g["by_channel"] if c["group"] == group), 0.0)) + "."
              + (f" Small base in {', '.join(thin)}." if thin else ""),
              subject=group, scope="recurring",
              short=(f"{group} {'lowered' if neg else 'raised'} ECVR by {RC_MIN_BP} bp or more in {len(rows)} of {len(markets)} "
                     f"analysed markets, {'mostly through traffic mix' if sum(abs(c['mix_bp']) for _, c in rows) >= 2 * sum(abs(c['rate_bp']) for _, c in rows) else 'mostly through own conversion' if sum(abs(c['rate_bp']) for _, c in rows) >= 2 * sum(abs(c['mix_bp']) for _, c in rows) else 'through both conversion and traffic mix'}: "
                     + ", ".join(f"{m} {_bp(c['total_bp'])}" for m, c in rows) + " (each in that market's own ECVR units)"
                     + (f"; small base in {', '.join(thin)}" if thin else "") + "."))

    # ---------------- all model-vs-GA4 channel discrepancies on a thin base, as ONE enumerated claim
    disc = [c for c in fx.get("lead_checks", []) if str(c.get("status", "")).startswith("DISCREPANCY")]
    if disc:
        names = [f"{c['variable'][len('channel_'):].replace('_', ' ').title()} in {c['site']} "
                 f"(model {c['model_direction']}, GA4 {_bp(c['ga4_contribution_bp'])})" for c in disc]
        word = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven", 8: "Eight"}.get(len(disc), str(len(disc)))
        K.add(f"{word} model channel leads disagree with GA4 on direction, all on a thin GA4 base (likely noise): "
              + "; ".join(names) + ".", scope="leads")

    # ---------------- model vs GA4
    for d in fx.get("discrepancies", []):
        K.add(f"Model vs GA4 [{d['scope']}]: {re.sub(r'channel_([a-z0-9_]+)', lambda m: m.group(1).replace('_', ' ').title(), d['flag'])}.",
              scope=d["scope"])
    for r in fx.get("resort_checks", []):
        v, c = r["views"], r["confirmations"]
        code = r["variable"][len("resort_view_"):]
        vy = (v[1] / v[0] - 1) * 100 if v[0] else None
        cy = (c[1] / c[0] - 1) * 100 if c[0] else None
        rel = (f" In relative terms confirmations moved {'more' if cy > vy else 'less'} favourably than views "
               f"({_pct(cy, 0)} vs {_pct(vy, 0)}).") if (vy is not None and cy is not None) else ""
        thin = f" Small base: {c[0]:,} vs {c[1]:,} confirmations." if min(c) < MIN_CONFIRMATIONS else ""
        K.add(f"Resort {code}: GA4 views {v[0]:,} to {v[1]:,} ({_pct(vy, 0)}); BE confirmations {c[0]:,} to {c[1]:,}"
              f"{' (' + _pct(cy, 0) + ')' if cy is not None else ''}.{rel}{thin}", scope="resort", key=f"resort:{code}")
    for c in fx.get("lead_checks", []):
        if c.get("status") in ("confirmed",) or str(c.get("status", "")).startswith("DISCREPANCY"):
            nm = c["variable"][len("channel_"):].replace("_", " ").title()
            extra = ""
            if c.get("ga4_share"):
                sh, cf = c["ga4_share"], c["ga4_confirmations"]
                extra = (f" The channel's share of {c['site']}'s sessions went {sh[0]:.1%} to {sh[1]:.1%}; its BE confirmations "
                         f"{cf[0]:,.0f} to {cf[1]:,.0f}." + (" Small base." if min(cf) < MIN_CONFIRMATIONS else ""))
            K.add(f"Model lead {nm} in {c['site']}: model direction {c['model_direction']}; GA4 contribution "
                  f"{_bp(c['ga4_contribution_bp'])} (rate {_bp(c['ga4_rate_bp'])}, mix {_bp(c['ga4_mix_bp'])}); status "
                  f"{c['status']}.{extra}", scope=c["site"], key=f"lead:{c['variable'].replace('channel_', '')}:{c['site']}")
    for c in fx.get("variable_checks", []):
        cx = c.get("ctx")
        if not cx or c.get("status") == "not checkable":
            continue
        a, b = c["ga4_counts"]
        sess, conf = cx["sessions"], cx["confirmations"]
        sy = (sess[1] / sess[0] - 1) * 100 if sess[0] else None
        ky = (conf[1] / conf[0] - 1) * 100 if conf[0] else None
        thin = " Small base." if min(conf) < MIN_CONFIRMATIONS else ""
        K.add(f"SIGNAL {c['variable'].replace('_', ' ')} in {c['site']}: GA4 events {a:,} to {b:,} ({_pct(c['ga4_yoy_pct'], 0)}); the model counts it "
              f"as pulling ECVR {c.get('model_impact') or 'in an unknown direction'}. In {c['site']} sessions moved {_pct(sy, 0)} "
              f"({sess[0]:,} to {sess[1]:,}) and BE confirmations {_pct(ky, 0)} ({conf[0]:,} to {conf[1]:,}).{thin}",
              scope=c["site"], key=f"sig:{c['variable']}:{c['site']}")
    return K


# ------------------------------------------------------------------ validation of model-written text
def used_licenses(sentence: str):
    s = sentence
    found = []
    for key, pat in LICENSE_PATTERNS:
        if pat.search(s):
            found.append(key)
            s = pat.sub(" ", s)          # a phrase counts once (e.g. "most BUs" is not also "most")
    return found


def sentence_supported(sentence: str, claim_objs: list, known_scopes=()):
    """True when every comparison word in the sentence is licensed by the cited claims TAKEN TOGETHER:
    the claims that carry the licence (and whose subject, if any, the sentence names) must between them
    cover every scope (market / Business Unit) the sentence names. A claim about the global figure
    therefore cannot license a statement about one BU, while one claim per BU can license a sentence
    that names several. Returns (ok, reason)."""
    low = sentence.lower()
    named = {n for n in known_scopes if re.search(r"\b" + re.escape(n.lower()) + r"\b", low)}
    for key in used_licenses(sentence):
        covered = set()
        has = False
        for c in claim_objs:
            if key in c["licenses"] and (not c["subject"] or c["subject"].lower() in low):
                has = True
                covered |= {n for n in known_scopes if re.search(r"\b" + re.escape(n.lower()) + r"\b", c["text"].lower())}
                if c["scope"]:
                    covered.add(c["scope"])
        if not has or not named <= covered:
            return False, f"'{key}' wording not licensed by the cited claims"
    return True, ""
