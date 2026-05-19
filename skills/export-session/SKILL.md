---
name: export-session
description: Export the current AI coding session to Markdown, JSON, or a beautiful self-contained HTML file — with agent threads, token counts, and tool call badges. Currently supports Claude Code; pluggable for Codex / OpenCode.
argument-hint: "[output-path] [--format markdown|json|html|pdf] [--title '...'] [--provider claude-code] [--include-thinking] [--no-tools] [--no-agents]"
user-invocable: true
allowed-tools: Bash
---

# Export Session

Export the current AI coding session from its provider's transcript files
to a readable format. Agent / skill threads are inlined.
Total tokens and per-thread token costs are shown.

## Arguments

```
ARGUMENTS: $ARGUMENTS
```

Parse from `$ARGUMENTS`:
- **Positional** `[output-path]` — where to write the file (optional; default: `~/<project>-YYYY-MM-DD-HH-MM.<ext>`)
- `--format markdown|json|html|pdf` — output format (default: `markdown`)
- `--title "..."` — document title (default: `"Conversation Export"`)
- `--provider <name>` — provider override (default: auto-detect). Known: `claude-code`.
- `--include-thinking` — include internal thinking blocks (hidden by default)
- `--no-tools` — omit tool call details
- `--no-agents` — omit agent / skill thread sections

---

## Steps

### Step 1 — Run the export script

Use the **Bash** tool to execute `~/.claude/skills/export-session/main.py`
with the parsed arguments mapped to environment variables.

```bash
EXP_OUTPUT="<resolved-output-path-or-empty>" \
EXP_FORMAT="<markdown|json|html|pdf>"        \
EXP_TITLE="<title>"                          \
EXP_PROVIDER="<provider-name-or-empty>"      \
EXP_THINKING="<1-or-0>"                      \
EXP_NO_TOOLS="<1-or-0>"                      \
EXP_NO_AGENTS="<1-or-0>"                     \
EXP_CWD="$(pwd)"                             \
python3 ~/.claude/skills/export-session/main.py
```

Capture stdout. Parse `EXPORT_PATH=`, `PROVIDER=`, `TOKENS_TOTAL=`,
`TOKENS_DETAIL=`, and (optional) `WARNING=` lines from the output.

---

### Step 2 — Report result

After the script completes, tell the user:

```
Exported to: <EXPORT_PATH>
Provider: <PROVIDER>
Tokens: <TOKENS_DETAIL> — <TOKENS_TOTAL> total
```

If there is a `WARNING=` line, display it.

If format is `html`, suggest opening the file:
```
open <EXPORT_PATH>
```

---

## Examples

```
/export-session
/export-session ~/Desktop/my-session.md
/export-session --format html ~/Desktop/session.html
/export-session --format json --no-agents
/export-session --format pdf --title "PRD-014 review"
/export-session --include-thinking --no-tools
/export-session --provider claude-code
```

---

## Adding a new provider

To support another tool (e.g. Codex, OpenCode):

1. Drop a module `~/.claude/skills/export-session/providers/<name>.py`
   subclassing `Provider` from `.base`.
2. Implement `detect(cwd)`, `find_session(cwd)`, `build_turns(...)`,
   `get_metadata(...)` — see `providers/base.py` for the IR schema.
3. Append the class to `ALL_PROVIDERS` in `providers/__init__.py`.

The renderers (`renderers.py`) are provider-agnostic — they consume only
the normalized IR.

---

## Notes

- **PDF**: Requires `weasyprint` (`pip install weasyprint`) or `wkhtmltopdf` on PATH.
  Without either, the HTML file is saved and a fallback message shown.
- **Token counts**: Claude Code provider sums `usage.output_tokens` + `usage.input_tokens`
  from assistant records. Cache-read tokens (`cache_read_input_tokens`) are shown
  separately as they incur reduced cost. Other providers may compute totals differently.
- **Agent threads (Claude Code)**: Resolved from
  `~/.claude/projects/<slug>/<uuid>/subagents/agent-*.jsonl`.
  Each thread shows its own token footprint.
- **Template**: The HTML output reads CSS from
  `~/.claude/skills/export-session/conversation-template.html`.
  Edit that file to customise the visual design.

---

**BEGIN EXPORT**

Parse `$ARGUMENTS`, set environment variables, run the Python script via Bash, then report the result.
