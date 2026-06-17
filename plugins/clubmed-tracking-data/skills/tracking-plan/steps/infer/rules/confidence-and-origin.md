# Rule — Confidence and origin

Every entry in `plan.json` carries `origin`. Inferred entries also carry `confidence`
and `rationale`.

| origin      | confidence | meaning                                                    |
|-------------|------------|------------------------------------------------------------|
| `confirmed` | 1.0        | Observed firing live (clubMedLayer push or /collect seen). |
| `legacy`    | 1.0        | Taken directly from an existing approved tracking sheet.   |
| `inferred`  | 0.0–1.0    | Proposed by the agent from Figma signals. MUST have a rationale. |

**Calibration guidelines:**

| Signal quality                                      | Max confidence |
|-----------------------------------------------------|---------------|
| ON_CLICK interaction with destination in Figma      | 0.90          |
| Instance with `designer_notes` confirming tracking  | 0.85          |
| CTA text inferred from label alone                  | 0.70          |
| Hidden layer / display impression inferred          | 0.65          |
| Ecommerce event inferred from page context only     | 0.60          |
| No direct signal — inferred from page type alone    | 0.40          |

**Why:** Overconfident plans create false certainty in implementation. A 0.9 confidence
inferred event still fails live ~10% of the time. Only `confirmed` earns 1.0.

**How to apply:**
- Set `confidence` at the candidate stage (step 03).
- Never round up to 1.0 for an inferred entry — even if the user confirms it in step 04,
  it stays `inferred` unless live-verified.
- If the user selects "Yes — as confirmed" in step 04, set `origin: "confirmed"`.
