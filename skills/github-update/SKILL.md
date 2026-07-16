---
name: github-update
description: 'Update the current branch with its remote counterpart using a rebase (git pull --rebase), keeping history linear and avoiding merge commits. Fetches the branch upstream, replays local commits on top, and handles conflicts (safe automatic resolution for trivial overlaps, asks the user to arbitrate genuine logic conflicts). Use when the user asks to pull with rebase, get the latest remote commits on their branch, update/sync the current branch with its remote, resolve a "your branch is behind" state without a merge commit, or catch up before continuing work. Refuses to run on a dirty working tree (stops and asks to commit or stash first), never force-pushes, never touches git config, and prefers `git rebase --abort` over leaving a broken state. Triggers on: "pull rebase", "git pull --rebase", "get the latest commits", "update my branch from remote", "sync with the remote", "my branch is behind origin", "catch up before I continue".'
allowed-tools: Bash, AskUserQuestion
version: 1.0.0
changelog:
  - version: 1.0.0
    date: 2026-07-16
    changes:
      - Initial release
created-at: 2026-07-16
created-by: "Jeremy Wallez <jeremy.wallez@clubmed.com>"
---

# Git Pull with Rebase

## Overview

Update the current branch with the commits that landed on its remote counterpart, replaying local commits on top instead of creating a merge commit. This keeps history linear and readable — the same effect as `git pull --rebase`, but with explicit state checks and careful conflict handling so the repo is never left in a broken mid-rebase state.

This skill only ever touches the **current** branch and its own upstream. It does not rebase onto a different branch — that is what `git-rebase-branch` is for (updating a feature branch with `main`/`develop`). If the user wants to sync with the default branch rather than the branch's own remote, use `git-rebase-branch` instead.

## Workflow

### 1. Inspect state

```bash
CURRENT=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $CURRENT"
git status --porcelain
```

If HEAD is detached (`CURRENT` is `HEAD`), stop and report — there is no branch to pull.

If the working tree is dirty (any output from `git status --porcelain`), **stop**. Tell the user to commit or stash first — this skill never stashes silently, because a rebase over stashed changes hides work the user may not expect to move. A short, clear message is enough:

```
✗ Working tree has uncommitted changes.
  Commit them (git-commit) or stash them, then run this again.
```

### 2. Determine the upstream

```bash
UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null)
echo "Upstream: ${UPSTREAM:-<none>}"
```

- If an upstream exists (e.g. `origin/feature-x`), use it.
- If there is **no** upstream, this branch was never pushed or tracks nothing. Stop and report — there is nothing to pull. Suggest `git-push-branch` if they meant to publish it first:

```
ℹ Branch '<current>' has no upstream — nothing to pull.
  Publish it first with git-push-branch, or set an upstream.
```

Derive the remote and branch from the upstream for the fetch:

```bash
REMOTE="${UPSTREAM%%/*}"          # e.g. origin
REMOTE_BRANCH="${UPSTREAM#*/}"     # e.g. feature-x
```

### 3. Fetch and check whether a rebase is needed

```bash
git fetch "$REMOTE" "$REMOTE_BRANCH"
git rev-list --left-right --count "$UPSTREAM"...HEAD
```

The two numbers are `behind` (left) and `ahead` (right):

- `behind = 0` → already up to date. Report and stop; no rebase runs.
- `behind > 0`, `ahead = 0` → local is a strict ancestor; the rebase fast-forwards cleanly.
- `behind > 0`, `ahead > 0` → local commits will be replayed on top; conflicts are possible.

### 4. Rebase

```bash
git rebase "$UPSTREAM"
```

- **Clean result** → continue to output.
- **Conflict** → go to Step 5.

### 5. Conflict handling

List what conflicted:

```bash
git diff --name-only --diff-filter=U
```

Attempt **safe** automatic resolution only when the resolution is unambiguous — resolve, `git add <file>`, then `git rebase --continue`:

- Pure import ordering, whitespace, or formatting overlap with no divergence in logic.
- Non-overlapping additions git flagged conservatively (each side only adds lines the other doesn't touch).
- Lockfiles or generated files that can be regenerated deterministically (regenerate, don't hand-merge).

For **any genuine logic conflict** — both sides changed the same statements with different intent — do **not** guess. Use `AskUserQuestion` to let the user arbitrate, one conflicted file (or hunk) at a time. Offer clear options: keep the remote version (theirs), keep the local version (ours), or describe how to combine them. Apply the choice, then:

```bash
git add <file>
git rebase --continue
```

Repeat until the rebase completes. Never leave the repo mid-rebase silently.

If the user cannot decide, asks to stop, or the conflicts are beyond safe automation:

```bash
git rebase --abort
```

This returns the branch to its exact pre-rebase state. Report that a manual rebase is required and nothing was changed.

### 6. Output

Up to date (no rebase ran):

```
✔ '<current>' is already up to date with <upstream>
```

Rebased:

```
✔ Rebased '<current>' onto <upstream>
  <behind> new commit(s) pulled, <ahead> local commit(s) replayed
```

Aborted:

```
ℹ Rebase aborted — branch restored to its previous state
  Conflicts need manual resolution
```

## Git Safety Protocol

- Only ever rebase the **current** branch onto its **own** upstream — never a different branch (use `git-rebase-branch` for that)
- NEVER stash or drop the user's uncommitted work silently — stop and ask them to commit or stash
- NEVER `--force` / force-push, and never as a way to "fix" a diverged state
- NEVER update git config
- On unresolved or ambiguous conflicts, prefer `git rebase --abort` over leaving a broken mid-rebase state
- If a later push is rejected because history was rewritten by the rebase, stop and report — do not force-push to resolve it
