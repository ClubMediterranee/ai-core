<p align="center">
  <img src="./docs/assets/banner.png" alt="Club Med AI Guild" width="100%" />
</p>

<p align="center">
  The central knowledge base of the <strong>Club Med AI Guild</strong> —<br/>
  skills, agents, benchmarks, tutorials, and best practices shared across teams.
</p>

<p align="center">
  <a href="https://github.com/ClubMediterranee/ai-core/stargazers">
    <img src="https://img.shields.io/github/stars/ClubMediterranee/ai-core?style=flat-square&color=b08850" alt="Stars" />
  </a>
  <a href="https://github.com/ClubMediterranee/ai-core/network/members">
    <img src="https://img.shields.io/github/forks/ClubMediterranee/ai-core?style=flat-square&color=b08850" alt="Forks" />
  </a>
  <a href="https://github.com/ClubMediterranee/ai-core/commits/main">
    <img src="https://img.shields.io/github/last-commit/ClubMediterranee/ai-core?style=flat-square&color=4a9d8f" alt="Last commit" />
  </a>
  <a href="https://github.com/ClubMediterranee/ai-core/graphs/contributors">
    <img src="https://img.shields.io/github/contributors/ClubMediterranee/ai-core?style=flat-square&color=4a9d8f" alt="Contributors" />
  </a>
  <a href="https://github.com/ClubMediterranee/ai-core/pulls">
    <img src="https://img.shields.io/badge/PRs-welcome-b08850?style=flat-square" alt="PRs welcome" />
  </a>
</p>

<p align="center">
  <a href="#overview">Overview</a> ·
  <a href="#whats-inside">What's inside</a> ·
  <a href="#quick-start">Quick start</a> ·
  <a href="#contributing">Contributing</a>
</p>

---

## Overview

`ai-core` is the shared AI resource layer for Club Med's engineering teams. It centralises everything the AI Guild produces so anyone can find, reuse, and build on it:

- **Claude Code skills** — slash commands that extend Claude Code for common dev tasks
- **Agents** — specialised AI agents for complex, multi-step workflows
- **Docs & tutorials** — practical guides, patterns, and team standards
- **Benchmarks** — quantitative evaluations of models, tools, and approaches

The goal is simple: avoid reinventing the wheel, move faster, and raise the quality bar across all teams.

## What's inside

```
ai-core/
├── skills/        # Claude Code slash commands  →  skills/README.md
├── agents/        # Specialised AI agents
├── docs/          # Tutorials, guides, ADRs, best practices
└── benchmarks/    # Model & tooling evaluations
```

### Skills

9 skills available, installable in one command. Categories covered:

| Category | Skills |
|----------|--------|
| Development | `git-commit` · `react-best-practices` · `typescript-advanced-types` |
| Automation | `agent-browser` |
| Config | `agent-creator` · `skill-creator` |
| Code Quality | `clean-code` |
| Testing | `e2e-testing` |
| Documentation | `excalidraw` |

→ Full descriptions and usage in [`skills/README.md`](skills/README.md)

## Quick start

**Prerequisites:** [Claude Code](https://claude.ai/code) installed · access to the Guild's Anthropic account (ask on **#guilde-ia** in Slack)

### Install skills

```bash
npx skills add https://github.com/ClubMediterranee/ai-core
```

An interactive selector lets you pick which skills to install. They are immediately available as `/slash-commands` in Claude Code.

## Contributing

All contributions are welcome — a new skill, a benchmark result, a tutorial, a fix.

```bash
git checkout -b feat/my-contribution
# Add your content in the right directory
git commit -m "feat(skills): add my-skill"   # Conventional Commits
# Open a PR against main
```

Read [CONTRIBUTING.md](CONTRIBUTING.md) for conventions, skill frontmatter format, and guidelines.

## Contributors

<a href="https://github.com/ClubMediterranee/ai-core/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=ClubMediterranee/ai-core" alt="Contributors" />
</a>

---

<p align="center">
  <sub>Built with care by the <strong>AI Guild · Club Med</strong> &nbsp;·&nbsp; <a href="https://github.com/ClubMediterranee/ai-core/issues/new">Report an issue</a></sub>
</p>
