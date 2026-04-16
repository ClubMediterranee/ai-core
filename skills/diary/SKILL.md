---
name: diary
description: 'Instruct Claude agents to keep a narrative diary during a work session. Use when the user says "keep a diary", "document your work", "log your decisions", "start a work diary", "write a diary entry", "diary mode", "log what you do", or any variation of journaling/documenting agent activity. Also use proactively at the start of long multi-step tasks when context compaction is likely. Covers three diary modes: feature work (incremental design decisions), research (architectural exploration), and validation (e2e workflows and reproducible patterns).'
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
changelog:
  - version: 1.0.0
    date: 2026-04-09
    changes:
      - Initial release — unified diary skill with feature/research/validation modes
credits: https://gogogolems.substack.com/p/why-i-make-my-agents-keep-diaries
created-at: 2026-04-03
created-by: "Emmanuel ERNEST <emmanuel.ernest.ext@clubmed.com>"
---

# Agent Diary

> Inspired by Manuel Odendahl's article [**"Why I make my agents keep diaries"**](https://gogogolems.substack.com/p/why-i-make-my-agents-keep-diaries).
>
> The core insight: standard memory systems store *facts*, but diaries preserve *causality* — the abandoned ideas, failed approaches, and decision rationale that makes work intelligible and resumable. The word "diary" is semantically powerful; it naturally evokes personal reflection, time-awareness, and an audience-of-one tone that produces the right documentation behavior with minimal engineering.

---

## When to Use

Activate this skill when the user asks to:

- "Keep a diary while you work on this"
- "Document your work / log your decisions"
- "Start a work diary"
- "Write diary entries as you go"
- "I want to be able to resume this later"
- "Log what you do so I can review it"

Also activate **proactively** at the start of long multi-step tasks where context compaction is likely (migrations, feature implementations, architecture research).

---

## Why Diaries Matter

| Problem | Diary Solution |
|---------|---------------|
| Context window compaction erases session history | Diary survives compaction — agent reads it and resumes |
| Code reviews lack decision rationale | Diary is a "literate PR" — narrative explains the why |
| Trial-and-error repeats across sessions | Diary captures what failed so you don't repeat it |
| Onboarding is slow | Diary shows how complexity accumulated over time |

---

## Diary Modes

Choose the mode based on the **primary activity** — not the topic. When in doubt, use this rule:

> **Are you writing or changing code/config?** → `feature`
> **Are you comparing options before deciding?** → `research`
> **Are you verifying something works end-to-end?** → `validation`

All modes use the same entry template.

### `feature` — Feature Work
Use when the primary activity is **writing, modifying, or refactoring code or configuration**. Even if the task involves some research (e.g., picking a library), if you're ultimately implementing something, use `feature`.

Best for: bug fixes, new features, refactors, migrations, adding middleware, configuration changes.
- Focus entries on *why* each design choice was made
- Record every significant decision point, not just final outcomes
- Note any constraints discovered mid-implementation

### `research` — Architectural Research
Use when the primary activity is **comparing options without yet writing production code**. The output is a recommendation or decision, not a code change.

Best for: tech spikes, ADRs, evaluating libraries/platforms/services, "should we use X or Y?" investigations.
- Capture platform constraints discovered during research
- Document rejected options and why they were ruled out
- Link to relevant docs/issues/benchmarks in Technical details

### `validation` — End-to-End Validation
Use when the primary activity is **running something and verifying it works correctly** — the code is already written and you're confirming it behaves as expected.

Best for: E2E testing, deployment verification, smoke tests, data migration dry-runs.
- Record exact commands that worked (paths, flags, env vars)
- Note environment-specific gotchas
- Document the verified happy path for future reproduction

---

## Workflow

### Step 1 — Create the diary file at session start

**Resolve the diary path** before creating the file:

1. Check `CLAUDE.md` for a `diary-path:` directive — if found, use it.
2. Otherwise check `agents.md` for a `diary-path:` directive — if found, use it.
3. Otherwise default to `docs/diaries/`.

```markdown
# Example override in CLAUDE.md or agents.md
diary-path: logs/ai
```

`docs/diaries/` is the right default: diaries are project documentation, not tool configuration. Keeping them in `docs/` makes them tool-agnostic, git-tracked by default, and visible to reviewers in pull requests — which is the whole point. Only override if the project has a different convention.

Create `<diary-path>/YYYY-MM-DD-<task-slug>.md` at the very beginning of the session.

**File naming**: kebab-case slug derived from the task description.
- `2026-04-03-auth-middleware-refactor.md`
- `2026-04-03-research-cdn-options.md`
- `2026-04-03-validate-payment-flow.md`

**Diary file header**:
```markdown
---
date: YYYY-MM-DD
task: <one-line description of the task>
mode: feature | research | validation
agent: claude-sonnet | claude-opus | ...
session-start: HH:MM
---

# Diary — <task description>
```

### Step 2 — Write entries continuously

Write entries **during** work, not at the end. Each meaningful decision point, discovery, or course correction deserves an entry.

**Entry template:**
```markdown
## Entry — HH:MM

### What I did
<!-- Factual actions taken: files changed, commands run, APIs called -->

### Why
<!-- Connect this action to the goal — the reasoning, not just the outcome -->

### What worked
<!-- Approaches, tools, or patterns that produced good results -->

### What didn't work
<!-- Failed attempts, dead ends, wrong assumptions — as valuable as successes -->

### What I learned
<!-- Tacit knowledge: non-obvious facts about the codebase, API, or domain -->

### What was tricky
<!-- Friction points, complexity, surprising constraints -->

### Future work
<!-- What remains, what this unblocks, what to watch out for next -->

### Technical details
<!-- Concrete anchors: file paths, commands, hashes, versions, env vars -->
```

### Step 3 — Handle context compaction

If context is compacted (you lose session history), **always read the diary first**:

1. `Read docs/diaries/<latest-diary>.md`
2. Resume from the last `## Future work` section
3. Write a new entry noting the context compaction and the resume point

### Step 4 — Write a closing summary

At session end (or when asked to stop), append a final entry:

```markdown
## Session Close — HH:MM

### Summary
<!-- 3-5 sentences: what was accomplished, what state things are in -->

### What's next
<!-- Unblocked tasks, pending decisions, handoff notes -->

### Open questions
<!-- Things still uncertain that the next session should address -->
```

---

## File Structure in the Project

Default (`docs/diaries/`):
```
<project-root>/
└── docs/
    └── diaries/
        ├── 2026-04-03-auth-middleware-refactor.md
        ├── 2026-04-03-research-cdn-options.md
        └── 2026-04-03-validate-payment-flow.md
```

Custom path via `CLAUDE.md` (`diary-path: logs/ai`):
```
<project-root>/
└── logs/
    └── ai/
        └── 2026-04-03-auth-middleware-refactor.md
```

Commit diaries to use them as literate PR documentation. Add the path to `.gitignore` only if you want them local-only.

---

## Anti-Patterns

| Anti-pattern | Why it's harmful |
|---|---|
| Writing all entries at the end of the session | Loses the causal chain — entries become retroactive summaries, not live decisions |
| One-line entries ("Fixed the bug") | No preservation of *why* — useless for future resumption or review |
| Skipping entries when things go smoothly | Failed experiments are as valuable as successes |
| Forgetting to read the diary after context compaction | Agent repeats work already done, misses learned constraints |
| Over-engineering the format | If it slows you down, you'll stop doing it — lean entries are better than no entries |

---

## References

- [Why I make my agents keep diaries — Manuel Odendahl](https://gogogolems.substack.com/p/why-i-make-my-agents-keep-diaries)
- Examples: `examples/feature-work-diary.md`, `examples/research-diary.md`, `examples/validation-diary.md`
