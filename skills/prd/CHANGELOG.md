# Changelog — `prd` skill

Complete version history. The SKILL.md frontmatter keeps only the two most recent
versions — this file is the archive and is never loaded during a PRD session.

## 1.7.4 — 2026-09-01

- The journey goal gets a definition that yields its format: the end state the actor comes to obtain, letting her stop there satisfied — one accomplishment infinitive + object + testable stake, the implicit subject being the actor; the goal is an input from the confirmed actor-goal list and the last step is checked against it, never the reverse. Real Goal lines carried whole paragraphs
- `**Capability:**` becomes optional with a deletion rule — kept only when it adds a boundary the title cannot carry, deleted when it would restate the title: the title names, a kept line bounds, the scenario proves. A field whose formulation cannot show its own value is a restatement

## 1.7.3 — 2026-09-01

- Mission restated: the document must last for those who work from it — altitude is the core discipline (every fact at its level, stated once, so a rule change touches one line, never a journey); nothing the PM says is lost, and nothing she has not said is invented
- The altitude ladder and its placement test live in SKILL.md, in context from Step 0 and at resume — the classification failures observed in real runs all happened at Step 2, before the step-loaded definitions arrived
- New golden rule *Park and Surface*: deferred PM input is parked in the canonical memory under the bucket of the step that consumes it, and the presentation names it — deferred, cut and wrong each have their home
- Provenance legitimises existence, never shape: what a mockup renders as a component enters the PRD as the capability it serves — a real PRD had carved its FUNCs from the DRD's component tree, one per tab, `GIVEN the layer is open`
- QG-2 gains a script half: an unambiguous UI-component noun in a journey step or a FUNC warns (EN+FR lexicon); the semantic half stays with the Challenge Pass, whose FUNC table gains the redesign test and a rule-detail row like the journeys table, and whose journeys out-of-scope fix now routes to an NG at the spotting step's `[C]`
- Step 0's `[C]` writes the frame at the `[PROJECT]` level and no `current_step` — the `[PRD<NN>]` section that carries it exists only from Step 1
- Quality gate movement A displays any reporting run — a WARN-only run exits 0 and was hidden by 'display only on failure'; the Step 6 `--up-to 6` and movement A runs are named as identical by design
- FUNC prose labels (Actor, Capability, Nominal scenario) follow the document's language; table column headers join the machine tokens; the complexity WARN says it counts FUNCs alone; `resolve_brief` matches ids punctuation-insensitively; personas in italics are content; a UI container state in a GIVEN is named as not a state of the world
- Template stripped of its meta-discourse (process sentences deleted, reader legends tightened); the acceptance-criteria placeholder covers all criterion types; changelog history moved to CHANGELOG.md; decision-record.md created

## 1.7.2 — 2026-08-30

- Sections 6/8/9 (and 10) are written at the `[C]` of the step that spotted the item — never parked until Step 6, which closes only what no earlier `[C]` wrote; the step table now says *close*. Two real runs read the previous sentence in opposite ways and a third stalled on it at Step 6
- Step 0's `[C]` creates nothing: the PRD file comes into existence at Step 1's own gate, never earlier — one real run in three creates it early and the scope gate silently disappears
- The quality gate presentation lists every remaining WARN verbatim before arbitration — a WARN the PM never saw is not arbitrated; one real run delivered its WARN unshown
- `brief:` is the source brief's filename stem, never its frontmatter `id:` — the validator resolves it on disk; a real run discovered this by reading the script's source
- The template's `**Acceptance criteria:**` placeholder bullets state their own fate: Step 3 deletes them, Step 4 back-fills one bullet per applicable BR/ERR

## 1.7.1 — 2026-08-30

- Provenance instead of a filter: derive from everything the docs root holds, and present what does not come from the brief or the PM with its source — a *Sources* recap closes every artifact presentation and the canonical memory keeps it. Three real runs wrote rules read in a mockup as established facts; the gate could not see where they came from
- Step 1 restructured: name, number and path are questions asked before the gate; `[C]` executes creation, memory and validator only. Two runs out of six chained Step 1 without its gate because the questions were listed as what `[C]` executes
- A WARN is not a pass: fixed, or justified in the delivery message; a FUNC without criteria is a question to the PM first

## 1.7.0 — 2026-08-28

- What validates a step: `[C]` or a clear confirmation, given to a gate block that is the last thing presented, with no modification, reservation or question; an agreement given to a question never closes a step, and the path confirmation at Step 1 precedes the gate. Three real runs chained a step, wrote acceptance criteria and moved `current_step` on an agreement to something else
- *Name the Arbitrations* states what is not an arbitration: a scope decision the brief leaves open is asked, never presented for confirmation; a behaviour neither the brief states nor the PM said — a default, a fallback, an ordering, a recommendation logic — is an assumption, marked and asked, never a table row. Two real runs arbitrated an open tension themselves, one wrote a recommendation rule the brief excludes
- The FUNC title patterns are shapes whose words follow the PM's language — three real French PRDs carried English titles because the template spelled `Users can` — stated in Language Adaptation, `REF-functional-blocks.md` and the template

## 1.6.1 — 2026-08-27

- `REF-advanced-elicitation.md` keeps only what `[A]` adds — the completeness and cut patterns per artifact (missing step, edge case, oversized / interaction-level / non-autonomous FUNC, missing ERR / ST / PERM); the protocol was already inlined in SKILL.md and the altitude patterns duplicated the Challenge Pass rows
- Validator: a bare filename passed from inside `prd/` resolves its brief in `../brief/` — the unresolved path made `parent.parent` the current directory, and a PRD validated from inside its own folder failed QG-11 for a brief that was there

## 1.6.0 — 2026-08-26

- Quality gate in three movements — the script, the Challenge Pass re-run on the finished document, and the two crossings no table can see (QG-5 implied capabilities, QG-7 assumptions linked to an OQ) — after the judged QG rows turned out to paraphrase the Challenge Pass tables, so that two definitions of one rule could drift
- One check, one home: what the script decides is no longer restated in a Challenge Pass row (a BR citing a BR), and what a reader decides is defined once, in `REF-challenge-pass.md`; QG-11's judged half became the first row of the Metrics table, checked at import and again at the gate
- Challenge Pass tables in one funnel order — existence, cut, altitude (technical before design), wording — with the rows real runs showed missing: out-of-scope leak on journeys and FUNCs, a misplaced variation, an LGM/DC with no brief anchor; the altitude rows apply to the four criterion types; a re-presentation re-runs the pass on the delta
- Step gates are two fixed lines, `[A]` and `[C]`, declared machine tokens: the checklist the block used to carry was translated away in every run seen, and what `[C]` executes is the agent's process, not something the PM reviews
- `[C]` runs `validate_prd.py --up-to <N>` on the sections written so far — a form error is caught at the step that made it, not six steps later
- Validator rewritten: one parse into a document model, checks grouped by the step that writes what they read, `--up-to`; a missing DC threshold warns like its neighbours; every id family is defined once; a `FUNC-XXX` cited outside its own sections must exist; a duplicated id no longer hides the other findings on its row

## 1.5.0 — 2026-08-26

- `[C]` is the whole gate, not the file write: every gate block carries its three numbered actions — backward check, section written, canonical memory updated with `current_step` — after a real run wrote its section and left the canonical memory behind
- `[A]` is a bare option again: the gate shows the choice, the substance comes only once the PM has picked it
- Validator: table headers are checked, since every cell in this format is read by position — a column added, removed or permuted is an error, a translated one only a warning, because a French PRD parses exactly as well; §5's four subsections are expected; the §4 ↔ §5 mirror runs both ways and an empty `Applies to` cell no longer switches it off
- Validator: journey shape (`*Goal:*` present, no `2a.` branch notation), metric completeness, glossary duplicates, empty personas, out-of-scope ids and the complexity grid — all rules the references state and nothing verified
- Diagnostics that named the wrong cause: an exotic dash no longer reads as a divergent text, and an unclosed fence says so instead of reporting eight missing sections
- QG-1 split between its script half (shape) and its judged half (altitude), as QG-11 already was
- Test suite: 28 regression cases, every new check mutation-verified

## 1.4.0 — 2026-08-26

- Gate contract made explicit: nothing reaches the PRD file before `[C]`, every gate block states which sections `[C]` writes, and the two remaining ungated authorisations — the incremental §6/§8/§9 note and the template's instantiation comment — now carry the gate too; the canonical memory keeps taking parked items during derivation
- `[A]` is the agent's work: the protocol is inlined in SKILL.md, answering it by asking the PM what to dig into is named as the one response it never means, and the *nothing is genuinely open* branch is inlined too — so a compacted agent never has to choose between inventing a question and handing the choice back
- New golden rule *Name the Arbitrations* — boundary decisions are presented with the artifact, and a PM-decidable ambiguity is asked before the gate rather than filed as an OQ
- Acceptance criteria and metrics references realigned on the PRD's tables: the block format they documented defined nothing the validator could see, in §5 and in §7 alike
- Step 4 back-fills each FUNC's acceptance-criteria bullets; FUNCs no longer derive from rules that do not exist yet
- Section 2 Personas filled at Step 2, where the persona is resolved, instead of Step 6, which counts them; PER-XXX dropped from complexity sizing
- Challenge Pass gains its Metrics table, so every artifact presentation has one
- Template no longer contradicts the method it instantiates: no FUNC ids where Step 2 must leave `TBD`, a §7 Lagging Metrics that may legitimately be empty, and personas in the plural
- `###` sub-headings named as machine tokens — a translated `### Lagging Metrics` silently failed QG-8
- Validator: a bold id, an escaped pipe, a fenced example and a byte-order mark no longer fail a gate; criteria bullets are read past a `####` grouping heading, which is what kept §4 and §5 from silently disagreeing; QG-11 split between the script and the judged block
- First test suite for `validate_prd.py` — 16 regression cases, stdlib only, one of which executes the acceptance-criteria reference's own worked examples

## 1.3.0 — 2026-08-24

- Step 2 opens on a persona-goal list confirmed with the PM before any flow is written — Cockburn's actor-goal list, absorbing the former coverage check; each journey then states its goal on a `*Goal:*` line at the user-goal level
- Journey rules reworked: completeness judged on the nominal path, a variation placed where it diverges, splitting given a test of its own against merging, and how many journeys to write settled as a readability decision that never changes the capabilities revealed
- Variation routing: same action on a different object is a parameter, a BR when the rules differ, a variation when the observable result differs — the result being what the user ends up with, not what they had to supply
- Saturation signal states which remedy applies (BR for rule detail, step or split for a different consequence) and is re-applied after any merge
- Journey-level preconditions distinct from a scenario GIVEN; the user stays the subject even when the system acts; Step 2 reasons in observable results, FUNC ids being assigned and frozen at Step 3
- A step presents what it derived; what the skill parks, logs or records stays in the canonical memory
- Pruned: the 10 journey validation criteria, the two altitudes table, the 4-8 step range, and two duplicated Challenge Pass rows

## 1.2.0 — 2026-08-24

- FUNCs: one boundary discriminant (autonomous observable outcome) replacing the format constraint, the upper/lower bounds and the multi-surface rule
- Step 3: derivation output is each journey's *Capabilities revealed:* line, filled in
- FUNC ids are identifiers, not ordinals — order fixed at derivation, never renumbered
- Nominal scenario: optional GIVEN prerequisite
- Step 2 gate: behavioural vocabulary frozen in one grouped confirmation
- Journeys: a cross-cutting population is a valid persona answer
- BR hygiene: atomicity, one-rule-one-BR, state adequacy, out-of-scope and perimeter leaks
- ACs referenced from a FUNC with their description; section 5 stays the source of truth
- Business Rules grouped into #### thematic sub-sections past ~10 rules
- Optional section 10 Constraints (CB/CL)
- Validator: referential integrity, AC bullet fidelity, author guard
- Layout aligned on the standard skill anatomy: refs/ renamed references/, canonical memory template moved into assets/

## 1.1.0 — 2026-08-15

- Step 2: skeleton-based sufficiency check with three routes (direct / annotated speculative / bootstrap canvas via one AskUserQuestion call)
- Step 2: journey granularity rules, two outcome altitudes, variation and orphan-action routing, ERR candidates parked for Step 4
- Challenge Pass journeys: Macro step, Bi-goal journey, Error path as step
- HITL rule: documented exception for the grouped journey bootstrap canvas

## 1.0.0 — 2026-07-28

- Initial release in ai-core (ported from the new-be project skill)
