# Plugin development guide

## How plugins work

A plugin is a directory with a `.claude-plugin/plugin.json` manifest and component subdirectories. Claude Code discovers components by scanning default directories (`skills/`, `agents/`, `commands/`, `hooks/`, `.mcp.json`) and any extra paths declared in the manifest.

Components in this repo are **shared globally** — skills live in `/skills/`, agents in `/agents/`. Each plugin references them via **symbolic links** rather than copies, so a fix to a skill propagates to every plugin that includes it.

```
plugins/clubmed-frontend/
├── .claude-plugin/
│   └── plugin.json          ← manifest
└── skills/
    ├── react-best-practices  → ../../../skills/react-best-practices
    ├── typescript-expert     → ../../../skills/typescript-expert
    └── jira-fetch            → ../../../skills/jira-fetch
```

## Version bump rule

The marketplace caches plugins by version. **Any time you add, remove, or rename a component, you must bump the version in `plugin.json`** — otherwise users who already installed the plugin keep the stale cached copy and the new component is silently missing.

| Change | Version bump |
|--------|-------------|
| Add / remove a skill or agent | MINOR (e.g. `1.0.0` → `1.1.0`) |
| Add / remove MCP server or hook | MINOR |
| Bug fix inside a skill or hook script | PATCH (e.g. `1.1.0` → `1.1.1`) |
| Breaking change (rename, restructure) | MAJOR (e.g. `1.1.0` → `2.0.0`) |

## Adding a skill to a plugin

**Step 1 — Create the global skill** (if it does not already exist):
Follow the root `AGENTS.md` workflow using the `skill-creator` skill.

**Step 2 — Create the symlink** in the plugin's `skills/` directory:
```bash
ln -s ../../../skills/<skill-name> plugins/<plugin-name>/skills/<skill-name>
```

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

**Step 1 — Create the global agent** (if it does not exist):
Follow the root `AGENTS.md` workflow using the `agent-creator` skill.

**Step 2 — Create the symlink** in the plugin's `agents/` directory (create the directory if needed):
```bash
mkdir -p plugins/<plugin-name>/agents
ln -s ../../../agents/<agent-name>.md plugins/<plugin-name>/agents/<agent-name>.md
```

**Step 3 — Bump the version** in `plugin.json` (MINOR).

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

Plugin composition (a plugin referencing another plugin via a `plugins[]` field) is **not supported**. Each plugin is standalone. Share components by making them global skills or agents and symlinking from multiple plugins.

## Checklist for any plugin change

- [ ] Global skill or agent exists in `/skills/` or `/agents/`
- [ ] Symlink created in the plugin's `skills/` or `agents/` directory
- [ ] Entry added / updated in `plugin.json`
- [ ] Version bumped in `plugin.json`
- [ ] Commit with `git-commit` skill (conventional commit)
