---
name: github-publish
description: 'End-to-end "send my work to GitHub": commit the current changes as a Conventional Commit, then either open a pull request for new work or add to the pull request already open for it, and finally ask whether to keep going or move on. Recognises whether the current work is already published, so a second send adds to the existing pull request instead of silently mixing unrelated work into it or failing on a rejected push. Use when the user wants to ship their work, send changes to GitHub, open a PR from their current changes, "commit push and PR", finalize a piece of work, or go from dirty working tree to an open PR. Composes the git-commit, git-rebase-branch, git-push-branch, and github-open-pr skills. Absolute invariant: NEVER pushes to the default branch (main, develop, etc.) — always a feature branch and a PR. Triggers on: "send to github", "ship it", "ship this", "open a PR for my changes", "commit push and open a PR", "send my work", "create a PR from my work", "/github-publish".'
allowed-tools: Bash, Skill, AskUserQuestion, mcp__github__*, mcp__plugin_clubmed-github_github__*
version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-07-23
    changes:
      - Detect whether the current work is already published and route to "add to the existing PR" instead of creating a duplicate or failing on a rejected push
      - Skip the rebase on an already-published branch, which rewrote pushed history and made the next push non-fast-forward
      - Ask the user what to do next once the PR is open (keep going, or move on via github-new)
      - Ask which work a change belongs to when the current branch already has an open PR
      - Generic user-facing wording — no assumption that the work is documentation
  - version: 1.0.0
    date: 2026-07-09
    changes:
      - Initial release
created-at: 2026-07-09
created-by: "Jeremy Wallez <jeremy.wallez@clubmed.com>"
---

# Send Work to GitHub

## Invariant

**Never push to the default branch (`main`, `develop`, …). Always a feature branch and a pull request.** Every step enforces this; if any step would push the default branch, it carves a feature branch first.

## Overview

Take the working tree from "dirty" to "pull request open", by delegating each concern to a dedicated skill: `git-commit`, `git-rebase-branch`, `git-push-branch`, `github-open-pr`. Keep the rules (branch naming, conflict handling, authentication) in those skills — this one decides *which path applies* and talks to the user.

The audience is often non-technical. Describe work by its commit subject or pull request title, never by branch name, and describe outcomes by what changed for them.

## The two paths

Everything depends on one question: **is the current work already published?**

- **New work** — the branch has no open pull request. Commit, rebase onto the latest base, push, open a PR.
- **Already published** — the branch has an open pull request. Commit and push only. **Do not rebase.**

That last point is not a detail. Rebasing a branch whose commits are already on the remote rewrites published history, and the next push is rejected as non-fast-forward — with no way out that does not involve force-pushing. Bringing a published branch up to date with the base is `github-update`'s job, and it does it without rewriting anything.

## Workflow

### 0. Read the state

```bash
DEFAULT=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@')
[ -z "$DEFAULT" ] && DEFAULT=$(git remote show origin | sed -n 's/.*HEAD branch: //p')
CURRENT=$(git rev-parse --abbrev-ref HEAD)
git status --porcelain
git log --oneline "origin/$DEFAULT..HEAD" 2>/dev/null
```

- Clean tree **and** nothing ahead of the base → nothing to send. Say so and stop.
- Clean tree but commits ahead → skip step 2, there is nothing to commit.
- Dirty → the full flow.

### 1. Identify the path

If `CURRENT` is the default branch, this is **new work** — go to step 2.

Otherwise, look for a pull request on this branch. Resolve `owner`/`repo` from `git remote get-url origin` (SSH and HTTPS forms, strip a trailing `.git`), then `mcp__github__list_pull_requests` with `head: "<owner>:<CURRENT>"`, `state: "all"`. If the MCP is unavailable or errors on auth, invoke `github-authentication` and retry once.

- **No pull request** → new work, and the branch is unpublished. Go to step 2.
- **Open pull request** → ask, with `AskUserQuestion`, which work these changes belong to. Frame it by content, not by git state — something like *"Are these changes part of «PR title», or is this something new?"*:
  - *Part of the same work* → **already published** path.
  - *Something new* → this work must not land in someone else's pull request. Invoke `github-new` to return to a clean base first, then continue as **new work**. Note that `github-new` will ask what to do with anything unpublished, which is exactly right here.
- **Merged pull request** → the branch is finished. Invoke `github-new` to return to a clean base, then continue as **new work**.

### 2. Commit

Invoke the **`git-commit`** skill: staging, type/scope detection, conventional message. If the commit fails (hook rejection), stop and report — do not continue.

### 3. Rebase — new work only

**Skip this step entirely on the already-published path.** See "The two paths" above.

For new work, invoke **`git-rebase-branch`**. It carves a speaking feature branch if HEAD is on the default branch (enforcing the invariant) and rebases onto the latest `origin/<default>`, resolving safe conflicts and asking the user to arbitrate genuine ones.

If the rebase is aborted, stop and report — do not push a half-rebased branch.

### 4. Push

Invoke the **`git-push-branch`** skill. It pushes the current feature branch with upstream tracking and refuses the default branch by design.

On the already-published path the push is a fast-forward, since nothing was rewritten. If it is still rejected, the remote branch moved on its own — stop and send the user to `github-update`. Never force-push to resolve it.

### 5. Open or update the pull request

- **New work** → invoke the **`github-open-pr`** skill.
- **Already published** → do not open anything. The push already updated the pull request. Report which one it landed in.

### 6. Report, then ask what is next

```
✔ Sent
  work   : <type>(scope): <description>  (<short-hash>)
  PR     : <html_url>
```

Already published:

```
✔ Added to «<PR title>»
  work   : <type>(scope): <description>  (<short-hash>)
  PR     : <html_url>
```

Then use `AskUserQuestion` — this is what keeps the user from drifting into the state this skill exists to prevent:

- **Keep working on this** — stay where they are. Tell them the next send will add to this same pull request, so the behaviour is not a surprise later.
- **Move on to something else** — invoke the `github-new` skill, which returns them to a clean, up-to-date base.

Ask every time, including on the already-published path. It costs one question and it is the moment the user is actually thinking about what comes next.

## Notes

- Delegate to the sub-skills; do not duplicate their rules here
- If the user only wants part of the flow, point them at `git-commit`, `git-rebase-branch`, `git-push-branch`, or `github-open-pr`
- Never force-push, never touch `git config`, never skip hooks unless the user explicitly asks
