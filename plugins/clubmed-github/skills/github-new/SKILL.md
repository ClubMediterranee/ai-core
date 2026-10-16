---
name: github-new
description: 'Move on to something else: leave the work in progress behind and return to a clean, up-to-date base branch, ready to start fresh. Nothing is discarded silently — if the current work only exists locally (uncommitted changes or commits never pushed), the user is asked what to do with it first, because work left behind on a local branch cannot be found again through github-my-prs. Use when the user has finished a piece of work and wants to start another one, asks to go back to a clean state, wants to start from scratch, or says they are done with what they were doing. Never deletes anything without asking. Triggers on: "I want to work on something else", "start something new", "back to a clean base", "I am done with this", "reset my working state", "start fresh", "/github-new".'
allowed-tools: Bash, Skill, AskUserQuestion
version: 1.0.0
changelog:
  - version: 1.0.0
    date: 2026-07-23
    changes:
      - Initial release
created-at: 2026-07-23
created-by: "Jeremy Wallez <jeremy.wallez@clubmed.com>"
---

# Start Something New

## Overview

Bring the user back to a clean, up-to-date base branch so the next piece of work starts from a fresh state.

This exists because the natural end of `github-publish` leaves the user on a feature branch. If they start editing again from there, the new work piles onto the previous pull request. This skill is the deliberate exit from that state.

The audience is often non-technical. Never surface branch names, rebases, or stashes as concepts the user has to reason about — describe work by *what it is* (the commit subject or pull request title), and describe outcomes by *what changed for them*.

## Core principle — nothing is lost silently

Work that exists only on the user's machine is invisible to `github-my-prs`, which lists pull requests. So before leaving a branch, anything unpublished must be either published or explicitly kept by an informed choice. Silently switching away is what makes people believe their work vanished.

## Workflow

### 1. Read the current state

```bash
DEFAULT=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@')
[ -z "$DEFAULT" ] && DEFAULT=$(git remote show origin | sed -n 's/.*HEAD branch: //p')
CURRENT=$(git rev-parse --abbrev-ref HEAD)
git status --porcelain
git log --oneline "origin/$DEFAULT..HEAD" 2>/dev/null
```

Three signals matter:

- **`CURRENT` vs `DEFAULT`** — is there any work in progress at all?
- **dirty tree** — changes not yet committed
- **commits ahead of `origin/$DEFAULT`** — committed work; check separately whether it is pushed (`git log @{u}..HEAD` when an upstream exists, otherwise every commit ahead is unpublished)

If HEAD is detached, stop and report — there is no branch to leave.

### 2. Already on a clean base

If `CURRENT` equals `$DEFAULT` and the tree is clean:

```bash
git pull --ff-only
```

Report and stop — this is the desired state already.

```
✔ You are on a clean, up-to-date base — ready to start something new
```

If `git pull --ff-only` fails, the local base has diverged from the remote. Do not force anything: report it and suggest `github-update`.

### 3. Work in progress — decide what happens to it

If there is anything unpublished (dirty tree **or** unpushed commits), use `AskUserQuestion`. Name the work by its commit subject or pull request title, state plainly what is unpublished, and offer:

- **Send it first** *(recommended)* — invoke the `github-publish` skill, then continue at step 4. This is the recommended option because published work reappears in `github-my-prs`; unpublished work does not.
- **Keep it here for later** — commit the uncommitted changes onto the current branch (invoke `git-commit`) so nothing is left loose, then continue at step 4. Warn explicitly that this work stays only on their machine and will not appear in `github-my-prs`; the way back is to run this skill again from the same computer.
- **Abandon it** — do not handle it here; point the user at `github-cancel`, which is built for that and confirms before destroying anything.

Never stash. A stash is an invisible holding area a non-technical user cannot reason about or recover from.

If everything is already published (clean tree, nothing unpushed), skip the question — there is nothing at risk. Go straight to step 4.

### 4. Return to the clean base

```bash
git switch "$DEFAULT"
git pull --ff-only
```

Do **not** delete the branch that was just left. It is the user's way back, and `github-cancel` is the only skill allowed to remove work.

### 5. Report

```
✔ Back on a clean base
  left behind : <commit subject or PR title>  (<PR link, if any>)
  base        : <default> — up to date
```

If the work was kept locally rather than published, say so in one line, because it is the one case the user needs to remember:

```
ℹ "<subject>" stays on this computer only — it will not show up in github-my-prs
```

## Safety

- NEVER stash or discard uncommitted work — publish it, commit it in place, or hand off to `github-cancel`
- NEVER delete the branch being left
- NEVER force-push or rewrite published history
- If `git pull --ff-only` fails on the base branch, stop and report — a diverged local base is a real problem, not something to paper over
