# Plugin development guide

## How plugins work

A plugin is a directory with a `.claude-plugin/plugin.json` manifest and component subdirectories. Claude Code discovers components by scanning default directories (`skills/`, `agents/`, `commands/`, `hooks/`, `.mcp.json`) and any extra paths declared in the manifest.

**A skill lives in the plugin that ships it.** The skill folder sits directly under `plugins/<plugin>/skills/` — no symbolic links, no copies. One skill, one home: the plugin is the unit of ownership, versioning, and review.

```
plugins/clubmed-tracking-data/
├── .claude-plugin/
│   └── plugin.json          ← manifest
├── .mcp.json
└── skills/
    ├── figma-client/
    │   ├── SKILL.md
    │   └── scripts/
    └── tracking-plan/
        └── SKILL.md
```

Top-level `/skills/` only holds **standalone** skills that belong to no plugin (installed one by one with `npx skills add`). When a standalone skill joins a plugin, move it (`git mv skills/<name> plugins/<plugin>/skills/<name>`) — never link it.

Inside a `SKILL.md`, reference bundled files with `${CLAUDE_SKILL_DIR}` (e.g. `python3 ${CLAUDE_SKILL_DIR}/scripts/tool.py`), never with a repo path like `.claude/skills/<name>/…` — it does not exist once the plugin is installed from the marketplace.

## Version bump rule

The marketplace caches plugins by version. **Any time you add, remove, or rename a component, you must bump the version in `plugin.json`** — otherwise users who already installed the plugin keep the stale cached copy and the new component is silently missing.

| Change | Version bump |
|--------|-------------|
| Add / remove a skill or agent | MINOR (e.g. `1.0.0` → `1.1.0`) |
| Add / remove MCP server or hook | MINOR |
| Bug fix inside a skill or hook script | PATCH (e.g. `1.1.0` → `1.1.1`) |
| Breaking change (rename, restructure) | MAJOR (e.g. `1.1.0` → `2.0.0`) |

## Adding a skill to a plugin

**Step 1 — Create the skill inside the plugin** at `plugins/<plugin-name>/skills/<skill-name>/`, using the `skill-creator` skill (or `git mv` an existing standalone skill from `/skills/`).

**Step 2 — List it** in the plugin's table in `plugins/README.md` (and remove its row from `skills/README.md` if it was standalone).

**Step 3 — Register it in `plugin.json`** under the `skills` array:
```json
"skills": [
  "./skills/existing-skill",
  "./skills/<skill-name>"
]
```

**Step 4 — Bump the version** in `plugin.json` (MINOR).

## Adding an agent to a plugin

Agents are auto-discovered from the `agents/` directory — no `agents[]` array needed in `plugin.json` (unlike skills).

**Step 1 — Create the agent inside the plugin** at `plugins/<plugin-name>/agents/<agent-name>.md`, using the `agent-creator` skill.

**Step 2 — Bump the version** in `plugin.json` (MINOR).

If you need to point to a non-default agents directory, declare it explicitly:
```json
"agents": ["./agents", "./agents/specialized"]
```

## Adding MCP servers to a plugin

> **Sync rule — always update the global registry AND README when adding an MCP anywhere.**
>
> Whether the server is declared in a plugin's `.mcp.json` or directly in `mcps/registry.json`, both of the following files must be updated in the same commit:
> - `mcps/registry.json` — add the server entry (name, description, category, auth, command)
> - `mcps/README.md` — add a row in the table (Server · Category · Description · Auth · Install)
> - `README.md` — add a row in the `### MCP Servers` table (Server · Category)
>
> Quick check before committing:
> ```bash
> # List all server names in registry vs README — they must match
> python3 -c "import json; r=json.load(open('mcps/registry.json')); [print(s['name']) for s in r['servers']]"
> grep '^\|' mcps/README.md | awk -F'|' '{print $2}' | xargs
> ```



Declare servers inline (simple case, fewer than 3 servers) or via an external `.mcp.json` file (recommended when there are multiple servers or env vars).

**Inline** in `plugin.json`:
```json
"mcpServers": {
  "my-server": {
    "command": "node",
    "args": ["${CLAUDE_PLUGIN_ROOT}/servers/my-server/index.js"],
    "env": {
      "API_TOKEN": "${API_TOKEN}"
    }
  }
}
```

**External file** — create `plugins/<plugin-name>/.mcp.json` and reference it:
```json
"mcpServers": "./.mcp.json"
```

The `.mcp.json` format:
```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/servers/my-server/index.js"],
      "env": { "API_TOKEN": "${API_TOKEN}" }
    }
  }
}
```

Use `${CLAUDE_PLUGIN_ROOT}` to reference files inside the plugin — this variable is resolved at runtime regardless of where the plugin was installed.

**Bump the version** after adding any MCP server (MINOR).

## Adding hooks to a plugin

Declare hooks inline (simple case) or via an external `hooks/hooks.json` file (recommended for complex setups).

**Inline** in `plugin.json`:
```json
"hooks": {
  "PreToolUse": [
    {
      "matcher": "Write|Edit",
      "hooks": [
        {
          "type": "command",
          "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate.sh",
          "timeout": 30
        }
      ]
    }
  ]
}
```

**External file** — create `plugins/<plugin-name>/hooks/hooks.json` and reference it:
```json
"hooks": "./hooks/hooks.json"
```

Supported hook events: `PreToolUse`, `PostToolUse`, `Stop`, `SubagentStop`, `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `PreCompact`, `Notification`.

Use `${CLAUDE_PLUGIN_ROOT}` in hook commands — same as MCP servers.

**Bump the version** after adding or changing hooks (MINOR / PATCH depending on impact).

## Nested plugins

Plugin composition (a plugin referencing another plugin via a `plugins[]` field) is **not supported**. Each plugin is standalone. If two plugins need the same capability, keep it in the plugin that owns the domain and make the other plugin's skill name it as a prerequisite ("requires the `clubmed-github` plugin") rather than duplicating or linking it.

## Checklist for any plugin change

- [ ] Skill or agent lives inside `plugins/<plugin>/` (no symlink)
- [ ] Bundled files referenced through `${CLAUDE_SKILL_DIR}` / `${CLAUDE_PLUGIN_ROOT}`
- [ ] Entry added / updated in `plugin.json`
- [ ] Version bumped in `plugin.json` **and** in `.claude-plugin/marketplace.json`
- [ ] Commit with `git-commit` skill (conventional commit)
