# Step 2 — Read and understand the PRD deeply

Read the full PRD. Build a mental model of:
- The product scope and user goals
- All functional specifications (FUNC-xxx) and the user outcomes they serve
- All business rules (BR-xxx)
- All error scenarios (ERR-xxx) — they are first-class: each in-scope `ERR-xxx` will need a non-passing acceptance test in §9
- The acceptance criteria
- Any open questions or constraints already noted in the PRD
- Any feature flags or toggle names mentioned

## No id scheme? Generate one — the pipeline needs ids to trace

The whole pipeline traces requirements by id (`FUNC-xxx`, `BR-xxx`, `ERR-xxx`…): the breakdown is
anchored on them, §5 quotes them, §9 tags them, the validator enforces their coverage. A PRD
normally carries them — but the source may be a **free-form brief, product doc or ticket** with no
id scheme at all.

In that case, **generate the reference scheme yourself**:
- Walk the document; for each requirement, business rule and error case, assign a stable generated
  id — `FUNC-G1`, `BR-G1`, `ERR-G1`… (`G` = generated) — paired with the **verbatim quote** of the
  source passage it names.
- This generated referential is **part of the breakdown the user confirms in Step 4** — it is an
  interpretation of their document, so they must see it (id → quote) before anything is composed.
- Downstream, everything works unchanged: §5 lists `BR-G1 — "<verbatim quote>"`, §9 tags
  `@BR-G1`, the coverage gate counts them. Add one standard `ℹ️ Assumption` in each spec's §2:
  the id scheme is generated, not the source document's.

**Language** is already decided globally — you write in the user's language (see `SKILL.md` §
Language). The PRD's own language is only a hint if the user's is ambiguous; it never overrides it.

## Supporting material — delegate the sweep to an Explore subagent

Beyond the PRD, `{DOCS_ROOT}` holds loosely-referenced material that clarifies scope and vocabulary: `context.md`, glossaries (`glossaire-*.md`), briefs (`brief/`), and sibling PRDs in `prd/`. You do not know in advance which of these matter — that is breadth-first, read-only discovery, so **dispatch an Explore subagent** rather than loading every file into the main context.

Task the subagent to sweep `{DOCS_ROOT}` (excluding the current PRD, the `drd/` tree handled in Step 3, and the generated `specs/` output) and return a **structured, cited digest** — nothing else:

```
- Glossary terms in scope: <term> → <definition> — <file>:<section>
- Scope / out-of-scope constraints relevant to this PRD — <file>:<section>
- Personas / journeys that touch this PRD — <file>:<section>
- Cross-PRD dependencies or shared components — <file>:<section>
- Anything that CONTRADICTS the PRD (flag explicitly) — <file>:<section>
```

Rules for the subagent: return only what is actually written in the files (never invent), always cite `file:section`, and keep it to what serves this PRD. Fold the digest into your mental model; a contradiction it flags becomes a §2 `❌ Inconsistency`. If `{DOCS_ROOT}` has no supporting material beyond the PRD, skip the subagent and note it. **On a re-run** (same `{DOCS_ROOT}` already swept in this conversation), reuse the existing digest instead of dispatching the subagent again.

