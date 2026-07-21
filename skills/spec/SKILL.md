---
name: spec
description: 'Transform a validated PRD into developer-ready specs — each scoped to a single testable user outcome. Reads docs/specs/prd/ and cross-references docs/specs/drd/ design files to produce structured markdown specs in docs/specs/. Each spec contains: a User Story anchored on a FUNC-XXX outcome, EARS-formatted business rules (complete and necessary), a UI contract (Figma + interaction table), implementation anchors (feature flag, CMS keys, API endpoints), and Gherkin acceptance tests (passing + non-passing) traceable to BR-XXX and ERR-XXX. Use this skill whenever the user says: "/spec", "generate specs", "create specs from PRD", "découper en specs", "créer des specs", "générer des specs", "spec from PRD", or starts work on a PRD file. Also triggers when the user mentions a specific PRD by name or number (e.g. "PRD01", "le PRD des activités") and wants to turn it into actionable developer specs.'
allowed-tools: Read, Write, Bash
version: 1.1.0
changelog:
  - version: 1.1.0
    date: 2026-07-09
    changes:
      - Add Section 7 — Acceptance Tests with Gherkin scenarios (happy path + selective non-passing) and mandatory traces: tag for BR-XXX/ERR-XXX/FUNC-XXX 
  - version: 1.0.0
    date: 2026-06-23
    changes:
      - Initial release
created-at: 2026-06-23
created-by: "Jeremy Wallez <jeremy.wallez@clubmed.com>"
---

# spec

You transform a PRD into one or more detailed, developer-ready specs. The specs are "super user stories" — rich enough for an AI developer to work completely autonomously, scoped tightly enough to produce a single testable user outcome.

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
- All functional specifications (FUNC-xxx) and the user outcomes they serve
- All business rules (BR-xxx) — including which FUNCs they constrain
- All error scenarios (ERR-xxx) — including which FUNCs they apply to
- The acceptance criteria
- Any open questions or constraints already noted in the PRD
- Any feature flags or toggle names mentioned

Also explore the `docs/` folder freely to find any supporting files that seem relevant — context documents, glossaries, other PRDs, briefs. Read whatever helps build a complete understanding of the domain, the terminology, and the broader product context.

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
- Interaction tables — extract only what describes what the user does and what they observe, not component names or layout positions
- Component composition tables
- Content contract fields (CMS keys)
- Data sources (API endpoints)

**If no DRD is found for a feature:** do not block. Note it clearly in the spec — the developer AI will need to propose its own interface design.

---

## Step 4 — Propose the spec breakdown

Before writing anything, present your proposed breakdown to the user and wait for their confirmation.

A spec should cover one coherent, valuable, testable and as independent as possible increment.  
**Foundation spec:** when a dependency is unavoidable, declare it explicitly, keep its scope minimal, and document what it unblocks.

**Signs a spec is too large → split:**
- The spec covers two independent surfaces with distinct DRD viewports (e.g. desktop sticky vs mobile panel) — each deployable without the other
- The spec contains "and also" / "as well as" two independent actions, each with its own observable outcome

**Signs a spec is too small → merge:**
- It describes a UI interaction or sub-component with no user-facing value on its own → merge into its parent capability
- The observable result only makes sense in the context of another spec → merge

Propose the breakdown anchored on FUNC-XXX groupings - to ensure the scope of specs is exhaustive:

```
Proposed spec breakdown for PRD-XX — Booking price clarity:

Foundation (must be implemented first — unblocks all other specs):
0. booking summary shell (FUNC-001)
   L'utilisateur·rice voit le résumé de son séjour (destination, dates, participants)
   sur toutes les pages du parcours
   → Foundation spec. Unblocks specs 1–4b.

Independent specs (developable in parallel once spec 0 is delivered):
1. formula breakdown (FUNC-002)
   L'utilisateur·rice voit la composition détaillée de sa formule,
   incluant les éléments conditionnels selon ses participants et le resort
   Depends on: spec 0

2. additional fees (FUNC-003)
   L'utilisateur·rice voit les frais additionnels applicables à son séjour
   (cotisation annuelle, taxe de séjour selon config resort)
   Depends on: spec 0

3. section interactions (FUNC-004 + FUNC-005) [MERGE]
   L'utilisateur·rice ouvre, ferme et réduit les sections du résumé
   Merge reason: FUNC-005 (mode compact) is not demoed without FUNC-004
   (expand/collapse) — both share the same ST-001 lifecycle object
   Depends on: spec 0

4a. summary desktop (FUNC-006 — desktop surface) [SPLIT]
    L'utilisateur·rice accède au résumé en mode sticky sur desktop
    DRD: SummaryWidget.drd.md / Desktop viewport
    Depends on: spec 0

4b. summary mobile (FUNC-006 — mobile surface) [SPLIT]
    L'utilisateur·rice accède au résumé via le panneau dédié sur mobile
    DRD: SummaryWidget.drd.md / Mobile viewport
    Split reason: distinct DRD viewport + independent deployability
    Depends on: specs 0, 3, 4a (content parity verifiable only once 4a exists)

6 FUNCs → 6 specs (1 foundation, 1 merge, 1 split).
Specs 1, 2, 3, 4a developable in parallel.
Spec 4b depends on 4a for content parity.

Does this breakdown look right? Any adjustments?
```

Only proceed once the user confirms (or adjusts the breakdown).

---

## Step 5 — HITL: ask questions one at a time

As you analyse each spec, surface ambiguities, missing information, or decisions only the product owner can make — **one at a time**. Wait for the answer before continuing.

**Do not block spec generation on unresolved OQs.** Surface them and continue.

Topics that require user input:
- **Unclear business rules** — contradictory or underspecified BRs
- **Missing acceptance criteria** — a FUNC with no clear "done" condition
- **Scope ambiguity** — if you're unsure whether something is in or out of scope

Mark everything you cannot resolve with `[OPEN]` in the §2 Points d'attention table (type : `❓ Question ouverte`).

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

One short paragraph. What does this spec cover? What does the user see or do? Name the FUNC-XXX it implements in passing, not as the opening clause.

---

#### 2. Points d'attention

This section is never skipped — it appears immediately after Description so the reader can assess quality before diving into requirements.

If there are no attention points:
```markdown
> ✅ Aucun point d'attention. Niveau de confiance : HIGH
```

Otherwise, open with the confidence level, then a table with one row per issue:

```markdown
> Niveau de confiance : **MEDIUM**

| # | Type | Description | Section impactée |
|---|------|-------------|-----------------|
| 1 | ⚠️ DRD manquant | Pas de DRD pour le layer Détail F&D — l'AI devra proposer l'interface | §6 UI Contract |
| 2 | 🔴 Incohérence | BR-007 ne précise pas le comportement sur mobile — en contradiction avec le DRD | §5 Business Rules |
```

**Four entry types — use exactly these labels:**
- `🔴 Incohérence` — contradiction or anomaly between sources (PRD vs DRD, BR vs BR, PRD vs glossary)
- `⚠️ DRD manquant` — UI surface with no design reference; the developer AI will have to invent the interface
- `❓ Question ouverte` — a decision only the PO can make; listed here in §2, not in a separate section
- `ℹ️ Hypothèse` — an assumption made in the absence of information; should be validated before dev starts

**Inline markers in the body:** wherever an attention point applies, add `> ⚠️ Point d'attention #N` — no need to repeat the full explanation; the table in §2 has the detail.

---

#### 3. Contexte & Objectifs

- Why does this feature exist?
- What problem does it solve for the user?
- What business goal does it serve?

**In scope:** [explicit list of capabilities this spec covers]

**Out of scope:** [adjacent capabilities explicitly excluded — with reference to the spec or NG-XXX that covers them]

> When the PRD defines NG-XXX (Non-Goals), list each applicable one here explicitly: `NG-XXX — [description] (hors scope v1)`. This makes the exclusion a first-class decision, not a footnote.

---

#### 4. User Story

```
EN TANT QUE <type d'utilisateur>
JE VEUX <action ou capacité>
AFIN DE <bénéfice ou objectif utilisateur>
```

(Use "AS A / I WANT / IN ORDER TO" for English PRDs.)

---

#### 5. Business Rules

Numbered list. Be exhaustive — copy and adapt every relevant BR from the PRD. Add any rules implied by the DRD that are not stated explicitly in the PRD.

```
1. BR-001 — ...
2. BR-007 — ...
3. (implied by DRD) — ...
```
---

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
---

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

#### 9. Acceptance Tests

Write the scenario for:
1. **Nominal Passing case** 
2. **Nominal Non-Passing case** 
1. **Alternative Passing case** 
1. **Alternative Non-Passing case** 
3. **Edge case** 

Skip when: the scenario only documents an implementation detail → belongs in unit tests.

**Format:**

````markdown
#### Scénario : [short Label]

```gherkin
**Scenario:** [Human-readable brief describing value]
  # traces: FUNC-XXX / BR-XXX / ERR-XXX
  **Given:** [Initial context or precondition]
  **and Given:** [Additional context or preconditions]
  **When:** [Event that triggers the action]
  **Then:** [Expected result]
```
````

The `# traces:` tag is a comment (before `Given`) — visible to the reader, ignored by standard parsers.
Multiple Givens are okay: Preconditions stack up (e.g., "Given I'm logged in" + "Given I have items in my cart")
Multiple Whens/Thens: Sign of scope creep—split the story 


---

## Pre-write validation — outcome test

Before writing a spec file, verify:
- [ ] Every FUNC-XXX from the PRD that belongs to this spec is covered in §4 and §8
- [ ] Figma links are real URLs from the DRD frontmatter — never invented
- [ ] Screenshot paths are valid relative paths from the DRD
- [ ] `related_specs` lists all sibling specs this one depends on
- [ ] Language matches the PRD throughout — section titles, user story, all body text
- [ ] Test coverage check: (a) 1 nominal passing case at least (b) each ERR-XXX in scope has at least 1 non-passing scenario; (c) every scenario carries a `# traces:` referencing an ID defined in this spec; (d) no scenario documents a technical implementation detail
- [ ] Every gap, assumption, inconsistency, and open question is captured in the §2 Points d'attention table — including those that did not surface naturally during drafting: re-read the PRD one final time with this explicit goal
- [ ] Every attention point has an inline `> ⚠️ Point d'attention #N` marker at the relevant spot in the body

---

## Handling edge cases

**PRD with no DRD at all:** proceed normally, note it in §2 Points d'attention (type `⚠️ DRD manquant`) for each UI surface.
**One DRD covers multiple specs:** extract only the relevant parts for each spec. Don't dump the entire DRD into each spec.
**PRD mentions a component not in `docs/specs/drd/`:** note it in §2 Points d'attention (type `⚠️ DRD manquant`) — the DRD may not have been written yet.
**Ambiguous scope between two PRDs:** surface it in §2 Points d'attention (type `❓ Question ouverte`) and tag both specs.
**PRD already contains a feature flag name:** use it directly, no need to ask.
**Spec count > 10 before covering all FUNCs:** pause, flag to the user that the PRD may need an intermediate epic-level breakdown before spec generation.
