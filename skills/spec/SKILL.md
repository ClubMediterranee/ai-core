---
name: spec
description: 'Generate developer-ready specs (US enrichies) from a PRD document. Reads docs/specs/prd/ and cross-references docs/specs/drd/ design files to produce structured markdown specs in docs/specs/. Each spec is sized for an AI developer to implement in under 2 hours and contains: description, context & objectives, user story (AS A / I WANT / IN ORDER TO), exhaustive business rules, Figma links + screenshots, feature flag, data contract placeholder, and open questions. Use this skill whenever the user says: "/spec", "generate specs", "create specs from PRD", "découper en specs", "créer des specs", "générer des specs", "spec from PRD", or starts work on a PRD file. Also triggers when the user mentions a specific PRD by name or number (e.g. "PRD01", "le PRD des activités") and wants to turn it into actionable developer specs.'
allowed-tools: Read, Write, Bash
version: 1.0.0
changelog:
  - version: 1.0.0
    date: 2026-06-23
    changes:
      - Initial release
created-at: 2026-06-23
created-by: "Jeremy Wallez <jeremy.wallez@clubmed.com>"
---

# spec

You transform a PRD into one or more detailed, developer-ready specs. The specs are "super user stories" — rich enough for an AI developer to work completely autonomously.

**Golden rule:** the `docs/` tree is read-only. Never modify any file in `docs/specs/prd/`, `docs/specs/drd/`, or any other `docs/` subdirectory.

---

## Step 1 — Identify the PRD

**If the user provided a path:** read that file directly.

**If no path was given:** list all `.md` files in `docs/specs/prd/` and ask the user which one to process. Example output:

```
Available PRDs:
1. docs/specs/prd/PRD00 - Booking engine Foundations.md
2. docs/specs/prd/PRD01 - All-inclusive details in Ticket price.md
...
Which PRD would you like to turn into specs?
```

**Ask once at the start:** "What is your name? (It will be used as the `author` field in all specs)" — unless the user's identity is already clear from context.

---

## Step 2 — Read and understand the PRD deeply

Read the full PRD. Build a mental model of:
- The product scope and user goals
- All functional specifications (FUNC-xxx)
- All business rules (BR-xxx)
- The acceptance criteria
- Any open questions or constraints already noted in the PRD
- Any feature flags or toggle names mentioned

Also explore the `docs/` folder freely to find any supporting files that seem relevant — context documents, glossaries, other PRDs, briefs, or any other reference. Read whatever helps build a complete understanding of the domain, the terminology, and the broader product context.

---

## Step 3 — Find and read the relevant DRDs

DRDs live in `docs/specs/drd/`. Each DRD is a subdirectory named after a component (organism or molecule), containing a `<ComponentName>.drd.md` file and a `screens/` folder with preview images.

**Your job:** identify which DRDs are relevant to this PRD. Do this by matching:
- Component names mentioned in the PRD (e.g. `Dashboard`, `ProductHeader`, `BasketTicketLayout`)
- Section names that map to DRD directories (e.g. "SectionLayoutActivities")
- Feature names that suggest a visual component

Read every relevant DRD fully. Extract:
- Figma source URLs (from the `figma-sources` frontmatter)
- Screenshot paths (e.g. `screens/images/previews/Desktop.png`, `Mobile.png`)
- Viewport descriptions (Desktop / Mobile)
- Interaction tables
- Component composition tables
- Content contract fields
- Data sources

**If no DRD is found for a feature:** do not block. Note it clearly in the spec — the developer AI will need to propose its own interface design.

---

## Step 4 — Propose the spec breakdown

Before writing anything, present your proposed breakdown to the user and wait for their confirmation.

A spec should cover one coherent, independently implementable unit — a screen, a user flow step, or a self-contained feature. The target: an AI developer should be able to implement it in under 2 hours.

Signs a spec is too big: it covers multiple screens, multiple user journeys, or has many independent business rules that don't share state. Split it.

Signs a spec is too small: it describes a pure sub-component with no user-facing value on its own. Merge it with its parent.

Present the breakdown like this:

```
Proposed spec breakdown for PRD00:
1. **cart-layer-structure** — Layer panier : ouverture, fermeture, ticket price vide (FUNC-001, FUNC-002)
2. **dashboard-structure** — Dashboard : shell, header, remote sticky, sections conditionnelles (FUNC-003, FUNC-004)
3. **participants-payment-navigation** — Navigation Participants ↔ Paiement via la remote (FUNC-005, FUNC-006, FUNC-007, FUNC-008)
4. **header-navigation** — Header : retour arrière, homepage, menu contacts/compte (FUNC-009, FUNC-010)

Dependencies: spec 2 depends on spec 1. Specs 3 and 4 depend on spec 2.

Does this breakdown look right? Any adjustments?
```

Only proceed once the user confirms (or adjusts the breakdown).

---

## Step 5 — HITL: ask questions one at a time

As you analyse each spec, you will encounter ambiguities, missing information, or decisions that only the product owner can make. Ask these questions **one at a time**, not as a batch. Wait for the answer before continuing.

Topics that require user input:
- **Unclear business rules** — if a BR is contradictory or underspecified, surface it
- **Missing acceptance criteria** — if a functional spec has no clear "done" condition
- **Scope ambiguity** — if you're unsure whether something is in or out of scope

Mark everything you cannot resolve with `[OPEN]` in the spec's "Open Questions" section.

---

## Step 6 — Generate the specs

For each spec in the confirmed breakdown, create a file in `docs/specs/` with a descriptive kebab-case name (e.g. `docs/specs/cart-layer-structure.md`).

### Frontmatter

```yaml
---
title: "Short human-readable title"
author: "<name provided by user>"
date: "<today's date, YYYY-MM-DD>"
status: draft
confidence: high | medium | low
related_specs:
  - other-spec-filename.md   # list sibling specs this one depends on or relates to
prd_source: "docs/specs/prd/<filename>.md"
---
```

**`confidence` calculation rules:**
- `high` — all DRDs present + Figma URLs resolved + no attention points
- `medium` — ≥1 DRD missing OR ≥1 open question OR ≥1 assumption
- `low` — DRDs missing on critical surfaces OR contradictory/incomplete BRs OR PRD itself incomplete

### Spec body

Write the spec in the **same language as the PRD** (French PRD → French spec, English PRD → English spec).

Use this exact section order:

---

#### 1. Description

One short paragraph. What does this spec cover? What does the user see or do?

---

#### 2. Points d'attention

This section is always the second section — it appears immediately after Description so the reader can assess quality before diving in.

If there are no attention points:
```markdown
> ✅ Aucun point d'attention. Niveau de confiance : HIGH
```

Otherwise, open with the confidence level, then a table with one row per issue:

```markdown
> Niveau de confiance : **MEDIUM**

| # | Type | Description | Section impactée |
|---|------|-------------|-----------------|
| 1 | ⚠️ DRD manquant | Pas de DRD pour le layer Détail F&D — l'AI devra proposer l'interface | §5 Figma & UI |
| 2 | 🔴 Incohérence | BR-007 ne précise pas le comportement sur mobile — en contradiction avec le DRD | §4 Business Rules |
```

**Four entry types — use exactly these labels:**
- `🔴 Incohérence` — contradiction or anomaly between sources (PRD vs DRD, BR vs BR, PRD vs glossary)
- `⚠️ DRD manquant` — UI surface with no design reference; the developer AI will have to invent the interface
- `❓ Question ouverte` — a decision only the PO can make; blocks or significantly risks the implementation
- `ℹ️ Hypothèse` — an assumption made in the absence of information; should be validated before dev starts

**Inline markers in the body:** wherever an attention point applies, add a lightweight reference back to the table:
```markdown
> ⚠️ Point d'attention #1 — Pas de DRD disponible pour ce layer.
```
This avoids duplicating the full explanation; the table in section 2 has the detail.

---

#### 3. Contexte & Objectifs

- Why does this feature exist?
- What problem does it solve for the user?
- What business goal does it serve?

#### 4. User Story

```
EN TANT QUE <type d'utilisateur>
JE VEUX <action ou capacité>
AFIN DE <bénéfice ou objectif>
```

(Use "AS A / I WANT / IN ORDER TO" for English PRDs.)

#### 5. Business Rules

Numbered list. Be exhaustive — copy and adapt every relevant BR from the PRD. Add any rules implied by the DRD that are not stated explicitly in the PRD.

```
1. BR-001 — ...
2. BR-007 — ...
3. (implied by DRD) — ...
```

#### 6. Figma & UI

If DRD(s) found:

```markdown
### Desktop
**Figma:** [Desktop](<url>)
**Screenshot:** ![Desktop](<relative path to preview image>)
<one paragraph describing the layout and key UI decisions from the DRD viewport section>

### Mobile
**Figma:** [Mobile](<url>)
**Screenshot:** ![Mobile](<relative path to preview image>)
<one paragraph describing the mobile-specific differences>

### Interactions
<copy the interaction table from the DRD, filtered to what's relevant to this spec>

### Component composition
<copy the component table from the DRD, filtered to what's relevant>
```

If no DRD found:

```markdown
> ⚠️ Point d'attention #N — Aucun DRD trouvé pour cette fonctionnalité. L'AI en charge du développement devra proposer une interface.
```

#### 7. Feature Flag

If the PRD contains a feature flag name, use it directly. Otherwise, propose a name derived from the PRD scope (e.g. `nbe_food_drinks`, `nbe_activities_booking`) and ask the user at the end of the spec generation — after all files are written — whether the feature should be feature-flagged and, if so, to confirm or adjust the proposed name.

```markdown
- **Nom du flag :** `<flag_name>` _(proposé — à confirmer)_
- **Valeur par défaut :** enabled | disabled
- **Comportement si désactivé :** <describe what the user sees or what fallback applies>
```

#### 8. Data Contract

> ℹ️ Les data contracts ne sont pas encore disponibles. Cette section sera complétée ultérieurement.

##### CMS Keys

| Clé | Description | Exemple de valeur |
|-----|-------------|-------------------|
| `<key>` | <what this content key controls> | `<example>` |

Infer likely CMS keys from the Content Contract section of the DRD (labels, button text, translated strings).

##### API Endpoints

| Méthode | Endpoint | Rôle |
|---------|----------|------|
| `GET` | `/api/...` | <purpose> |

Infer likely endpoints from the Data Sources section of the DRD and the functional specs in the PRD.

---

## Quality checklist before writing each file

Before writing a spec file, mentally verify:
- [ ] Every FUNC-xxx from the PRD that belongs to this spec is represented in the Business Rules
- [ ] The Figma links are real URLs from the DRD frontmatter (not invented)
- [ ] Screenshot paths are relative to the spec file location or use the correct path from the DRD
- [ ] `related_specs` lists all sibling specs that this one depends on or that depend on it
- [ ] The feature flag section has a proposed name (even if not yet confirmed by the PO)
- [ ] Every gap, assumption, inconsistency, and open question is captured in the "Points d'attention" table
- [ ] Every attention point has an inline `> ⚠️ Point d'attention #N` marker at the relevant spot in the body
- [ ] The `confidence` frontmatter field reflects the overall quality of sources
- [ ] The language matches the PRD throughout — including section titles, user story, and all body text

---

## Handling edge cases

**PRD with no DRD at all:** proceed normally, mark every UI section with the ⚠️ warning.

**One DRD covers multiple specs:** extract only the relevant parts of the DRD for each spec. Don't dump the entire DRD into each spec.

**PRD mentions a component not in `docs/specs/drd/`:** note it as an open question — the DRD may not have been written yet.

**Ambiguous scope between two PRDs:** surface it as an `[OPEN]` question and tag both specs.

**PRD already contains a feature flag name:** use it directly, no need to ask.