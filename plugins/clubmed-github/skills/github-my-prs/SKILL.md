---
name: github-my-prs
description: 'Show where the user stands: what they are working on right now, the pull requests they have open, the review comments waiting for them, and what they can do next — resume a piece of work, or abandon it. This is the way back to work that was left behind: switching to a pull request from the list restores the branch without the user ever naming it. Also the entry point for closing an older pull request. Use when the user asks what they are working on, wants to see their pull requests, wants to know if anyone reviewed their work, wants to pick something back up, or is simply lost about their current state. Triggers on: "where am I", "what am I working on", "show my pull requests", "list my PRs", "did anyone review my work", "any comments on my PR", "I want to go back to what I was doing", "resume my work", "/github-my-prs".'
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

# Where I Stand

## Overview

Answer three questions in one place: *what am I working on, what is waiting for me, and what do I do next?*

This is more than a listing. It is the **way back**: someone who ran `github-new` and moved on has no other non-technical route to the work they left. Resuming from this list restores their branch without them ever seeing a branch name. Without this skill, `github-new` is a one-way door.

The audience is often non-technical. Never print branch names, SHAs, or git state — describe work by its pull request title, and its status by what the user should do about it.

## Prerequisite — GitHub access

Everything here goes through the **GitHub MCP** (`mcp__github__*`). If those tools are unavailable or a call fails with an auth error, invoke the `github-authentication` skill, then retry once.

## Workflow

### 1. Resolve identity and repository

```bash
DEFAULT=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@')
[ -z "$DEFAULT" ] && DEFAULT=$(git remote show origin | sed -n 's/.*HEAD branch: //p')
CURRENT=$(git rev-parse --abbrev-ref HEAD)
git remote get-url origin
```

Parse `owner`/`repo` from the remote URL (SSH `git@github.com:OWNER/REPO.git` and HTTPS forms, strip a trailing `.git`). Get the account with `mcp__github__get_me` — the `login` is what filters the search.

### 2. Fetch the pull requests

Use `mcp__github__search_pull_requests` (not `list_pull_requests` — it cannot filter by author):

```
query: "repo:<owner>/<repo> author:<login>"
sort: "updated", order: "desc", perPage: 10
```

Keep it to the ten most recent. A non-technical user is trying to find one thing, not audit their history; a long list buries the item they came for.

### 3. Enrich the ones that need attention

For **open** pull requests only, find out whether something is waiting on the user — this is the information they actually came for, and the reason they would otherwise have to open the GitHub web interface.

Use `mcp__github__pull_request_read` with `method: "get_review_comments"` and, when useful, `get_reviews`. Read the comment bodies: they are what the user has to act on.

Do not enrich merged or closed pull requests — nothing is expected of the user there, and each call costs time.

### 4. Present the state

Lead with where they are right now, because that is what orients them:

```
You are working on: <PR title>   (PR #142)

Your recent work
  #142  Summer 2027 offers        ⟳ 2 comments waiting for you
  #138  Booking guide             ⧗ waiting for review
  #131  Pricing update            ✔ published
  #127  Old draft                 ✗ cancelled
```

If `CURRENT` is the default branch, replace the first line with `You are on a clean base — nothing in progress`.

Map GitHub state to something actionable, never to raw API vocabulary:

| Situation | Show |
|---|---|
| open, review comments unanswered | `⟳ N comments waiting for you` |
| open, changes requested | `⟳ changes requested` |
| open, no review yet | `⧗ waiting for review` |
| open, approved | `✔ approved — waiting to be published` |
| draft | `⏸ put aside` |
| merged | `✔ published` |
| closed, not merged | `✗ cancelled` |

When comments are waiting, **show them inline** — author and text, quoted. Sending someone to the web interface to find out what was asked of them is exactly the break in the flow this skill exists to remove.

### 5. Offer what to do next

Use `AskUserQuestion` when there is a plausible action, and only offer options that fit the state:

- **Resume one of these** — available for open and draft pull requests. Go to step 6.
- **Abandon one of these** — hand off to the `github-cancel` skill for the chosen pull request.
- **Nothing for now** — stop.

If the list is empty, say so and point at `github-publish` as the way to send a first piece of work. Do not ask a question with no useful answer.

### 6. Resume a piece of work

The user picks a pull request by its title; translate that to its branch yourself.

Before switching, check the working tree:

```bash
git status --porcelain
```

If it is dirty, stop and ask — switching away would carry or block their current changes. Offer to send the current work first (`github-publish`) or to move on without it (`github-new`). Never stash.

Then restore the branch, whether or not it still exists locally:

```bash
git fetch origin "<branch>"
git switch "<branch>" 2>/dev/null || git switch -c "<branch>" --track "origin/<branch>"
git pull --ff-only
```

If the pull request was closed, reopening it is part of resuming — set `state: "open"` via `mcp__github__update_pull_request`, and say so.

Report in the user's terms:

```
✔ Back on "<PR title>"  (PR #142)
  2 comments to address — shown above
```

## Safety

- NEVER switch branches over a dirty working tree — ask first, and never stash
- NEVER close, reopen, or modify a pull request without the user choosing it
- NEVER force-push or rewrite history
- Read-only by default: this skill only writes when the user explicitly picks an action
