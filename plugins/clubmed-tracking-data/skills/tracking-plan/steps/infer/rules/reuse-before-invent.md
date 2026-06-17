# Rule — Reuse before invent

Before proposing a new event name or variable name, check `data/event-catalog.json`
`canonical_events` and `data/variable-dictionary.json`.

**For event names:**
- If an existing canonical event covers the interaction → reuse it. Add a `detail_click`
  slug to differentiate, rather than creating a new event.
- Example: a "Book Now" CTA in a highlights section → `click_highlights` with
  `detail_click: "book_now"` — not a new `click_book_now` event.

**For variable names:**
- If the variable-dictionary has a name that fits → use that exact name.
- Never invent `item_label` if `detail_click` covers the case.

**For truly new names:**
- The proposed name must follow `click_%zone` / `display_%content_type` conventions.
- It must appear in the confirmation question to the user with a rationale for why no
  existing name fits.
- It lands in `plan.json` with `origin: "inferred"` and a `rationale`.

**Why:** A fragmented event taxonomy is the main cause of GA4 dashboards that are hard
to maintain. Fewer distinct event names = more data per event = better analysis.
