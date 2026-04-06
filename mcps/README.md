# MCP Servers

A curated list of Model Context Protocol servers recommended by the Club Med AI Guild.

## Available Servers

> Run commands in your project directory (project-scoped) or add `-s user` for global install.

| Server | Category | Description | Auth | Install |
|--------|----------|-------------|:----:|---------|
| `context7` | Development | Up-to-date docs for any library, fetched live. Prevents hallucinated APIs. | ✅ _(optional key for higher rate limits)_ | `claude mcp add context7 -- npx -y @upstash/context7-mcp@latest` |
| `figma` | Design | Access Figma files and design tokens. Implement designs in one shot. | 🔑 OAuth | `claude mcp add --transport http figma https://mcp.figma.com/mcp` |
| `playwright` | Testing / Automation | Browser automation: navigate, click, screenshot, extract data. | ✅ | `claude mcp add playwright -- npx -y @playwright/mcp@latest` |
| `trident-icons` | Design | Search Club Med Trident icons by semantic description. | ✅ | 🚧 In progress |

## Contributing

To add a new MCP server, open a PR with:
- A new entry in [`registry.json`](./registry.json)
- The corresponding row in this README

Prefer servers that are actively maintained, have an npm package or stable HTTP endpoint, and bring clear value to the Guild's workflows.
