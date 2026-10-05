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
version: 1.8.0
changelog:
  - version: 1.8.0
    date: 2026-10-05
    changes:
      - "Canonical memory removed: `## Parked` in the PRD (written as items are parked, consumed at its step's [C])"
      - "A decision record per project, `record/<brief-stem>.md`, created at Step 1's [C]; §8 mirrored in Vocabulary"
      - "The PRD holds the fact, the record the why; an answered OQ leaves §9 with a `Resolves` decision"
      - "[C] is four actions; the validator fails a section written before its gate and ends with the next step's card"
      - "The brief is not a wall (`brief: none`); resume is the PM's choice, no pointer; `[C] Step N validated` echo"
      - "§10 in every PRD with the legal baseline as its legend; UI lexicon in a file; 69-finding review applied"
  - version: 1.7.4
    date: 2026-09-01
    changes:
      - "Journey goal defined by its format: accomplishment infinitive + object + testable stake; an input, never reworded to fit the flow"
      - "`**Capability:**` optional, with a deletion rule: kept only when it bounds what the title cannot"
  - note: "Older entries (1.0.0 → 1.7.3): see CHANGELOG.md in this directory"
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

## How the skill works

PRD runs in **sequential steps**. Each step ends with a **Step Gate**. Wait for the user validation to move to the next step

| Step | Objective | Gates |
|------|-----------|---------|
| **Step 1 — Frame & scope** | Resolve the docs root, frame the brief, select the single opportunity this PRD addresses | [C] |
| **Step 2 — User journeys** | Derive end-to-end flows anchored on the selected opportunity | [A] [C] |
| **Step 3 — Functional blocks** | Derive FUNCs from validated journeys | [A] [C] |
| **Step 4 — Acceptance criteria** | Derive BR, ST, PERM, ERR from journeys and user input | [A] [C] |
| **Step 5 — Leading metrics** | Identify observable user behaviors that predict adoption | [A] [C] |
| **Step 6 — Complexity** | Size the PRD before the quality gate | [C] |

### The altitude ladder

Every piece of information met at any step belongs to exactly one level. These one-line
definitions are the compressed form of each reference's own — key phrases identical:

| Level | What it is | Derived at |
|---|---|---|
| Journey goal | the end state the actor comes to obtain, **in one sitting** — she can stop there satisfied; Cockburn's sea level | Step 2 |
| Journey step | **one user action → one observable product result** | Step 2 |
| FUNC | a distinct user capability with an **autonomous observable outcome** | Step 3 |
| BR / ST / PERM / ERR | the conditions under which it behaves — decided rules, lifecycles, access, failure responses | Step 4 |
| CB / CL | a condition this PRD **inherits** rather than defines | any step |

**The placement test:** an item that would make the current artifact false when a lower level
changes belongs to that lower level — park it, named, for the step that derives it (*Park and
Surface*). At Step 2 the sort is coarse — belongs to the journey or not, plus the step it is
parked for (`For`); the fine typing happens at that step's `[C]`.

**Step Gate options** — two fixed lines, and nothing else in the block:
```
[A] Advanced Elicitation
[C] Validate → <next step>
```

`[A]` is offered at Steps 2–5 only. Both lines are machine tokens: not translated, not reworded,
and carrying no checklist — what `[C]` executes is the agent's process (see *Write Only After
[C]*), not something the PM reviews or amends. `[C]` is a gate, not a save: its actions run
together or the step is not validated — the four actions of *Write Only After [C]* at Steps 2–6,
Step 1's own list at its gate. A section written with the record left behind loses what the step
surfaced, and the step that was to consume it cannot bring it back.

**What a step presents:** the artifact it has just derived, plus whatever that step explicitly says to surface. What it *parks* or *records* is named in one line and comes back at the step that consumes it. A step that shows more than it produced turns its gate into a discussion of work that is not up for validation yet. And an open question at presentation time means **the gate is not due yet** — ask it, wait for the answer, then surface the gate.

A presentation closes with a **gate recap** — the list of what `[C]` writes, and what survives a
compaction before the gate: the Sources used beyond the brief and the PM's words (one row each,
with what it produced), the items parked and the rows consumed, the decisions and tensions to
record, by title.

```
| Source | What it produced |
|---|---|
| DRD — product page, low-stock badge | BR-004, ST-001 |
Parked for Step 4: the default-preselection rule · To record: T — brief KR altered
```

After the PM chooses `[C]`, before continuing, the four actions of *Write Only After [C]*: backward check, write the step's section and whatever it surfaced, append the step's rows to the decision record, run the validator on what the file holds so far.

| Step validated | Fill in the PRD | Decision record |
|---------------|-------------|------------------|
| Step 1 | Create the PRD from the full skeleton — frontmatter + Section 1 Executive Summary; `## Parked` rows parked since the start | Created if absent; OPP selected, scope confirmed, the frame's decisions (D); the brief's status, an OPP outside the brief (T) |
| Step 2 | Section 2 — Personas + Section 3 — User Journeys *(Capabilities revealed: TBD — filled at Step 3)*; §8 terms; `## Parked` rows consumed | Frozen terms (V), tensions (T), decisions (D) |
| Step 3 | Section 4 — FUNCs + update Section 3 (Capabilities revealed) | Decisions (D), sources (S) |
| Step 4 | Section 5 — Acceptance Criteria + back-fill each FUNC's `**Acceptance criteria:**` bullets in Section 4; the `For: Step 4` rows of `## Parked` removed | Decisions (D), sources (S) |
| Step 5 | Section 7 — Metrics | Divergence tensions (T) |
| Step 6 | Frontmatter (complexity) + close Sections 6, 8, 9, 10 and empty `## Parked` | Complexity override (D) |

> Sections 6 (Out of Scope), 8 (Glossary), 9 (Open Questions) and 10 (Constraints) grow across
> the steps: an item spotted mid-step lives in the conversation, named
> in the presentation, and is written at the `[C]` of the step that spotted it, alongside that
> step's own section — it does not wait for Step 6. Step 6 closes only what no earlier `[C]` has
> written.

---

## Golden Rules

### Human-In-The-Loop

You will meet ambiguities, missing information and decisions only the product owner can make.
**Questions go through `AskUserQuestion`, never as a list in prose.** Independent questions share
one call (up to 4) — the frame's fields when there is no brief, the journey bootstrap canvas of
Step 2 (`references/REF-user-journeys.md`), a name and a path. A decision that shapes the scope or
the journeys is asked alone, because the next question depends on its answer. If the tool is
unavailable, one question per message. Wait for the answer before surfacing the step gate.

### Name the Arbitrations

Every artifact is presented with the boundary decisions that produced it: *here are the N calls I had
to make — confirm or correct*, never *did I miss anything?*. The second form moves the work onto the
PM and buys a silent validation.

A decision only the PM can make is **asked before the gate** — not absorbed into the artifact, and
not filed as an `OQ-XXX`. An `OQ-XXX` records what stays open **after** asking, or what the PM
explicitly defers.

**What is not an arbitration.** A scope decision the brief leaves open — a tension the brief carries
(the brief's `T-XX`), an in/out status not settled, the exclusion of something the PM listed as a need — is a
**question** to the PM, never a decision presented for confirmation. « Comparaison de produits exclue — d'accord ? » (*product
comparison excluded — agreed?*) takes the decision away from the PM and leaves her no room to say she
does not know; « la comparaison de produits est-elle dans le périmètre ? » (*is it in scope?*) gives it
back.

**Derive from everything, and show where it comes from.** The docs root is yours to read — the DRD
(the design source: mockups, a Figma file, the organisation's design requirement document), the
glossary, other PRDs, context documents — and what they show is legitimate material to derive from. What
they do not do is decide. And a source shows that something **exists** — never how it is written:
what the DRD renders as a component (a modal, a layer, a tab) enters the PRD as the capability it
serves, at product altitude; the component stays with its source. A capability, a rule, a state or a threshold that comes from anywhere but the
brief or the PM's own words is presented **with its source**, so the PM can keep it or cut it at the gate
— never as an established fact. Every artifact presentation closes with a *Sources* recap, and the
decision record's Sources table keeps it with the PM's verdict, `kept` or `cut`.

### Park and Surface

Nothing the PM gives you disappears. An element that does not belong to the artifact under
derivation — a rule detail, a failure response, an exclusion, a term — has one of three homes, and
the presentation names it in one line (*parked for Step 4: the default-preselection rule*), so
the PM sees where her words went: input that visibly lands somewhere is input she never has to
repeat.

| It is | Home |
|---|---|
| **Deferred** — belongs to a later step | A row of the PRD's `## Parked` table (`\| Item \| Kind \| For \| Origin \|`, `For: Step N`), **written the moment it is parked**. Step N's `[C]` gives it its home and removes the row — or re-targets it to a later step, named at the gate; what finds no home becomes an NG in §6 or an OQ in §9 — nothing waits for "later" |
| **Cut** | An arbitration to name (*Name the Arbitrations*); an exclusion is an NG in §6, an inherited constraint a CB/CL in §10, at this `[C]` |
| **Wrong** | The Challenge Pass's, named with its correction |

Between the three, nothing is silently dropped. One boundary for what goes where: **the PRD holds
the fact** — rule, exclusion, constraint, open question — **the decision record holds the why no
section can carry**: arbitration, tension, source kept or cut. An OQ is a product ambiguity still
open after asking (§9); a tension is a divergence between this PRD and its brief, its sources or
another PRD (the record).

### Step Confirmation

No passive progression. The user must explicitly choose to validate and move to the next step at the Step Gate — `[C]` or a clear confirmation given to the gate block itself, the last thing presented. An agreement given to a question, anywhere else, is not that choice.

**Say when you read one.** The first line of your message after a validation is the fixed token `[C] Step N validated` — then the gate's actions. It names how you read the PM's answer, so a « ok » meant for a question is corrected on the spot, not a step later; and it is countable in a transcript.

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
and never hand the choice back to the PM. Otherwise, in this order — never collapsed into one
message:

1. the questions, with nothing below them;
2. once the PM has answered, the artifact updated with the answers — a change applied, an
   assumption lifted, an arbitration settled — and the Challenge Pass on the delta;
3. that artifact re-presented with its arbitrations and the gate recap, closed by the gate block.

Read the reference for the pattern list of the artifact at hand.

### Write Only After [C]

**Nothing reaches the PRD file before the PM has chosen `[C]`.** A derivation presented at a gate
lives in the conversation until it is validated — the PRD file records validated work, it is not a
scratchpad. This holds at every step, including a version corrected after `[A]`.

**What validates a step.** The PM's answer to the gate block — `[C]`, or any clear confirmation
in the PM's language (FR: « OK », « ça me va », « on y va », « valide ») — provided three things hold at once:

1. it **follows a gate block that is the last thing you presented** — after any exchange (a question
   answered, a modification applied) the gate block is presented again, and only a confirmation that
   follows it counts;
2. it carries **no modification, no reservation, no question** — « OK mais… », « oui, sauf… »,
   « ok pour le premier, pas sûr du second » are modifications: apply, run the Challenge Pass on the
   delta, re-present the gate;
3. an agreement given **to a question** answers that question, never the step — the path confirmation
   at Step 1, « ça te va ? » on a partial artifact, « d'accord ? » on an arbitration.

Three real runs slipped on exactly that: a step chained on a « ça convient » about the file path,
acceptance criteria written after a « ça me va » given to a question, the record appended on the same
word — every time, an agreement to something else was read as the gate's answer.

**`## Parked` is exempt: a row is written the moment an item is parked** — it is scratch, nothing in
it is validated, and it is the one thing that must be on disk before any compaction. The numbered sections and the decision record wait for `[C]`; the validator
fails a section written before its gate.

**`[C]` is a gate, not a save.** The four actions below run together, or the step is not
validated; Step 1 lists its own at its gate. A section written with the rest left behind loses
what the step surfaced, silently.

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
2. **Write the PRD** — the step's section (mapping in *How the skill works*), the §6/§8/§9/§10 items it spotted, and the `## Parked` rows it consumes removed. **An OQ the PM answered**: integrate the answer where it blocked, remove its §9 row (the id is never reused), and record the decision below with `Resolves: OQ-XXX`.
3. **Append to `{DOCS_ROOT}/record/<brief-stem>.md`** — one row per entry, at the end of its table, never a rewrite: decisions (`D-<NN>-XX`; `Step` is the step's number, `Resolves` the OQ it answers, `Affects` the FUNC, section or other PRD it touches), tensions (`T-<NN>-XX`, `open` / `accepted` / `resolved`), terms frozen (Vocabulary), sources used (`kept` / `cut`).
4. **Run the validator on what exists so far** — `python3 ${CLAUDE_SKILL_DIR}/scripts/validate_prd.py --up-to <N> {DOCS_ROOT}/prd/prd<NN>-<short-name>.md`, `<N>` being the step just validated. It checks only what Steps 1 to N have written, fails a section a later step owns that already holds content, and a parked row whose step has passed; it ends with the next step's card — its reference, its gate block, the parked rows it consumes. Fix every ERROR before moving on; read every WARN and either fix it or record why it stays as a decision — a WARN already covered by a record row is cited, not re-recorded.

### Language Adaptation

Detect the PM's language from their first message. Apply it consistently to all agent messages, the PRD and the decision record. Do not switch language mid-session unless the PM explicitly does so.

**What does not translate.** Section titles — the `## N.` headings **and** the `###` sub-headings inside §5 (`Business Rules`, `States & Transitions`, `Permissions`, `Error Scenarios`) and §7 (`Lagging Metrics`, `Damage Control`, `Leading Metrics`), which the validator matches literally — id prefixes (`FUNC-`, `BR-`, `ST-`, `PERM-`, `ERR-`, `CB-`, `CL-`, `LGM-`, `DC-`, `LDM-`, `NG-`, `OQ-`, `OPP-`), frontmatter keys, the scenario keywords `GIVEN` / `WHEN` / `THEN` / `AND`, the labels `*Goal:*`, `*Capabilities revealed:*` and `**Acceptance criteria:**`, the table column headers (`ID | Rule | Applies to`, `Term | Definition`, …), the structural markers `None identified.` / `None defined.`, the draft marker `[ASSUMPTION: ...]`, the `## Parked` heading with its columns and its `Step N` values, the decision record's four `##` headings, their columns, the prefixes `D-` / `T-` and the values `open` / `accepted` / `resolved`, `kept` / `cut`, the two step-gate lines `[A] Advanced Elicitation` / `[C] Validate → …` and the echo `[C] Step N validated` stay exactly as written here, in English. They are machine tokens: `scripts/validate_prd.py` matches on some of them, and the downstream `spec` skill parses the same structure. Only the prose adapts — a French PRD has French journeys under an English `## 3. User Journeys` heading. The FUNC title patterns `Users can [verb] [object]` and `Users benefit from [X] when [condition]` are **shapes, not tokens**: their words follow the PM's language — « L'utilisateur.rice peut [verbe] [objet] », « L'utilisateur.rice bénéficie de [X] quand [condition] ». The FUNC block labels `**Actor:**`, `**Capability:**` and `**Nominal scenario:**`, and the journey labels `*Precondition:*` and `Variation:`, are prose labels, not tokens: they follow the document's language (« Acteur : », « Capacité : », « Scénario nominal : », « Précondition : », « Variante : ») — nothing machine-reads them.

---

## Bundled resources

Paths are relative to this skill's directory, `${CLAUDE_SKILL_DIR}` — expanded to an absolute path
when the skill loads, wherever it is installed. If a command below still shows the variable
unexpanded, use the base directory given when the skill was loaded; if you have none, or if
`python3 --version` fails or reports less than 3.8, tell the PM the script half of the quality gate
is unavailable and say so in the delivery message — never skip it silently.

| File | Read it when |
|------|--------------|
| `assets/TEMPLATE-prd.md` | Step 1 — instantiate the PRD skeleton |
| `assets/TEMPLATE-decision-record.md` | Step 1's `[C]` — create `{DOCS_ROOT}/record/<brief-stem>.md` if absent |
| `references/REF-brief-contract.md` | Step 1 — what the PRD consumes from the brief, and how to degrade |
| `references/REF-challenge-pass.md` | Before every artifact presentation and re-presentation, and again at the quality gate |
| `references/REF-advanced-elicitation.md` | Whenever the PM chooses `[A]` |
| `references/REF-user-journeys.md` | Step 2 |
| `references/REF-functional-blocks.md` | Step 3 |
| `references/REF-acceptance-criteria.md` | Step 4 |
| `references/REF-metrics.md` | Step 5 |
| `references/REF-complexity-sizing.md` | Step 6 |
| `scripts/validate_prd.py` | Every `[C]` (`--up-to <N>`), and in full at the quality gate |
| `references/ui-lexicon.txt` | Never read in a session — the validator loads it; calibrate it there, one `lang:` line per language |

---

## Step 1 — Frame & scope

One step, from the brief to the opportunity this PRD addresses; its `[C]` creates the PRD and the
project record. Every question below precedes the gate.

### Resolve the docs root

The docs tree is **not** assumed to live under the current working directory — it often sits in a sibling repository; the downstream `spec` skill searches `prd/` the same way. Establish `{DOCS_ROOT}` before anything else, and use it in every later step instead of a bare relative path. Expected layout:

```
{DOCS_ROOT}/
├── brief/        ← brief sources (read-only), when the project has one — `briefs/` is accepted
├── prd/          ← OUTPUT — PRDs, written by this skill
├── record/       ← one decision record per project, written at every [C]
└── …             ← other analysis material (a glossary, context.md)
```

1. Search for a `brief/`, `briefs/` or `prd/` directory **that actually contains `.md` files**: in the cwd, then in sibling repositories / parent directories (e.g. `docs/brief/`, `../*/docs/briefs/`). **Ignore empty scaffolds** and deduplicate the cwd from the sibling matches.
2. **Exactly one candidate** → its parent is `{DOCS_ROOT}`; state it once and move on.
3. **Several candidates, or none** → ask the user which docs root to use. Do not guess. Writing a PRD into a docs tree nobody else uses is how PRDs get lost.

### Offer to resume

If `{DOCS_ROOT}/prd/` holds PRDs with `status: in-progress` (one `Grep`), name them and, for each,
the step to resume at — the first step, in step order (§1, §2–3, §4, §5, §7), whose section still
holds placeholders — and let the PM choose: resume one, or start another PRD. On resume: read the
PRD's record (create it at the first `[C]` reached if absent), skip this step's gate, continue at
that step. A `prd/canonical-memory.md` left by 1.7 is never read as a source: show it to the PM,
who moves its open items once — to `## Parked` or to the record — and deletes it.

### Explore and understand deeply the context

Explore `{DOCS_ROOT}` freely to find any supporting files that seem relevant — context documents, a glossary, other PRDs, briefs. Read whatever helps build a complete understanding of the domain, the terminology, and the broader product context. `Grep` before `Read`: a term, an id, a status across the docs root is one call, not one per file.

### Identify and sum up the Brief

Read `references/REF-brief-contract.md` first — it states which fields the PRD consumes and how to proceed when the brief does not carry them.

**If the user provided a path:** read that file directly.
**If no path was given:** list all `.md` files in `{DOCS_ROOT}/brief/` (or `briefs/`) and ask the user which one to process.
**If there is no brief:** the brief is not a wall. Every step of this skill works the same way — explore, judge whether you hold enough to derive what the step expects, derive if so, ask if not. Here, what the step expects is the brief contract's fields: look for them in `{DOCS_ROOT}`, and ask the PM for what is missing — one `AskUserQuestion` call, up to four fields; the block below is the shape of the summary, not a questionnaire. The PM also names the project, which names the record. The frontmatter then carries `brief: none` and `record: <project>`, §1 carries the frame as the PRD's source, and the absence is a tension (`accepted`) in the record.

**Check the brief's status now, not at the quality gate.** QG-11 requires `status: validated`; discovering that after six steps of work wastes the PM's afternoon. If the frontmatter says anything else — or carries no `status` at all — name the file and its status, ask whether to continue anyway, and if they do, the tension (`accepted`) is written to the record at this step's `[C]`. This is a signal, not a wall: the PM may legitimately explore ahead of formal validation.

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

### Read the project record

A project is a brief, and its decision record is `{DOCS_ROOT}/record/<brief-stem>.md` — with no
brief, the PM names the project and the file takes that name. If it exists, read it once: it holds
the decisions, tensions, frozen vocabulary and sources of every PRD of this project. **A decision
of another PRD is context to cite, never a requirement to import without a gate; a term already
frozen is reused, never re-frozen; a divergence is a question to the PM.** A row the record already
holds for this brief — its status, its frame — is cited, not appended again.

### Identify the scope

Show the list of opportunities imported from the brief. Ask the PM to choose the opportunity — alone: the questions below depend on it.

**If the named opportunity is not in the brief's list:** signal it; it is a tension row at `[C]`. Do not block the Step Gate.

**Then, before the gate**, in one `AskUserQuestion` call unless the context already settles them:

1. **The PM's name** — used as the `author`, unless already clear from context. The name alone; the frontmatter takes no email.
2. **The path** `{DOCS_ROOT}/prd/prd<NN>-<short-opportunity-name>.md` — lowercase kebab-case, no spaces and no `&`. Those characters break the filename regexes used downstream (a PRD cited in a spec's `prd_source` gets truncated at the first space), and they turn every shell path into an escaping exercise. `<NN>` you determine yourself: scan `{DOCS_ROOT}/prd/` with `Glob("[Pp][Rr][Dd]*.md")` — deliberately case-tolerant, because existing projects hold PRDs written before this convention (`PRD07 - Gift cards.md`) — extract the leading number from each match, take the highest, increment by 1; start at `01` if none exist. If a file matches but carries no extractable number, say so and ask rather than silently restarting at `01` — a colliding id is exactly the failure this scan exists to prevent. The PM's answer confirms the path — it is not the step's validation: the gate below is still due. **Never rename existing PRDs** to this convention: specs already produced reference their current names.

**Step Gate:**
```
[C] Validate → Step 2 — User journeys
```

**What `[C]` executes at this step** — no backward check, no PRD section exists yet to revise:

1. **Create the PRD** — copy `assets/TEMPLATE-prd.md` in full (the 10 sections and the `## Parked` block, placeholders included), delete its instantiation comment block, then fill the frontmatter (`record:` is the record's stem) and Section 1 — with no brief, §1's Source line carries the frame confirmed above. Write as `## Parked` rows what was parked since the start, and the brief's `For: /prd` items this PRD defers.
2. **Create the record if absent** — copy `assets/TEMPLATE-decision-record.md`, delete its comment block, name the project — **then append**: the opportunity selected and the scope confirmed (D), the frame's decisions (D), the brief's status when not validated or absent (T, `accepted`), an opportunity outside the brief's list (T). No Sources row yet: a source is recorded at the `[C]` where it produced something.
3. **Run the validator** — `--up-to 1`: frontmatter, title, brief, structure, Section 1 and the record.

---

## Step 2 — User journeys

**Methodology:** Read `references/REF-user-journeys.md`

1. **List the goals before writing any flow** — one line per persona → goal, from OPP-XXX and the brief, each passing the user-goal question: the actor could stop there satisfied, in one sitting. Confirm the list with the PM in one message; a single-goal scope is acceptable — a decision row at `[C]`. This settles the section's scope while a correction still costs one line. **The personas confirmed here are what Section 2 states at `[C]`** — including the case where the answer is a cross-cutting population rather than a named persona.
2. Run the **skeleton-based sufficiency check** for each confirmed goal — persona, trigger, variations — and follow its routing: direct derivation (assumed elements marked `[ASSUMPTION: ...]`), partial derivation plus ONE grouped AskUserQuestion call for the empty fields, or full bootstrap canvas.
3. Derive the flows, each carrying its goal on a `*Goal:*` line. Apply the granularity and routing rules — parameters, variations, orphan actions, ERR candidates parked for Step 4 (`## Parked`, written as they come). Reason in **observable results, never in `FUNC-` ids**: those are assigned and frozen at Step 3.
4. Challenge Pass, then **one** presentation: the journeys with their arbitrations and the gate recap, closed by the gate. No separate check on the derived flows — a « ok » given to one would be read as the step's validation.
5. Before the gate, **freeze the behavioural vocabulary** — the 2 to 4 terms carrying an implementation implication, checked against the record's Vocabulary, then the docs root's glossary when it has one: a frozen term is reused as is, or a distinct term is coined — a changed meaning is a Tensions row, never a second Vocabulary row. Confirmed in one message, written at `[C]` to §8 and to the record.

Before the gate: every remaining `[ASSUMPTION]` marker is confirmed by the PM or converted to an OQ-XXX — none survives into Section 3. That confirmation is a question, so it precedes the gate like any other.

**Step Gate:**
```
[A] Advanced Elicitation
[C] Validate → Step 3 — Functional blocks
```

**Before [C]:** the derivation stays in the conversation — nothing is written to the PRD file, a `## Parked` row excepted.

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

**Before [C]:** the derivation stays in the conversation — nothing is written to the PRD file, a `## Parked` row excepted.

---

## Step 4 — Acceptance criteria

**Methodology:** Read `references/REF-acceptance-criteria.md`
Derive acceptance criteria when you have enough information. Start from the `## Parked` rows `For: Step 4` — the ERR and BR candidates of Steps 2 and 3; each becomes a criterion or is discarded with its reason named at the gate, and this `[C]` removes the rows.

**This step also completes Section 4.** A FUNC written at Step 3 could not cite criteria that did not
exist yet, so its `**Acceptance criteria:**` bullets are filled here, at `[C]`, from the ids just
derived. Section 5 is the source of truth for the wording — see the reference for the per-type
linearisation. A FUNC left with no criterion is unspecified, not simple, and the validator says so.

**Step Gate:**
```
[A] Advanced Elicitation
[C] Validate → Step 5 — Leading metrics
```

**Before [C]:** the derivation stays in the conversation — nothing is written to the PRD file, a `## Parked` row excepted.

---

## Step 5 — Leading metrics

**Methodology:** Read `references/REF-metrics.md`
Derive leading metrics when you have enough information.

**Step Gate:**
```
[A] Advanced Elicitation
[C] Validate → Step 6 — Complexity
```

**Before [C]:** the derivation stays in the conversation — nothing is written to the PRD file, a `## Parked` row excepted.

---

## Step 6 — Complexity

**Methodology:** Read `references/REF-complexity-sizing.md`
Count FUNCs and personas. Apply grid. Propose result with justification. If PM disagrees: make the case, then defer to PM's final call — an override is a decision row.

This `[C]` also closes §6, §8, §9 and §10 (`None identified.` where nothing came) and empties `## Parked`: a row it cannot consume becomes an NG in §6 or an OQ in §9.

**Step Gate:**
```
[C] Validate → the quality gate
```

**Before [C]:** the derivation stays in the conversation — nothing is written to the PRD file, a `## Parked` row excepted.

---

## Check Quality Gate

Three movements, in this order, before `status: review`. Fix every failure first. The twelve QG ids are
identifiers, not ranks: they stay stable across versions, and where a check changed home the
movement says so.

### A — The script

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/validate_prd.py {DOCS_ROOT}/prd/prd<NN>-<short-name>.md
```

The full run, without `--up-to`: everything a machine can decide — QG-4, QG-6, QG-8, QG-9, QG-10,
QG-12, the shape half of QG-1 (a `*Goal:*` line, flat numbering), the lexical half of QG-2
(UI-component nouns in §3 and §4) and the resolution half of QG-11 (the brief resolves and is
validated) — plus the unnumbered structural checks: sections present,
ordered and unique, the template's instantiation comment removed, no surviving
`[ASSUMPTION: ...]` marker, no placeholder left behind. The checks are listed step by step in the
script's own docstring. Exit `0` = clean, `1` = at least one error, `2` = bad path. Display the
output whenever it reports anything — an ERROR or a WARN; stay silent only on a clean pass. The
Step 6 `[C]` already ran `--up-to 6`, which checks the same lines: the two runs are identical by
design — both must appear.

**A WARN is not a pass.** The gate presentation lists every remaining WARN verbatim; each is then
fixed, or arbitrated by the PM at this gate and its reason stated in the delivery message and as a
decision row before `status: review` — a WARN the PM never saw is not arbitrated. A FUNC without criteria is first a
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
a FUNC. This movement is where QG-1's judged half (userflow vs wireflow), QG-2's semantic half (journey and FUNC altitude) and
QG-3 (criteria altitude) live: their fail conditions are the tables' rows, defined once, there.
QG-11's judged half — every LGM and DC traces to the brief — is the first row of the Metrics table.

### C — The two crossings no table can see

| # | Check | Pass | Fail |
|---|-------|------|------|
| QG-5 | **Journey → FUNC** | Every journey step implying a capability has a matching FUNC — the *implied* capability, beyond the declared *Capabilities revealed* list the script already checks | A step promises an outcome ("the total is recalculated") that no FUNC carries |
| QG-7 | **Assumptions → OQ** | Every ambiguity still open after being put to the PM is an `OQ-XXX`, and every provisional choice — in a journey, a FUNC, a criterion or a metric — is linked to the OQ that keeps it open: the OQ's `Blocks` column names it | An assumption encoded anywhere in the document with no linked OQ |

Judge each one and display the result.

**On QG pass:** delete the `## Parked` block (it holds no row by then) and set `status: review`.

> PRD saved with status: review.

**Status lifecycle:**

| Transition | Trigger | Actor |
|------------|---------|-------|
| *(file created)* → `in-progress` | Step 1 — the PRD file is written | This skill (automatic) |
| `in-progress → review` | The three movements of the quality gate passed | This skill (automatic) |
| `review → accepted` | Section 9 empty + human sign-off — the PM resolves the last OQs herself: the same three moves as at a `[C]` (integrate, remove the row, a decision row with `Resolves`), without a gate | Human |
