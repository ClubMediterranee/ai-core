#!/usr/bin/env python3
"""
manage-token.py — Manages the complete lifecycle of FIGMA_TOKEN.

Usage:
  python3 manage-token.py                    # Detect, validate or guide generation
  python3 manage-token.py --save "figd_xxx"  # Persist a token to .env
  python3 manage-token.py --check-only       # Validate only, do not generate
  python3 manage-token.py --generate         # Force generation even if token exists

Exit codes:
  0 — Token valid and available
  2 — Token missing/expired or no credentials — browser generation required (handled by caller)
  3 — Credentials (FIGMA_USERNAME + FIGMA_PASSWORD) found — auto-login possible
  1 — Unexpected error
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

FIGMA_API_ME = "https://api.figma.com/v1/me"

# Accepted variable names (in env and .env files)
TOKEN_ENV_NAMES = ["FIGMA_TOKEN", "VITE_FIGMA_TOKEN", "NEXT_PUBLIC_FIGMA_TOKEN"]

# Variable names for login credentials
USERNAME_ENV_NAMES = ["FIGMA_USERNAME", "FIGMA_EMAIL"]
PASSWORD_ENV_NAMES = ["FIGMA_PASSWORD"]

# .env files searched in priority order
ENV_FILES_PRIORITY = [".env.local", ".env", ".env.development.local", ".env.development"]

# .env file to write to
ENV_WRITE_TARGET = ".env"


# ── Utilities ──────────────────────────────────────────────────────────────────

def mask(token: str) -> str:
    if not token or len(token) < 12:
        return "***"
    return token[:8] + "..." + token[-4:]


def mask_password(password: str) -> str:
    if not password:
        return "***"
    return "*" * min(len(password), 8)


def separator(char="─", width=55):
    print(char * width)


def section(title: str):
    separator()
    print(f"  {title}")
    separator()


def parse_env_value(content: str, var_name: str) -> str:
    """
    Extracts the value of a variable from .env file content.
    Handles single-quoted, double-quoted, and unquoted values.
    """
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
    """Searches current shell environment variables."""
    for name in TOKEN_ENV_NAMES:
        val = os.environ.get(name, "").strip()
        if val:
            return val, f"environment variable ${name}"
    return "", ""


def find_token_in_files() -> tuple[str, str, str]:
    """Searches .env files in the current directory."""
    cwd = Path.cwd()
    for filename in ENV_FILES_PRIORITY:
        filepath = cwd / filename
        if not filepath.exists():
            continue
        try:
            content = filepath.read_text(encoding="utf-8")
            for name in TOKEN_ENV_NAMES:
                val = parse_env_value(content, name)
                if val:
                    return val, f"file {filename} (variable {name})", str(filepath)
        except Exception as e:
            print(f"  ⚠️  Cannot read {filename}: {e}")
    return "", "", ""


# ── 2. Login Credentials Detection ────────────────────────────────────────────

def find_credentials() -> tuple[str, str, dict]:
    """
    Searches for FIGMA_USERNAME/FIGMA_EMAIL and FIGMA_PASSWORD in env and .env files.
    Returns (username, password, sources) where sources is a dict with origins.
    """
    username = ""
    password = ""
    sources = {}

    # Search environment variables first
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

    # If incomplete, search .env files
    if not username or not password:
        cwd = Path.cwd()
        for filename in ENV_FILES_PRIORITY:
            filepath = cwd / filename
            if not filepath.exists():
                continue
            try:
                content = filepath.read_text(encoding="utf-8")

                if not username:
                    for name in USERNAME_ENV_NAMES:
                        val = parse_env_value(content, name)
                        if val:
                            username = val
                            sources["username"] = f"file {filename} (variable {name})"
                            break

                if not password:
                    for name in PASSWORD_ENV_NAMES:
                        val = parse_env_value(content, name)
                        if val:
                            password = val
                            sources["password"] = f"file {filename} (variable {name})"
                            break

            except Exception as e:
                print(f"  ⚠️  Cannot read {filename}: {e}")

            if username and password:
                break

    return username, password, sources


# ── 3. Token Validation ────────────────────────────────────────────────────────

def validate_token(token: str) -> tuple[bool, str, dict]:
    """Calls /v1/me to validate the token. Retries up to 3 times if needed."""
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                FIGMA_API_ME,
                headers={"X-Figma-Token": token}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                name = data.get("name") or "Unknown user"
                email = data.get("email") or "?"
                return True, f"{name} ({email})", data
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                body = ""
                try:
                    body = e.read().decode()
                except Exception:
                    pass
                return False, f"HTTP {e.code} — invalid or expired token. Detail: {body[:100]}", {}
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


# ── 4. Persistence to .env ─────────────────────────────────────────────────────

def check_gitignore(filepath: Path) -> bool:
    """Checks whether the file is listed in .gitignore."""
    gitignore = Path.cwd() / ".gitignore"
    if not gitignore.exists():
        return False
    content = gitignore.read_text(encoding="utf-8")
    name = filepath.name
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            if name == line or f"/{name}" == line or line == f"{name}":
                return True
    return False


def save_token_to_env(token: str) -> tuple[bool, str]:
    """
    Writes FIGMA_TOKEN to the target .env file.
    If the file exists: replaces existing lines or appends at the end.
    If the file does not exist: creates it.
    """
    cwd = Path.cwd()
    filepath = cwd / ENV_WRITE_TARGET

    # Warning if .env (non-local) is not gitignored
    if ENV_WRITE_TARGET == ".env" and not check_gitignore(filepath):
        print(f"  ⚠️  WARNING: {ENV_WRITE_TARGET} is not in .gitignore")
        print(f"     Add '{ENV_WRITE_TARGET}' to .gitignore to avoid committing the token")

    vars_to_write = {
        "FIGMA_TOKEN": token,
    }

    if filepath.exists():
        content = filepath.read_text(encoding="utf-8")
        lines = content.splitlines(keepends=True)
        written_vars = set()

        # Replace existing lines
        new_lines = []
        for line in lines:
            replaced = False
            for var_name, var_val in vars_to_write.items():
                pattern = re.compile(
                    rf'^({re.escape(var_name)}\s*=\s*)([^\n]*)$'
                )
                if pattern.match(line.rstrip("\n")):
                    new_lines.append(f"{var_name}={var_val}\n")
                    written_vars.add(var_name)
                    replaced = True
                    break
            if not replaced:
                new_lines.append(line)

        # Append variables not yet present
        missing = {k: v for k, v in vars_to_write.items() if k not in written_vars}
        if missing:
            if new_lines and not new_lines[-1].endswith("\n"):
                new_lines.append("\n")
            new_lines.append("\n# Figma Personal Access Token\n")
            for var_name, var_val in missing.items():
                new_lines.append(f"{var_name}={var_val}\n")

        filepath.write_text("".join(new_lines), encoding="utf-8")
        action = "updated"
    else:
        # Create the file
        content = (
            "# Figma Personal Access Token\n"
            "# Auto-generated — do not commit\n"
            f"FIGMA_TOKEN={token}\n"
        )
        filepath.write_text(content, encoding="utf-8")
        # Permissions 600 (owner read/write only)
        os.chmod(filepath, stat.S_IRUSR | stat.S_IWUSR)
        action = "created"

    return True, f"{filepath} {action}"


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="FIGMA_TOKEN lifecycle manager")
    parser.add_argument("--save", metavar="TOKEN", help="Persist this token to .env")
    parser.add_argument("--check-only", action="store_true", help="Validate only, do not generate")
    parser.add_argument("--generate", action="store_true", help="Force generation even if token exists")
    args = parser.parse_args()

    # --save mode: just persist a provided token
    if args.save:
        section("💾  Saving token")
        token = args.save.strip()
        print(f"  Token : {mask(token)}")

        print("  Validating before saving...")
        ok, msg, _ = validate_token(token)
        if not ok:
            print(f"  ❌ Invalid token: {msg}")
            print("     Token was not saved.")
            sys.exit(1)
        print(f"  ✅ Valid: {msg}")

        saved, path_msg = save_token_to_env(token)
        if saved:
            print(f"  ✅ Saved: {path_msg}")
            print()
            print("  To activate in the current shell:")
            print(f"  source {ENV_WRITE_TARGET}")
            sys.exit(0)
        else:
            print(f"  ❌ Save failed")
            sys.exit(1)

    # ── Step 1: Look for an existing token ──
    section("🔍  Looking for existing FIGMA_TOKEN")

    token, source = find_token_in_env()
    if token:
        print(f"  ✅ Found in {source}")
        print(f"     Value: {mask(token)}")
    else:
        token, source, _ = find_token_in_files()
        if token:
            print(f"  ✅ Found in {source}")
            print(f"     Value: {mask(token)}")
        else:
            print("  ○  No token found in environment or .env files")
            for f in ENV_FILES_PRIORITY:
                exists = "✓" if Path(f).exists() else "✗"
                print(f"     {exists} {f}")

    # ── Step 2: Validate if found ──
    if token and not args.generate:
        print()
        print("  Validating token...")
        ok, msg, _ = validate_token(token)
        if ok:
            separator()
            print(f"  ✅ Token valid — {msg}")
            separator()
            print()
            print("  Token is ready. To activate in the current shell:")
            print(f"  export FIGMA_TOKEN=$(grep \"^FIGMA_TOKEN=\" {ENV_WRITE_TARGET} 2>/dev/null | head -1 | cut -d= -f2)")
            sys.exit(0)
        else:
            print(f"  ❌ Invalid or expired token: {msg}")
            print("  → A new token must be generated.")

    # ── Step 3: Generate a new token ──
    if args.check_only:
        print()
        print("  --check-only mode: generation disabled.")
        sys.exit(2)

    # ── Step 3a: Check credentials for auto-login ──
    section("🔐  Looking for Figma credentials (FIGMA_USERNAME / FIGMA_PASSWORD)")

    username, password, creds_sources = find_credentials()

    if username and password:
        print(f"  ✅ Username: {username}")
        print(f"     Source  : {creds_sources.get('username', '?')}")
        print(f"  ✅ Password: {mask_password(password)}")
        print(f"     Source  : {creds_sources.get('password', '?')}")
        print()
        print("  Auto-login enabled — credentials will be used to log in.")
        print()
        # Structured output parseable by the agent for automatic login
        print("─" * 55)
        print("FIGMA_AUTO_LOGIN_USERNAME=" + username)
        print("FIGMA_AUTO_LOGIN_PASSWORD=" + password)
        print("─" * 55)
        sys.exit(3)
    else:
        missing = []
        if not username:
            missing.append("FIGMA_USERNAME (or FIGMA_EMAIL)")
        if not password:
            missing.append("FIGMA_PASSWORD")
        print(f"  ○  Credentials not found: {', '.join(missing)}")
        print()
        print("  💡 To enable auto-login, add to your .env.local:")
        print("     FIGMA_USERNAME=your@email.com")
        print("     FIGMA_PASSWORD=your_password")

    # ── Step 3b: Manual login (no credentials — caller handles the browser) ──
    section("🆕  Manual login required")
    print("  ○  No credentials found. The browser will be opened by the calling agent.")
    sys.exit(2)


if __name__ == "__main__":
    main()
