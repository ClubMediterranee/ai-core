# Rule — Ask before emit

**Never add an event entry to `plan.json` without explicit user confirmation.**

Every inferred candidate must go through step 04 (confirm). The agent proposes; the user
decides. This applies even to high-confidence candidates (confidence = 1.0).

**Why:** Tracking has implementation cost and privacy implications. A plan that the
developer implements should only contain events the product owner consciously chose.

**How to apply:**
- In step 03 (infer): build candidates, do not write to `plan.json`.
- In step 04 (confirm): call `AskUserQuestion` for each candidate, one at a time.
- In step 05 (map-taxonomy): only write entries that the user accepted in step 04.
- If the user selects "Modify it" → ask a follow-up question immediately and apply the
  modification before moving to the next candidate.
- Always offer a free-text option (`Other`) alongside the structured choices.
