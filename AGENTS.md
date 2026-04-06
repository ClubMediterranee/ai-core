## Language

All skills, agents, and MCP documentation must be written in English.

## Adding a skill

Use the `skill-creator` skill — it handles the full lifecycle and enforces the correct frontmatter. Verify all frontmatter fields are properly filled before writing the file.

After creating a skill:
1. Update `skills/README.md` — add a row with name, category, and description (keep rows sorted alphabetically by name)
2. Update `README.md` — add the skill in the relevant category row, update the count

## Adding an agent

Use the `agent-creator` skill — it covers agent structure, frontmatter fields, and triggering conditions. Verify all frontmatter fields are properly filled before writing the file.

After creating an agent:
1. Update `agents/README.md` — add a row with name and description (keep rows sorted alphabetically by name)
2. Update `README.md` — add the agent in the relevant section, update the count

## Committing changes

Always use the `git-commit` skill to create commits. It analyzes the diff, detects type and scope, and generates a Conventional Commits message. Never commit manually without it.

## Adding an MCP server

1. Update `mcps/README.md` — add a row with server name, category, description, auth, and install command (keep rows sorted alphabetically by name)
2. Update `mcps/registry.json` — add the server entry with its config
3. Update `README.md` — add the server in the MCP table
