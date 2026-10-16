# git-commit

Analyses your staged (or unstaged) diff and generates a standardized [Conventional Commits](https://www.conventionalcommits.org/) message. Handles file staging, auto-detects the commit type and scope from the changes, and executes the commit.

## Usage

Trigger with `/commit` or any phrasing like "commit my changes", "create a git commit".

```
/commit
commit these changes
```

## What it does

1. Runs `git status` and `git diff --staged` (falls back to `git diff` if nothing staged)
2. Infers type (`feat`, `fix`, `docs`, `refactor`, etc.) and scope from the diff
3. Generates a commit message under 72 characters in imperative mood
4. Stages and commits — or groups changes into multiple logical commits if needed

## Output

```
✔ feat(auth): implement JWT-based authentication
  commit a1b2c3d
```
