# Step 5 — Compose the spec body (§1–§7 and §9)

For each spec in the confirmed breakdown, prepare its frontmatter and sections **1 through 7 and §9**, and pick the descriptive kebab-case filename it will later be written under, in `{DOCS_ROOT}/specs/<prd-slug>/` (e.g. `{DOCS_ROOT}/specs/prd04-transport-transfer-booking/cart-layer-structure.md`). Only §8 (Data Contract) is deferred — it is resolved live in Step 6. §9 (Acceptance Tests) derives from §5/ERR and needs no MCP, so it is composed here even though it sits after §8 in the file.

> **Do not write into `{DOCS_ROOT}` yet.** §8 must be resolved first (Step 6), and the final file is written **once, complete (frontmatter + §1–§9), in Step 6.8**.
>
> **Do park each draft in the session scratchpad** (`<scratchpad>/spec-drafts/<filename>.md`) as you compose it. The MCP-resolution phase is long and noisy; the verbatim §5 text must not be carried through it in memory. Step 6.8 re-reads the draft from disk and assembles it with §8 — the scratchpad is never the final artifact.

## Frontmatter

Emit **real values**, never the alternatives shown here — `confidence: high | medium | low` written literally fails validation.

```yaml
---
title: "Short human-readable title"
author: "<name provided by user>"
date: "2026-07-22"                       # today, YYYY-MM-DD
status: draft
confidence: medium                       # one of: high · medium · low
data_contract_confidence: medium         # one of: high · medium · low — §8 resolution quality (Step 6)
data_contract_sources: [api, directus]   # only the sources this spec actually uses: [api], [directus], or both
related_specs:
  - other-spec-filename.md               # sibling specs this one depends on; each must exist on disk
prd_source: "{DOCS_ROOT}/prd/<filename>.md"
---
```

**`confidence` calculation rules** (source quality — PRD/DRD):
- `high` — all DRDs present + Figma URLs resolved + no attention points
- `medium` — ≥1 DRD missing OR ≥1 open question OR ≥1 assumption
- `low` — DRDs missing on critical surfaces OR contradictory/incomplete BRs OR PRD itself incomplete

**`data_contract_confidence`** is the worst-case bucket across the critical §8 entries, computed in Step 6 per `references/confidence-rubric.md`. It is **independent** of `confidence`: a spec can have solid PRD/DRD sources (`confidence: high`) yet an unresolved data surface (`data_contract_confidence: medium`).

## Spec body

Write the spec in the **user's language** — the single global rule in `SKILL.md` § Language.

Use this exact section order (headings are `#### N. Title`). The section titles and labels below are the **canonical English reference** — render them, and every other human-readable string, in the user's language per `SKILL.md` § Language (machine tokens excepted).

---

#### 1. Description

One short paragraph. What does this spec cover? What does the user see or do?

---

#### 2. Attention points

This section is always the second section — it appears immediately after Description so the reader can assess quality before diving in.

Always surface **both** confidences here, using these two canonical labels consistently — **Source confidence (PRD/DRD)** = the `confidence` frontmatter field (source quality), and **Data-contract confidence** = the `data_contract_confidence` field (§8 resolution). Use the same two terms everywhere; do not vary the wording ("sources quality", "source confidence", etc.).

If there are no attention points:
```markdown
> ✅ No attention points. Source confidence (PRD/DRD): HIGH · Data-contract confidence: HIGH
```

Otherwise, open with both confidence levels, then a table with one row per issue:

```markdown
> Source confidence (PRD/DRD): **MEDIUM** · Data-contract confidence: **MEDIUM**

| # | Type | Description | Section |
|---|------|-------------|---------|
| 1 | ⚠️ Missing DRD | No DRD for the F&D detail layer — the AI will have to propose the interface | §6 UI Contract |
| 2 | ❌ Inconsistency | BR-007 does not specify mobile behaviour — contradicts the DRD | §5 Business Rules |
```

**Four entry types — use exactly these labels:**
- `❌ Inconsistency` — contradiction or anomaly between sources (PRD vs DRD, BR vs BR, PRD vs glossary)
- `⚠️ Missing DRD` — UI surface with no design reference; the developer AI will have to invent the interface
- `❓ Open question` — a decision only the PO can make; blocks or significantly risks the implementation
- `ℹ️ Assumption` — an assumption made in the absence of information; should be validated before dev starts

These four icons mark the **type** of an attention point. They are deliberately not traffic-light circles — `🟢🟡🔴` are reserved for §8 confidence, and severity words (Blocking/Medium/Minor) for §8. One icon per axis, no overlap across the document.

**Inline markers in the body:** wherever an attention point applies, add a lightweight reference back to the table:
```markdown
> ⚠️ Attention point #1 — No DRD available for this layer.
```
This avoids duplicating the full explanation; the table in section 2 has the detail.

---

#### 3. Context & Objectives

- Why does this feature exist?
- What problem does it solve for the user?
- What business goal does it serve?

**In scope:** an explicit list of the capabilities this spec covers.

**Out of scope:** adjacent capabilities explicitly excluded, each with the spec or `NG-xxx` that covers them. When the PRD defines Non-Goals, list each applicable one here as `NG-xxx — <description> (out of scope, v1)` — this makes the exclusion a first-class decision, not a footnote, and stops a DRD's out-of-scope surface from creeping back in (see the "ignore the surplus" rule in Step 3).

#### 4. User Story

```
AS A <type of user>
I WANT <action or capability>
IN ORDER TO <benefit or goal>
```

(Rendered in the user's language — e.g. "EN TANT QUE / JE VEUX / AFIN DE" in French.)

#### 5. Business Rules

Numbered list. Be exhaustive.

**Copy every relevant rule from the PRD verbatim — the text must be textually identical to the PRD.** Do not reword, summarise, shorten, "lightly translate", or improve the phrasing: a business rule is the PRD's wording, and any drift between PRD and spec makes the two impossible to reconcile. Keep the PRD ids (`BR-xxx`, `ERR-xxx`, `ACC-xxx`, `PERM-xxx`, `ST-xxx`, `FUNC-xxx`) so Step 7's coverage check can see them.

A rule the DRD implies but the PRD does not state is the **only** thing you may write yourself — mark it explicitly `(implied by DRD)` so a reviewer can tell it apart from PRD text at a glance. If a PRD rule looks wrong or ambiguous, copy it verbatim anyway and raise the issue in §2 Attention points — never fix it silently in §5.

```
1. BR-001 — ...
2. BR-007 — ...
3. (implied by DRD) — ...
```

#### 6. UI Contract

(Canonical English title — rendered in the spec's language, e.g. "Contrat UI" for a French spec.)

If DRD(s) found:

```markdown
##### Desktop
**Figma:** [Desktop](<url from figma-sources>)
**Screenshot:** ![Desktop](<relative path to preview image>)
<one paragraph describing the layout and key UI decisions from the DRD viewport section>

##### Mobile
**Figma:** [Mobile](<url from figma-sources>)
**Screenshot:** ![Mobile](<relative path to preview image>)
<one paragraph describing the mobile-specific differences>

##### Interactions
<copy the interaction table from the DRD, filtered to what's relevant to this spec>

##### Component composition
<copy the component table from the DRD, filtered to what's relevant>
```

Figma links must be the real URLs from the DRD `figma-sources` frontmatter — never invented. Screenshot paths must resolve on disk relative to the spec file (Step 7 checks this).

If no DRD found:

```markdown
> ⚠️ Attention point #N — No DRD found for this feature. The developer AI will have to propose an interface.
```

#### 7. Feature Flag

If the PRD contains a feature flag name, use it directly. Otherwise, propose a name derived from the PRD scope (e.g. `nbe_food_drinks`, `nbe_activities_booking`), write it into the spec marked `(proposed — to confirm)`, and **confirm it with the user in Step 7.3** (after all files are written) — whether the feature should be feature-flagged and, if so, to confirm or adjust the proposed name. This confirmation is a scheduled pipeline step, not an optional afterthought.

```markdown
- **Flag name:** `<flag_name>` _(proposed — to confirm)_
- **Default value:** enabled | disabled
- **Behaviour when disabled:** <what the user sees, or which fallback applies>
```

If the feature genuinely needs no flag, say so explicitly ("No feature flag — <why>") rather than inventing one.

#### 8. Data Contract

**Leave the heading and move on — do not write a placeholder.** §8 is resolved live in **Step 6** and assembled from `references/data-contract-template.md`, which owns its structure, its anchors and its house style.

#### 9. Acceptance Tests

**Draft** §9 now from the PRD alone (it derives from §5 Business Rules and the `FUNC`/`BR`/`ERR` ids), using `references/acceptance-tests-template.md`. It is placed **after §8** in the file, and it is **finalized in Step 6.7**: error cases discovered against the real API (option expiry, conflicts, availability) become non-passing scenarios that the PRD alone could not predict.

Write **standard Gherkin** (parseable — the `e2e-test-generator` skill consumes it), inside a ```` ```gherkin ```` block, under the heading carrying the anchor `<!-- at:tests -->`. The Gherkin follows the user's language through Gherkin's own localization — a French spec starts the block with `# language: fr` and uses `Fonctionnalité/Scénario/Étant donné/Quand/Alors/Et`; an English spec uses the default keywords with no header. One language per block, never mixed. Tags stay canonical English. Cover **every observable behaviour and every in-scope ERR**. The five types — **nominal passing, nominal non-passing, alternative passing, alternative non-passing, edge** — are a completeness checklist, not a quota: skip a type with a one-line reason when it does not apply, and never fabricate a scenario to tick a box (an implementation detail belongs in unit tests).

Tag every `Scenario:` with **one category tag** (`@nominal-passing` / `@nominal-non-passing` / `@alternative-passing` / `@alternative-non-passing` / `@edge`) and **at least one trace tag** to the ids it exercises (`@FUNC-xxx` / `@BR-xxx` / `@ERR-xxx`), every id defined in this spec's §5. Coverage the validator enforces: ≥1 passing scenario, and **every `ERR-xxx` in §5 has a non-passing scenario** tagged with that ERR id.
