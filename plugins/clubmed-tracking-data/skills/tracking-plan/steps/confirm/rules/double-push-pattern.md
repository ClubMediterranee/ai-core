# Rule — Double-push pattern

All `click_*` events (family=click) MUST be pushed **twice in sequence**:

```js
// 1. Reset the previous event_click value
clubMedLayer.push({ event: "click_%zone", event_click: null })

// 2. Push with the actual data
clubMedLayer.push({ event: "click_%zone", event_click: { detail_click: "%action" } })
```

**Why:** The data layer is persistent. If the first push is not reset, GTM will read the
previous event's `detail_click` value for the new event. The null push clears it.

**How to apply:**
- Every entry with `payload_shape: "nested_event_click"` implies this double-push.
- The `payload` field in `plan.json` records the second (populated) push.
- The null push is implicit and does not need its own entry.
- Exceptions: `page_view`, `display_*`, `form_error`, ecommerce events — single push only.
