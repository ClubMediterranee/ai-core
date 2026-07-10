---
name: git-push-branch
description: 'Push the current branch to the remote under a speaking branch name derived from the last conventional commit (<type>/<scope>-<description>). Use when the user asks to push their branch, publish their work, push before opening a PR, or push with a meaningful branch name. Hard guard: NEVER pushes the default branch (detected dynamically from origin/HEAD — main, develop, etc.) — if HEAD is on it, a speaking feature branch is carved and switched to first. Sets upstream with -u. Triggers on: "push", "push my branch", "push this", "publish my branch", "push with a good branch name", "push before PR".'
allowed-tools: Bash
version: 1.0.0
changelog:
  - version: 1.0.0
    date: 2026-07-09
    changes:
      - Initial release
created-at: 2026-07-09
created-by: "Jeremy Wallez <jeremy.wallez@clubmed.com>"
---

# Git Push with a Speaking Branch Name

## Overview

Push the current branch to `origin` under a human-readable name derived from the last conventional commit. The default branch is never pushed directly — a feature branch is carved first if needed.

## Branch Naming Rule (canonical)

This is the single source of truth for the speaking branch name, referenced by `git-rebase-branch` and `send-to-github`.

Read the last commit subject:

```bash
SUBJECT=$(git log -1 --pretty=%s)
```

Parse the Conventional Commits form and build the branch:

- `<type>(scope): desc` → `<type>/<scope>-<desc-kebab>`
- `<type>: desc` → `<type>/<desc-kebab>`
- No conventional prefix → `chore/<subject-kebab>`

Kebab-case the description/scope: lowercase, replace any run of non-alphanumeric chars with a single `-`, trim leading/trailing `-`, and truncate the whole branch name to ~60 characters (don't cut mid-word when avoidable).

Examples:
- `feat(tracking-plan): add confidence display` → `feat/tracking-plan-add-confidence-display`
- `fix: remove enum param type` → `fix/remove-enum-param-type`

## Workflow

### 1. Detect default branch and current state

```bash
DEFAULT=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@')
[ -z "$DEFAULT" ] && DEFAULT=$(git remote show origin | sed -n 's/.*HEAD branch: //p')
CURRENT=$(git rev-parse --abbrev-ref HEAD)
echo "Default: $DEFAULT | Current: $CURRENT"
```

### 2. Guard — never push the default branch

If `CURRENT` equals `$DEFAULT`, do **not** push. Carve a speaking branch (naming rule above) from the current commit and switch to it:

```bash
git switch -c "<speaking-branch>"
CURRENT="<speaking-branch>"
```

If `CURRENT` is already a feature branch, keep its name — do not rename an existing branch the user chose. Only derive a name when carving from the default branch or when the current branch has no upstream and its name is a non-descriptive placeholder (e.g. `HEAD`, `tmp`).

### 3. Push with upstream

```bash
git push -u origin "$CURRENT"
```

If the remote rejects because history diverged, stop and report — do **not** force-push. Suggest the user rebase (`git-rebase-branch`) first.

### 4. Output

```
✔ Pushed <branch> → origin/<branch>
  upstream set, <n> commits
```

## Git Safety Protocol

- NEVER push the default branch (`main`, `develop`, …) — always a feature branch + PR
- NEVER `--force` / `--force-with-lease` without an explicit user request
- NEVER update git config
- On rejected push (diverged history), stop and recommend a rebase — do not force
