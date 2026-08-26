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
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
version: 1.4.0
changelog:
  - version: 1.4.0
    date: 2026-08-26
    changes:
      - "Gate contract made explicit: nothing reaches the PRD file before `[C]`, and every gate block states what `[C]` writes — the canonical memory keeps taking parked items during derivation"
      - "`[A]` is the agent's work: the protocol is inlined in SKILL.md, and answering it by asking the PM what to dig into is named as the one response it never means"
      - "New golden rule *Name the Arbitrations* — boundary decisions are presented with the artifact, and a PM-decidable ambiguity is asked before the gate rather than filed as an OQ"
      - "Acceptance criteria reference realigned on §5's tables: the block format it documented defined nothing the validator could see"
      - "Step 4 back-fills each FUNC's acceptance-criteria bullets; FUNCs no longer derive from rules that do not exist yet"
      - "Section 2 Personas filled at Step 2, where the persona is resolved, instead of Step 6, which counts them; PER-XXX dropped from complexity sizing"
      - "Challenge Pass gains its Metrics table, so every artifact presentation has one"
      - "Validator: a bold id and an escaped pipe no longer fail a gate, country variant tags are content; QG-11 split between the script and the judged block"
      - "First test suite for `validate_prd.py` — 12 regression cases, stdlib only"
  - version: 1.3.0
    date: 2026-08-24
    changes:
      - "Step 2 opens on a persona-goal list confirmed with the PM before any flow is written — Cockburn's actor-goal list, absorbing the former coverage check; each journey then states its goal on a `*Goal:*` line at the user-goal level"
      - "Journey rules reworked: completeness judged on the nominal path, a variation placed where it diverges, splitting given a test of its own against merging, and how many journeys to write settled as a readability decision that never changes the capabilities revealed"
      - "Variation routing: same action on a different object is a parameter, a BR when the rules differ, a variation when the observable result differs — the result being what the user ends up with, not what they had to supply"
      - "Saturation signal states which remedy applies (BR for rule detail, step or split for a different consequence) and is re-applied after any merge"
      - "Journey-level preconditions distinct from a scenario GIVEN; the user stays the subject even when the system acts; Step 2 reasons in observable results, FUNC ids being assigned and frozen at Step 3"
      - "A step presents what it derived; what the skill parks, logs or records stays in the canonical memory"
      - "Pruned: the 10 journey validation criteria, the two altitudes table, the 4-8 step range, and two duplicated Challenge Pass rows"
  - version: 1.2.0
    date: 2026-08-24
    changes:
      - "FUNCs: one boundary discriminant (autonomous observable outcome) replacing the format constraint, the upper/lower bounds and the multi-surface rule"
      - "Step 3: derivation output is each journey's *Capabilities revealed:* line, filled in"
      - "FUNC ids are identifiers, not ordinals — order fixed at derivation, never renumbered"
      - "Nominal scenario: optional GIVEN prerequisite"
      - "Step 2 gate: behavioural vocabulary frozen in one grouped confirmation"
      - "Journeys: a cross-cutting population is a valid persona answer"
      - "BR hygiene: atomicity, one-rule-one-BR, state adequacy, out-of-scope and perimeter leaks"
      - "ACs referenced from a FUNC with their description; section 5 stays the source of truth"
      - "Business Rules grouped into #### thematic sub-sections past ~10 rules"
      - "Optional section 10 Constraints (CB/CL)"
      - "Validator: referential integrity, AC bullet fidelity, author guard"
      - "Layout aligned on the standard skill anatomy: refs/ renamed references/, canonical memory template moved into assets/"
  - version: 1.1.0
    date: 2026-08-15
    changes:
      - "Step 2: skeleton-based sufficiency check with three routes (direct / annotated speculative / bootstrap canvas via one AskUserQuestion call)"
      - "Step 2: journey granularity rules, two outcome altitudes, variation and orphan-action routing, ERR candidates parked for Step 4"
      - "Challenge Pass journeys: Macro step, Bi-goal journey, Error path as step"
      - "HITL rule: documented exception for the grouped journey bootstrap canvas"
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
cache, project `.claude/skills/`, or the repository itself). The quality gate command below calls
that same directory `<skill-dir>`.

| File | Read it when |
|------|--------------|
| `assets/TEMPLATE-prd.md` | Step 1 — instantiate the PRD skeleton |
| `assets/TEMPLATE-canonical-memory.md` | Step 0 — bootstrap the project's canonical memory if absent |
| `references/REF-brief-contract.md` | Step 0 — what the PRD consumes from the brief, and how to degrade |
| `references/REF-challenge-pass.md` | Before every artifact presentation |
| `references/REF-advanced-elicitation.md` | Whenever the PM chooses `[A]` |
| `references/REF-user-journeys.md` | Step 2 |
| `references/REF-functional-blocks.md` | Step 3 |
| `references/REF-acceptance-criteria.md` | Step 4 |
| `references/REF-metrics.md` | Step 5 |
| `references/REF-complexity-sizing.md` | Step 6 |
| `scripts/validate_prd.py` | Quality gate — the structural checks |

---

## How the skill works

PRD runs in **sequential steps**. Each step ends with a **Step Gate**. Wait for the user validation to move to the next step

| Step | Objective | Gates |
|------|-----------|---------|
| **Step 0 — Context** | Explore the context, resolve the docs root, frame the brief | [C] |
| **Step 1 — Scope** | Select the single opportunity this PRD addresses | [C] |
| **Step 2 — User journeys** | Derive end-to-end flows anchored on the selected opportunity | [A] [C] |
| **Step 3 — Functional blocks** | Derive FUNCs from validated journeys | [A] [C] |
| **Step 4 — Acceptance criteria** | Derive BR, ST, PERM, ERR from journeys and user input | [A] [C] |
| **Step 5 — Leading Metrics** | Identify observable user behaviors that predict adoption | [A] [C] |
| **Step 6 — Complexity** | Size the PRD before drafting | [C] |

**Step Gate options:**
```
[A] Advanced Elicitation — I name what I could not settle, and ask about it
[C] Validate → the step's section is written to file, then the next step
```

**What a step presents:** the artifact it has just derived, plus whatever that step explicitly says to surface. Anything the skill tells you to *park*, *log* or *record* goes to the canonical memory and is not part of the presentation — it comes back at the step that consumes it. A step that shows more than it produced turns its gate into a discussion of work that is not up for validation yet. And an open question at presentation time means **the gate is not due yet** — ask it, wait for the answer, then surface the gate.

After the PM chooses `[C]`, before continuing : run a backward check to ensure consistency, fill the corresponding PRD section to log the work done and update the canonical memory to record decisions and tensions.

| Step validated | Fill in the PRD | Canonical memory |
|---------------|-------------|------------------|
| Step 1 | Create the PRD from the full skeleton — frontmatter + Section 1 Executive Summary | OPP selected, scope confirmed |
| Step 2 | Section 2 — Personas + Section 3 — User Journeys *(Capabilities revealed: TBD — filled at Step 3)* | Journeys validated, OQs opened, ERR candidates parked |
| Step 3 | Section 4 — FUNCs + update Section 3 (Capabilities revealed) | FUNCs validated, OQs opened/resolved |
| Step 4 | Section 5 — Acceptance Criteria + back-fill each FUNC's `**Acceptance criteria:**` bullets in Section 4 | ACs validated, OQs opened/resolved |
| Step 5 | Section 7 — Metrics | Metrics validated |
| Step 6 | Frontmatter (complexity) + Sections 6, 8, 9 | Final complexity |

> Sections 6 (Out of Scope), 8 (Glossary), 9 (Open Questions) — and 10 (Constraints) when the PRD
> inherits any — are filled incrementally at each step as new items emerge.

---

## Golden Rules

### Human-In-The-Loop

As you analyse, you will encounter ambiguities, missing information, or decisions that only the product owner can make. Ask one question at a time. Exceptions:
- Up to 2 questions may be grouped if they are (a) clearly independent and (b) factual with no structural impact on scope or journeys.
- The **journey bootstrap canvas** (Step 2) — full, or reduced to the empty skeleton fields — is ONE AskUserQuestion call grouping up to 4 fields; never decompose it into sequential questions. See `references/REF-user-journeys.md`.

Wait for the answer before surfacing the step gate.

### Name the Arbitrations

Every artifact is presented with the boundary decisions that produced it: *here are the N calls I had
to make — confirm or correct*, never *did I miss anything?*. The second form moves the work onto the
PM and buys a silent validation.

A decision only the PM can make is **asked before the gate** — not absorbed into the artifact, and
not filed as an `OQ-XXX`. An `OQ-XXX` records what stays open **after** asking, or what the PM
explicitly defers.

### Step Confirmation

No passive progression. The user must explicitly choose to validate and move to the next step at the Step Gate.

### Language Adaptation

Detect the PM's language from their first message. Apply it consistently to all agent messages, canonical memory content, and PRD file content. Do not switch language mid-session unless the PM explicitly does so.

**What does not translate.** Section titles, id prefixes (`FUNC-`, `BR-`, `ST-`, `PERM-`, `ERR-`, `CB-`, `CL-`, `LGM-`, `DC-`, `LDM-`, `NG-`, `OQ-`), frontmatter keys, the scenario keywords `GIVEN` / `WHEN` / `THEN` / `AND`, the labels `*Goal:*`, `*Capabilities revealed:*`, `*Precondition:*` and `**Acceptance criteria:**`, the structural markers `None identified.` / `None defined.`, the journey variation prefix `Variation:` and the draft marker `[ASSUMPTION: ...]` stay exactly as written here, in English. They are machine tokens: `scripts/validate_prd.py` matches on some of them, and the downstream `spec` skill parses the same structure. Only the prose adapts — a French PRD has French journeys under an English `## 3. User Journeys` heading.

### Challenge Pass

Read `references/REF-challenge-pass.md`, apply the protocol and surface the result.

### Advanced Elicitation

`[A]` is **the agent's work, not a question to the PM.** Never answer `[A]` by asking what they want
to dig into — that is the one thing the option does not mean. Produce, in one message:

1. what you could not settle on your own, reasoned visibly;
2. 2–3 patterns identified for the current artifact — the per-artifact lists live in
   `references/REF-advanced-elicitation.md`;
3. 1–3 questions derived from that reasoning, never generic.

Then re-present the gate. Read the reference for the pattern list of the artifact at hand.

### Write Only After [C]

**Nothing reaches the PRD file before the PM has chosen `[C]`.** A derivation presented at a gate
lives in the conversation until it is validated — the PRD file records validated work, it is not a
scratchpad. This holds at every step, including a version corrected after `[A]`.

**The canonical memory is the other file, and it plays by other rules.** It receives items *during*
derivation — the ERR candidates parked at Step 2, a tension spotted mid-analysis — because that is
what it is for. Only the PRD waits for `[C]`.

Once validated, a section is filled **in place**: the file has held the full skeleton, every section
and every placeholder, since Step 1, and each step **replaces its own placeholders**. A replacement
is idempotent and position-independent, whereas inserting into a half-written file is how sections
end up duplicated, out of order, or missing from the table of contents.

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

If `{DOCS_ROOT}/prd/canonical-memory.md` does not exist, create it by copying `assets/TEMPLATE-canonical-memory.md` from this skill's directory. Every later update targets that **project** file — never the template, which ships inside the skill, is shared by all projects, and may live in a read-only plugin cache.

If it already exists, read it. If it holds a PRD whose `current_step` is not `Step 6`, that work was interrupted: name it, and offer to resume at that step rather than starting a new PRD.

### Explore and understand deeply the context

Explore `{DOCS_ROOT}` freely to find any supporting files that seem relevant — context documents, glossaries, other PRDs, briefs. Read whatever helps build a complete understanding of the domain, the terminology, and the broader product context.

### Identify and sum up the Brief

Read `references/REF-brief-contract.md` first — it states which fields the PRD consumes and how to proceed when the brief does not carry them.

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
[C] Confirm the opportunity → the PRD file is created, then Step 2 — User journeys
```

Execute in this order before continuing

1. Ask "What is your name?" unless the user's identity is already clear from context — the name will be used as the `author`. The name alone; the frontmatter takes no email.
2. **Determine the PRD number.** Scan `{DOCS_ROOT}/prd/` with `Glob("[Pp][Rr][Dd]*.md")` — deliberately case-tolerant, because existing projects hold PRDs written before this convention (`PRD07 - Food & Drinks details.md`). Extract the leading number from each match, take the highest, increment by 1. Start at `01` if none exist. If a file matches but carries no extractable number, say so and ask the PM rather than silently restarting at `01` — a colliding id is exactly the failure this scan exists to prevent.
3. **Propose the path** `{DOCS_ROOT}/prd/prd<NN>-<short-opportunity-name>.md` — lowercase kebab-case, no spaces and no `&`. Those characters break the filename regexes used downstream (a PRD cited in a spec's `prd_source` gets truncated at the first space), and they turn every shell path into an escaping exercise. Wait for confirmation before writing. **Never rename existing PRDs** to this convention: specs already produced reference their current names.
4. **Create the PRD** — copy `assets/TEMPLATE-prd.md` in full (all 9 sections with placeholders), delete its instantiation comment block, then fill the frontmatter and Section 1.
5. **Update the canonical memory** — add the `[PRD<NN>]` section, set `current_step: Step 1`.

---

## Step 2 — User journeys

**Methodology:** Read `references/REF-user-journeys.md`

1. **List the goals before writing any flow** — one line per persona → goal, from OPP-XXX and the brief, each passing the user-goal question: the actor could stop there satisfied, in one sitting. Confirm the list with the PM in one message; a single-goal scope is acceptable, log it. This settles the section's scope while a correction still costs one line. **The personas confirmed here are what Section 2 states at `[C]`** — including the case where the answer is a cross-cutting population rather than a named persona.
2. Run the **skeleton-based sufficiency check** for each confirmed goal — persona, trigger, variations — and follow its routing: direct derivation (assumed elements marked `[ASSUMPTION: ...]`), partial derivation plus ONE grouped AskUserQuestion call for the empty fields, or full bootstrap canvas.
3. Derive the flows, each carrying its goal on a `*Goal:*` line. Apply the granularity and routing rules — parameters, variations, orphan actions, ERR candidates parked in the canonical memory for Step 4. Reason in **observable results, never in `FUNC-` ids**: those are assigned and frozen at Step 3.
4. Challenge Pass, then present for the user check.
5. Before the gate, **freeze the behavioural vocabulary** — the 2 to 4 terms carrying an implementation implication, confirmed in one message and recorded in the canonical memory's *Project glossary*.

**Step Gate:**
```
[A] Advanced Elicitation — I name what I could not settle, and ask about it
[C] Validate → Sections 2 and 3 are written to file, then Step 3 — Functional blocks
```

At the gate: every remaining `[ASSUMPTION]` marker is confirmed by the PM or converted to an OQ-XXX — none survives into Section 3.

**Before [C]:** the derivation stays in the conversation — nothing is written to the PRD file.
**On [C]:** backward check → fill the PRD section → update the canonical memory.

---

## Step 3 — Functional blocks

**Methodology:** Read `references/REF-functional-blocks.md`
Derive functional blocks when you have enough information. **The output of this step is each
journey's `*Capabilities revealed:*` line, filled in** — a journey step carrying an observable
outcome that appears in no line is a missing FUNC, or a step to name explicitly as covered by a
cross-cutting FUNC. Fix the FUNC order before the gate; the ids are frozen once assigned.

**Step Gate:**
```
[A] Advanced Elicitation — I name what I could not settle, and ask about it
[C] Validate FUNCs → Section 4 is written to file, then Step 4 — Acceptance criteria
```

**Before [C]:** the derivation stays in the conversation — nothing is written to the PRD file.
**On [C]:** backward check → fill the PRD section → update the canonical memory.

---

## Step 4 — Acceptance criteria

**Methodology:** Read `references/REF-acceptance-criteria.md`
Derive acceptance criteria when you have enough information. Start from the **ERR candidates** parked in the canonical memory at Step 2.

**This step also completes Section 4.** A FUNC written at Step 3 could not cite criteria that did not
exist yet, so its `**Acceptance criteria:**` bullets are filled here, at `[C]`, from the ids just
derived. Section 5 is the source of truth for the wording — see the reference for the per-type
linearisation. A FUNC left with no criterion is unspecified, not simple, and the validator says so.

**Step Gate:**
```
[A] Advanced Elicitation — I name what I could not settle, and ask about it
[C] Validate → Section 5 is written and Section 4 completed, then Step 5 — Leading metrics
```

**Before [C]:** the derivation stays in the conversation — nothing is written to the PRD file.
**On [C]:** backward check → fill the PRD section → update the canonical memory.

---

## Step 5 — Leading Metrics

**Methodology:** Read `references/REF-metrics.md`
Derive leading metrics when you have enough information.

**Step Gate:**
```
[A] Advanced Elicitation — I name what I could not settle, and ask about it
[C] Validate → Section 7 is written to file, then Step 6 — Complexity
```

**Before [C]:** the derivation stays in the conversation — nothing is written to the PRD file.
**On [C]:** backward check → fill the PRD section → update the canonical memory.

---

## Step 6 — Complexity

**Methodology:** Read `references/REF-complexity-sizing.md`
Count FUNCs and personas. Apply grid. Propose result with justification. If PM disagrees: make the case, then defer to PM's final call.

**Step Gate:**
```
[C] Confirm complexity → the remaining sections are written to file, then the quality gate
```

**Before [C]:** the derivation stays in the conversation — nothing is written to the PRD file.
**On [C]:** backward check → fill the PRD section → update the canonical memory.

---

## Check Quality Gate

Run all 12 checks before saving. Fix any failure first. QG-11 appears in both tables — one number, two halves, because only one of them is decidable by a script.

**Structural block** — run the deterministic validator, do not eyeball it:

```bash
python3 <skill-dir>/scripts/validate_prd.py {DOCS_ROOT}/prd/prd<NN>-<short-name>.md
```

It covers QG-4, QG-6, QG-8, QG-9, QG-10, QG-12 and the resolvable half of QG-11 — everything a
machine can decide, including the PRD's referential integrity (duplicate ids, orphan criteria, the
FUNC ↔ AC mirror) and the fidelity of each acceptance-criteria bullet to its section 5 definition.
**QG-11 is split on purpose:** the script resolves the brief and reads its status, while whether
every LGM/DC traces back to the brief is judged with the content block below — no script can decide
that half, and leaving it implied is how it ended up checked by nobody. This
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
| QG-11 | **Brief resolution** *(script half)* | The `brief` field resolves to a file on disk carrying `status: validated` | The brief resolves to nothing (ERROR) — OR — it is not validated (WARN: a signal, not a wall — continue and log the tension, see `references/REF-brief-contract.md`) |
| QG-12 | **AC integrity** | Every id referenced in a FUNC is defined in Section 5, every id is defined once, every FUNC carries criteria, and Section 5's *Applies to* mirrors the FUNCs' lists | A dangling or duplicated id — OR — a FUNC with no criteria — OR — the two directions disagreeing |

**Content block** — semantic checks, no script can decide these. Judge each one and display the result.

| # | Check | Pass | Fail |
|---|-------|------|------|
| QG-1 | **Userflow vs Wireflow** | Every journey step: one user action + observable result, true if mockup changes | Step describes layout, scroll, UI component, names a tech mechanism, bundles several actions, or describes a failure response |
| QG-2 | **FUNC altitude** | Every FUNC: user capability (WHAT), not implementation (HOW) | FUNC contains framework, endpoint, SQL type, UI component, or layout detail |
| QG-3 | **BR altitude** | Every BR: observable product behavior, no tech mechanism or design detail | BR names API, endpoint, UI component, or prescribes layout |
| QG-5 | **Journey → FUNC** | Every journey step implying a capability has a matching FUNC | A journey step describes a capability with no FUNC |
| QG-7 | **OQ completeness** | Every product ambiguity is an OQ-XXX; no OQ contains a tech choice | An assumption is embedded in a FUNC or BR — OR — an OQ asks about frameworks or protocols |
| QG-11 | **Brief traceability** *(judged half)* | Every LGM and DC traces to a Desired Outcome or a Damage Control item of the brief | An LGM or DC introduced with no brief anchor and no divergence tension logged |

**On QG pass:** set `status: review` and save.

> PRD saved with status: review.

**Status lifecycle:**

| Transition | Trigger | Actor |
|------------|---------|-------|
| *(file created)* → `in-progress` | Step 1 — the PRD file is written | This skill (automatic) |
| `in-progress → review` | 12 QG checks passed | This skill (automatic) |
| `review → accepted` | Section 9 empty + human sign-off | Human |
