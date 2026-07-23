---
name: github-authentication
description: 'Generates, validates, and persists a GitHub personal access token (PAT) to the user-global ~/.claude/settings.json, so it is created once and valid in every repository. Use this skill whenever a GitHub token is needed, missing, expired, or must be refreshed — before any task that calls the GitHub API or connects the GitHub MCP server. Triggers on: "generate github token", "create github token", "set up github token", "update github token", "GITHUB_TOKEN missing", "GITHUB_TOKEN not set", "GITHUB_TOKEN expired", "github token invalid", "github authentication", "connect github mcp", "configure github access", or any task that requires GitHub API access and the token is absent or invalid. Works by checking for an existing valid token first, then manual browser login (the primary path — GitHub enforces 2FA), with optional best-effort auto-login if GITHUB_USERNAME/GITHUB_PASSWORD are available. Token is stored in ~/.claude/settings.json and auto-injected by Claude Code into every shell session; a legacy project-level .claude/settings.local.json is still read and takes precedence when present. Browser automation uses the Playwright MCP.'
allowed-tools: Bash, mcp__playwright__*
user-invocable: false
version: 1.2.0
changelog:
  - version: 1.2.0
    date: 2026-07-23
    changes:
      - Persist the token to the user-global ~/.claude/settings.json instead of the project .claude/settings.local.json — generated once, valid in every repository, and outside every git work tree
      - Merge into the existing settings document and abort on a malformed one, instead of rebuilding it (the previous "reset to an empty object on parse error" would have wiped the user's whole configuration at this scope)
      - Drop the .gitignore guard and its side effect on the user's repository — no longer needed now that the file lives outside every work tree
      - Still read a legacy project-level token and prefer it, matching Claude Code precedence; document how to clear one that shadows the global token
  - version: 1.1.0
    date: 2026-07-23
    changes:
      - Hidden from the slash-command menu (user-invocable false) — invoked on demand by the other GitHub skills when the token is missing or expired
      - Declare Bash and the Playwright MCP tools in allowed-tools — the skill had none, so each of its ~20 browser calls prompted for permission
created-at: 2026-07-08
created-by: "Jeremy Wallez <jeremy.wallez@clubmed.com>"
---

# github-authentication

Manages the complete lifecycle of `GITHUB_TOKEN`: detection, validation, automated generation of a **classic** Personal Access Token via browser, and persistence to the user-global `~/.claude/settings.json`.

The token is stored in the `env` block of `~/.claude/settings.json` — Claude Code injects it automatically into every shell session, in every repository, so the browser flow runs once rather than per clone. No `export` or `.env` sourcing required. This is exactly what the GitHub MCP server needs:

```bash
claude mcp add --transport http github https://api.githubcopilot.com/mcp/ \
  --header "Authorization: Bearer ${GITHUB_TOKEN}"
```

> **Why a PAT and not OAuth?** The GitHub MCP endpoint's OAuth server does not support dynamic client registration, so Claude Code's built-in OAuth flow fails with *"Incompatible auth server"*. A PAT passed in the `Authorization` header sidesteps OAuth entirely and connects reliably.

## Prerequisite — Playwright MCP

Browser automation uses the **Playwright MCP** (`mcp__playwright__browser_*` tools). If it is not installed:

```bash
claude mcp add playwright -- npx -y @playwright/mcp@latest
```

Confirm with `claude mcp list` → `playwright ... ✔ Connected`. Then continue.

---

## Workflow (follow this exact order)

### Step 1 — Run the main script

```bash
GITHUB_USERNAME=$(python3 .claude/skills/github-authentication/scripts/manage-token.py)
EXIT_CODE=$?
echo "EXIT_CODE=$EXIT_CODE"
```

Human-readable output goes directly to stderr and is visible in the conversation.
`$GITHUB_USERNAME` is populated only on exit 3 (username is not sensitive). The password is **never** written to stdout or any file — it stays in the process environment.

The script returns:
- `exit 0` → token valid, nothing to do — **stop here**
- `exit 2` → no token/expired **or** no credentials → **manual login** (see Step 2)
- `exit 3` → `GITHUB_USERNAME`/`GITHUB_PASSWORD` found → **best-effort auto-login** (see Step 3)
- `exit 1` → unexpected error

> ℹ️ For GitHub, **manual login (Step 2) is the primary and recommended path** because GitHub enforces 2FA. Auto-login (Step 3) is best-effort and will pause at the 2FA prompt.

---

### Step 2 — Manual login (exit 2) — PRIMARY PATH

Open a visible browser at the GitHub login page:

```
mcp__playwright__browser_navigate  { "url": "https://github.com/login" }
mcp__playwright__browser_snapshot  {}
```

Read the current URL from the snapshot header.

- If the URL does **not** contain `/login` → already logged in, **skip to Step 4 immediately**.
- If the URL contains `/login` → **tell the user to sign in** (including any 2FA) in the browser window that just opened, then wait for them to finish:

```
mcp__playwright__browser_wait_for  { "textGone": "Sign in to GitHub", "time": 120 }
```

Then re-snapshot and confirm the URL no longer contains `/login`:

```
mcp__playwright__browser_snapshot  {}
```

If still on `/login` after the wait, prompt the user again and repeat the wait. Once logged in, continue to Step 4.

> ℹ️ A browser session from an earlier step in the same conversation may already be authenticated — always check the URL before waiting.

---

### Step 3 — Best-effort auto-login (exit 3)

The script found `GITHUB_USERNAME` and `GITHUB_PASSWORD`. `$GITHUB_USERNAME` is available from Step 1.

> ⚠️ **Security rule — never extract or echo the password.** GitHub's login page needs the password typed into the browser. Do **not** print `$GITHUB_PASSWORD`. If it is not already in the shell environment (credentials come from a `.env` file), the automated fill cannot proceed safely — fall back to **manual login (Step 2)** instead.

Open the login page and snapshot to get field refs:

```
mcp__playwright__browser_navigate  { "url": "https://github.com/login" }
mcp__playwright__browser_snapshot  {}
```

Fill and submit using `browser_fill_form` (refs come from the snapshot). Reference the password only as the env var — never expand it in visible text:

```
mcp__playwright__browser_fill_form { "fields": [
  { "name": "Username or email", "type": "textbox", "ref": "<login_field_ref>", "value": "<GITHUB_USERNAME>" },
  { "name": "Password",          "type": "textbox", "ref": "<password_field_ref>", "value": "<GITHUB_PASSWORD>" }
]}
mcp__playwright__browser_click    { "target": "<sign_in_button_ref>" }
```

Then wait and check for 2FA:

```
mcp__playwright__browser_wait_for { "time": 5 }
mcp__playwright__browser_snapshot {}
```

If the page shows a 2FA / verification prompt (URL contains `/sessions/two-factor` or the snapshot shows a code field), **tell the user to complete 2FA in the browser** and wait:

```
mcp__playwright__browser_wait_for { "textGone": "verification code", "time": 120 }
```

Once the URL no longer contains `/login` or `/sessions`, continue to Step 4.

---

### Step 4 — Create the classic PAT

Navigate directly to the classic token creation page:

```
mcp__playwright__browser_navigate { "url": "https://github.com/settings/tokens/new" }
mcp__playwright__browser_snapshot {}
```

From the snapshot, get the refs for the **Note** textbox, the **Expiration** dropdown, and the scope checkboxes.

**1. Fill the Note** — auto-name it after the current project:

```bash
PROJECT_NAME=$(basename "$(pwd)")
echo "Token note: Claude Code - $PROJECT_NAME"
```

```
mcp__playwright__browser_type { "target": "<note_field_ref>", "text": "Claude Code - <PROJECT_NAME>" }
```

**2. Set the longest expiration.** The Expiration control is a native `<select>` on this page — use `browser_select_option`. Prefer "No expiration" if offered, otherwise the longest value (e.g. "90 days"):

```
mcp__playwright__browser_select_option { "target": "<expiration_select_ref>", "values": ["none"] }
```

If `"none"` is rejected, re-snapshot to read the exact option values and pick the longest one.

**3. Check the scopes needed.** The GitHub MCP works across repos, orgs, discussions, and project boards, so check this set: `repo`, `read:org`, `workflow`, `read:discussion`, and `read:project`. Use `browser_evaluate` to tick them in one call (language-agnostic, by the checkbox `value` attribute — the exact-match on `value` picks `read:discussion`/`read:project` without also selecting their `write:`/`project` parents):

```
mcp__playwright__browser_evaluate { "function": "() => { const want = ['repo','read:org','workflow','read:discussion','read:project']; const boxes = Array.from(document.querySelectorAll('input[type=checkbox]')); let n = 0; boxes.forEach(cb => { if (want.some(w => cb.value === w || cb.value.startsWith(w+':')) && !cb.checked) { cb.click(); n++; } }); return n + ' scopes checked'; }" }
```

> Note: `read:project` is a child of the `project` scope, and `read:discussion` a child of `write:discussion`. The exact-match (`cb.value === w`) selects only the read-level child. If you instead want full control, add `project` / `write:discussion` to the `want` list.

> To generate an all-scopes token (matching the figma skill's approach), replace the function body with: `document.querySelectorAll('input[type=checkbox]').forEach(cb => { if (!cb.checked) cb.click(); }); return document.querySelectorAll('input[type=checkbox]:checked').length + ' checked';`

**4. Click "Generate token".** Click via JS to avoid ref staleness:

```
mcp__playwright__browser_evaluate { "function": "() => { const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim().startsWith('Generate token')); if (btn && !btn.disabled) { btn.scrollIntoView({block:'center'}); btn.click(); return 'clicked'; } return 'not found or disabled'; }" }
mcp__playwright__browser_wait_for { "time": 2 }
```

---

### Step 5 — Retrieve the token (DOM read — primary)

After generation, GitHub shows the new token in a read-only input with a copy button. Read it directly from the DOM — this is reliable here because the field is a plain input:

```
mcp__playwright__browser_evaluate { "function": "() => { const el = Array.from(document.querySelectorAll('input, code, span')).map(e => (e.value||e.textContent||'').trim()).find(v => v.startsWith('ghp_') || v.startsWith('github_pat_')); return el || ''; }" }
```

Capture the returned value as the token. **Guard**: if the result is empty or does not start with `ghp_` / `github_pat_`, **stop and report the error** — do not attempt to save. Check that the generation page is still open and the token is visible.

> ⚠️ Clipboard read via the Playwright MCP requires launching the server with `--grant-permissions clipboard-read`, which we do not assume. The DOM read above is the primary and default method for GitHub.

---

### Step 6 — Persist the token

Save via the script, which re-validates against the GitHub API before writing:

```bash
python3 .claude/skills/github-authentication/scripts/manage-token.py --save "$TOKEN_VALUE"
```

On success the token is written to `~/.claude/settings.json` → `env.GITHUB_TOKEN` and the file is `chmod 600`. The write merges into the existing document, so the rest of the user's configuration is untouched; a malformed file aborts the save instead of being replaced.

---

### Step 7 — Close the browser

```
mcp__playwright__browser_close {}
```

---

### Step 8 — Connect the GitHub MCP (if not already done)

```bash
claude mcp add --transport http github https://api.githubcopilot.com/mcp/ \
  --header "Authorization: Bearer ${GITHUB_TOKEN}"
```

Tell the user to **restart the Claude Code session** so `GITHUB_TOKEN` from `~/.claude/settings.json` is injected into the environment, then verify:

```bash
claude mcp list   # expect: github ... ✔ Connected
```

---

## Storage — `~/.claude/settings.json` (user-global)

The token is stored in the `env` block of the **user-global** settings:

```json
{
  "env": {
    "GITHUB_TOKEN": "ghp_xxxxx"
  }
}
```

Claude Code automatically injects all `env` entries into the shell environment for every session — **no manual `export` or `source` needed**.

**Why user-global rather than per-project.** A PAT belongs to the person, not to a repository. Storing it once means it is generated once and works in every repository, instead of repeating the browser flow for each new clone. It also removes a whole class of risk: the file lives outside every git work tree, so it cannot be committed, and no `.gitignore` entry has to be correct for the secret to stay safe.

**Writing is a merge, never a rebuild.** This file usually holds the user's entire Claude Code configuration — `model`, `hooks`, `permissions`, `statusLine`, `enabledPlugins`. Only `env.GITHUB_TOKEN` is touched; everything else, including other `env` variables such as `FIGMA_TOKEN`, is carried over verbatim. If the file cannot be parsed, the save **aborts** and reports the error rather than replacing it with a fresh document, which would silently delete that configuration.

**Precedence.** User settings are the *lowest* precedence in Claude Code. A project-level `.claude/settings.local.json` containing `env.GITHUB_TOKEN` therefore overrides the global one. The script still reads that legacy location — and prefers it, matching what Claude Code itself will inject — but never writes to it. If a stale project token is shadowing a valid global one, remove `env.GITHUB_TOKEN` from the project file. The same mechanism is what makes a deliberate per-project override possible, for someone who needs a different GitHub identity on a given repository.

## Variables read (credentials — optional, best-effort auto-login only)

```dotenv
GITHUB_USERNAME=your@email.com   # or GITHUB_EMAIL
GITHUB_PASSWORD=your_password
```

Because GitHub enforces 2FA, credentials only get you past the first login screen — the user still completes 2FA in the browser. Manual login (Step 2) is the recommended path.

---

## Security

- Token is never logged in plaintext (masked: `ghp_W86...zjyM`)
- Password is **never written to stdout, a file, or any shell variable** — it stays in the process environment (`$GITHUB_PASSWORD`)
- `~/.claude/settings.json` is set to `chmod 600` on every write
- The file sits outside every git work tree, so the token cannot be committed — no `.gitignore` entry has to be right for it to stay safe
- One copy instead of one per repository: fewer places for the secret to leak from
- A malformed settings file aborts the save — the script never replaces a configuration it could not read
- The Playwright MCP working directory `.playwright-mcp/` is already gitignored in ai-core
- Never commit `GITHUB_USERNAME` or `GITHUB_PASSWORD` in a non-gitignored `.env` file

---

## Troubleshooting

**"GitHub MCP still fails with 'Incompatible auth server'"**
→ This is the OAuth error. Make sure you added the server with the `--header "Authorization: Bearer ${GITHUB_TOKEN}"` flag (Step 8), not a bare `claude mcp add`.

**"GITHUB_TOKEN not set even after saving"**
→ The token is injected by Claude Code at session start. Restart the Claude Code session, or run:
→ `export GITHUB_TOKEN=$(python3 -c "import json,pathlib; print(json.load(open(pathlib.Path.home()/'.claude/settings.json'))['env']['GITHUB_TOKEN'])")`

**"A valid token is saved but the MCP still reports it invalid"**
→ A project-level `.claude/settings.local.json` is probably shadowing it — project settings outrank user settings. Remove `env.GITHUB_TOKEN` from that file and restart the session.

**"Token read returns empty even though it's visible on screen"**
→ Re-snapshot and confirm the generation succeeded (URL should be `/settings/tokens`). Widen the DOM query to include `code`/`span` elements (already in the Step 5 selector). Do not save an empty value.

**"Expiration select fails"**
→ Re-snapshot to read the exact option values available, then pass the longest one to `browser_select_option`. GitHub's expiration is a native `<select>`, so `browser_select_option` is correct (unlike figma's custom combobox).

**"Playwright MCP tools are not available"**
→ Install it: `claude mcp add playwright -- npx -y @playwright/mcp@latest`, confirm with `claude mcp list`, then retry.

**"Login page keeps returning after sign-in"**
→ GitHub may require device verification or 2FA. Let the user complete the flow in the visible browser, then re-snapshot to confirm the URL left `/login`.

**"Token generated but immediately invalid"**
→ GitHub may have a short propagation delay. The `--save` step retries validation up to 3 times with a 2s interval.

**"Permission denied on settings.json"**
→ `chmod 600 ~/.claude/settings.json` then retry.
