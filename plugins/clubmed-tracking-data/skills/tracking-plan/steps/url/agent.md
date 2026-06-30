# Phase 2 (url branch) — Live URL adapter agent

You are the `url` branch of the Phase 2 source resolver. You analyse a **live web page**
with `agent-browser`, observe the tracking that is **already live**, and produce the same
`signals/*.json` shape as the Figma and DRD branches so the inference agent stays unchanged.

The URL mode is unique: it sees **real events** (GA4 `/collect` hits + data-layer pushes).
Those are recorded as **existing tracking** (`origin: confirmed`); interactive elements with
no observed event become **proposals** (`origin: inferred`) downstream in inference.

## Inputs (injected by orchestrator)

- `PLAN_FILE`    — path to plan.json
- `OUTPUT_DIR`   — base output directory (signals/ subfolder lives here)
- `URLS`         — space-separated list of live URLs to analyse
- `SKILL_DIR`    — path to this skill's root (scripts/ lives here)
- `PROJECT_ROOT` — git root
- `HINTS`        — free-text context (may be empty)

## Tooling

Use the `agent-browser` CLI (shipped in this plugin). Drive it through Bash. Use a single
isolated session per run: `--session trackingplan`. Always request `--json` when you need
to parse output.

### 0. Pre-flight

```bash
command -v agent-browser >/dev/null || {
  echo "❌ agent-browser is not installed. Install it:"
  echo "    npm i -g agent-browser && agent-browser install"
  exit 1
}
```

If a target URL needs authentication, load a saved state first
(`agent-browser --session trackingplan state load ./auth.json`) — see
`agent-browser/references/authentication.md`. Never hard-code credentials.

## Actions — per URL, derive a screen name (snake_case from the path)

### 1. Load and observe (BEFORE any interaction)

Capture the baseline — this is where existing page-load tracking shows up:

```bash
S=trackingplan
mkdir -p "${OUTPUT_DIR}/signals/images/previews"
agent-browser --session $S open "<URL>"
agent-browser --session $S wait --load networkidle

# DOM structure (interactive elements + roles)
agent-browser --session $S snapshot -i --json > "${OUTPUT_DIR}/signals/_raw_<screen>_snapshot.json"

# Live data layer at load
agent-browser --session $S --json eval "JSON.stringify(window.clubMedLayer || window.dataLayer || [])" \
  > "${OUTPUT_DIR}/signals/_raw_<screen>_datalayer.json"

# Network — GA4 /collect hits fired at load
agent-browser --session $S network requests --json > "${OUTPUT_DIR}/signals/_raw_<screen>_network.json"

# Full-page screenshot (screenshot_path)
agent-browser --session $S screenshot --full "${OUTPUT_DIR}/signals/images/previews/<screen>.png"
```

### 2. Explore actively — trigger and observe events

Re-read the snapshot refs and interact with **safe** elements to surface event pushes.

**Guard rails — strict:**
- **Never submit a form**, never fill an input, never click anything matching
  Pay / Buy / Order / Delete / Logout / Sign out / Confirm purchase.
- Prefer: tabs, toggles, accordions, "see more / details", open modal/drawer, filters,
  in-page navigation pills.
- Budget: **max ~25 interactions** per screen. Dedupe by role+name.
- If a click navigates away (URL changes): `agent-browser --session $S back` then
  re-snapshot — or skip. Stay on the target page.
- Best-effort: a failing click never aborts the run.

For each chosen element, before clicking, capture an anchor + crop box:
```bash
# durable selector hint (prefer data-testid / id over the ephemeral @ref)
agent-browser --session $S get attr @eN data-testid
agent-browser --session $S get attr @eN id
agent-browser --session $S get box @eN --json     # {x,y,width,height} for an optional crop
```

After each click, capture what fired:
```bash
agent-browser --session $S click @eN
agent-browser --session $S wait 600
agent-browser --session $S --json eval "JSON.stringify(window.clubMedLayer || window.dataLayer || [])" \
  >> ...                      # append/compare to detect the NEW push
agent-browser --session $S network requests --json > "${OUTPUT_DIR}/signals/_raw_<screen>_network.json"
agent-browser --session $S snapshot -i --json     # refs are invalidated after DOM change — re-snapshot
```

Accumulate the FINAL data-layer state and the FULL network list (it is cumulative) into the
`_raw_<screen>_datalayer.json` / `_raw_<screen>_network.json` files passed to the helper.

### 3. Optional per-element crops

For tracked elements you want illustrated, capture a scoped screenshot keyed by selector:
```bash
agent-browser --session $S screenshot "<css-selector>" "${OUTPUT_DIR}/signals/images/previews/<screen>-<slug>.png"
```
Build a small `_raw_<screen>_boxes.json` mapping `{ "<selector-or-ref>": "images/previews/<screen>-<slug>.png" }`.

### 4. Assemble the signals (deterministic helper)

Do NOT hand-build the JSON. Run the helper — it parses the GA4 /collect query strings and
the data layer reliably:

```bash
python3 "${SKILL_DIR}/scripts/url_to_signals.py" \
  --snapshot   "${OUTPUT_DIR}/signals/_raw_<screen>_snapshot.json" \
  --network    "${OUTPUT_DIR}/signals/_raw_<screen>_network.json" \
  --datalayer  "${OUTPUT_DIR}/signals/_raw_<screen>_datalayer.json" \
  --boxes      "${OUTPUT_DIR}/signals/_raw_<screen>_boxes.json" \
  --screen     "<screen>" \
  --screenshot "images/previews/<screen>.png" \
  --out        "${OUTPUT_DIR}/signals/<screen>.json"
```

The output `signals/<screen>.json` is figma-client-shaped **plus** `observed_events[]`
(existing live tracking). The inference agent uses `observed_events[]` to emit existing
events as `origin: confirmed` and the remaining interactive elements as `inferred` proposals.

Clean up the `_raw_*` files when done (optional):
```bash
rm -f "${OUTPUT_DIR}/signals/"_raw_*.json
```

### 5. Close + update meta

```bash
agent-browser --session trackingplan close
python3 -c "
import json
p = json.load(open('${PLAN_FILE}'))
p['meta']['steps']['extract-source'] = 'done'
json.dump(p, open('${PLAN_FILE}', 'w'), indent=2, ensure_ascii=False)
"
```

## Output

```
✓ URL extraction complete
  <screen>: <N> interactive · <O> observed live events (existing) · <C> crops
  Files: <OUTPUT_DIR>/signals/*.json
```

Return control to orchestrator.
