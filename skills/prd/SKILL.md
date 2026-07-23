---
name: prd
description: >
  Use when writing a new PRD from a validated brief. Requires a validated brief as input.
  Triggers on requests like "write a spec", "create a PRD", "feature spec",
  "functional requirements", "acceptance criteria",
  or when a brief has been validated and solution-space definition must begin.
allowed-tools: Read, Write, Edit, Glob, Grep, mcp__*
version: 3.0.0
changelog:
  - version: 3.0.0
    date: 2026-07-21
    changes:
      - Initial release in ai-core (ported from new-be project skill)
      - Fixed plugin-relative paths for all REF file references
      - Replaced project-specific canonical-memory.md with empty template
created-at: 2026-07-21
created-by: "Céline Net <celine.net.ext@clubmed.com>"
---

# PRD

You **translate a validated problem into a solution**. The problem and the scope of opportunities to solve it are established in a Brief. Each scoped opportunity is addressed by a PRD. The PRD resolves the solution space by defining the user journeys, acceptance criteria and capabilities - functional blocks. The PRD does not describe the conception - Design or Technical decisions. 

---

## How the skill works

PRD runs in **sequential steps**. Each step ends with a **Step Gate**. Wait for the user validation to move to the next step

| Step | Objective | Gates |
|------|-----------|---------|
| **Step 0 — Context** | Explore the context | NA |
| **Step 1 — Scope** | Select the single opportunity this PRD addresses | [C] |
| **Step 2 — User journeys** | Derive end-to-end flows anchored on the selected opportunity | [A] [C] |
| **Step 3 — Functional blocks** | Derive FUNCs from validated journeys and ACs | [A] [C] |
| **Step 4 — Acceptance criteria** | Derive BR, ST, PERM, ERR from journeys and user input | [A] [C] |
| **Step 5 — Leading Metrics** | Identify observable user behaviors that predict adoption | [A] [C] |
| **Step 6 — Complexity** | Size the PRD before drafting | [C] |

**Step Gate options:**
```
[A] Advanced Elicitation
[C] Validate and continue to the next step
```

After the PM chooses `[C]`, before continuing : run a backward check to ensure consistency, write the corresponding PRD section to log the work done and update canonical-memory.md to record decisions and tensions.

| Step validated | Write to PRD | Canonical memory |
|---------------|-------------|------------------|
| Step 1 | Create PRD file — frontmatter (partial) + Section 1 Executive Summary | OPP selected, scope confirmed |
| Step 2 | Section 3 — User Journeys *(Capabilities revealed: TBD — filled at Step 3)* | Journeys validated, OQs opened |
| Step 3 | Section 4 — FUNCs + update Section 3 (Capabilities revealed) | FUNCs validated, OQs opened/resolved |
| Step 4 | Section 5 — Acceptance Criteria | ACs validated, OQs opened/resolved |
| Step 5 | Section 7 — Metrics | Metrics validated |
| Step 6 | Finalize frontmatter (complexity) + Sections 2, 6, 8, 9 | Final complexity, status set to in-progress |

> Sections 6 (Out of Scope), 8 (Glossary), and 9 (Open Questions) are updated incrementally at each step as new items emerge.

---

## Golden Rules 

### Human-In-The-Loop

As you analyse, you will encounter ambiguities, missing information, or decisions that only the product owner can make. Ask one question at a time. Exception: up to 2 questions may be grouped if they are (a) clearly independent and (b) factual with no structural impact on scope or journeys. Wait for the answer before surfacing the step gate.

### Step Confirmation

No passive progression. The user must explicitly choose to validate and move to the next step at the Step Gate. 

### Language Adaptation

Detect the PM's language from their first message. Apply it consistently to all agent messages, canonical-memory.md content, and PRD file content. Do not switch language mid-session unless the PM explicitly does so.

### Challenge Pass

Read `.claude/plugins/clubmed-product/skills/prd/refs/REF-challenge-pass.md`, apply the protocol and surface the result.

### Advanced Elicitation

Read `.claude/plugins/clubmed-product/skills/prd/refs/REF-advanced-elicitation.md` and apply the protocol whenever the user chooses Advanced Elicitation. 

### Progressive File Writing 

After each `[C]` validated by the PM, execute in this order before continuing:

1. **Backward check** — 3 questions:
   - Does this decision modify the scope (Section 1)?
   - Does this decision modify a journey (Section 3)?
   - Does this decision modify a FUNC or an AC (Sections 4-5)?
   - No to all 3 → continue silently. Yes → identify the section, surface the modification, wait for confirmation, then continue.
2. **Write the PRD section** for this step - refer to mapping in How this skill works : read `.claude/plugins/clubmed-product/skills/prd/TEMPLATE-prd.md` to obtain the template
3. **Update `canonical-memory.md`** — decisions confirmed, questions resolved, OQs opened.

---

## Step 0 — Context

### Explore and understand deeply the context

Explore the `docs/` folder freely to find any supporting files that seem relevant — context documents, glossaries, other PRDs, briefs. Read whatever helps build a complete understanding of the domain, the terminology, and the broader product context.

### Identify and sum up the Brief

**If the user provided a path:** read that file directly.
**If no path was given:** list all `.md` files in `docs/brief/` and ask the user which one to process. 

Read and understand deeply the brief and present the main points to the user to anchor the PRD creation frame. 

```
Problem Statement

What is the key problem? "[Key problem]" 
Who has this problem? [Persona]
How to solve it? [list of included opportunities]
What is the goal? [list of KRs with T0 and targets]

These elements frame the PRD creation. Are you aligned ? 
```

**If information are absent in the brief:** do not invent, inform the user "Not in the brief "

### Present the process

Present the process to show the user the path — after the brief summary.

---

## Step 1 — Scope

### Identify the scope 

Show the list of opportunities imported from the brief. Ask user to choose the opportunity. 

**If the named opportunity is not in the brief's list:** signal and open a tension. Do not block the Step Gate.

**Step Gate:**
```
[C] Confirm the opportunity and continue
```

Execute in this order before continuing

1. Ask "What is your name?" unless the user's identity is already clear from context - the name will be used as the author.
2. Scan `docs/prd/` with `Glob("docs/prd/prd-*.md")`. Take the highest existing numeric suffix and increment by 1. - the number will be used as ID. Start at `prd-001` if none exist.
3. Ask where to save and propose default path: `docs/prd/PRD[id]-[Short opportunity Name].md`. Wait for confirmation before writing.
4. Write PRD section 
5. Update `canonical-memory.md`: set the PRD section `status` to match the PRD frontmatter

---

## Step 2 — User journeys

**Methodology:** Read `.claude/plugins/clubmed-product/skills/prd/refs/REF-user-journeys.md`
Derive user journey when you have enough information. 

**Step Gate:** 
```
[A] Advanced Elicitation 
[C] Continue to Step 3 — Functional blocks
```

**After [C]:** backward check, write the PRD section, update `canonical-memory.md`

---

## Step 3 — Functional blocks

**Methodology:** Read `.claude/plugins/clubmed-product/skills/prd/refs/REF-functional-blocks.md`
Derive functional blocks when you have enough information.

**Step Gate:** 
```
[A] Advanced Elicitation 
[C] Validate FUNCs and continue to Step 4 — Acceptance criteria
```

**After [C]:** backward check, write the PRD section, update `canonical-memory.md`

---

## Step 4 — Acceptance criteria

**Methodology:** Read `.claude/plugins/clubmed-product/skills/prd/refs/REF-acceptance-criteria.md`
Derive acceptance criteria when you have enough information.

**Step Gate:** 
```
[A] Advanced Elicitation 
[C] Validate and continue to Step 5
```

**After [C]:** backward check, write the PRD section, update `canonical-memory.md`

---

## Step 5 — Leading Metrics

**Methodology:** Read `.claude/plugins/clubmed-product/skills/prd/refs/REF-metrics.md` 
Derive leading metrics when you have enough information.

**Step Gate:** 
```
[A] Advanced Elicitation 
[C] Validate and continue to Step 6 — Complexity
```

**After [C]:** backward check, write the PRD section, update `canonical-memory.md`

---

## Step 6 — Complexity

**Methodology:** Read `.claude/plugins/clubmed-product/skills/prd/refs/REF-complexity-sizing.md`
Count FUNCs and personas. Apply grid. Propose result with justification. If PM disagrees: make the case, then defer to PM's final call.

**Step Gate:** 
```
[C] Confirm complexity and continue to PRD generation
```

**After [C]:** backward check, write the PRD section, update `canonical-memory.md`

---

## Check Quality Gate

Run all 12 checks before saving. Fix any failure first.

**Structural block** — silent verification. Display only on failure.

| # | Check | Pass | Fail |
|---|-------|------|------|
| QG-9 | **Frontmatter fields** | 8 required fields present and valid (see Standards) | A required field missing, misspelled, or invalid value |
| QG-10 | **Document title** | First content line after `---` is a H1 matching `title` exactly | H1 absent — OR — H1 text differs from `title` field |
| QG-11 | **Brief traceability** | Referenced brief exists with `status: validated`; every LGM/DC traces to brief | `brief` references non-existent or non-validated file — OR — LGM/DC introduced without brief anchor without tension |

**Content block** — display the result of each check.

| # | Check | Pass | Fail |
|---|-------|------|------|
| QG-1 | **Userflow vs Wireflow** | Every journey step: user action + observable result, true if mockup changes | Step describes layout, scroll, UI component, or names a tech mechanism |
| QG-2 | **FUNC altitude** | Every FUNC: user capability (WHAT), not implementation (HOW) | FUNC contains framework, endpoint, SQL type, UI component, or layout detail |
| QG-3 | **BR altitude** | Every BR: observable product behavior, no tech mechanism or design detail | BR names API, endpoint, UI component, or prescribes layout |
| QG-4 | **Scenario completeness** | Every FUNC has ≥ 1 WHEN/THEN scenario | A FUNC has no scenario block |
| QG-5 | **Journey → FUNC** | Every journey step implying a capability has a matching FUNC | A journey step describes a capability with no FUNC |
| QG-6 | **FUNC → Journey** | Every FUNC appears in ≥ 1 journey's *Capabilities revealed* list | A FUNC not backed by any journey |
| QG-7 | **OQ completeness** | Every product ambiguity is an OQ-XXX; no OQ contains a tech choice | An assumption is embedded in a FUNC or BR — OR — an OQ asks about frameworks or protocols |
| QG-8 | **Metrics completeness** | Section 7 has all 3 subsections; each either populated or explicitly "None identified." / "None defined." | A subsection absent — OR — a DC row without numeric threshold |
| QG-12 | **AC completeness** | Every BR/ST/PERM/ERR referenced in a FUNC is defined in Section 5 | A FUNC references an ID not defined in Section 5 |

**On QG pass:** set `status: review` and save. Then:
> PRD saved with status: review.
> For an independent review (blank context, no production bias) → type `/review-prd`

**Status lifecycle:**

| Transition | Trigger | Actor |
|------------|---------|-------|
| `draft → in-progress` | Session started | This skill (automatic) |
| `in-progress → review` | 12 QG checks passed | This skill (automatic) |
| `review → accepted` | Section 9 empty + human sign-off | Human |
