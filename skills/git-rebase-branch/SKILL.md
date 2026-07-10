---
name: git-rebase-branch
description: 'Rebase the current branch onto the latest default branch (detected dynamically from the remote — main, develop, or whatever origin/HEAD points to), safely. Use when the user asks to rebase, update their branch with the default branch, sync with the default branch, resolve a "branch is behind" state, or before pushing/opening a PR. Protects the default branch: if HEAD is on it, it carves a speaking feature branch from the last commit FIRST and never rebases the default branch itself. Attempts safe automatic conflict resolution and only asks the user to arbitrate genuine conflicts. Triggers on: "rebase", "rebase on main", "update my branch", "sync with main", "my branch is behind", "rebase before pushing".'
allowed-tools: Bash, AskUserQuestion
version: 1.0.0
changelog:
  - version: 1.0.0
    date: 2026-07-09
    changes:
      - Initial release
created-at: 2026-07-09
created-by: "Jeremy Wallez <jeremy.wallez@clubmed.com>"
---

# Git Rebase onto Default Branch

## Overview

Rebase the current branch on top of the latest remote default branch (detected dynamically — `main`, `develop`, or whatever `origin/HEAD` resolves to), keeping history linear before a push or PR. The default branch itself is never rebased — if you are on it, a speaking feature branch is carved first.

## Workflow

### 1. Detect the default branch

```bash
# Primary
DEFAULT=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@')

# Fallback if origin/HEAD is not set
if [ -z "$DEFAULT" ]; then
  git remote set-head origin --auto >/dev/null 2>&1
  DEFAULT=$(git remote show origin | sed -n 's/.*HEAD branch: //p')
fi
echo "Default branch: $DEFAULT"
```

### 2. Inspect state

```bash
CURRENT=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $CURRENT"
git status --porcelain
```

If the working tree is dirty, stop and tell the user to commit or stash first (this skill does not stash silently). If HEAD is detached, stop and report.

### 3. Fetch the latest default branch

```bash
git fetch origin "$DEFAULT"
```

### 4. Safety — never rebase the default branch

If `CURRENT` equals `$DEFAULT`, do **not** rebase it. Carve a speaking branch from the current commit, then reset the local default to the remote:

**Speaking branch name** — parse the last commit subject `git log -1 --pretty=%s`:

- `<type>(scope): desc` → `<type>/<scope>-<desc-kebab>`
- `<type>: desc` → `<type>/<desc-kebab>`
- kebab-case the description (lowercase, non-alphanumerics → `-`, collapse repeats, trim), truncate to ~60 chars.

```bash
git switch -c "<speaking-branch>"
git branch -f "$DEFAULT" "origin/$DEFAULT"   # keep local default clean, no rebase of it
CURRENT="<speaking-branch>"
```

Report the new branch name to the user. Now proceed to rebase this new branch.

### 5. Rebase

```bash
git rebase "origin/$DEFAULT"
```

- **Clean result** → done, continue to output.
- **Conflict** → go to Step 6.

### 6. Conflict handling

Attempt **safe** automatic resolution only when it is unambiguous:

```bash
git diff --name-only --diff-filter=U   # list conflicted files
```

Safe-auto cases (resolve, `git add`, then `git rebase --continue`):
- Pure import/whitespace/formatting overlap with no logic divergence.
- One side only adds lines the other doesn't touch (non-overlapping hunks git flagged conservatively).
- Lockfiles/generated files that can be regenerated deterministically.

For **any genuine logic conflict** (both sides changed the same statements with different intent), do **not** guess. Use `AskUserQuestion` to let the user arbitrate per file/hunk (options: keep ours / keep theirs / describe the merge). Apply the choice, `git add <file>`, then:

```bash
git rebase --continue
```

Never leave the repo mid-rebase silently. If the user cannot decide or asks to stop:

```bash
git rebase --abort   # returns to the pre-rebase state
```

and report that a manual rebase is required.

### 7. Output

```
✔ Rebased <branch> onto origin/<default>
  <n> commits replayed
```

If a branch was carved from the default branch, state it explicitly:

```
ℹ Was on <default> — carved branch <speaking-branch> before rebasing (default branch untouched)
```

## Git Safety Protocol

- NEVER rebase the default branch (`main`, `develop`, …) — carve a feature branch first
- NEVER run `--force` / force-push without an explicit user request
- NEVER update git config
- NEVER stash or drop the user's uncommitted work silently — stop and ask
- On unresolved conflict, prefer `git rebase --abort` over leaving a broken state
