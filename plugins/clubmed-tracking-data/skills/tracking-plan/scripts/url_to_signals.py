#!/usr/bin/env python3
"""
URL → signals adapter for the tracking-plan skill (url source mode).

Turns the RAW JSON that the url-agent collected from agent-browser into one
`signals/<screen>.json` file in the **figma-client shape** that the inference agent
already consumes — plus an `observed_events[]` block listing the tracking that is
ALREADY LIVE on the page (parsed from GA4 /collect hits and the data layer).

Zero third-party dependencies (stdlib only). Deterministic and unit-testable: the LLM
agent only collects raw inputs; this script does the structured transformation.

Inputs (all optional except --snapshot and --screen):
  --snapshot   path to JSON from `agent-browser snapshot -i --json`
               shape: {"data": {"origin": "...", "refs": {"e1": {"name","role"}}, "snapshot": "<tree>"}}
  --network    path to JSON from `agent-browser network requests --json`
               shape: {"data": {"requests": [{"method","resourceType","url","status",...}]}}
  --datalayer  path to JSON: the result of eval'ing window.clubMedLayer || window.dataLayer
               either a raw JSON array, or {"data": {"result": [...] }}
  --boxes      path to JSON map {selector_or_ref: "images/previews/<file>.png"} for per-element crops
  --screen     screen name (e.g. "desktop")
  --screenshot screen-level screenshot_path (relative, e.g. images/previews/desktop.png)
  --out        output signals/<screen>.json path

Run: python3 url_to_signals.py --snapshot snap.json --network net.json \
        --datalayer dl.json --screen desktop --screenshot images/previews/desktop.png \
        --out OUTPUT_DIR/signals/desktop.json
"""

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote


# ── GA4 /collect detection ─────────────────────────────────────────────────────

_COLLECT_RE = re.compile(r"(/g/collect|/collect|google-analytics\.com|/gtag/|/gtm\.js|/g/s/collect)", re.I)


def _load(path):
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _unwrap(obj, *keys):
    """agent-browser --json wraps payloads in {"data": {...}}. Unwrap defensively."""
    if isinstance(obj, dict) and "data" in obj and isinstance(obj["data"], dict):
        obj = obj["data"]
    for k in keys:
        if isinstance(obj, dict) and k in obj:
            return obj[k]
    return obj


# ── Observed events (existing live tracking) ───────────────────────────────────


def parse_collect_url(url):
    """Parse a GA4 /collect URL into {event, params{}}.

    GA4 Measurement Protocol query keys: en = event name, ep.<k> = string event param,
    epn.<k> = numeric event param, up.<k> = user property.
    """
    q = parse_qs(urlparse(url).query)
    flat = {k: v[0] for k, v in q.items() if v}
    event = flat.get("en")
    if not event:
        return None
    params = []
    for k, v in flat.items():
        if k.startswith("ep.") or k.startswith("epn.") or k.startswith("up."):
            name = k.split(".", 1)[1]
            ptype = "number" if k.startswith("epn.") else "string"
            params.append({"name": name, "type": ptype, "example": unquote(v)})
    return {"event": event, "evidence": "collect", "params": params}


def events_from_network(network):
    requests = _unwrap(network, "requests") or []
    if not isinstance(requests, list):
        return []
    out = []
    for r in requests:
        url = r.get("url", "") if isinstance(r, dict) else ""
        if url and _COLLECT_RE.search(url):
            parsed = parse_collect_url(url)
            if parsed:
                out.append(parsed)
    return out


def events_from_datalayer(datalayer):
    dl = _unwrap(datalayer, "result")
    if not isinstance(dl, list):
        return []
    out = []
    for entry in dl:
        if not isinstance(entry, dict):
            continue
        event = entry.get("event")
        if not event:
            continue
        params = [
            {"name": k, "type": "number" if isinstance(v, (int, float)) else "string",
             "example": json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)}
            for k, v in entry.items() if k != "event"
        ]
        out.append({"event": event, "evidence": "datalayer", "params": params})
    return out


def dedupe_observed(events):
    """Merge by event name; collect-sourced wins (real network proof)."""
    by_name = {}
    for e in events:
        name = e["event"]
        if name not in by_name:
            by_name[name] = {"event": name, "origin": "confirmed",
                             "evidence": e["evidence"], "params": e.get("params", [])}
        else:
            # prefer collect evidence, merge params by name
            if e["evidence"] == "collect":
                by_name[name]["evidence"] = "collect"
            seen = {p["name"] for p in by_name[name]["params"]}
            for p in e.get("params", []):
                if p["name"] not in seen:
                    by_name[name]["params"].append(p)
                    seen.add(p["name"])
    return list(by_name.values())


# ── Interactive elements (figma-client-shaped signals) ─────────────────────────

# roles that represent a user-triggerable interaction
_INTERACTIVE_ROLES = {"button", "link", "tab", "menuitem", "checkbox", "radio",
                      "switch", "option", "combobox", "slider", "textbox", "searchbox"}
# roles whose text is worth keeping as semantic content
_HEADING_ROLES = {"heading"}


def signals_from_snapshot(snapshot):
    refs = _unwrap(snapshot, "refs") or {}
    interactions, instances, texts = [], [], []
    cta_primary = None
    for ref_id, meta in refs.items() if isinstance(refs, dict) else []:
        if not isinstance(meta, dict):
            continue
        name = (meta.get("name") or "").strip()
        role = (meta.get("role") or "").strip().lower()
        node_id = f"dom:{ref_id}"
        instances.append({
            "name": name or role or ref_id,
            "designer_notes": None,
            "semantic_hints": {"role": role},
            "node_id": node_id,
        })
        if role in _INTERACTIVE_ROLES:
            interactions.append({
                "path": name or ref_id,
                "node_id": node_id,
                "name": name or role,
                "depth": 0,
                "triggers": ["ON_CLICK"],
                "actions": [{"type": "DOM"}],
                "source": "dom",
                "role": role,
                "accessible_name": name,
            })
            if cta_primary is None and role in ("button", "link") and name:
                cta_primary = name
        if role in _HEADING_ROLES and name:
            texts.append({"role": "heading", "content": name})
    return interactions, instances, texts, cta_primary


def build(args):
    snapshot = _load(args.snapshot)
    network = _load(args.network)
    datalayer = _load(args.datalayer)
    boxes = _load(args.boxes) or {}

    interactions, instances, texts, cta_primary = signals_from_snapshot(snapshot or {})

    observed = dedupe_observed(
        events_from_network(network or {}) + events_from_datalayer(datalayer or {})
    )

    origin = None
    if isinstance(snapshot, dict):
        origin = _unwrap(snapshot, "origin") if "origin" in (snapshot.get("data", {}) or {}) else None

    out = {
        "screen": args.screen,
        "source": "dom",
        "url": origin,
        "interactions": interactions,
        "instances": instances,
        "texts": texts,
        "hidden_layers": [],
        "semantic_hints": {
            "inferred": True,
            "viewport": args.screen,
            "content_roles": {"cta_primary": cta_primary},
        },
        "component_descriptions": {},
        "screenshot_path": args.screenshot,
        "screenshots": boxes if isinstance(boxes, dict) else {},
        "observed_events": observed,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ signals written: {out_path}")
    print(f"  interactions={len(interactions)} · instances={len(instances)} · "
          f"observed_events={len(observed)} (existing live tracking)")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Transform agent-browser raw JSON into a signals/<screen>.json")
    ap.add_argument("--snapshot")
    ap.add_argument("--network")
    ap.add_argument("--datalayer")
    ap.add_argument("--boxes")
    ap.add_argument("--screen", required=True)
    ap.add_argument("--screenshot", default=None)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if not args.snapshot:
        print("ERROR: --snapshot is required", file=sys.stderr)
        return 1
    return build(args)


if __name__ == "__main__":
    sys.exit(main())
