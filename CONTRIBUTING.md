# Contributing to ai-core

Thank you for taking the time to contribute. This guide covers everything you need to add a skill, agent, doc, or benchmark to this repository.

## Prerequisites

- [Claude Code](https://claude.ai/code) installed and configured
- Access to the repository — ask on **#guilde-ia** (Slack)

## Workflow

```bash
git checkout -b feat/my-contribution   # branch off main
# add your content in the right directory
git commit -m "feat(skills): add my-skill"
# open a Pull Request against main
```

Commits must follow [Conventional Commits](https://www.conventionalcommits.org/). Use the `/git-commit` skill to generate the message automatically.

Common types: `feat`, `fix`, `docs`, `chore`, `refactor`

## Repository structure

| Directory | Contents |
|-----------|----------|
| `plugins/` | Role-based plugins — each one owns its skills under `plugins/<plugin>/skills/` |
| `skills/` | Standalone skills that belong to no plugin |
| `agents/` | Specialised AI agents |
| `docs/` | Tutorials, guides, best practices |
| `benchmarks/` | Model and tooling evaluations |

## Adding a skill

Create the skill inside the plugin that ships it — `plugins/<plugin>/skills/<name>/` (see [`plugins/CLAUDE.md`](plugins/CLAUDE.md)). Use `skills/<name>/` only for a standalone skill that belongs to no plugin. Either way, add a `SKILL.md` file using this frontmatter:

```yaml
---
name: skill-name
description: 'Short description used by Claude to trigger the skill'
model: haiku          # haiku | sonnet | opus
allowed-tools: Bash
version: 1.0.0
changelog:
  - version: 1.0.0
    date: YYYY-MM-DD
    changes:
      - Initial release
created-at: YYYY-MM-DD
created-by: "First Last <email@clubmed.com>"
---
```

Use the `/skill-creator` skill for guided creation, iteration, and benchmarking.

## Questions

Open a [GitHub issue](https://github.com/ClubMediterranee/ai-core/issues).
