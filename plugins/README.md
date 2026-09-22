# Plugins

A plugin is a curated collection of skills bundled for a specific role or stack. Instead of installing skills one by one, you install a plugin and get everything your team needs in one command.

## Installation

**Step 1 — Register the Club Med marketplace** (once globally, on your machine):

```bash
claude plugin marketplace add ClubMediterranee/ai-core
```

**Step 2 — Install the plugin for your project** (per project, scoped to the repo):

```bash
claude plugin install clubmed-tracking-data@clubmed --scope project   # GA4 tracking plans / analytics
claude plugin install clubmed-product@clubmed --scope project         # Spec generation / PRD / Product
claude plugin install clubmed-github@clubmed --scope project          # GitHub workflow / PR / MCP
claude plugin install clubmed-qa@clubmed --scope project              # Playwright E2E test generation
```

Skills become available immediately as slash commands in Claude Code.

## Updating

First refresh the marketplace to pull the latest plugin definitions:

```bash
claude plugin marketplace update
```

Then update each installed plugin:

```bash
claude plugin update clubmed-tracking-data@clubmed --scope project
claude plugin update clubmed-product@clubmed --scope project
claude plugin update clubmed-github@clubmed --scope project
claude plugin update clubmed-qa@clubmed --scope project
```

---

## Available Plugins

### `clubmed-tracking-data` — Club Med - Tracking & Analytics

> Skills for the data / analytics team: build GA4 tracking plans from a Figma link or a URL, inspired by the existing Club Med plan.

**Keywords:** `tracking` · `ga4` · `analytics` · `gtm` · `tracking-plan` · `figma` · `data`

| Skill | Description |
|-------|-------------|
| `agent-browser` | Drives a headless browser to capture live signals (DOM, dataLayer pushes, /collect hits) that back or correct Figma-inferred events. |
| `figma-authentication` | Manages the `FIGMA_TOKEN` lifecycle: detect, validate, auto-generate, and persist. Dependency of `figma-client`. |
| `figma-client` | Figma REST client — fetches node metadata, interactions, instances, hidden layers, and semantic hints. Feeds the Figma inference path. |
| `tracking-plan` | GA4 tracking-plan engine. From a Figma link, a DRD (Design Requirement Details), or a live URL, infers the trackable moments (clicks, impressions, ecommerce, page views), auto-approves every event with a confidence score, and produces a validated, tool-agnostic `plan.json` plus a review markdown. Fully automatic — the user reviews and adjusts the rendered markdown afterwards. |
| `tracking-plan-render` | Renders a validated `plan.json` to Excel, PDF or Markdown for sharing and review. The Markdown render shows each event's confidence level. |

---

### `clubmed-product` — Club Med Product

> Skills for product managers and product owners: spec generation from PRDs, user story enrichment, and developer-ready documentation.

**Keywords:** `product` · `spec` · `prd` · `user-story` · `documentation`

| Skill | Description |
|-------|-------------|
| `spec` | Generates developer-ready specs (enriched user stories) from a PRD document. Reads `docs/specs/prd/`, cross-references `docs/specs/drd/` design files, and produces structured markdown specs in `docs/specs/`. Each spec covers one independently implementable unit sized for an AI developer to complete in under 2 hours. |

---

### `clubmed-github` — Club Med - GitHub

> Send work to GitHub without knowing git. Five commands cover the whole loop from local changes to a merged pull request; the git building blocks underneath stay available to developers but are hidden from the command menu.

**Keywords:** `github` · `git` · `pull-request` · `pat` · `mcp` · `workflow`

**The five commands**

| Skill | What the user understands |
|-------|---------------------------|
| `github-publish` | *I send my work.* Commits, then opens a pull request — or adds to the one already open for this work — and asks whether to keep going or move on. |
| `github-update` | *I get the latest version.* Picks the right method for the situation: pull on a clean base, rebase for work never sent, GitHub-side update for work already sent (so published history is never rewritten). |
| `github-new` | *I move on to something else.* Returns to a clean, up-to-date base, after asking what to do with anything unpublished. |
| `github-cancel` | *I abandon this work.* Closes its pull request (or turns it into a draft), always confirming what is lost first. Never deletes the remote branch, so a closed PR stays reopenable. |
| `github-my-prs` | *Where do I stand?* Current work, open pull requests, review comments inline, and the way back into work that was left behind. |

**Building blocks** — invoked by the commands above and by natural language, but not listed as slash commands (`user-invocable: false`), except `git-commit`.

| Skill | Description |
|-------|-------------|
| `git-commit` | Analyses the diff and generates a Conventional Commits message. Handles staging, type/scope detection, and commit execution. |
| `git-rebase-branch` | Rebases the current branch onto the latest default branch, resolving safe conflicts and asking to arbitrate genuine ones. Never rebases the default branch. |
| `git-push-branch` | Pushes under a speaking name derived from the last conventional commit. Refuses to push the default branch — carves a feature branch first. |
| `github-open-pr` | Opens a pull request via the GitHub MCP, deriving owner/repo/base/head and building title and body from the commits. |
| `github-authentication` | Manages the complete lifecycle of `GITHUB_TOKEN`: detect, validate, auto-generate a classic PAT via browser, and persist to the user-global `~/.claude/settings.json` — generated once, valid in every repository. Unblocks the GitHub MCP server. Uses the Playwright MCP. |

**MCP servers:** `github` (HTTP, `https://api.githubcopilot.com/mcp/`) — authenticated with the `GITHUB_TOKEN` produced by `github-authentication`.

### `clubmed-qa` — Club Med - QA

> Skills for QA automation engineers: robust Playwright/TypeScript E2E test generation with live-site selector grounding, repeated cross-browser flake proofing, and independent multi-lens review.

**Keywords:** `qa` · `e2e` · `playwright` · `testing` · `automation` · `cross-browser`

| Skill | Description |
|-------|-------------|
| `e2e-test-generator` | Orchestrates E2E test generation via 5 scoped subagents (ground/plan/author/harden/review): grounds selectors on the live site, plans scenarios, authors from the grounded contract, proves non-flakiness by repeated cross-browser runs, and reviews with independent critics. |

---

## Plugin vs Skill

| | Plugin | Skill |
|---|--------|-------|
| **What it is** | Curated bundle for a role/stack | Single-purpose slash command |
| **Install** | `claude plugin install <name>@clubmed` | Install individually |
| **Best for** | Onboarding a team or setting up a project | Adding one specific capability |

You can mix both: install a plugin for your core stack, then add individual skills for cross-cutting concerns (e.g. `a11y-web`, `e2e-test-generator`).
