# export-session — internals

Contributor-facing notes for the skill. End users only need [`SKILL.md`](SKILL.md).

## Layout

```
export-session/
├── SKILL.md                        # user-facing: slash command spec
├── README.md                       # this file
├── conversation-template.html      # source of the HTML output CSS
├── main.py                         # entry point — reads EXP_* env vars
├── renderers.py                    # markdown / json / html / pdf — provider-agnostic
├── providers/
│   ├── __init__.py                 # ALL_PROVIDERS list + detect_provider()
│   ├── base.py                     # Provider ABC + IR schema docstring
│   └── claude_code.py              # Claude Code session parser
└── tests/                          # stdlib unittest, no extra deps
    ├── _path.py                    # sys.path bootstrap so tests can import
    ├── test_renderers.py
    ├── test_provider_claude_code.py
    └── test_provider_registry.py
```

## How it runs

1. The user types `/export-session [args]`. Claude (via `SKILL.md`) parses `$ARGUMENTS`,
   sets `EXP_OUTPUT` / `EXP_FORMAT` / `EXP_TITLE` / `EXP_PROVIDER` / `EXP_THINKING` /
   `EXP_NO_TOOLS` / `EXP_NO_AGENTS` / `EXP_CWD`, then runs
   `python3 ~/.claude/skills/export-session/main.py`.
2. `main.py` asks `providers.detect_provider(cwd, override)` for a `Provider` instance.
3. The provider returns a `session` handle, then a normalized list of `Turn` dicts (the IR).
4. The chosen renderer in `renderers.py` consumes the IR and writes the file.
5. `main.py` prints `EXPORT_PATH=`, `PROVIDER=`, `TOKENS_TOTAL=`, `TOKENS_DETAIL=`,
   and optionally `WARNING=` on stdout. Claude parses those lines and reports back.

The renderers **never** see raw provider records — they only consume the IR.
This is the boundary that makes new providers safe to drop in.

## The intermediate representation (IR)

Defined in [`providers/base.py`](providers/base.py).

```python
Turn = {
    'role':      'human' | 'assistant',
    'text':      str,
    'ts':        str,              # 'HH:MM:SS'
    'tools':     [str],            # assistant only
    'thinking':  str | None,
    'agents':    [Agent],          # nested threads
    'usage':     {'input', 'output', 'cache_create', 'cache_read', 'total'},
}

Agent = {
    'agent_id':    str,
    'agent_type':  str,
    'description': str,
    'turns':       [Turn],         # recursive
    'usage':       {...},
}

Metadata = {
    'project_name':  str,
    'project_path':  str,
    'git_branch':    str,
    'session_id':    str,
    'export_date':   'YYYY-MM-DD HH:MM UTC',
    'message_count': int,          # human turns only
    'total_usage':   {...},
}
```

Providers that don't have a concept of nested threads return `agents: []`.
Providers without token accounting return zeros in `usage`.

## Adding a provider

1. Create `providers/<name>.py` subclassing `Provider`:

   ```python
   from .base import Provider

   class CodexProvider(Provider):
       name = 'codex'

       @classmethod
       def detect(cls, cwd: str) -> bool:
           # Cheap on-disk check
           ...

       def find_session(self, cwd: str):
           # Return a handle dict, or None
           ...

       def build_turns(self, session, *, include_thinking,
                       no_tools, no_agents):
           # Parse session into list[Turn]
           ...

       def get_metadata(self, session, turns):
           # Return Metadata dict
           ...
   ```

2. Register it in `providers/__init__.py`:

   ```python
   from .codex import CodexProvider
   ALL_PROVIDERS = [ClaudeCodeProvider, CodexProvider]
   ```

   Order matters — `detect_provider` returns the first match. Put more specific
   providers first.

3. Add tests under `tests/test_provider_<name>.py`. Mirror the structure of
   `test_provider_claude_code.py`: pure-function tests, parser tests with
   inline fixtures, and `detect`/`find_session` tests using a temp directory.

4. Update `SKILL.md`'s `--provider` argument doc and the table in `skills/README.md`.

## Known session formats (research notes)

| Tool | Path | Format | Notes |
|---|---|---|---|
| Claude Code | `~/.claude/projects/<cwd-slug>/*.jsonl` | JSONL | `type: user\|assistant\|...`, `message.content` block list, sub-agents under `<uuid>/subagents/agent-*.jsonl` |
| Codex CLI | `~/.codex/sessions/<date>/rollout-<id>.jsonl` | JSONL | `type: session_meta\|response_item`, `payload` carries the actual content |
| OpenCode | — | — | Not yet investigated on this machine |

## Running tests

```bash
cd skills/export-session
python3 -m unittest discover -s tests -t .
```

No external dependencies. Tests cover:
- XSS regression on `text_to_html` (4 dedicated cases + 1 end-to-end via `render_html`).
- The `toolUseResult`-as-string regression in the Claude provider.
- IR schema produced by `build_turns` / `get_metadata`.
- Registry behavior: auto-detect, explicit override, unknown name, no-match.
- `Provider` ABC enforces abstract methods.

Add new tests for every new provider and every renderer change.

## Security model

- The exported HTML opens under `file://` in a browser — a successful XSS there
  can exfiltrate transcript content (often containing tokens, paths, internal URLs).
- `renderers._text_to_html` is the only path where attacker-influenced message
  text reaches HTML. It escapes the prose first (`html.escape`) and only then
  re-introduces `<code>` wrappers around backtick-spans. The XSS regression
  tests pin this ordering — do not refactor it without re-running them.
- Code fence content, agent descriptions, tool names, project/branch/session
  fields all flow through `e()` (= `html.escape(..., quote=True)`).
- Anything new being injected into the HTML output **must** pass through `e()`.

## Env var reference

| Var | Required | Default | Purpose |
|---|---|---|---|
| `EXP_OUTPUT` | no | `~/<project>-<stamp>.<ext>` | Output file path |
| `EXP_FORMAT` | no | `markdown` | `markdown`\|`json`\|`html`\|`pdf` |
| `EXP_TITLE` | no | `Conversation Export` | Document title |
| `EXP_PROVIDER` | no | auto-detect | Provider name (`claude-code`, ...) |
| `EXP_THINKING` | no | `0` | `1` to include thinking blocks |
| `EXP_NO_TOOLS` | no | `0` | `1` to drop tool call details |
| `EXP_NO_AGENTS` | no | `0` | `1` to drop nested agent threads |
| `EXP_CWD` | no | `$PWD` | Working directory used for session lookup |
