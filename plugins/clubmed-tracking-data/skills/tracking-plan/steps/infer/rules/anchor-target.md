# Rule — Anchor the target

Every entry SHOULD carry a `target` anchor so the plan is **implementable** — a developer
knows exactly where to wire the `clubMedLayer.push` call.

| Source                     | `kind`      | Fields to populate                                               |
|----------------------------|-------------|------------------------------------------------------------------|
| Figma / DRD ON_CLICK signal | `figma`     | `figma_node_id`, `figma_path`, `component` (if known)           |
| Live URL / DOM element      | `dom`       | `role`, `accessible_name`, `selector` (if robust), `stability`  |
| No structural signal        | `component` | `component` name hint; `stability: "needs-selector"`            |

Set `stability`:
- `stable` — node_id from a Figma interaction (reliable anchor).
- `fragile` — inferred from instance name or text label (may break on rename).
- `needs-selector` — no reliable anchor found; a developer must supply one.

**Why:** A plan without anchors is a specification that nobody can implement reliably.
The target field is what turns a tracking plan into an actionable engineering spec.

**How to apply:**
- In step 05 (map-taxonomy): populate `target` for every entry before writing to `plan.json`.
- Never leave `target` absent when a `figma_node_id` is available from the extraction.
- When the Figma has no ON_CLICK signal but the interaction is inferred from a CTA label,
  set `kind: "component"` and `stability: "fragile"`.
