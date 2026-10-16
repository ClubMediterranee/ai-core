# Step 3 — Find and read the relevant DRDs

DRDs live in `{DOCS_ROOT}/drd/`. Each DRD is a subdirectory named after a component (organism or molecule), containing a `<ComponentName>.drd.md` file and a `screens/` folder with preview images (paths vary — often `screens/images/previews/<node-id>.png`, sometimes descriptive names like `Desktop.png` / `Mobile.png`; read the real filename on disk, never assume the node-id form).

**Your job:** identify which DRDs are relevant to this PRD. Do this by matching:
- Component names mentioned in the PRD (e.g. `Dashboard`, `ProductHeader`, `BasketTicketLayout`)
- Section names that map to DRD directories (e.g. `SectionLayoutActivities`, `SectionLayoutChildcare`)
- Feature names that suggest a visual component

**A name match is a candidate, not a confirmation.** Component names are ambiguous — e.g. a
`MainFilterControlPanel` may filter *accommodation*, not the flights your PRD is about. Before
using a matched DRD, **read its `Purpose` section** and reject it if it does not concern this PRD's
scope. Never anchor a spec on a DRD you matched on the name alone.

Read every relevant DRD fully and extract:
- Figma source URLs (from the `figma-sources` frontmatter — a list of `{name, url}`)
- Screenshot paths — **as written in the DRD they are relative to the DRD's own folder** (e.g. `screens/images/previews/3294-33195.png`). Every path must be **re-based** when it lands in §6: a spec lives two levels down (`specs/<prd-slug>/`), so prefix with `../../drd/<ComponentName>/` → `../../drd/SectionLayoutTransport/screens/images/previews/3294-33195.png`. Copying the DRD path verbatim always fails Step 7's on-disk check. Read the real filename on disk — it is not always a node-id (`Desktop.png`, `Mobile.png` also occur).
- Viewport descriptions (Desktop / Mobile)
- Interaction tables
- Component composition tables
- Content Contract fields (the source of truth for the editorial **label text** and its format — not for the Directus key name; used in Step 6)
- Data Sources (business fields, used in Step 6)

**When several DRDs are relevant, parallelise with subagents.** DRDs are large (tables + screenshots); dispatch **one subagent per DRD** (via `Task`) and have each return a structured extract of exactly the fields above, keyed by component name — nothing invented, only what the file contains. Read a single DRD directly. Merge the returned extracts; they feed Step 5 (§6 UI Contract) and Step 6 (inventory).

**A DRD is exhaustive — extract only what traces to a FUNC/BR.** A DRD documents the whole
component, including surfaces and states outside this PRD's scope. Pull only the parts that answer
a `FUNC-xxx` / `BR-xxx` of the PRD. Any DRD component or state with **no corresponding FUNC**, or one
the PRD lists as **out of scope** (Hors-périmètre), is **ignored** — do not copy it into the spec —
and noted once in §2 as an `ℹ️ Assumption` / scope note (e.g. "the DRD's conversational AI panel is
out of scope per NG-004 and is not implemented"). Do not treat "it is in the DRD" as "it must be built".

**Design sources come in three grades — use what exists, degrade gracefully:**
1. **Full DRD** (`{DOCS_ROOT}/drd/<Component>/`) → the structured extraction above.
2. **Partial design source** — a bare Figma URL, a screenshots folder, a mockup embedded in a
   ticket or doc. Do **not** treat this as "Missing DRD": §6 references what exists (link,
   images) and describes what is visible, and §2 gets an `ℹ️ Assumption` noting that the
   Interactions / Content Contract tables are missing. An editorial label read off a screenshot
   is graded 🟡 with evidence `label read from design screenshot (no Content Contract)`.
3. **Nothing** → `⚠️ Missing DRD`, as below.

**If no DRD is found for a feature:** do not block. Note it clearly in the spec (§2 Attention points, type `⚠️ Missing DRD`) — the developer AI will need to propose its own interface design.
