# Changelog — `brief` skill

Complete version history. The SKILL.md frontmatter keeps only the two most recent versions — this
file is the archive and is never loaded during a brief session.

## 1.2.0 — 2026-09-20

The 1.1.0 runs kept every behaviour and trimmed the PM's turns, but tool calls rose on one scenario
(35 → 54) and stayed above target on the other (54 → 37), and latency and duration got worse: a
ten-minute final review, whole-file rewrites at each validation, and six to
ten writes to the project logbook per session.

- **The brief file is the only state.** The canonical memory is removed. Guided resume of an
  interrupted session is dropped for now: a brief stays editable until it is `validated` — **revise**
  it in its own file, **amend** a validated one in a new file, restarting at the earliest step the
  change touches
- **§7 Parked**, outside the commitment: what belongs to `/prd` or to a future brief, as
  `Item · Kind · For · Origin` — never referred to from §1–§6. Invariant 1 now reads "no solution
  in the brief's commitment (§1–§6)"
- **At `[C]`, everything the step brought up is written, not only its artifact**: the step's
  section, plus §3, §6 and §7. §7 also holds what belongs to a later step (`For: Step N`) — written
  at the `[C]` of the step that saw it, removed at the `[C]` of the step that consumes it — so
  nothing depends on the conversation surviving an interruption
- **Step 0 opens with an orientation** for the PM, six lines at most: problem space and parked
  solutions, the path, how validations and `[A]` work, what they leave with
- **Writes:** a single creating `Write`, then as few edits as possible — never a whole-file
  rewrite; "one write per file" could not be applied to non-contiguous sections
- **Confidence grades the problem's existence only.** The cap introduced in 1.1.0 is removed — it
  contradicted the grid and turned a well-evidenced brief into "not yet". The root cause is stated
  at product altitude; the technical reason sits below the brief; an unknown root cause is a
  tension that weighs on the readiness verdict
- **Step 4 in one message:** tensions, central value and gate; tensions are carried by default
- **Final review bounded:** only findings that would change the document, applied in as few edits as
  possible, no search pass afterwards; the PM is told it takes a few minutes. A quotation from a source, the
  Painted Door and §7 are not solution leaks
- After an independent review and the 1.2.0 runs (PM turns 13 and 9, tool calls 43 and 34, 23.9 and
  20.6 min): description brought under the 1 024-character limit; two leftover confidence caps
  removed; readiness line written at Step 4's `[C]` and cross-checked at the gate; a substantive fix
  at the quality gate goes through the backward check; `Blocks` means what `/prd` cannot start on;
  the language rule is the prd skill's (structure in English; prose, labels and values in the PM's language); the Step 3 deposit is a *need*;
  examples moved to another domain; signals column renamed `Grade`; `credits` added
- Readiness verdict written in §6 (`Ready for /prd:`); `Blocks` may name a deferred lever in words;
  an account relayed by the PM is an `Indirect signal`; a study's count is typed like what it
  aggregates; the opportunity example no longer anchors on the root cause

## 1.1.0 — 2026-09-20

After the first dry runs (simulated PM): the rebuilt skill halved the PM's turns against the source
skill, but each reply was about three times slower, and two debriefs named the same frictions.

- Rules reorganised as **three models** (altitude ladder, three classes of content, three homes),
  **six invariants** that neither the agent nor the PM may waive, and **judgment** guidance with
  its reason, its limit and a contrasting example — agents were helped by models and slowed by rule
  conflicts and uncovered cases, never by length
- **Derive first, then close the gaps in one move**: nothing missing → artifact and gate in one
  message; independent gaps → one grouped question; never one question per message. Signals and
  structuring decisions are never derived; every other call is named with the gate — this removes
  the conflict between "asked, never presented" and "name the arbitrations"
- Step 0 empties the PM's head before any framing is shown
- A rival reading is no longer listed as part of a presentation: most presentations carry none, and
  one that would not change the artifact is left out — it had become a routine section
- One write per file per `[C]`; memory written at `[C]` and at checkpoints only; slimmer memory
  template (no sources table, no duplicated tensions); presentations show tensions by title and
  recap sources only when they changed
- Legitimate `Not established` states (root cause, supporting elements), a floor deferred until T0
  is known, a deferred opportunity; `Blocks` accepts a metric
- Readiness verdict for `/prd` in the closing message; quality gate movement B run by an
  independent sub-agent; **Validate** intent on an existing brief
- Confidence: an indirect signal with no identifiable origin grades `Weak`, and `Weak` or
  `Hypothesis` signals cannot lift a brief above `Hypothetical`
- Challenge Pass gains a *Fuzzy term* row; `[A]` gains four patterns (reframe the question,
  second-order effect, source triangulation, inversion); the PM is referred to neutrally
- `bmad-comparison.md` added: what was applied from the BMAD method, what may come in an iteration,
  what is set aside, and the why of this skill's own stances

## 1.0.0 — 2026-09-18

- Initial release in ai-core — ported from the sf project skill (its v2.0) and rebuilt on the `prd`
  skill's architecture, so that the two skills of the chain share one mental model
- Golden Rules replace the DO / DON'T table, each with its reason: Human-In-The-Loop, Derive Before
  You Ask, Challenge the Framing, Name the Arbitrations, Park and Surface, Write Only After [C],
  Language Adaptation, Challenge Pass, Advanced Elicitation
- Party Mode removed. Its purpose — breaking a strong position that the evidence does not settle —
  becomes the *Challenge the Framing* rule, bounded so it cannot nag; its three lenses (opportunity
  cost, most likely failure, behaviour-change resistance) become `[A]` patterns
- Five steps, one gate per step, gates in two fixed lines; the artifact, its arbitrations, its
  sources and the gate arrive in one message. Step 2 keeps its derivation order (signals → persona
  → key problem) with checkpoints asked only when the ground is uncertain
- The brief file exists from Step 0's `[C]` — author, number and path settled before that gate —
  and every later step fills its own section in place; the source skill wrote the file once, at
  the end, so its resume check could never find anything to resume
- The canonical memory lives in the project (`{DOCS_ROOT}/brief/canonical-memory.md`); the skill
  ships only its template. The source skill wrote it inside its own directory — a plugin cache
  shared by every project
- Scripted prompts replaced by exit criteria, shapes and the decisions that belong to the PM: the
  agent derives first, from everything, and asks only for what is missing. Three classes are kept
  apart — derived from a source, the agent's own hypothesis (`[ASSUMPTION: …]`, never evidence), a
  decision only the PM can make (asked, never presented for confirmation)
- Output aligned on what `/prd` consumes: `{DOCS_ROOT}/brief/brief<NN>-<short-name>.md`, frontmatter
  modelled on the PRD's, `### Lagging Metrics` / `### Damage Control` with the PRD's columns, open
  tensions with a `Blocks` column. One opportunities table instead of two
- Status lifecycle `in-progress → review` (the skill) `→ validated` (a person, by hand)
- Skill written in English with a Language Adaptation rule (tokens vs shapes); layout on the
  standard skill anatomy (`references/`, `assets/`); `mcp__*` dropped from `allowed-tools`
