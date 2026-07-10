---
name: send-to-github
description: 'End-to-end "send my work to GitHub": commit the current changes as a Conventional Commit, rebase onto the default branch, push under a speaking branch name, and open a GitHub pull request — in one flow. Use when the user wants to ship their work, send changes to GitHub, open a PR from their current changes, "commit push and PR", finalize a feature, or go from dirty working tree to an open PR. Composes the git-commit, git-rebase-branch, git-push-branch, and github-open-pr skills. Absolute invariant: NEVER pushes to the default branch (main, develop, etc.) — always a feature branch and a PR. Triggers on: "send to github", "ship it", "ship this", "open a PR for my changes", "commit push and open a PR", "finalize this feature", "create a PR from my work", "/send-to-github".'
allowed-tools: Bash, Skill, AskUserQuestion
version: 1.0.0
changelog:
  - version: 1.0.0
    date: 2026-07-09
    changes:
      - Initial release
created-at: 2026-07-09
created-by: "Jeremy Wallez <jeremy.wallez@clubmed.com>"
---

# Send to GitHub — commit → rebase → push → PR

## Invariant

**Never push to the default branch (`main`, `develop`, …). Always a feature branch and a pull request.** Every step below enforces this; if any step would push the default branch, it carves a feature branch first.

## Overview

Orchestrates four skills, in order, to take the working tree from "dirty" to "PR open":

1. **`git-commit`** — analyze the diff, stage logically, create a Conventional Commit.
2. **`git-rebase-branch`** — carve a speaking branch if on the default branch, then rebase onto `origin/<default>`.
3. **`git-push-branch`** — push the branch with `-u` under a name derived from the commit.
4. **`github-open-pr`** — open the PR via the GitHub MCP.

## Workflow

### 0. Pre-checks

```bash
git status --porcelain
```

- If the working tree is **clean** and there are no unpushed commits → nothing to ship; stop and tell the user.
- If clean but there **are** local commits ahead of the remote → skip step 1 (nothing to commit) and start at step 2.
- If dirty → run the full flow from step 1.

### 1. Commit

Invoke the **`git-commit`** skill. It handles staging, type/scope detection, and the conventional message. If the commit fails (hook rejection), stop and report — do not continue to rebase/push.

### 2. Rebase

Invoke the **`git-rebase-branch`** skill. It will:
- carve a speaking feature branch if HEAD is on the default branch (enforcing the invariant), and
- rebase onto the latest `origin/<default>`, resolving safe conflicts automatically and asking you to arbitrate genuine ones.

If the rebase is aborted (unresolved conflict), stop and report — do not push a half-rebased branch.

### 3. Push

Invoke the **`git-push-branch`** skill. It pushes the current feature branch with upstream tracking. It refuses to push the default branch by design.

### 4. Open the PR

Invoke the **`github-open-pr`** skill. It derives owner/repo/base/head, builds the title and body from the commits, and calls `mcp__github__create_pull_request` (falling back to `github-authentication` if the token is missing).

### 5. Final summary

Print a concise recap:

```
✔ Shipped
  commit : <type>(scope): <description>  (<short-hash>)
  branch : <speaking-branch> → <default>
  PR     : <html_url>
```

## Notes

- The skill delegates each concern to its dedicated sub-skill — keep logic (naming rules, conflict handling, auth) in those, not duplicated here.
- If the user only wants part of the flow, point them at the relevant sub-skill (`git-commit`, `git-rebase-branch`, `git-push-branch`, `github-open-pr`).
- Never force-push, never touch `git config`, never skip hooks unless the user explicitly asks.
