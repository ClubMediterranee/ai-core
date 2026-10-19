---
name: ecvr-forensics
description: "ECVR BE forensics (v2) for Club Med — monthly analysis of the Booking Engine conversion rate where the explicability model only PROPOSES leads and every claim is computed from live GA4 (mix/rate decomposition by channel, device, Business Unit, market, resort) and cross-checked against the model, flagging any discrepancy. Produces the same 4 Teams cards and Word report as ecvr-be-explicability (v1), and posts the Teams cards automatically, like v1 (`--dry-run` to only build them). Use when the user provides the month's explicability CSVs and wants the v2 / forensics analysis, or asks for a decomposition of the ECVR BE change."
allowed-tools: Bash, Read, Write, Edit
version: 1.0.0
changelog:
  - version: 1.0.0
    date: 2026-10-19
    changes:
      - Initial release
created-at: 2026-10-19
created-by: "Mathéo Rak <rakma@clubmed.com>"
---

# ECVR-forensics (v2)

v2 of `ecvr-be-explicability` (v1 is kept untouched as a fallback).

**ECVR BE** = GA4 `eventCount` of the event `BE_Confirmation` / sessions. It is the event count, not the
number of sessions in which the event fired. Sessions are the deduplicated GA4 total of the scope (summing
channel x country rows overcounts them). The **BE Entry Rate** is the exception: it counts the *sessions* in
which `BE_Entry` fired, divided by sessions.

## Principle

- The explicability model (the CSVs) **only suggests what to look at**. It is not the final data.
- **Final claims = model leads cross-checked with GA4.** GA4 figures are computed by code, not written by a
  language model. Where the model and GA4 disagree, the discrepancy is **flagged (⚑)** on the item; the
  figure shown is GA4.
- **Nothing is hardcoded from a given month's analysis** (no market, channel, resort or month named in code).
  **One deliberate exception:** `NO_TRANSPORT` price-check errors are tracked every month as a standing
  *"Intentional watch point"* (`STANDING_ERROR` in `forensics.py`), whatever the model proposes. The report
  states that its link to the ECVR change is not measured.
- **No assumption about what a channel, market or metric is, or why it moved.** The data gives a name and
  figures. Recommendations and watch points name *what to check*, never a guessed reason, and never propose
  re-running or modifying the model or the ECVR computation.
- **Teams cards post automatically**, like v1. `teams_message.py --dry-run` only builds and saves them.

## Pipeline

```
filter_results.py → forensics.py → claims.py (library) + compose.py → verify_synthesis.py → teams_message.py
                                                                                          → word_report.py
```

Run each step from the folder that holds the monthly files (`ECVR_DOWNLOADS_DIR`):

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/filter_results.py
python3 ${CLAUDE_SKILL_DIR}/scripts/forensics.py
python3 ${CLAUDE_SKILL_DIR}/scripts/compose.py
python3 ${CLAUDE_SKILL_DIR}/scripts/verify_synthesis.py
python3 ${CLAUDE_SKILL_DIR}/scripts/teams_message.py        # posts the 4 cards (add --dry-run to only build them)
python3 ${CLAUDE_SKILL_DIR}/scripts/word_report.py
```

1. **`filter_results.py`** — reads the three CSVs (explicability, countries, BU), buckets the model's
   variables into leads, picks the top markets per BU and the resorts. Edit the three CSV filenames at the
   top each month. → `analysis_input.json`.
2. **`forensics.py`** — pulls GA4 by Custom Channel Group and by device for Global, each Business Unit and
   each BU-focus market, current vs prior year, and splits the change in ECVR BE into a **mix** effect
   (traffic share moved) and a **rate** effect (the group's own conversion moved). Components add up exactly
   to each scope's total change. It also computes each BU's contribution to the global change, GA4
   views / entries / confirmations per resort, the sessions and confirmations of the markets behind the
   strongest model signals, the `NO_TRANSPORT` standing item, and checks every model lead against GA4.
   → `forensics_output.json`.
3. **`claims.py` + `compose.py`** — build `synthesis_output.json`. Code computes **verified claims**
   (numbered statements, each tagged with the comparison words it proves: largest, only, mostly, entirely,
   above/below average, all, partly offset). The language model writes the narrative, one sentence or short
   paragraph per card, and every sentence must cite the claims it rests on. Code then checks each sentence:
   figures must appear in the cited claims, no unmeasured cause, no linking of two channels, every proof
   word licensed by a claim about the same entity, share movements consistent with their wording, openings
   varied within a batch. A rejected sentence is sent back; if it still fails it is replaced by a
   deterministic sentence built from the data. Basis points are converted to percentage points only in the
   finished text. A card carries verified analysis or verified fact, never an unsupported statement.
4. **`verify_synthesis.py`** — live-GA4 fact check of the finished synthesis; exits 1 on a real mismatch.
5. **`teams_message.py`** — builds and posts the 4 Adaptive Cards (part 4 carries Resort Focus, Other Key
   Signals, Top Actions and Watch Points). `--dry-run` posts nothing; `--only part3,part4` posts only those
   parts. HTTP 202 ≠ delivered: confirm in the channel. Above ~28 KB a card is accepted but never appears.
6. **`word_report.py`** — the Word report from the same `synthesis_output.json`.

## Reading the output

- Effects are in percentage points of ECVR (1 bp = 0.01 point). `mix` = traffic share moved; `rate` =
  conversion inside the group moved. A BU or market figure is in that scope's **own** ECVR units and must not
  be added to a global figure.
- Flags: 🔍 small base (under 50 BE confirmations on either side, so the rate is fragile); ⚑ model vs GA4
  (direction or size differs).
- BU figures from the model and from GA4 can differ: the model is trained on each market's own GA4 property,
  while GA4 here is the B2C rollup (property `310694998`).
- The top of card 1 carries one sentence on the funnel (sessions → BE entries → confirmations, % only).

## Setup

`pip install --user anthropic google-analytics-data google-auth-oauthlib python-docx`, `ANTHROPIC_API_KEY`,
and `ECVR_DOWNLOADS_DIR` (the default path in the scripts is a placeholder: **set the variable or edit it**).
Put the OAuth client-secret JSON in that folder (`deepdive.py`'s `get_ga4_credentials()` handles the flow and
writes `ga4_oauth_token.json`). `deepdive.py` is kept only as the GA4 helper library.
The Teams webhook is hardcoded in `teams_message.py` as in v1 (private repository); `TEAMS_WEBHOOK_URL`
overrides it. If the repository's access ever widens, regenerate the webhook.
**Never commit** the OAuth files, the monthly CSVs or the generated JSON / Word files (see `.gitignore`).

## Thresholds (structural, set once)

- `forensics.py`: negligible contribution 0.05 bp; model-vs-GA4 size gap 10 pts (20 for variables and
  resorts); small base 50 confirmations; 8 model variables get their market context.
- `compose.py`: 3 channels per direction, 2 per market, 5 other-signal rows per kind; model temperature 0.2.
- `claims.py`: an effect "dominates" at 2/3 of rate + mix, "entirely" at 95%; an offset needs the smaller
  opposite effect to cancel at least half of the larger; a *recurring channel effect* is a channel outside
  the global top 3 that moves ECVR by at least 0.3 bp, the same way, in at least 3 markets and at least twice
  as many markets as the other way (max 5; the watch points cover them).

Change them in one place if the reading needs to be stricter or looser, never to fit a particular month.

## Status

Built 2026-10-12, reworked 2026-10-15 to 2026-10-19 (GA4 session totals, prose per card, funnel sentence,
standing watch item, 4-card layout). Run on September 2026 only; not yet run on a second month.
