# Club Med E2E Rules

One rule per file. Each rule declares its own scope in frontmatter, and the orchestrator
**pushes** the matching set into every subagent it spawns (see the skill's *Rule injection*
section). Rules are not "read if relevant" — they are injected into the subagent's prompt and
mandatory.

```yaml
applies-to: [write, review, harden]    # which subagents load this rule
enforcement: grep | judgment | runtime  # how it is checked
```

- **grep** — mechanically detectable; the `harden` phase greps for it (`file:line`).
- **judgment** — assessed by reading the code; the `review` lenses judge it.
- **runtime** — proven by running a command (the quality gate).

Build the exact set for an agent with:

```bash
python3 scripts/build_rule_bundle.py <agent>          # write | review | harden | plan | ground
python3 scripts/build_rule_bundle.py <agent> --list   # just the filenames
```

These rules reflect the reality of the target sites: **live, multi-locale production websites**
(FR/EN, cookie-consent walls, popups), not locally-runnable apps with a test database. Where a
rule conflicts with a generic Playwright tutorial (e.g. class-based Page Objects, DB-seeding
fixtures), **these rules win**.

## Scope matrix

Legend: ● applies · enforcement in the last column.

| Rule | ground | plan | write | harden | review | Enforce |
|------|:------:|:----:|:-----:|:------:|:------:|---------|
| [import-from-fixtures](import-from-fixtures.md) | | | ● | ● | ● | grep |
| [reusable-interaction-functions](reusable-interaction-functions.md) | | ● | ● | | ● | judgment |
| [multi-locale-selectors](multi-locale-selectors.md) | | | ● | | ● | judgment |
| [no-hardcoded-dates](no-hardcoded-dates.md) | | | ● | ● | ● | grep |
| [web-first-assertions](web-first-assertions.md) | | | ● | ● | ● | grep |
| [desktop-mobile-split](desktop-mobile-split.md) | | ● | ● | | ● | judgment |
| [grounded-selectors](grounded-selectors.md) | ● | | ● | | ● | judgment |
| [ban-waitfortimeout](ban-waitfortimeout.md) | | | ● | ● | ● | grep |
| [no-eslint-disable](no-eslint-disable.md) | | | ● | ● | ● | grep |
| [quality-gate](quality-gate.md) | | | | ● | | runtime |
| [small-functions](small-functions.md) | | ● | ● | | ● | judgment |
| [no-repo-pollution](no-repo-pollution.md) | ● | | ● | ● | ● | judgment |

The matrix is documentation; the frontmatter `applies-to` fields are the source of truth. If the
two disagree, the frontmatter wins (the resolver reads it, not this table).
