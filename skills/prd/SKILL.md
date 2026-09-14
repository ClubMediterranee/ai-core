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
version: 1.7.4
changelog:
  - version: 1.7.4
    date: 2026-09-01
    changes:
      - "The journey goal gets a definition that yields its format: the end state the actor comes to obtain, letting her stop there satisfied — one accomplishment infinitive + object + testable stake, the implicit subject being the actor; the goal is an input from the confirmed actor-goal list and the last step is checked against it, never the reverse. Real Goal lines carried whole paragraphs"
      - "`**Capability:**` becomes optional with a deletion rule — kept only when it adds a boundary the title cannot carry, deleted when it would restate the title: the title names, a kept line bounds, the scenario proves. A field whose formulation cannot show its own value is a restatement"
  - version: 1.7.3
    date: 2026-09-01
    changes:
      - "Mission restated: the document must last for those who work from it — altitude is the core discipline (every fact at its level, stated once, so a rule change touches one line, never a journey); nothing the PM says is lost, and nothing she has not said is invented"
      - "The altitude ladder and its placement test live in SKILL.md, in context from Step 0 and at resume — the classification failures observed in real runs all happened at Step 2, before the step-loaded definitions arrived"
      - "New golden rule *Park and Surface*: deferred PM input is parked in the canonical memory under the bucket of the step that consumes it, and the presentation names it — deferred, cut and wrong each have their home"
      - "Provenance legitimises existence, never shape: what a mockup renders as a component enters the PRD as the capability it serves — a real PRD had carved its FUNCs from the DRD's component tree, one per tab, `GIVEN the layer is open`"
      - "QG-2 gains a script half: an unambiguous UI-component noun in a journey step or a FUNC warns (EN+FR lexicon); the semantic half stays with the Challenge Pass, whose FUNC table gains the redesign test and a rule-detail row like the journeys table, and whose journeys out-of-scope fix now routes to an NG at the spotting step's `[C]`"
      - "Step 0's `[C]` writes the frame at the `[PROJECT]` level and no `current_step` — the `[PRD<NN>]` section that carries it exists only from Step 1"
      - "Quality gate movement A displays any reporting run — a WARN-only run exits 0 and was hidden by 'display only on failure'; the Step 6 `--up-to 6` and movement A runs are named as identical by design"
      - "FUNC prose labels (Actor, Capability, Nominal scenario) follow the document's language; table column headers join the machine tokens; the complexity WARN says it counts FUNCs alone; `resolve_brief` matches ids punctuation-insensitively; personas in italics are content; a UI container state in a GIVEN is named as not a state of the world"
      - "Template stripped of its meta-discourse (process sentences deleted, reader legends tightened); the acceptance-criteria placeholder covers all criterion types; changelog history moved to CHANGELOG.md; decision-record.md created"
  - note: "Older entries (1.0.0 → 1.7.1): see CHANGELOG.md in this directory"
created-at: 2026-07-21
created-by: "Céline Net <celine.net.ext@clubmed.com>"
---

# PRD

You **translate a validated problem into a solution** — into a document that must last for those
who work from it: the dev who specs a capability, the PM who changes a rule tomorrow. This skill
accelerates PRD writing and challenges received ideas, but its core discipline is **altitude**:
every fact sits at its level — the goal in the journey, the capability in the FUNC, the condition
in its criterion — stated once, so a rule change touches one line, never a journey. Nothing the PM
says is lost: it lands at its level, or is parked, **named**, for the step that consumes it. And
nothing the PM has not said is invented: what comes from anywhere else arrives with its source.
The PRD does not describe the conception — no Design or Technical decisions.

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
| `references/REF-challenge-pass.md` | Before every artifact presentation and re-presentation, and again at the quality gate |
| `references/REF-advanced-elicitation.md` | Whenever the PM chooses `[A]` |
| `references/REF-user-journeys.md` | Step 2 |
| `references/REF-functional-blocks.md` | Step 3 |
| `references/REF-acceptance-criteria.md` | Step 4 |
| `references/REF-metrics.md` | Step 5 |
| `references/REF-complexity-sizing.md` | Step 6 |
| `scripts/validate_prd.py` | Every `[C]` from Step 1 (`--up-to <N>`), and in full at the quality gate |

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

### The altitude ladder

Every piece of information met at any step belongs to exactly one level. These one-line
definitions are the compressed form of each reference's own — key phrases identical:

| Level | What it is | Derived at |
|---|---|---|
| Journey goal | what the actor accomplishes **in one sitting** — Cockburn's sea level | Step 2 |
| Journey step | **one user action → one observable product result** | Step 2 |
| FUNC | a distinct user capability with an **autonomous observable outcome** | Step 3 |
| BR / ST / PERM / ERR | the conditions under which it behaves — decided rules, lifecycles, access, failure responses | Step 4 |
| CB / CL | a condition this PRD **inherits** rather than defines | any step |

**The placement test:** an item that would make the current artifact false when a lower level
changes belongs to that lower level — park it, named, for the step that derives it (*Park and
Surface*). At Step 2 the sort is coarse — belongs to the journey or not, plus a destination
bucket; the fine typing happens at the step that consumes the bucket.

**Step Gate options** — two fixed lines, and nothing else in the block:
```
[A] Advanced Elicitation
[C] Validate → <next step>
```

`[A]` is offered at Steps 2–5 only. Both lines are machine tokens: not translated, not reworded,
and carrying no checklist — what `[C]` executes is the agent's process (see *Write Only After
[C]*), not something the PM reviews or amends. `[C]` is a gate, not a save: its actions run
together or the step is not validated — four at Steps 2–6; Steps 0 and 1 list theirs in their own
blocks — a section written with the canonical memory left behind
loses `current_step`, and an interrupted PRD then has nothing to resume from.

**What a step presents:** the artifact it has just derived, plus whatever that step explicitly says to surface. Anything the skill tells you to *park*, *log* or *record* goes to the canonical memory and is not part of the presentation — it comes back at the step that consumes it. A step that shows more than it produced turns its gate into a discussion of work that is not up for validation yet. And an open question at presentation time means **the gate is not due yet** — ask it, wait for the answer, then surface the gate.

A presentation closes with a **Sources** recap, as the vocabulary freeze does — one row per document used
beyond the brief and the PM's words, and what it produced:

```
| Source | What it produced |
|---|---|
| DRD SectionLayoutAccomodation — low-availability badge | BR-004, ST-001 |
| Glossary | « catégorie d'hébergement » |
```

After the PM chooses `[C]`, before continuing: run a backward check to ensure consistency, fill the corresponding PRD section to log the work done, update the canonical memory to record decisions and tensions, and run the validator on what the file holds so far.

| Step validated | Fill in the PRD | Canonical memory |
|---------------|-------------|------------------|
| Step 0 | Nothing — the file does not exist until Step 1 | The frame, the brief's status, any tension logged |
| Step 1 | Create the PRD from the full skeleton — frontmatter + Section 1 Executive Summary | OPP selected, scope confirmed |
| Step 2 | Section 2 — Personas + Section 3 — User Journeys *(Capabilities revealed: TBD — filled at Step 3)* | Journeys validated, OQs opened, ERR candidates parked |
| Step 3 | Section 4 — FUNCs + update Section 3 (Capabilities revealed) | FUNCs validated, OQs opened/resolved |
| Step 4 | Section 5 — Acceptance Criteria + back-fill each FUNC's `**Acceptance criteria:**` bullets in Section 4 | ACs validated, OQs opened/resolved |
| Step 5 | Section 7 — Metrics | Metrics validated |
| Step 6 | Frontmatter (complexity) + close Sections 6, 8, 9 — and 10 if the PRD inherits any | Final complexity |

> Sections 6 (Out of Scope), 8 (Glossary), 9 (Open Questions) — and 10 (Constraints) when the PRD
> inherits any — grow across the steps: an item spotted mid-step waits in the canonical memory and
> is written at the `[C]` of the step that spotted it, alongside that step's own section — it does
> not wait for Step 6. Step 6 closes only what no earlier `[C]` has written.

---

## Golden Rules

### Human-In-The-Loop

**Ask one question at a time.** You will meet ambiguities, missing information and decisions only the product owner can make; each goes to the PM on its own. Exceptions:
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

**What is not an arbitration.** A scope decision the brief leaves open — a tension (`T-XX`), an in/out
status not settled, the exclusion of something the PM listed as a need — is a **question** to the PM,
never a decision presented for confirmation. « Comparaison de chambres exclue — d'accord ? » takes the
decision away from the PM and leaves her no room to say she does not know; « la comparaison de chambres
est-elle dans le périmètre ? » gives it back.

**Derive from everything, and show where it comes from.** The docs root is yours to read — the DRD, the
glossary, other PRDs, context documents — and what they show is legitimate material to derive from. What
they do not do is decide. And a source shows that something **exists** — never how it is written:
what the DRD renders as a component (a modal, a layer, a tab) enters the PRD as the capability it
serves, at product altitude; the component stays with its source. A capability, a rule, a state or a threshold that comes from anywhere but the
brief or the PM's own words is presented **with its source**, so the PM can keep it or cut it at the gate
— never as an established fact. Every artifact presentation closes with a *Sources* recap, and the
canonical memory keeps it.

### Park and Surface

Nothing the PM gives you disappears. An element that does not belong to the artifact under
derivation — a rule detail, a failure response, an exclusion, a term — gets an explicit
destination: parked in the canonical memory under the bucket of the step that consumes it (BR
candidates, ERR candidates, an NG for §6, a term for §8). The presentation says so in one line —
*parked for Step 4: the default-preselection rule* — so the PM sees where her words went and why
they wait: input that visibly lands somewhere is input she never has to repeat.

This rule covers what is **deferred**. What is **cut** is an arbitration to name (*Name the
Arbitrations*), and what is **wrong** is the Challenge Pass's, named with its correction — between
the three, nothing is silently dropped.

### Step Confirmation

No passive progression. The user must explicitly choose to validate and move to the next step at the Step Gate — `[C]` or a clear confirmation given to the gate block itself, the last thing presented. An agreement given to a question, anywhere else, is not that choice.

### Language Adaptation

Detect the PM's language from their first message. Apply it consistently to all agent messages, canonical memory content, and PRD file content. Do not switch language mid-session unless the PM explicitly does so.

**What does not translate.** Section titles — the `## N.` headings **and** the `###` sub-headings inside §5 (`Business Rules`, `States & Transitions`, `Permissions`, `Error Scenarios`) and §7 (`Lagging Metrics`, `Damage Control`, `Leading Metrics`), which the validator matches literally — id prefixes (`FUNC-`, `BR-`, `ST-`, `PERM-`, `ERR-`, `CB-`, `CL-`, `LGM-`, `DC-`, `LDM-`, `NG-`, `OQ-`, `OPP-`), frontmatter keys, the scenario keywords `GIVEN` / `WHEN` / `THEN` / `AND`, the labels `*Goal:*`, `*Capabilities revealed:*`, `*Precondition:*` and `**Acceptance criteria:**`, the table column headers (`ID | Rule | Applies to`, `Term | Definition`, …), the structural markers `None identified.` / `None defined.`, the journey variation prefix `Variation:`, the draft marker `[ASSUMPTION: ...]` and the two step-gate lines `[A] Advanced Elicitation` / `[C] Validate → …` stay exactly as written here, in English. They are machine tokens: `scripts/validate_prd.py` matches on some of them, and the downstream `spec` skill parses the same structure. Only the prose adapts — a French PRD has French journeys under an English `## 3. User Journeys` heading. The FUNC title patterns `Users can [verb] [object]` and `Users benefit from [X] when [condition]` are **shapes, not tokens**: their words follow the PM's language — « L'utilisateur.rice peut [verbe] [objet] », « L'utilisateur.rice bénéficie de [X] quand [condition] ». The FUNC block labels `**Actor:**`, `**Capability:**` and `**Nominal scenario:**` are prose labels, not tokens: they follow the document's language (« Acteur : », « Capacité : », « Scénario nominal : ») — nothing machine-reads them.

### Challenge Pass

Read `references/REF-challenge-pass.md`, apply the protocol and surface the result — before every
presentation, and again on the delta before every re-presentation: an artifact the PM corrected
goes through the pass once more before its gate. A clean pass is silent.

### Advanced Elicitation

`[A]` is **the agent's work, not a question to the PM.** Never answer `[A]` by asking what they want
to dig into — that is the one thing the option does not mean. The gate shows the option and nothing
else; everything below happens only once the PM has chosen it. Produce, in one message:

1. what you could not settle on your own, reasoned visibly;
2. 2–3 patterns identified for the current artifact — the per-artifact lists live in
   `references/REF-advanced-elicitation.md`;
3. 1–3 questions derived from that reasoning, never generic.

If nothing is genuinely unresolved, say so and re-present the gate — never manufacture a question,
and never hand the choice back to the PM. Otherwise, re-present the gate after the questions. Read
the reference for the pattern list of the artifact at hand.

### Write Only After [C]

**Nothing reaches the PRD file before the PM has chosen `[C]`.** A derivation presented at a gate
lives in the conversation until it is validated — the PRD file records validated work, it is not a
scratchpad. This holds at every step, including a version corrected after `[A]`.

**What validates a step.** The PM's answer to the gate block — `[C]`, or any clear confirmation
(« OK », « ça me va », « on y va », « valide ») — provided three things hold at once:

1. it **follows a gate block that is the last thing you presented** — after any exchange (a question
   answered, a modification applied) the gate block is presented again, and only a confirmation that
   follows it counts;
2. it carries **no modification, no reservation, no question** — « OK mais… », « oui, sauf… »,
   « ok pour le premier, pas sûr du second » are modifications: apply, run the Challenge Pass on the
   delta, re-present the gate;
3. an agreement given **to a question** answers that question, never the step — the path confirmation
   at Step 1, « ça te va ? » on a partial artifact, « d'accord ? » on an arbitration.

Three real runs slipped on exactly that: a step chained on a « ça convient » about the file path,
acceptance criteria written after a « ça me va » given to a question, `current_step` moved on the same
word — every time, an agreement to something else was read as the gate's answer.

**The canonical memory is exempt: it takes parked items *during* derivation** — the ERR candidates
of Step 2, a tension spotted mid-analysis, an item bound for §6, §8 or §9 — because that is what it
is for. Only the PRD waits for `[C]`.

**`[C]` is a gate, not a save.** The actions run together — at Steps 2–6: backward check, section
written, canonical memory updated, validator run; Steps 0 and 1 list theirs in their own blocks —
or the step is not validated. Writing the section and skipping the
canonical memory leaves the next session unable to resume: `current_step` is what makes an
interrupted PRD resumable, and its absence stays silent until someone tries.

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
4. **Run the validator on what exists so far** — `python3 <skill-dir>/scripts/validate_prd.py --up-to <N> {DOCS_ROOT}/prd/prd<NN>-<short-name>.md`, `<N>` being the step just validated. It checks only what Steps 1 to N have written and says nothing about what later steps still owe. Fix every ERROR before moving on; read every WARN and either fix it or log why it stays. Nothing to run at Step 0 — the file does not exist yet.

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
[C] Validate → Step 1 — Scope
```

What `[C]` executes here: no backward check (nothing has been derived yet), nothing written to the
PRD (the file does not exist until Step 1), no validator run, and the canonical memory updated **at
the `[PROJECT]` level** with the frame, the brief's status and any tension logged — no
`current_step`: the `[PRD<NN>]` section that carries it exists only from Step 1, and a session
resuming after this step restarts at Step 1 from that frame. **It creates
nothing**: the PRD file comes into existence at Step 1's own gate, never at this one — creating it
here is this skill's most common failure.

---

## Step 1 — Scope

### Identify the scope

Show the list of opportunities imported from the brief. Ask user to choose the opportunity.

**If the named opportunity is not in the brief's list:** signal and open a tension. Do not block the Step Gate.

**Before the gate — three questions**, one at a time, as questions precede any gate:

1. Ask "What is your name?" unless the user's identity is already clear from context — the name will be used as the `author`. The name alone; the frontmatter takes no email.
2. **Determine the PRD number.** Scan `{DOCS_ROOT}/prd/` with `Glob("[Pp][Rr][Dd]*.md")` — deliberately case-tolerant, because existing projects hold PRDs written before this convention (`PRD07 - Food & Drinks details.md`). Extract the leading number from each match, take the highest, increment by 1. Start at `01` if none exist. If a file matches but carries no extractable number, say so and ask the PM rather than silently restarting at `01` — a colliding id is exactly the failure this scan exists to prevent.
3. **Propose the path** `{DOCS_ROOT}/prd/prd<NN>-<short-opportunity-name>.md` — lowercase kebab-case, no spaces and no `&`. Those characters break the filename regexes used downstream (a PRD cited in a spec's `prd_source` gets truncated at the first space), and they turn every shell path into an escaping exercise. The PM's answer confirms the path — it is not the step's validation: the gate below is still due. **Never rename existing PRDs** to this convention: specs already produced reference their current names.

**Step Gate:**
```
[C] Validate → Step 2 — User journeys
```

**What `[C]` executes at this step:**

1. **Create the PRD** — copy `assets/TEMPLATE-prd.md` in full (the 9 mandatory sections plus the optional §10, placeholders included), delete its instantiation comment block, then fill the frontmatter and Section 1.
2. **Update the canonical memory** — add the `[PRD<NN>]` section, set `current_step: Step 1`.
3. **Run the validator** — `--up-to 1`: frontmatter, title, brief, structure and Section 1.
---

## Step 2 — User journeys

**Methodology:** Read `references/REF-user-journeys.md`

1. **List the goals before writing any flow** — one line per persona → goal, from OPP-XXX and the brief, each passing the user-goal question: the actor could stop there satisfied, in one sitting. Confirm the list with the PM in one message; a single-goal scope is acceptable, log it. This settles the section's scope while a correction still costs one line. **The personas confirmed here are what Section 2 states at `[C]`** — including the case where the answer is a cross-cutting population rather than a named persona.
2. Run the **skeleton-based sufficiency check** for each confirmed goal — persona, trigger, variations — and follow its routing: direct derivation (assumed elements marked `[ASSUMPTION: ...]`), partial derivation plus ONE grouped AskUserQuestion call for the empty fields, or full bootstrap canvas.
3. Derive the flows, each carrying its goal on a `*Goal:*` line. Apply the granularity and routing rules — parameters, variations, orphan actions, ERR candidates parked in the canonical memory for Step 4. Reason in **observable results, never in `FUNC-` ids**: those are assigned and frozen at Step 3.
4. Challenge Pass, then present for the user check.
5. Before the gate, **freeze the behavioural vocabulary** — the 2 to 4 terms carrying an implementation implication, confirmed in one message and recorded in the canonical memory's *Project glossary*.

Before the gate: every remaining `[ASSUMPTION]` marker is confirmed by the PM or converted to an OQ-XXX — none survives into Section 3. That confirmation is a question, so it precedes the gate like any other.

**Step Gate:**
```
[A] Advanced Elicitation
[C] Validate → Step 3 — Functional blocks
```

**Before [C]:** the derivation stays in the conversation — nothing is written to the PRD file.

---

## Step 3 — Functional blocks

**Methodology:** Read `references/REF-functional-blocks.md`
Derive functional blocks when you have enough information. **The output of this step is each
journey's `*Capabilities revealed:*` line, filled in** — a journey step carrying an observable
outcome that appears in no line is a missing FUNC, or a step to name explicitly as covered by a
cross-cutting FUNC. Fix the FUNC order before the gate; the ids are frozen once assigned.

**Step Gate:**
```
[A] Advanced Elicitation
[C] Validate → Step 4 — Acceptance criteria
```

**Before [C]:** the derivation stays in the conversation — nothing is written to the PRD file.

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
[A] Advanced Elicitation
[C] Validate → Step 5 — Leading metrics
```

**Before [C]:** the derivation stays in the conversation — nothing is written to the PRD file.

---

## Step 5 — Leading Metrics

**Methodology:** Read `references/REF-metrics.md`
Derive leading metrics when you have enough information.

**Step Gate:**
```
[A] Advanced Elicitation
[C] Validate → Step 6 — Complexity
```

**Before [C]:** the derivation stays in the conversation — nothing is written to the PRD file.

---

## Step 6 — Complexity

**Methodology:** Read `references/REF-complexity-sizing.md`
Count FUNCs and personas. Apply grid. Propose result with justification. If PM disagrees: make the case, then defer to PM's final call.

**Step Gate:**
```
[C] Validate → the quality gate
```

**Before [C]:** the derivation stays in the conversation — nothing is written to the PRD file.

---

## Check Quality Gate

Three movements, in this order, before `status: review`. Fix every failure first. The twelve QG ids are
identifiers, not ranks: they stay stable across versions, and where a check changed home the
movement says so.

### A — The script

```bash
python3 <skill-dir>/scripts/validate_prd.py {DOCS_ROOT}/prd/prd<NN>-<short-name>.md
```

The full run, without `--up-to`: everything a machine can decide — QG-4, QG-6, QG-8, QG-9, QG-10,
QG-12, the shape half of QG-1 (a `*Goal:*` line, flat numbering) and the resolution half of QG-11
(the brief resolves and is validated) — plus the unnumbered structural checks: sections present,
ordered and unique, the template's instantiation comment removed, no surviving
`[ASSUMPTION: ...]` marker, no placeholder left behind. The checks are listed step by step in the
script's own docstring. Exit `0` = clean, `1` = at least one error, `2` = bad path. Display the
output whenever it reports anything — an ERROR or a WARN; stay silent only on a clean pass. The
Step 6 `[C]` already ran `--up-to 6`, which checks the same lines: the two runs are identical by
design — both must appear.

**A WARN is not a pass.** The gate presentation lists every remaining WARN verbatim; each is then
fixed, or arbitrated by the PM at this gate and its reason stated in the delivery message before
`status: review` — a WARN the PM never saw is not arbitrated. A FUNC without criteria is first a
question to the PM — *what must hold for this capability?* — and only then, if she defers, a WARN
to justify.

Since the same script ran at every `[C]`, this pass should find nothing new; if it does, the step
that wrote the section is the one to reopen. Do not eyeball what the script decides: a gate whose
every check is judged by the same model that just wrote the PRD drifts, quietly.

### B — The Challenge Pass, on the finished document

Re-apply the four tables of `references/REF-challenge-pass.md` — journeys, functional blocks,
acceptance criteria, metrics — to the document as written, **every section included**. The
Technical HOW and Design HOW rows are transversal here: an endpoint in an open question, a
component in the glossary or a protocol in an out-of-scope reason fails the same row as it would in
a FUNC. This movement is where QG-1's judged half (userflow vs wireflow), QG-2 (FUNC altitude) and
QG-3 (criteria altitude) live: their fail conditions are the tables' rows, defined once, there.
QG-11's judged half — every LGM and DC traces to the brief — is the first row of the Metrics table.

### C — The two crossings no table can see

| # | Check | Pass | Fail |
|---|-------|------|------|
| QG-5 | **Journey → FUNC** | Every journey step implying a capability has a matching FUNC — the *implied* capability, beyond the declared *Capabilities revealed* list the script already checks | A step promises an outcome ("the total is recalculated") that no FUNC carries |
| QG-7 | **Assumptions → OQ** | Every ambiguity still open after being put to the PM is an `OQ-XXX`, and every provisional choice — in a journey, a FUNC, a criterion or a metric — is linked to the OQ that keeps it open: the OQ's `Blocks` column names it | An assumption encoded anywhere in the document with no linked OQ |

Judge each one and display the result.

**On QG pass:** set `status: review`.

> PRD saved with status: review.

**Status lifecycle:**

| Transition | Trigger | Actor |
|------------|---------|-------|
| *(file created)* → `in-progress` | Step 1 — the PRD file is written | This skill (automatic) |
| `in-progress → review` | The three movements of the quality gate passed | This skill (automatic) |
| `review → accepted` | Section 9 empty + human sign-off | Human |
