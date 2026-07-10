---
name: github-open-pr
description: 'Open a GitHub pull request for the current branch via the GitHub MCP server (mcp__github__create_pull_request). Use when the user asks to open a PR, create a pull request, or submit their branch for review. Derives owner/repo from the git remote, uses the current branch as head and the default branch as base, and builds a title/body from the last commit. If GITHUB_TOKEN is missing or the GitHub MCP is not connected, it invokes the github-authentication skill first, then retries. Never targets main as head. Triggers on: "open a PR", "create a pull request", "open pull request", "submit for review", "PR this branch", "raise a PR".'
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

# Open a GitHub Pull Request

## Overview

Create a pull request from the current branch using the **GitHub MCP** (`mcp__github__create_pull_request`). Owner, repo, base, head, and the initial title/body are all derived from local git state.

## Prerequisite — GitHub access

The GitHub MCP server must be connected and `GITHUB_TOKEN` valid. If `mcp__github__*` tools are unavailable or a call fails with an auth/connection error → **invoke the `github-authentication` skill**, then retry. (Same pattern as `figma-client` → `figma-authentication`.)

## Workflow

### 1. Resolve owner / repo / branches

```bash
DEFAULT=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@')
[ -z "$DEFAULT" ] && DEFAULT=$(git remote show origin | sed -n 's/.*HEAD branch: //p')
HEAD_BRANCH=$(git rev-parse --abbrev-ref HEAD)
REMOTE_URL=$(git remote get-url origin)
echo "remote=$REMOTE_URL | head=$HEAD_BRANCH | base=$DEFAULT"
```

Parse `owner`/`repo` from `REMOTE_URL`, handling both forms:
- SSH: `git@github.com:OWNER/REPO.git`
- HTTPS: `https://github.com/OWNER/REPO.git`

Strip a trailing `.git`.

### 2. Guard

- If `HEAD_BRANCH` equals `$DEFAULT`, **stop** — you cannot open a PR from the default branch into itself. Tell the user to create/switch to a feature branch (or use `git-push-branch`, which carves one).
- Confirm the branch exists on the remote (`git ls-remote --heads origin "$HEAD_BRANCH"`). If not, tell the user to push it first (`git-push-branch`).

### 3. Build title and body

- **Title**: last commit subject — `git log -1 --pretty=%s`.
- **Body**: short summary from the commit body / the commits ahead of base:

```bash
git log --pretty='- %s' "origin/$DEFAULT..$HEAD_BRANCH"
```

  Include a `## Summary` list of those commit subjects. If a commit references an issue (`#123`), add a `Closes #123` line. Search the repo for a PR template first (`.github/PULL_REQUEST_TEMPLATE.md` or `.github/PULL_REQUEST_TEMPLATE/`) and follow it when present.

### 4. Create the PR

Call the MCP tool:

```
mcp__github__create_pull_request {
  "owner": "<OWNER>",
  "repo":  "<REPO>",
  "title": "<title>",
  "head":  "<HEAD_BRANCH>",
  "base":  "<DEFAULT>",
  "body":  "<body>"
}
```

On an auth/connection error → run `github-authentication`, then retry this call once.

### 5. Output

```
✔ PR opened: <title>
  <html_url>
  <head> → <base>
```

Print the PR URL returned by the MCP so the user can click it.

## Safety

- NEVER open a PR with `head` = default branch
- Do not create duplicate PRs — if `mcp__github__list_pull_requests` shows an open PR for this head, report it instead of creating a new one
- Do not push here — this skill only opens the PR (use `git-push-branch` to push)
