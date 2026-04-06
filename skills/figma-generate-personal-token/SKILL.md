---
name: figma-generate-personal-token
description: 'Generates, validates, and persists a Figma personal access token to FIGMA_TOKEN. Use this skill whenever a Figma token is needed, missing, expired, or must be refreshed — before any task that calls the Figma API. Triggers on: "generate figma token", "create figma token", "set up figma token", "update figma token", "FIGMA_TOKEN missing", "FIGMA_TOKEN not set", "FIGMA_TOKEN expired", "figma token invalid", "figma authentication", "configure figma access", or any task that requires Figma API access and the token is absent or invalid. Works by checking for an existing valid token first, then auto-login with FIGMA_USERNAME/FIGMA_PASSWORD if available, otherwise falls back to manual login — no manual copy-paste required.'
version: 1.0.0
changelog:
  - version: 1.0.0
    date: 2026-04-05
    changes:
      - Initial release — check, generate, persist token
created-at: 2026-04-05
created-by: "Jeremy Wallez <jeremy.wallez@clubmed.com>"
---

# figma-generate-personal-token

Manages the complete lifecycle of `FIGMA_TOKEN`: detection, validation, automated generation via browser, and persistence to the project `.env`.

Supports auto-login if `FIGMA_USERNAME` and `FIGMA_PASSWORD` are available in the environment or `.env` files.

---

## Workflow (follow this exact order)

### Step 1 — Run the main script

```bash
SCRIPT_OUTPUT=$(python3 .claude/skills/figma-generate-personal-token/scripts/manage-token.py)
EXIT_CODE=$?
echo "$SCRIPT_OUTPUT"
echo "EXIT_CODE=$EXIT_CODE"
```

The script returns:
- `exit 0` → token valid, nothing to do
- `exit 3` → `FIGMA_USERNAME`/`FIGMA_PASSWORD` found → **auto-login** (see Step 2)
- `exit 2` → no token/expired **or** no credentials → **manual login** (see Step 3)
- `exit 1` → unexpected error

---

### Step 2 — Auto-login with credentials (exit 3)

The script found `FIGMA_USERNAME` and `FIGMA_PASSWORD`. Its stdout contains two lines with the values
to use — note: `FIGMA_AUTO_LOGIN_*` is just the script's output format, **not** the name of the source
env vars. Extract them from `$SCRIPT_OUTPUT`:

```bash
USERNAME=$(echo "$SCRIPT_OUTPUT" | grep "^FIGMA_AUTO_LOGIN_USERNAME=" | cut -d= -f2-)
PASSWORD=$(echo "$SCRIPT_OUTPUT" | grep "^FIGMA_AUTO_LOGIN_PASSWORD=" | cut -d= -f2-)
```

**Open the browser, fill the form and submit in one chain:**

```bash
agent-browser open "https://www.figma.com/login" && agent-browser wait --load networkidle && agent-browser snapshot -i
```

Fill the form (refs `@eX` come from the snapshot):

```bash
agent-browser fill @eX "$USERNAME" && agent-browser fill @eY "$PASSWORD" && agent-browser click @eZ
```

Wait for post-login redirect:

```bash
agent-browser wait --load networkidle --timeout 30000 && agent-browser get url
```

If the URL still contains `/login`, Figma may require 2FA — wait for the user to complete the flow:

```bash
agent-browser wait --fn "!window.location.href.includes('/login')" --timeout 120000
```

**Then continue to Step 4.**

---

### Step 3 — Manual login (exit 2)

No credentials available. Navigate to settings and immediately check the resulting URL:

```bash
agent-browser open "https://www.figma.com/settings" && agent-browser wait --load networkidle && agent-browser get url
```

- If the URL does **not** contain `/login` → already logged in, **skip to Step 4 immediately**
- If the URL contains `/login` → inform the user, then wait up to 2 minutes:

```bash
agent-browser wait --fn "!window.location.href.includes('/login')" --timeout 120000
```

> ℹ️ A browser session from an earlier step in the same conversation may already be authenticated — always check the URL before waiting.

Then continue to Step 4.

---

### Step 4 — Open Settings and click the Security tab

After login, open settings. Figma redirects to the files page but **opens the settings dialog automatically**:

```bash
agent-browser open "https://www.figma.com/settings" && agent-browser wait --load networkidle
```

Take ONE snapshot, grep the Security tab ref, then click it directly:

```bash
agent-browser snapshot -i | grep -E "tab.*(Séc|Secur)"
agent-browser click @eREF
```

> ⚠️ **Never use `agent-browser scroll`** inside a Figma modal — it can close the dialog.
> ⚠️ **Do NOT use JS eval with escaped quotes** to find the Security tab — it returns `null` unreliably. Use snapshot refs instead.

---

### Step 5 — Create the token

Click "Generate new token" via JS with `--stdin` (avoids all shell escaping issues):

```bash
agent-browser eval --stdin <<'EVALEOF'
(() => {
  const btn = Array.from(document.querySelectorAll("button"))
    .find(b => b.textContent.includes("Générer un nouveau token") || b.textContent.includes("Create new token") || b.textContent.includes("Generate new token"));
  if (btn) { btn.scrollIntoView({ block: "center", behavior: "instant" }); btn.click(); return "clicked: " + btn.textContent.trim(); }
  return "not found";
})()
EVALEOF
agent-browser wait 500
```

ONE snapshot to get the name input and expiry combobox refs:

```bash
agent-browser snapshot -i | grep -E "(textbox|combobox)"
```

Fill the form in a single sequence:

```bash
# 1. Token name — auto-detect project name from cwd
PROJECT_NAME=$(basename $(pwd))
agent-browser fill @eNAME_REF "Claude Code - $PROJECT_NAME"

# 2. Longest expiry — the combobox is CUSTOM (not a <select>), use click + JS
# Click the combobox ref to open it:
agent-browser click @eEXPIRY_REF
# Then click the last [role="option"] via JS (longest duration):
agent-browser eval --stdin <<'EVALEOF'
(() => {
  const options = Array.from(document.querySelectorAll('[role="option"]'));
  const last = options[options.length - 1];
  if (last) { last.click(); return "selected: " + last.textContent.trim(); }
  return "no options found";
})()
EVALEOF

# 3. Check ALL permissions in one JS call — always use --stdin
agent-browser eval --stdin <<'EVALEOF'
document.querySelectorAll('input[type="checkbox"]').forEach(cb => { if (!cb.checked) cb.click(); });
document.querySelectorAll('input[type="checkbox"]:checked').length + " checked"
EVALEOF
```

> ⚠️ **Never use `agent-browser select` for the expiry field** — Figma's expiry combobox is a custom component, not a native `<select>`. It will always fail with "Element is not a \<select\> element". Always use click + JS `[role="option"]`.

Click Generate via JS directly — **no snapshot needed**:

```bash
agent-browser eval --stdin <<'EVALEOF'
(() => {
  const btn = Array.from(document.querySelectorAll("button"))
    .find(b => b.textContent.trim() === "Générer un token" || b.textContent.trim() === "Generate token");
  if (btn && !btn.disabled) { btn.click(); return "clicked"; }
  return "not found or disabled: " + Array.from(document.querySelectorAll("button")).map(b => b.textContent.trim()).filter(Boolean).join(", ");
})()
EVALEOF
agent-browser wait 1000
```

---

### Step 6 — Retrieve and persist the token

Click the Copy button and read via `pbpaste` (primary method — most reliable):

```bash
agent-browser eval --stdin <<'EVALEOF'
(() => {
  const btn = Array.from(document.querySelectorAll("button"))
    .find(b => b.title?.match(/Copi/i) || b.getAttribute("aria-label")?.match(/Copi/i) || b.textContent?.match(/Copi/i));
  if (btn) { btn.click(); return "clicked"; }
  return "not found";
})()
EVALEOF
agent-browser wait 300
TOKEN_VALUE=$(pbpaste)
echo "Token retrieved: ${TOKEN_VALUE:0:8}..."
```

If `pbpaste` returns empty or not a Figma token, try reading from the DOM as a last resort:

```bash
TOKEN_VALUE=$(agent-browser eval --stdin <<'EVALEOF'
Array.from(document.querySelectorAll("input")).find(i => i.value?.startsWith("figd_"))?.value || ""
EVALEOF
)
```

> ⚠️ **Do not use DOM read as primary** — Figma's token display field may use internal React state rather than the DOM `.value` property, causing the read to return empty even when the token is visible on screen. The clipboard approach is always reliable.

If `TOKEN_VALUE` is still empty after both attempts, **stop and report the error** — do not call `--save`:

```bash
if [ -z "$TOKEN_VALUE" ] || [[ "$TOKEN_VALUE" != figd_* ]]; then
  echo "❌ Could not retrieve token — check the Figma dialog is still open and the token is visible."
  exit 1
fi
```

Then save:

```bash
python3 .claude/skills/figma-generate-personal-token/scripts/manage-token.py --save "$TOKEN_VALUE"
```

### Step 7 — Close the browser

Always close the browser session after the token has been saved:

```bash
agent-browser close
```

---

## Supported `.env` files (priority order)

The script searches and updates in this order:

| File | Usage | Priority |
|------|-------|----------|
| `.env.local` | Vite/Next.js — gitignored by default | 1st (read) |
| `.env` | Standard — **write target** | 2nd (read) / **1st (write)** |
| `.env.development.local` | Local dev | 3rd |
| `.env.development` | Dev only | 4th |

The token is **always written to `.env`**. If `.env` is not gitignored, a warning is shown.

## Variables read (credentials)

```dotenv
FIGMA_USERNAME=your@email.com   # or FIGMA_EMAIL
FIGMA_PASSWORD=your_password
```

## Variables written (token)

```dotenv
FIGMA_TOKEN=figd_xxxxx
```

---

## Security

- Token is never logged in plaintext (masked: `figd_W86...zjyM`)
- Password is masked in human-readable output (`********`); the structured exit-3 output prints it in plaintext so the agent can extract it — do not persist `$SCRIPT_OUTPUT`
- If `.env` is not gitignored, the script shows a warning
- Never commit `FIGMA_USERNAME` or `FIGMA_PASSWORD` in a non-gitignored `.env` file

---

## Troubleshooting

**"The generation dialog closes unexpectedly"**
→ Always use JS to click the "Generate new token" button — never use a snapshot ref click. The JS approach calls `scrollIntoView` first to ensure the element is in view before clicking.

**"Checkboxes fail partway through"**
→ Do not use a shell `for` loop over refs. Use exclusively the JS command in Step 5 which checks everything in a single evaluation.

**"`agent-browser clipboard read` returns empty"**
→ Use `pbpaste` directly on macOS. It is more reliable and synchronous.

**"Figma keeps redirecting without showing tokens"**
→ Figma may require 2FA re-authentication. Let the user complete the flow in the visible browser.

**"Permission denied on .env"**
→ `chmod 644 .env` then retry.

**"Token generated but immediately invalid"**
→ Figma may have a propagation delay of a few seconds. The script retries automatically 3 times with a 2s interval.

**"Auto-login fails despite valid credentials"**
→ Verify `FIGMA_USERNAME` and `FIGMA_PASSWORD` are correct via manual login.
→ If 2FA is enabled, auto-login will stop at the 2FA step — the user must complete it manually.

**"Expiry select fails with 'Element is not a \<select\> element'"**
→ Figma's expiry field is a custom combobox, not a native `<select>`. Do not use `agent-browser select`. Instead: click the combobox ref to open it, then click the last `[role="option"]` via JS (see Step 5).

**"DOM input read returns empty even though the token is visible on screen"**
→ Figma's token display input uses internal React state; `.value` may not reflect the rendered text. Always use the Copy button + `pbpaste` as the primary retrieval method (see Step 6).
