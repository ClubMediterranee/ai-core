---
name: spec
description: 'Turn a PRD into developer-ready specs (enriched user stories). Reads the PRD sources (docs/prd/) and cross-references DRD design files (docs/drd/) — or any analysis document, generating a requirement id scheme when the source has none — to produce structured markdown specs in docs/specs/<prd-slug>/ with an index.md manifest, each spec sized for an AI developer to implement in under 2 hours. Every spec carries a §8 Data Contract — API endpoints resolved live through the clubmed_api MCP (which must be connected) plus the Directus CMS translation keys the feature needs — and a §9 of standard Gherkin acceptance tests traceable to FUNC/BR/ERR. Each generated spec is validated by a deterministic script. Use this skill when the user says "/spec", "generate specs", "create specs from PRD", "spec from PRD", "découper en specs", "générer des specs", or names a PRD to turn into developer specs (e.g. "PRD01", "le PRD des activités").'
allowed-tools: Read, Write, Bash, Glob, Grep, Task, mcp__clubmed_api__*
version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-07-22
    changes:
      - "Step-based pipeline (steps/ + references/), SKILL.md as orchestrator, MCP hard gate"
      - "§8 Data Contract resolved live against the API with per-entry evidence and confidence"
      - "§9 Gherkin acceptance tests, traced to FUNC/BR/ERR, with mandatory ERR failure coverage"
      - "§5 business rules copied verbatim from the PRD; spec written in the user's language"
      - "Deterministic validator (scripts/validate_specs.py) over structure, §8, §9 and assets"
      - "Per-PRD output folders ({DOCS_ROOT}/specs/<prd-slug>/) with an index.md manifest (order, dependencies, out-of-scope); sources under {DOCS_ROOT}/prd|drd"
      - "Re-run policy — existing specs are diffed and never overwritten without confirmation"
      - "Unstructured sources supported: generated ids (BR-G1…) with verbatim quotes when the document has no id scheme; partial design sources (bare Figma link, screenshots) accepted"
      - "Id-coverage gate at the Step 4 breakdown; §9 finalized after API resolution to harvest real error cases"
  - version: 1.0.0
    date: 2026-06-23
    changes:
      - Initial release
created-at: 2026-06-23
created-by: "Jeremy Wallez <jeremy.wallez@clubmed.com>"
---

# spec

You transform a PRD into one or more detailed, developer-ready specs. The specs are "super user stories" — rich enough for an AI developer to work completely autonomously, and structured so a human can review them fast.

Each spec includes a **live-resolved §8 Data Contract**: rather than inferring API endpoints, you resolve them against the real product API through the `clubmed_api` MCP and document them with evidence, a confidence level per entry, ranked "Points to clarify", and a Developer Handoff for anything you cannot confirm.

**Two things the MCP serves — and what belongs in a spec:**
- The **product API** (OpenAPI routes) → resolved live; this is the bulk of §8.
- The **API team's scenarios**, written to document that API and make the MCP searchable → a **route-discovery aid only**. They tell you *which* endpoints matter and *in what order* to call them. **Nothing about a scenario is ever written into a spec** — no scenario id, no "business journey" section, no channel gating — and a scenario is never evidence for a confidence tier.

**Directus** is the editorial CMS. It is **not** served by the MCP and appears in exactly one place in a spec: the §8 **CMS Keys** table, listing the **translation keys** the feature needs (label text grounded in the DRD Content Contract, key name proposed).

**Golden rules:**
- **Resolve `{DOCS_ROOT}` first** (Step 1.0) — the docs tree may live in a sibling repo, not under the cwd. Every path in the pipeline hangs off `{DOCS_ROOT}`, never a bare relative path.
- The **source** trees `{DOCS_ROOT}/prd/` and `{DOCS_ROOT}/drd/` are **read-only**. `{DOCS_ROOT}/specs/` is **output-only**: everything you create goes to `{DOCS_ROOT}/specs/<prd-slug>/` (the specs + the `index.md` manifest), one folder per PRD.
- **Never overwrite an existing spec silently.** If the PRD's folder already exists, this run is an update — diff and ask before writing (Step 6.8).
- **Never assert a guess as fact** in §8. Every resolved entry carries evidence; everything you cannot confirm goes to the Developer Handoff, clearly labeled as a best-guess. Confidence is a bucket (`🟢 high` / `🟡 medium` / `🔴 low`) plus an evidence string — never a fabricated percentage.
- **Never leak secrets or PII into a spec.** Specs are committed to the docs repo. API keys are always placeholders (`YOUR_API_KEY` / `process.env.*`); example values are synthetic — never copy a real value from a live MCP response that could be customer data (booking ids, emails, names, account-bound prices).

---

## Language — one global rule for the whole skill

**You answer in the user's language, and you write the spec in the user's language.** The user
writes to you in French → the specs are French. In English → the specs are English. This is decided
once, at the start, and holds for every step, every section and every generated file. (The PRD's own
language is only a hint when the user's is ambiguous — it never overrides it.)

**Everything a human reads is translated**, with no exception carved out for "technical-sounding"
terms: section titles ("UI Contract" → "Contrat UI", "Data Contract" → "Contrat de données",
"User Story" → "Récit utilisateur", "Feature Flag" → "Indicateur de fonctionnalité"), sub-section
labels, table headers, prose, and the acceptance-test wording. The English forms used throughout
these instructions are the **canonical reference**, not the output.

**Machine tokens are never translated** — tools read them, people don't:

| Never translate | Why |
|---|---|
| Anchors `<!-- dc:clarify -->`, `<!-- dc:index -->`, `<!-- dc:handoff -->`, `<!-- at:tests -->` | the validator finds §8/§9 sub-sections by these — that is exactly what lets the visible labels be translated |
| Gherkin tags `@nominal-passing`, `@edge`, `@FUNC-001`, `@BR-007`, `@ERR-002` | parsed by the validator and downstream tooling |
| Frontmatter keys and enum values (`confidence: high`, `data_contract_sources: [api, directus]`) | schema, not prose |
| Identifiers: endpoint paths, response field paths, operation ids, CMS key names, code | they are the contract itself |

Gherkin **keywords** are prose-side: they follow the spec's language through Gherkin's own
localization (`# language: fr` + `Fonctionnalité/Scénario/Étant donné/Quand/Alors/Et`), see
`references/acceptance-tests-template.md`.

---

## How this skill runs — the pipeline

The skill runs as an ordered pipeline. Each step has a dedicated file under `steps/` with the full instructions. **Read the step file before running that step — do not skip it, and do not run a later step before an earlier one.**

| Step | Purpose | Full instructions |
|------|---------|-------------------|
| **0** | **Hard gate** — the `clubmed_api` MCP must respond to a liveness probe, else stop and print the connect message | `steps/step-0-mcp-gate.md` |
| **1** | Resolve `{DOCS_ROOT}`; identify the PRD and its slug; ask the author's name once — 🙋 *asks the user if either is ambiguous* | `steps/step-1-identify-prd.md` |
| **2** | Read & understand the PRD deeply; **Explore subagent** digests the supporting material | `steps/step-2-read-prd.md` |
| **3** | Find & read the relevant DRDs (Figma, screenshots, Content Contract, Data Sources) — **parallel subagents** when several | `steps/step-3-drds.md` |
| **4** | Propose the spec breakdown with a mechanical **id-coverage gate**, raise blocking questions one at a time — 🙋 **waits for user confirmation** | `steps/step-4-breakdown.md` |
| **5** | Compose the spec body §1–§7 **and a §9 draft** — parked in the scratchpad, **not written to docs yet** | `steps/step-5-compose-body.md` |
| **6** | Resolve §8 live via the MCP (once, by data family), finalize §9 with the harvested API error cases, then write each file (§1–§9, single Write) + the `index.md` manifest — 🙋 *asks before touching an existing folder* | `steps/step-6-data-contract.md` |
| **7** | Validate (deterministic script) + **independent reviewer subagent**; confirm the feature flag — 🙋 *asks the user* | `steps/step-7-validate.md` |

🙋 marks a step that talks to the user. Step 4 is the true gate — nothing is composed until the breakdown is confirmed.

**Shared references (read when a step points to them):**
- `references/data-contract-template.md` — the §8 structure (labels render in the spec's language).
- `references/acceptance-tests-template.md` — the §9 standard-Gherkin structure, scenario types, and trace tags.
- `references/confidence-rubric.md` — the three confidence buckets and the evidence each requires.
- `scripts/validate_specs.py` — the deterministic output validator run in Step 7.

**Subagents (via `Task`).** Four phases delegate to subagents; the main agent stays the single writer of the specs.
- **Step 2 — Explore subagent** sweeps `{DOCS_ROOT}/specs/` for loosely-referenced supporting material and returns a structured, cited digest (read-only; no invariant at risk).
- **Step 3 — one subagent per DRD** (when several are relevant) returns a structured extract, keeping the main context lean.
- **Step 6 — one MCP-resolution subagent per data family** (e.g. transport, transfer+price) runs the large `search_openapi` / scenario calls out of the main context and returns only distilled endpoint blocks. This is why MCP resolution never overflows the main agent.
- **Step 7 — an independent reviewer subagent** re-reads each spec against the PRD/DRD and re-checks a sample of 🟢 evidence via the MCP — an adversarial second opinion the author cannot give itself.

User interactions and the file Write (Step 6.8) always stay on the main agent — never delegate a question or the resolve-once §8 assembly to a subagent.

The spec carries two confidences, surfaced together in §2 under their canonical labels:
**source confidence (PRD/DRD)** (`confidence`) rates the quality of the *input* material, and
**data-contract confidence** (`data_contract_confidence`) rates the §8 *resolution*. They move
independently — so a §8 doubt echoed into §2 counts for `data_contract_confidence` only and must
**not** drag `confidence` down. Their rules live in `steps/step-5-compose-body.md` (sources) and
`references/confidence-rubric.md` (§8).

---

## Handling edge cases

Only the cases no step file owns. Everything about DRDs is in Step 3, the breakdown in Step 4, §8 in Step 6.

**MCP not connected:** stop at Step 0 with the actionable message. Never generate a spec with a guessed §8.

**One DRD covers multiple specs:** extract only the relevant parts of the DRD for each spec. Don't dump the entire DRD into each spec.

**Ambiguous scope between two PRDs:** surface it in §2 Attention points as an `❓ Open question` in each affected spec, naming the other PRD.

**PRD already contains a feature flag name:** use it directly, no need to propose one or ask.

**A need spans both families:** a slot card needs a price (API) and a label (editorial) — resolve each part in its own source and list both.

**An endpoint inferred from the PRD/DRD:** treat it as a hypothesis to confirm or replace against the API — never ship it unverified.
