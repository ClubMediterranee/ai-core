---
name: prd
description: >
  Write a PRD from a validated brief — translate a problem into a solution by resolving the
  solution space: scope, user journeys, functional blocks, acceptance criteria, leading metrics,
  complexity. Runs as sequential steps with a validation gate after each one.
  Use whenever the user says "write a PRD", "create a PRD", "start the PRD", "PRD from the brief",
  "rédige un PRD", "écrire un PRD", "créer un PRD", "on part du brief", or names a brief to turn
  into a PRD — even if they only say "let's spec out this opportunity" while pointing at a brief.
  Requires a validated brief as input. NOT for turning an existing PRD into developer specs or
  user stories — that is the `spec` skill.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
version: 1.0.0
changelog:
  - version: 1.0.0
    date: 2026-07-28
    changes:
      - Initial release in ai-core (ported from the new-be project skill)
created-at: 2026-07-21
created-by: "Céline Net <celine.net.ext@clubmed.com>"
---

# PRD

You **translate a validated problem into a solution**. The problem and the scope of opportunities to solve it are established in a Brief. Each scoped opportunity is addressed by a PRD. The PRD resolves the solution space by defining the user journeys, acceptance criteria and capabilities - functional blocks. The PRD does not describe the conception - Design or Technical decisions.

---

## Bundled resources

Paths are relative to this skill's directory — they resolve wherever the skill is installed (plugin
cache, project `.claude/skills/`, or the repository itself).

| File | Read it when |
|------|--------------|
| `assets/TEMPLATE-prd.md` | Step 1 — instantiate the PRD skeleton |
| `TEMPLATE-canonical-memory.md` | Step 0 — bootstrap the project's canonical memory if absent |
| `refs/REF-brief-contract.md` | Step 0 — what the PRD consumes from the brief, and how to degrade |
| `refs/REF-challenge-pass.md` | Before every artifact presentation |
| `refs/REF-advanced-elicitation.md` | Whenever the PM chooses `[A]` |
| `refs/REF-user-journeys.md` | Step 2 |
| `refs/REF-functional-blocks.md` | Step 3 |
| `refs/REF-acceptance-criteria.md` | Step 4 |
| `refs/REF-metrics.md` | Step 5 |
| `refs/REF-complexity-sizing.md` | Step 6 |
| `scripts/validate_prd.py` | Quality gate — the structural checks |

---

## How the skill works

PRD runs in **sequential steps**. Each step ends with a **Step Gate**. Wait for the user validation to move to the next step

| Step | Objective | Gates |
|------|-----------|---------|
| **Step 0 — Context** | Explore the context, resolve the docs root, frame the brief | [C] |
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

After the PM chooses `[C]`, before continuing : run a backward check to ensure consistency, fill the corresponding PRD section to log the work done and update the canonical memory to record decisions and tensions.

| Step validated | Fill in the PRD | Canonical memory |
|---------------|-------------|------------------|
| Step 1 | Create the PRD from the full skeleton — frontmatter + Section 1 Executive Summary | OPP selected, scope confirmed |
| Step 2 | Section 3 — User Journeys *(Capabilities revealed: TBD — filled at Step 3)* | Journeys validated, OQs opened |
| Step 3 | Section 4 — FUNCs + update Section 3 (Capabilities revealed) | FUNCs validated, OQs opened/resolved |
| Step 4 | Section 5 — Acceptance Criteria | ACs validated, OQs opened/resolved |
| Step 5 | Section 7 — Metrics | Metrics validated |
| Step 6 | Frontmatter (complexity) + Sections 2, 6, 8, 9 | Final complexity |

> Sections 6 (Out of Scope), 8 (Glossary), and 9 (Open Questions) are filled incrementally at each step as new items emerge.

---

## Golden Rules

### Human-In-The-Loop

As you analyse, you will encounter ambiguities, missing information, or decisions that only the product owner can make. Ask one question at a time. Exception: up to 2 questions may be grouped if they are (a) clearly independent and (b) factual with no structural impact on scope or journeys. Wait for the answer before surfacing the step gate.

### Step Confirmation

No passive progression. The user must explicitly choose to validate and move to the next step at the Step Gate.

### Language Adaptation

Detect the PM's language from their first message. Apply it consistently to all agent messages, canonical memory content, and PRD file content. Do not switch language mid-session unless the PM explicitly does so.

**What does not translate.** Section titles, id prefixes (`FUNC-`, `BR-`, `ST-`, `PERM-`, `ERR-`, `LGM-`, `DC-`, `LDM-`, `NG-`, `OQ-`), frontmatter keys, the scenario keywords `WHEN` / `THEN` / `AND`, the label `*Capabilities revealed:*` and the structural markers `None identified.` / `None defined.` stay exactly as the template writes them, in English. They are machine tokens: `scripts/validate_prd.py` matches on them, and the downstream `spec` skill parses the same structure. Only the prose adapts — a French PRD has French journeys under an English `## 3. User Journeys` heading.

### Challenge Pass

Read `refs/REF-challenge-pass.md`, apply the protocol and surface the result.

### Advanced Elicitation

Read `refs/REF-advanced-elicitation.md` and apply the protocol whenever the user chooses Advanced Elicitation.

### Progressive File Writing

The PRD file exists in full from Step 1 — the whole skeleton, every section, placeholders included. Each step then **replaces its section's placeholders in place**. This is what keeps the document consistent: a replacement is idempotent and position-independent, whereas inserting into a half-written file is how sections end up duplicated, out of order, or missing from the table of contents.

After each `[C]` validated by the PM, execute in this order before continuing:

1. **Backward check** — 3 questions:
   - Does this decision modify the scope (Section 1)?
   - Does this decision modify a journey (Section 3)?
   - Does this decision modify a FUNC or an AC (Sections 4-5)?
   - No to all 3 → continue silently. Yes → identify the section, surface the modification, wait for confirmation, then continue.
2. **Fill the PRD section** for this step — refer to the mapping in *How the skill works*.
3. **Update `{DOCS_ROOT}/prd/canonical-memory.md`** — decisions confirmed, questions resolved, OQs opened, tensions logged, and `current_step` set to the step just validated.

---

## Step 0 — Context

### Resolve the docs root

The docs tree is **not** assumed to live under the current working directory — it often sits in a sibling repository, and the downstream `spec` skill resolves it the same way. Establish `{DOCS_ROOT}` before anything else, and use it in every later step instead of a bare relative path. Expected layout:

```
{DOCS_ROOT}/
├── brief/        ← brief sources (read-only)
├── prd/          ← OUTPUT — PRDs and canonical-memory.md, written by this skill
└── …             ← other analysis material (glossary, context.md)
```

1. Search for a `brief/` or `prd/` directory **that actually contains `.md` files**: in the cwd, then in sibling repositories / parent directories (e.g. `docs/brief/`, `../*/docs/brief/`). **Ignore empty scaffolds** and deduplicate the cwd from the sibling matches.
2. **Exactly one candidate** → its parent is `{DOCS_ROOT}`; state it once and move on.
3. **Several candidates, or none** → ask the user which docs root to use. Do not guess. Writing a PRD into a docs tree nobody else uses is how PRDs get lost.

### Bootstrap the canonical memory

If `{DOCS_ROOT}/prd/canonical-memory.md` does not exist, create it by copying `TEMPLATE-canonical-memory.md` from this skill's directory. Every later update targets that **project** file — never the template, which ships inside the skill, is shared by all projects, and may live in a read-only plugin cache.

If it already exists, read it. If it holds a PRD whose `current_step` is not `Step 6`, that work was interrupted: name it, and offer to resume at that step rather than starting a new PRD.

### Explore and understand deeply the context

Explore `{DOCS_ROOT}` freely to find any supporting files that seem relevant — context documents, glossaries, other PRDs, briefs. Read whatever helps build a complete understanding of the domain, the terminology, and the broader product context.

### Identify and sum up the Brief

Read `refs/REF-brief-contract.md` first — it states which fields the PRD consumes and how to proceed when the brief does not carry them.

**If the user provided a path:** read that file directly.
**If no path was given:** list all `.md` files in `{DOCS_ROOT}/brief/` and ask the user which one to process.
**If `{DOCS_ROOT}/brief/` does not exist or holds no `.md`:** say so explicitly and stop. There is nothing to translate, and inventing a problem statement is worse than stopping.

**Check the brief's status now, not at the quality gate.** QG-11 requires `status: validated`; discovering that after six steps of work wastes the PM's afternoon. If the frontmatter says anything else — or carries no `status` at all — name the file and its status, ask whether to continue anyway, and if they do, log the tension in the canonical memory. This is a signal, not a wall: the PM may legitimately explore ahead of formal validation.

Read and understand deeply the brief and present the main points to the user to anchor the PRD creation frame.

```
Problem Statement

What is the key problem? "[Key problem]"
Who has this problem? [Persona]
How to solve it? [list of included opportunities]
What is the goal? [list of KRs with T0 and targets]

These elements frame the PRD creation. Are you aligned ?
```

**If information are absent in the brief:** do not invent, inform the user "Not in the brief"

### Present the process

Present the process to show the user the path — after the brief summary.

**Step Gate:**
```
[C] Confirm the frame and continue to Step 1 — Scope
```

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

1. Ask "What is your name?" unless the user's identity is already clear from context — the name will be used as the `author`. The name alone; the frontmatter takes no email.
2. **Determine the PRD number.** Scan `{DOCS_ROOT}/prd/` with `Glob("[Pp][Rr][Dd]*.md")` — deliberately case-tolerant, because existing projects hold PRDs written before this convention (`PRD07 - Food & Drinks details.md`). Extract the leading number from each match, take the highest, increment by 1. Start at `01` if none exist. If a file matches but carries no extractable number, say so and ask the PM rather than silently restarting at `01` — a colliding id is exactly the failure this scan exists to prevent.
3. **Propose the path** `{DOCS_ROOT}/prd/prd<NN>-<short-opportunity-name>.md` — lowercase kebab-case, no spaces and no `&`. Those characters break the filename regexes used downstream (a PRD cited in a spec's `prd_source` gets truncated at the first space), and they turn every shell path into an escaping exercise. Wait for confirmation before writing. **Never rename existing PRDs** to this convention: specs already produced reference their current names.
4. **Create the PRD** — copy `assets/TEMPLATE-prd.md` in full (all 9 sections with placeholders), delete its instantiation comment block, then fill the frontmatter and Section 1.
5. **Update the canonical memory** — add the `[PRD<NN>]` section, set `current_step: Step 1`.

---

## Step 2 — User journeys

**Methodology:** Read `refs/REF-user-journeys.md`
Derive user journey when you have enough information.

**Step Gate:**
```
[A] Advanced Elicitation
[C] Continue to Step 3 — Functional blocks
```

**After [C]:** backward check, fill the PRD section, update the canonical memory

---

## Step 3 — Functional blocks

**Methodology:** Read `refs/REF-functional-blocks.md`
Derive functional blocks when you have enough information.

**Step Gate:**
```
[A] Advanced Elicitation
[C] Validate FUNCs and continue to Step 4 — Acceptance criteria
```

**After [C]:** backward check, fill the PRD section, update the canonical memory

---

## Step 4 — Acceptance criteria

**Methodology:** Read `refs/REF-acceptance-criteria.md`
Derive acceptance criteria when you have enough information.

**Step Gate:**
```
[A] Advanced Elicitation
[C] Validate and continue to Step 5
```

**After [C]:** backward check, fill the PRD section, update the canonical memory

---

## Step 5 — Leading Metrics

**Methodology:** Read `refs/REF-metrics.md`
Derive leading metrics when you have enough information.

**Step Gate:**
```
[A] Advanced Elicitation
[C] Validate and continue to Step 6 — Complexity
```

**After [C]:** backward check, fill the PRD section, update the canonical memory

---

## Step 6 — Complexity

**Methodology:** Read `refs/REF-complexity-sizing.md`
Count FUNCs and personas. Apply grid. Propose result with justification. If PM disagrees: make the case, then defer to PM's final call.

**Step Gate:**
```
[C] Confirm complexity and continue to PRD generation
```

**After [C]:** backward check, fill the PRD section, update the canonical memory

---

## Check Quality Gate

Run all 12 checks before saving. Fix any failure first.

**Structural block** — run the deterministic validator, do not eyeball it:

```bash
python3 <skill-dir>/scripts/validate_prd.py {DOCS_ROOT}/prd/prd<NN>-<short-name>.md
```

It covers QG-4, QG-6, QG-8, QG-9, QG-10, QG-11 and QG-12 — everything a machine can decide. This
matters because the remaining checks are judged by the same model that just wrote the PRD, and a
self-graded gate drifts. Exit `0` = clean, `1` = at least one error, `2` = bad path. Display the
output only on failure.

| # | Check | Pass | Fail |
|---|-------|------|------|
| QG-4 | **Scenario completeness** | Every FUNC has ≥ 1 WHEN/THEN scenario | A FUNC has no scenario block |
| QG-6 | **FUNC → Journey** | Every FUNC appears in ≥ 1 journey's *Capabilities revealed* list | A FUNC not backed by any journey |
| QG-8 | **Metrics completeness** | Section 7 has all 3 subsections; each either populated or explicitly "None identified." / "None defined." | A subsection absent — OR — a DC row without numeric threshold |
| QG-9 | **Frontmatter fields** | The 8 required fields present and valid: `id`, `title`, `version`, `status`, `complexity`, `date`, `author`, `brief` | A required field missing, misspelled, or invalid value |
| QG-10 | **Document title** | First content line after `---` is a H1 matching `title` exactly | H1 absent — OR — H1 text differs from `title` field |
| QG-11 | **Brief traceability** | Referenced brief exists with `status: validated`; every LGM/DC traces to brief | `brief` references non-existent or non-validated file — OR — LGM/DC introduced without brief anchor without tension |
| QG-12 | **AC completeness** | Every BR/ST/PERM/ERR referenced in a FUNC is defined in Section 5 | A FUNC references an ID not defined in Section 5 |

**Content block** — semantic checks, no script can decide these. Judge each one and display the result.

| # | Check | Pass | Fail |
|---|-------|------|------|
| QG-1 | **Userflow vs Wireflow** | Every journey step: user action + observable result, true if mockup changes | Step describes layout, scroll, UI component, or names a tech mechanism |
| QG-2 | **FUNC altitude** | Every FUNC: user capability (WHAT), not implementation (HOW) | FUNC contains framework, endpoint, SQL type, UI component, or layout detail |
| QG-3 | **BR altitude** | Every BR: observable product behavior, no tech mechanism or design detail | BR names API, endpoint, UI component, or prescribes layout |
| QG-5 | **Journey → FUNC** | Every journey step implying a capability has a matching FUNC | A journey step describes a capability with no FUNC |
| QG-7 | **OQ completeness** | Every product ambiguity is an OQ-XXX; no OQ contains a tech choice | An assumption is embedded in a FUNC or BR — OR — an OQ asks about frameworks or protocols |

**On QG pass:** set `status: review` and save.

> PRD saved with status: review.

**Status lifecycle:**

| Transition | Trigger | Actor |
|------------|---------|-------|
| *(file created)* → `in-progress` | Step 1 — the PRD file is written | This skill (automatic) |
| `in-progress → review` | 12 QG checks passed | This skill (automatic) |
| `review → accepted` | Section 9 empty + human sign-off | Human |
