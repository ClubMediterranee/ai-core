#!/usr/bin/env python3
"""
manage-token.py — Manages the complete lifecycle of GITHUB_TOKEN.

Reads from / writes to .claude/settings.local.json (Claude Code local settings).
The token is injected into the shell environment automatically by Claude Code.

Usage:
  python3 manage-token.py                    # Detect, validate or guide generation
  python3 manage-token.py --save "ghp_xxx"   # Persist a token to settings.local.json
  python3 manage-token.py --check-only       # Validate only, do not generate
  python3 manage-token.py --generate         # Force generation even if token exists

Exit codes:
  0 — Token valid and available
  2 — Token missing/expired, or no credentials — browser generation required
  3 — Credentials found — auto-login available; username written to stdout
  1 — Unexpected error

Output contract:
  All human-readable output goes to stderr.
  exit 3 only: username (not sensitive) written to stdout.
  The password is NEVER written to stdout or any file — callers must read
  $GITHUB_PASSWORD directly from the environment (or source the .env file).
"""

import os
import sys
import re
import json
import time
import stat
import urllib.request
import urllib.error
import argparse
from pathlib import Path


# ── Configuration ──────────────────────────────────────────────────────────────

GITHUB_API_ME = "https://api.github.com/user"

# Only GITHUB_TOKEN: it is what the GitHub MCP header (`Bearer ${GITHUB_TOKEN}`)
# reads. GH_TOKEN (gh CLI) is intentionally NOT detected — a valid GH_TOKEN does
# not populate GITHUB_TOKEN for the MCP, so treating it as "done" leaves the MCP
# broken with an empty header.
TOKEN_ENV_NAMES      = ["GITHUB_TOKEN"]
USERNAME_ENV_NAMES   = ["GITHUB_USERNAME", "GITHUB_EMAIL"]
PASSWORD_ENV_NAMES   = ["GITHUB_PASSWORD"]
ENV_FILES_PRIORITY   = [".env.local", ".env", ".env.development.local", ".env.development"]
SETTINGS_FILE        = ".claude/settings.local.json"
SETTINGS_GITIGNORE_PATTERNS = [
    ".claude/settings.local.json",
    "settings.local.json",
    ".claude/settings.local*",
]

# GitHub PAT prefixes: classic = ghp_, fine-grained = github_pat_
TOKEN_PREFIXES = ("ghp_", "github_pat_")


# ── Output helpers ─────────────────────────────────────────────────────────────

def eprint(*args, **kwargs):
    """All human-readable output goes to stderr."""
    print(*args, file=sys.stderr, **kwargs)


def mask(token: str) -> str:
    if not token or len(token) < 12:
        return "***"
    return token[:8] + "..." + token[-4:]


def mask_password(password: str) -> str:
    return "*" * min(len(password), 8) if password else "***"


def separator(char="─", width=55):
    eprint(char * width)


def section(title: str):
    separator()
    eprint(f"  {title}")
    separator()


# ── .env parsing ───────────────────────────────────────────────────────────────

def parse_env_value(content: str, var_name: str) -> str:
    """Extract the value of a variable from .env file content."""
    pattern = re.compile(
        rf'^{re.escape(var_name)}\s*=\s*'
        r'(?:"([^"]*)"'
        r"|'([^']*)'"
        r'|([^\s\n#]*))\s*(?:#.*)?$',
        re.MULTILINE
    )
    m = pattern.search(content)
    if m:
        val = m.group(1) if m.group(1) is not None else (
              m.group(2) if m.group(2) is not None else (
              m.group(3) or ""))
        return val.strip()
    return ""


# ── 1. Token Detection ─────────────────────────────────────────────────────────

def find_token_in_env() -> tuple[str, str]:
    """Search current shell environment variables."""
    for name in TOKEN_ENV_NAMES:
        val = os.environ.get(name, "").strip()
        if val:
            return val, f"environment variable ${name}"
    return "", ""


def find_token_in_settings() -> tuple[str, str]:
    """Read GITHUB_TOKEN from .claude/settings.local.json → env block."""
    filepath = Path.cwd() / SETTINGS_FILE
    if not filepath.exists():
        return "", ""
    try:
        data = json.loads(filepath.read_text(encoding="utf-8"))
        for name in TOKEN_ENV_NAMES:
            val = data.get("env", {}).get(name, "").strip()
            if val:
                return val, f"{SETTINGS_FILE} (env.{name})"
    except Exception as e:
        eprint(f"  Warning: cannot read {SETTINGS_FILE}: {e}")
    return "", ""


# ── 2. Credentials Detection ───────────────────────────────────────────────────

def find_credentials() -> tuple[str, str, dict]:
    """Search for GITHUB_USERNAME/GITHUB_EMAIL and GITHUB_PASSWORD in env and .env files."""
    username, password, sources = "", "", {}

    for name in USERNAME_ENV_NAMES:
        val = os.environ.get(name, "").strip()
        if val:
            username = val
            sources["username"] = f"environment variable ${name}"
            break

    for name in PASSWORD_ENV_NAMES:
        val = os.environ.get(name, "").strip()
        if val:
            password = val
            sources["password"] = f"environment variable ${name}"
            break

    if not username or not password:
        for filename in ENV_FILES_PRIORITY:
            filepath = Path.cwd() / filename
            if not filepath.exists():
                continue
            try:
                content = filepath.read_text(encoding="utf-8")
                if not username:
                    for name in USERNAME_ENV_NAMES:
                        val = parse_env_value(content, name)
                        if val:
                            username = val
                            sources["username"] = f"{filename} ({name})"
                            break
                if not password:
                    for name in PASSWORD_ENV_NAMES:
                        val = parse_env_value(content, name)
                        if val:
                            password = val
                            sources["password"] = f"{filename} ({name})"
                            break
            except Exception as e:
                eprint(f"  Warning: cannot read {filename}: {e}")
            if username and password:
                break

    return username, password, sources


# ── 3. Token Validation ────────────────────────────────────────────────────────

def validate_token(token: str) -> tuple[bool, str, dict]:
    """Call /user to validate the token. Retries up to 3 times on transient errors."""
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                GITHUB_API_ME,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "github-authentication-skill",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                login = data.get("login") or "unknown"
                name  = data.get("name") or login
                return True, f"{name} (@{login})", data
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                body = ""
                try:
                    body = e.read().decode()
                except Exception:
                    pass
                return False, f"HTTP {e.code} — invalid or expired token. {body[:100]}", {}
            elif attempt < 2:
                time.sleep(2)
                continue
            else:
                return False, f"HTTP {e.code} after 3 attempts", {}
        except urllib.error.URLError as e:
            if attempt < 2:
                time.sleep(1)
                continue
            return False, f"Network error: {e.reason}", {}
    return False, "Failed after 3 attempts", {}


# ── 4. Gitignore Guard ─────────────────────────────────────────────────────────

def is_settings_gitignored() -> bool:
    """Check whether .claude/settings.local.json is covered by .gitignore."""
    gitignore = Path.cwd() / ".gitignore"
    if not gitignore.exists():
        return False
    for line in gitignore.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        if line in SETTINGS_GITIGNORE_PATTERNS:
            return True
        if line in ("*.local.json", "*.local*", ".claude/", ".claude/*"):
            return True
    return False


def ensure_settings_gitignored() -> tuple[bool, str]:
    """Add .claude/settings.local.json to .gitignore if not already present."""
    if is_settings_gitignored():
        return False, "already gitignored"

    gitignore = Path.cwd() / ".gitignore"
    entry = ".claude/settings.local.json"
    block = f"\n# Claude Code local settings — contains secrets, never commit\n{entry}\n"

    if gitignore.exists():
        gitignore.write_text(gitignore.read_text(encoding="utf-8") + block, encoding="utf-8")
    else:
        gitignore.write_text(block.lstrip(), encoding="utf-8")

    return True, f"added '{entry}' to .gitignore"


# ── 5. Persistence ─────────────────────────────────────────────────────────────

def save_token_to_settings(token: str) -> tuple[bool, str]:
    """
    Write GITHUB_TOKEN into .claude/settings.local.json → env block.
    Creates the file if it does not exist. Merges with existing content.
    Enforces gitignore protection before writing.
    """
    filepath = Path.cwd() / SETTINGS_FILE
    filepath.parent.mkdir(parents=True, exist_ok=True)

    added, gi_msg = ensure_settings_gitignored()
    if added:
        eprint(f"  Gitignore: {gi_msg}")

    existed = filepath.exists()  # check BEFORE writing
    data = {}
    if existed:
        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
        except Exception:
            data = {}

    if not isinstance(data.get("env"), dict):
        data["env"] = {}
    data["env"]["GITHUB_TOKEN"] = token

    filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.chmod(filepath, stat.S_IRUSR | stat.S_IWUSR)

    action = "updated" if existed else "created"
    return True, f"{SETTINGS_FILE} {action}"


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="GITHUB_TOKEN lifecycle manager")
    parser.add_argument("--save",       metavar="TOKEN", help="Persist token to .claude/settings.local.json")
    parser.add_argument("--check-only", action="store_true", help="Validate only, do not generate")
    parser.add_argument("--generate",   action="store_true", help="Force generation even if a valid token exists")
    args = parser.parse_args()

    # ── --save mode ───────────────────────────────────────────────────────────
    if args.save:
        section("Saving token")
        token = args.save.strip()
        eprint(f"  Token    : {mask(token)}")
        if not token.startswith(TOKEN_PREFIXES):
            eprint(f"  Warning  : token does not start with {' or '.join(TOKEN_PREFIXES)} — "
                   "may not be a GitHub PAT.")
        eprint("  Validating...")
        ok, msg, _ = validate_token(token)
        if not ok:
            eprint(f"  Invalid  : {msg}")
            sys.exit(1)
        eprint(f"  Valid    : {msg}")
        saved, path_msg = save_token_to_settings(token)
        if not saved:
            eprint("  Save failed.")
            sys.exit(1)
        eprint(f"  Saved    : {path_msg}")
        sys.exit(0)

    # ── Check for an existing token ───────────────────────────────────────────
    section("Checking GITHUB_TOKEN")

    token, source = find_token_in_env()
    if not token:
        token, source = find_token_in_settings()

    if token:
        eprint(f"  Found    : {source}")
        eprint(f"  Token    : {mask(token)}")
    else:
        eprint("  No token found in environment or .claude/settings.local.json.")

    # ── Validate if found ─────────────────────────────────────────────────────
    if token and not args.generate:
        eprint("  Validating...")
        ok, msg, _ = validate_token(token)
        if ok:
            separator()
            eprint(f"  Token valid — {msg}")
            separator()
            sys.exit(0)
        else:
            eprint(f"  Invalid  : {msg}")
            eprint("  A new token must be generated.")

    if args.check_only:
        sys.exit(2)

    # ── Check credentials for auto-login ──────────────────────────────────────
    section("Checking credentials")
    username, password, creds_sources = find_credentials()

    if username and password:
        eprint(f"  Username : {username}  ({creds_sources.get('username', '?')})")
        eprint(f"  Password : {mask_password(password)}  ({creds_sources.get('password', '?')})")
        eprint("  Auto-login available (best-effort — will pause at 2FA).")
        # Only the username (not sensitive) goes to stdout.
        # The password is NEVER written to stdout, a file, or any other output.
        # The caller must read it directly from $GITHUB_PASSWORD env var,
        # or source the appropriate .env file in the same shell session.
        print(username)
        sys.exit(3)

    missing = []
    if not username:
        missing.append("GITHUB_USERNAME (or GITHUB_EMAIL)")
    if not password:
        missing.append("GITHUB_PASSWORD")
    eprint(f"  Not found: {', '.join(missing)}")
    eprint("  Manual login is the recommended path for GitHub (2FA-friendly).")
    eprint("  To enable best-effort auto-login, add to .env.local:")
    eprint("    GITHUB_USERNAME=your@email.com")
    eprint("    GITHUB_PASSWORD=your_password")

    # ── Manual login required ─────────────────────────────────────────────────
    section("Manual login required")
    sys.exit(2)


if __name__ == "__main__":
    main()
