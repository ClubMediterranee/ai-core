---
name: github-update
description: 'Get the latest version: bring whatever the user is currently on up to date, choosing the right method for their situation — a clean base is pulled, work that was never sent is rebased onto the latest base, and work with an open pull request is updated through GitHub itself so nothing already sent is rewritten. Also detects work whose pull request was already merged and offers to return to a clean base. Never force-pushes, never rewrites published history, and refuses to run over uncommitted changes. Use when the user wants the latest changes, thinks they are out of date, is told their pull request is behind or conflicting, or wants to catch up before continuing. Triggers on: "get the latest version", "update my work", "am I up to date", "my PR is behind", "sync with the latest", "catch up before I continue", "pull the latest changes", "/github-update".'
allowed-tools: Bash, Skill, AskUserQuestion, mcp__github__*, mcp__plugin_clubmed-github_github__*
version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-07-23
    changes:
      - Choose the update method from the user's actual situation instead of always rebasing onto the branch's own upstream, which reported "up to date" while the work was stale against the base
      - Update already-published work through the GitHub API rather than a local rebase, so pushed history is never rewritten and no force-push is ever needed
      - Detect a merged pull request and offer a return to a clean base instead of failing on a deleted upstream
      - Generic user-facing wording — no assumption that the work is documentation
  - version: 1.0.0
    date: 2026-07-16
    changes:
      - Initial release
created-at: 2026-07-16
created-by: "Jeremy Wallez <jeremy.wallez@clubmed.com>"
---

# Get the Latest Version

## Overview

Bring the user up to date. What that means depends entirely on where they are, and picking the wrong method is how people end up with rejected pushes and rewritten history — so this skill identifies the situation first and only then acts.

The audience is often non-technical. "Update" to them means *"make sure I have the latest, and that what I sent is not stale"*. They should never have to know which mechanism achieved it.

## Prerequisite — GitHub access

The published-work path uses the **GitHub MCP** (`mcp__github__*`). If those tools are unavailable or a call fails with an auth error, invoke the `github-authentication` skill, then retry once.

## Workflow

### 1. Read the state

```bash
DEFAULT=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@')
[ -z "$DEFAULT" ] && DEFAULT=$(git remote show origin | sed -n 's/.*HEAD branch: //p')
CURRENT=$(git rev-parse --abbrev-ref HEAD)
git status --porcelain
git fetch origin
```

If HEAD is detached, stop and report — there is no branch to update.

If the working tree is dirty, **stop**. Never stash: a rebase over stashed changes moves work the user did not expect to move, and a stash is invisible to someone who does not know git. Offer, via `AskUserQuestion`, to send the current changes first (`github-publish`) or to set them aside properly (`github-new`).

```
✗ You have changes that are not saved yet.
  Send them first, or put them aside, then try again.
```

### 2. Identify the situation

If `CURRENT` is the default branch → **clean base**, go to 3a.

Otherwise resolve `owner`/`repo` from `git remote get-url origin` and look up the pull request for this branch — `mcp__github__list_pull_requests` with `head: "<owner>:<CURRENT>"`, `state: "all"`:

- **No pull request** → the work was never sent → **unpublished work**, go to 3b.
- **Open pull request** → **published work**, go to 3c.
- **Merged pull request** → **finished work**, go to 3d.

### 3a. Clean base — pull

```bash
git pull --ff-only
```

```
✔ You have the latest version
```

If `--ff-only` fails, the local base has diverged from the remote. Do not paper over it with a merge or a reset: report it and say a developer should look, because on a base branch a divergence usually means something went wrong earlier.

### 3b. Unpublished work — rebase onto the latest base

Nothing has been sent, so local history can safely be replayed on top of the latest base. Invoke the **`git-rebase-branch`** skill: it handles the fetch, the rebase onto `origin/<default>`, safe automatic conflict resolution, and asks the user to arbitrate genuine conflicts.

```
✔ Your work is now based on the latest version
```

### 3c. Published work — update through GitHub

The branch is on the remote and a pull request points at it. Rebasing here would rewrite commits that are already published and make the next push non-fast-forward, with force-push as the only way out. So do not rebase — let GitHub merge the base into the branch server-side:

```
mcp__github__update_pull_request_branch { "owner": ..., "repo": ..., "pullNumber": <n> }
```

Then bring the local copy in line:

```bash
git pull --ff-only
```

```
✔ «<PR title>» is up to date with the latest version
  PR : <html_url>
```

If GitHub reports a conflict it cannot resolve, the two sides changed the same lines and someone has to choose. Say that plainly, name the files, and offer to resolve them locally — do **not** improvise a force-push:

```
⚠ «<PR title>» conflicts with the latest version
  Same lines changed on both sides: <files>
  This needs a human decision — I can walk you through it.
```

### 3d. Finished work — the pull request was merged

There is nothing left to update: the work is published and the remote branch may already be gone (which is why the old behaviour failed here with a fetch error). Say so and offer a way forward with `AskUserQuestion`:

- **Return to a clean base** — invoke `github-new`.
- **Stay here** — fine, but say plainly that this work is done and new changes made here will not be part of it.

```
✔ «<PR title>» has been published (PR #<n> was merged)
```

## Safety

- NEVER rebase work that is already published — update it through GitHub instead
- NEVER force-push, and never as a way to "fix" a diverged state
- NEVER stash or drop uncommitted work silently — stop and ask
- NEVER update git config
- On an unresolved conflict, prefer `git rebase --abort` over leaving a broken mid-rebase state
- If `git pull --ff-only` fails on the default branch, stop and report — do not merge or reset to force it through
