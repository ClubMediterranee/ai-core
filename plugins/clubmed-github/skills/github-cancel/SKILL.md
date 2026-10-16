---
name: github-cancel
description: 'Abandon the work in progress: close its pull request (or turn it into a draft), drop the local branch, and return to a clean base. The symmetric inverse of github-publish — the way to undo an attempt at sending work. Always confirms first, spelling out exactly what will be lost and that closing a pull request is visible to the team. Never deletes the remote branch, so a closed pull request can still be reopened. Use when the user wants to cancel, abandon, drop, or throw away what they are working on, close a pull request they opened, or undo something they sent by mistake. Refuses on already-merged pull requests, which need a revert instead. Triggers on: "cancel this", "abandon this work", "drop what I am doing", "close my pull request", "I sent this by mistake", "throw this away", "undo my PR", "/github-cancel".'
allowed-tools: Bash, AskUserQuestion, mcp__github__*, mcp__plugin_clubmed-github_github__*
version: 1.0.0
changelog:
  - version: 1.0.0
    date: 2026-07-23
    changes:
      - Initial release
created-at: 2026-07-23
created-by: "Jeremy Wallez <jeremy.wallez@clubmed.com>"
---

# Abandon the Work in Progress

## Overview

Undo an attempt: close the pull request opened for the current work, drop the local branch, and return to a clean base.

This is the inverse of `github-publish`. A surface where work can be sent but not un-sent is incomplete — people who cannot cancel simply leave dead pull requests open forever, which is worse for the team than an explicit close.

The audience is often non-technical. This skill destroys work and its effect is visible to colleagues, so the confirmation is the most important part of it — not the git commands.

## Prerequisite — GitHub access

Closing a pull request goes through the **GitHub MCP** (`mcp__github__*`). If those tools are unavailable or a call fails with an auth error, invoke the `github-authentication` skill, then retry once.

## Distinction from `github-new`

Both leave the current work. They are not interchangeable, and the difference is the whole point:

- `github-new` — *"I'll come back to this"*: the work is kept, the pull request stays open.
- `github-cancel` — *"I don't want this"*: the pull request is closed, the local branch is dropped.

If the user seems to mean "put this aside for now" rather than "throw this away", offer the draft option below, or send them to `github-new`.

## Workflow

### 1. Read the current state

```bash
DEFAULT=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@')
[ -z "$DEFAULT" ] && DEFAULT=$(git remote show origin | sed -n 's/.*HEAD branch: //p')
CURRENT=$(git rev-parse --abbrev-ref HEAD)
git status --porcelain
git log --oneline "origin/$DEFAULT..HEAD" 2>/dev/null
```

If `CURRENT` equals `$DEFAULT`, there is nothing in progress to cancel. Say so and point at `github-my-prs`, which can close an older pull request:

```
ℹ Nothing in progress to cancel — you are on a clean base
  To close something you sent earlier, use github-my-prs
```

### 2. Find the pull request for this work

Resolve `owner`/`repo` from `git remote get-url origin` (both SSH and HTTPS forms, strip a trailing `.git`), then look for a pull request whose head is the current branch — `mcp__github__list_pull_requests` with `head` set to `<owner>:<CURRENT>` and `state: "all"`.

Three outcomes:

- **An open pull request** → the full flow below.
- **No pull request** → the work was never sent; there is nothing to close on GitHub, only local work to drop. Skip the draft option in step 4.
- **A merged pull request** → **stop**. It cannot be cancelled; the change is already published. Undoing it means reverting, which is a developer action with consequences this skill will not improvise:

```
✗ This work is already published (PR #<n> was merged) — it cannot be cancelled
  Undoing a merged change means reverting it. Ask a developer.
```

### 3. Build the inventory of what will be lost

The confirmation is only meaningful if it is specific. Gather:

- the uncommitted changes (`git status --porcelain` — count and name the files)
- the local commits (`git log --oneline "origin/$DEFAULT..HEAD"`)
- which of those were never pushed (`git log @{u}..HEAD` when an upstream exists) — **these are the ones that disappear for good**
- the pull request number, title, and whether anyone has already reviewed or commented on it

### 4. Confirm — always, with the consequences spelled out

Use `AskUserQuestion`. Describe the work by its title, quantify what is lost, and say that closing is visible to the team. Never phrase this as a yes/no on a git operation.

With an open pull request, offer three options:

- **Close it** — the pull request is closed on GitHub. State that colleagues will see it as closed, and that it can be reopened later.
- **Put it aside** — the pull request becomes a draft (`mcp__github__update_pull_request` with `draft: true`). Nothing is closed, nothing is destroyed, it stops asking for review. This option exists because people hesitate in front of irreversible actions and end up doing nothing at all; a reversible middle path keeps the pull request list honest.
- **Never mind** — stop, change nothing.

Without a pull request, offer two: **abandon this work** / **never mind**.

If there are unpushed commits or uncommitted changes, they must appear in the question text — not in the report afterwards. That is the only moment the user can still say no.

### 5. Apply the choice

**Close it:**

```
mcp__github__update_pull_request { "owner": ..., "repo": ..., "pullNumber": <n>, "state": "closed" }
```

Then return to a clean base and drop the local branch:

```bash
git switch "$DEFAULT"
git pull --ff-only
git branch -D "<branch>"
```

`-D` (not `-d`) is deliberate: the branch is intentionally unmerged and `-d` would refuse. The user has just consented to exactly that.

**Never delete the branch on the remote.** It costs nothing to keep, and it is what makes a closed pull request reopenable — the safety net that lets a hesitant user say yes.

**Put it aside:** set `draft: true`, leave the pull request open, then return to the clean base the same way. Keep the local branch in this case: the work is paused, not abandoned.

**Never mind:** change nothing and say so plainly.

### 6. Report

```
✔ Cancelled
  work : <PR title>
  PR   : #<n> closed — reopenable from github-my-prs
  base : <default> — up to date
```

Put aside:

```
✔ Put aside
  work : <PR title>
  PR   : #<n> is now a draft — no longer waiting for review
```

## Safety

- NEVER close a pull request or delete a branch without an explicit confirmation naming what is lost
- NEVER delete the branch on the remote — closed pull requests must stay reopenable
- NEVER touch a merged pull request — stop and explain that a revert is needed
- NEVER force-push
- Uncommitted and unpushed work must be named in the confirmation, before the action, never only in the report
