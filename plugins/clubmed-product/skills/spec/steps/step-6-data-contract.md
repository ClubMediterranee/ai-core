# Step 6 — Resolve the §8 Data Contract (via the clubmed_api MCP)

This engine runs **once for the whole breakdown, in two phases** — after composing §1–§7 and §9 (Step 5) and **before** the single Write in 6.8. The data needs come from each spec's §5 Business Rules and §6 UI Contract (from the PRD/DRD already read).

1. **Resolve, grouped by data family** (6.0–6.6) — pool the data needs of *all* the specs, group them by family (e.g. transport, transfer + price), and resolve each family **once**, in its own subagent. The unit of resolution is the family, never the spec.
2. **Assemble, per spec** (6.7–6.8) — from that single resolution table, write each spec's §8 and then its file.

> **Resolve shared needs once.** An endpoint or CMS key used by several sibling specs (see `related_specs`) is resolved a single time and reused with the **identical** path, confidence and evidence. In the output, the full endpoint block is rendered in the one **owner** spec; the others keep the endpoint in their index with a one-line reference (see `references/data-contract-template.md` § Cross-referencing a shared endpoint). Never let two specs diverge on the same source.

## 6.0 — Delegate the MCP resolution to subagents (keep the main context lean)

MCP responses are large — a single `search_openapi` call can return **60 KB+** (each result carries a full operation with request/response examples) and will overflow the main context if resolved inline. So **do the resolution in subagents**, one **per data family** (e.g. one for the transport endpoints, one for transfer + price), not per spec. Each subagent:
- receives the family's data needs and any known endpoints,
- runs the MCP calls (6.3–6.4) under the operational rules below,
- returns **only distilled endpoint blocks** (method + path, required params, response field paths, errors, confidence + evidence) and scenario facts — never the raw payloads.

The main agent stays the single writer: it merges the distilled blocks, applies "resolve shared needs once", assembles §8, and performs the Write (6.8). Never delegate the assembly or the Write.

**MCP operational rules (for the main agent and every subagent):**
- Use a **small `top_k`** (≈3) on `search_openapi` / `search_scenarios`.
- Call MCP tools **sequentially**, not in parallel (parallel calls have returned `500`s).
- On a transient `5xx` / `InternalServerError`, **retry once**.
- If the harness saves an oversized result to a file instead of inlining it, **`jq` that file** for the fields you need (`.results[].metadata` / `.results[].content` — `operation`, `path`, `method`, `parameters`, `responses[].example`) rather than re-reading it whole.

**Document only what a FUNC/BR needs.** An endpoint's response can carry dozens of fields; list only the field paths a `FUNC-xxx` / `BR-xxx` of this spec actually consumes. Do not inventory the whole payload.

## 6.1 — The two families of data

Every field the UI needs falls into one of two families. This decides which source to explore.

| Family | Nature | Source | Localization |
|--------|--------|--------|--------------|
| **Business / product** | availability, price, stock, age ranges, clubs per resort, states, schedules | **Club Med API** | value-level; API uses the `accept-language` header |
| **Editorial** | labels, titles, CTAs, messages, static copy | **Directus CMS** | per-locale keys (fr-FR, en-US, …) |

**What the MCP actually serves.** The `clubmed_api` MCP exposes the **product API** (OpenAPI routes) and the **scenarios written by the Club Med API team to document that API** — the narrative that makes the MCP searchable. It does **not** serve the editorial Directus CMS. Consequently:
- **Business/product needs** are resolved live against the API (Step 6.3).
- **Scenarios are a discovery aid only** (Step 6.3 bis) — they help you find the right routes and their call order. **Nothing about a scenario is written into the spec**: no scenario id, no "business journey" sub-section, no channel gating.
- **Editorial needs** are *not* resolved live. Directus holds the translation keys; the spec documents the keys the feature needs, grounding their **label text** in the DRD (Step 6.4).

## 6.2 — Build the data-need inventory

Produce an internal list of every distinct piece of data the spec requires. For each item: **name/purpose**, **family** (business or editorial), **localized?** (which dimension), **starting hypothesis** (any key/endpoint the DRD or PRD suggests). Be exhaustive — a single BR often implies several fields (label + price + state + stock).

When a DRD was read (Step 3), use both its tables as inventory inputs:
- **Data Sources** table (business fields, `Confirmed ✅`) → each row is a data need; it often surfaces one the spec text omits.
- **Content Contract** table (editorial labels) → each row is an editorial-key need, already grounded in the real label text — the source of truth for the **label**, never for the Directus key name.

## 6.3 — Resolve business/product needs against the API

For each **business/product** need:

1. **Find the operation** — `mcp__clubmed_api__search_openapi` (natural-language query) or `mcp__clubmed_api__suggest_openapi_operations` (from intent). Use `mcp__clubmed_api__list_routes` to browse when a keyword is known.
2. **Capture the real contract** — enough to write a full endpoint block: the **base URL** from the OpenAPI `servers` block (never hardcode a host — if the MCP does not expose `servers`, look for a host hint in the examples' `_links[].href` and offer it as a hypothesis in Points to clarify, keeping the `<API_BASE_URL>` placeholder), method + **real path** (replaces any guessed endpoint), required params/headers (`x-api-key`, `accept-language` are typically required), **response shape and the exact field path** to the value (read from `responses[].example`), and the **error responses** (400/401/403/404/409…) and their meaning.
3. **Validate when possible** — form a concrete request and call `mcp__clubmed_api__validate_route`. A passing validation (`is_valid: true`) is the **evidence** that earns 🟢. A **failing** validation is also valuable — it reveals the real required fields; fold the corrections in, then re-validate.

**Do not invent field paths.** If the operation payload does not expose the full response schema (only a summary), you cannot confirm the path — mark the entry 🟡 `medium`, record "response schema not exposed by the MCP" as the gap, and add it to Points to clarify. Never fabricate a path to reach 🟢.

**Example values in the curl/TypeScript are illustrative:** use the value documented in the OpenAPI example when one exists; otherwise use a clearly synthetic placeholder and label the block `(illustrative values)`. Never present an invented value as coming from a live response, and never copy a real value that could be customer/PII data (see the security golden rule).

## 6.3 bis — Use API scenarios to *discover* routes (never to fill the spec)

The API team's scenarios describe how the API is meant to be used. Use them to find the right operations and the order to call them: `mcp__clubmed_api__search_scenarios` / `list_scenarios` to locate one, `mcp__clubmed_api__search_scenario_routes` for its deduplicated route list, `mcp__clubmed_api__scenario_next_steps` for call ordering, `mcp__clubmed_api__get_scenario` for full detail.

What you keep from a scenario is **only** the knowledge that shapes the contract: *which* endpoints matter (they go in the 🗺️ endpoint index) and *in what order* they are called (shown naturally in the TypeScript example, e.g. apply → refresh). **Emit nothing else** — no scenario id, no title, no prerequisites block, no channel gating, no "business journey" sub-section. A scenario is internal API documentation, not part of the developer's contract, and it is **never evidence** for a confidence tier.

## 6.4 — Document the editorial (CMS translation) keys

Editorial keys are **not resolved live** — the MCP does not serve Directus. The spec documents the keys the feature needs so the team can create/confirm them in Directus:

1. **DRD Content Contract first** — if a DRD exists, its Content Contract is the source of truth for the real **label text**, format, and i18n. Record the DRD component as source (e.g. `drd:SectionLayoutChildcare`). Note that the DRD attests the *label*, never the *key name* — the key stays a proposal (🟡, see `references/confidence-rubric.md`).
2. **Developer Handoff** — if no DRD grounds the label (static copy with no design entry). Give a best-guess key, clearly labeled (stays 🔴).

## 6.5 — Score confidence per entry

Apply `references/confidence-rubric.md`: 🟢 `high` (resolved with evidence — a passing `validate_route` or the operation id, or a DRD Content Contract row for a label; **a scenario is never evidence**), 🟡 `medium` (found but a field path / param / shape is unconfirmed), 🔴 `low` (not found in any connected source; inferred only → Developer Handoff). The bucket **is** the granularity — display `🟢/🟡/🔴 + evidence`, never a numeric percentage or a progress bar (that would be fabricated precision). Every 🟢 entry carries a mandatory evidence string. `data_contract_confidence` is the worst-case bucket across the **critical** entries.

## 6.6 — Developer Handoff (fallback)

Everything 🔴 or unresolved becomes an actionable checklist: Directus translation keys with no DRD grounding, API fields whose path could not be confirmed. For each: state what is missing, give the **best-guess** (labeled as a guess), and point to where the developer should look (which CMS collection, which API tag, which team).

## 6.7 — Collect the "Points to clarify" (doubts first)

Gather every uncertainty into one ranked list — the first thing read in §8. Pull from: 🟡 entries with an unconfirmed field path/enum/body; structural choices the spec does not settle (e.g. does the funnel operate on a `proposal` or an existing `booking`?); business-rule gaps the API cannot answer; and any §2 attention point with a data impact.

**Confront each doubt with the PRD before ranking:**
- PRD **answers** it → close it, resolve the entry, drop from Points to clarify.
- PRD **explicitly leaves it open** → keep it, marked "unresolved in the PRD" (a genuine PO decision, not a skill gap).
- **No PRD** → note the doubt is unconfronted (built from the spec alone).

Rank each by **severity, written as a text label** — `🟢🟡🔴` stay reserved for confidence and must not be reused here: **Blocking** (blocks implementation / forces a design decision), **Medium** (a field/enum/body unconfirmed but with a reasonable default), **Minor** (cosmetic or already worked around). Each row: point · impact · resolution path. **Echo every Blocking point into §2 Attention points** as an `❓ Open question`, with an inline `> ⚠️ Attention point #N` marker in §8.

**Harvest the API error cases into §9.** Before leaving 6.7, finalize each spec's §9 draft
(from Step 5): every error case discovered during resolution that maps to an observable behaviour —
an option expiring between listing and applying (404), an economic-control conflict (409), an
availability collapse — becomes a **non-passing scenario**, tagged on the ERR or BR it exercises.
The PRD alone cannot predict these; the API just did. This is the last edit to §9.

## 6.8 — Write the complete spec file (single Write)

Assemble §8 following `references/data-contract-template.md` (Points to clarify → index → endpoint blocks → CMS Keys → Localization → Developer Handoff — there is **no** business-journey sub-section), with all labels rendered in the spec's language. Then, for each spec: re-read its **draft from the scratchpad** (Step 5), merge in this §8 and the finalized §9, and write the **entire file in one `Write` call** to `{DOCS_ROOT}/specs/<prd-slug>/<filename>.md` — frontmatter (with `data_contract_confidence` and `data_contract_sources` set) plus §1–§9 in document order. Never write part of the file first and patch the rest afterwards.

**Re-run policy — never overwrite silently.** If `{DOCS_ROOT}/specs/<prd-slug>/` already holds files:
1. **Read** each existing counterpart before writing anything.
2. Build a **per-section diff summary** for the lot (e.g. "spec X — §2: 2 open questions were answered manually · §5: unchanged · §8: 1 endpoint changed").
3. **Ask the user once for the whole lot**: overwrite everything / merge / decide spec by spec.
4. **Merge** preserves, at minimum: answers added to §2 `❓ Open questions`, a frontmatter `status` more advanced than `draft` (`review`/`approved`), and a confirmed feature-flag name. When merging is ambiguous, ask — the user's manual edits outrank the regeneration.

Real endpoints replace any guessed endpoints; every API entry has an exact response field path (or is 🟡 with the gap recorded); example values are illustrative or documented, never presented as live and never real PII; guesses live only in Points to clarify + Developer Handoff.

## 6.9 — Write the `index.md` manifest

After the specs, write `{DOCS_ROOT}/specs/<prd-slug>/index.md` — the folder's entry point, and the only durable trace of the confirmed breakdown. It is **not** a spec (no 9 sections); it contains:

```markdown
---
prd_source: "{DOCS_ROOT}/prd/<filename>.md"
date: "<today>"
specs: <n>
---

# <PRD title> — spec index

## Implementation order
1. <foundation spec> (foundation — unblocks …)
2. In parallel: <spec>, <spec>
3. <spec> (depends on …)

## Specs
| Spec | Covers | Depends on | Status |
|------|--------|------------|--------|
| <filename>.md | FUNC-…, BR-… | — | draft |

## Out of scope (confirmed at breakdown)
- <id or NG-xxx> — <reason given by the user at the Step 4 gate>
```

An AI implementing this PRD reads `index.md` first (what to pick, in what order) and updates `Status` as it goes. On a re-run, refresh the manifest with the same care as the specs (the re-run policy applies to it too).

Once every spec and the manifest are written, go to **Step 7 (validation)**. Do not report anything yet — the per-spec summary is produced there, after validation.
