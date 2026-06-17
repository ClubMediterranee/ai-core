# Rule — Reuse before invent

Before proposing a new event name, check the GTM snapshot `ga4_events_confirmed` and
`ga4_events_dynamic` — these are the real event names that already fire in production.

**For event names:**
- If an event from the GTM snapshot covers the interaction → reuse it.
- Add a `detail_click` slug to differentiate, rather than creating a new event.
- Example: a "Book Now" CTA → `click_highlights` with `detail_click: "book_now"`,
  not a new `click_book_now` event.
- If no GTM match, follow the naming convention: `click_%zone` / `display_%content_type`.

**For param names:**
- Use the leaf names from `dl_variables` in the GTM snapshot — these are the exact
  keys that GTM reads from the data layer.
- Never invent a param name when a DL variable already covers the case.

**For truly new names:**
- Follow `click_%zone` / `display_%content_type` conventions.
- Present to the user in the confirmation step with a rationale.
- Land in `plan.json` with `origin: "inferred"` and a `rationale`.

**Why:** A fragmented event taxonomy is the main cause of GTM containers that are hard
to maintain. Fewer distinct event names = more data per event = better analysis.
