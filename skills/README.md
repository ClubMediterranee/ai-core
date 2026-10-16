# Skills

A skill is a reusable prompt module that Claude Code can invoke to perform a specific task.

## Installation

Install Clubmed skills from this repository using the [`skills` CLI](https://github.com/anthropics/claude-code/pkgs/npm/skills):

```bash
npx skills add https://github.com/ClubMediterranee/ai-core
```

The command launches an interactive selector : pick the skills you want to install, skip the ones you don't. 
Skills are added to your Claude Code configuration and become available immediately as slash commands.

## Available Skills

Standalone skills only. Skills that ship inside a plugin live in that plugin — see [Plugins](../plugins/README.md).

| Skill | Category | Description |
|-------|----------|-------------|
| `a11y-audit` | Accessibility | Audits live pages using Playwright + axe-core. Verifies real contrast, dynamic content, and focus order on deployed pages via sitemap or URL list. |
| `a11y-web` | Accessibility | Audits and fixes RGAA 4.1.2 accessibility issues in any web framework (React, Vue, Svelte, Astro, Angular, Next.js, etc.). Proactive static analysis before deployment. |
| `agent-creator` | Config | Guides the creation of Claude Code agents: subagents (hierarchical delegation) and multi-agent swarms (peer-to-peer coordination). Covers frontmatter, system prompt design, triggering examples, and tool/permission configuration. |
| `excalidraw` | Documentation | Generates Excalidraw diagrams from natural language descriptions. Supports flowcharts, system architecture, relationship diagrams, and mind maps. Outputs `.excalidraw` files. |
| `jira-fetch` | Project Management | Fetches a Jira ticket and writes its full structured content to `.jira/<KEY>/`. Extracts all standard fields, all custom fields, attachments, and linked assets (Figma URLs, images, files). Supports MCP and CLI methods. |
| `skill-creator` | Config | Guides the full lifecycle of a skill: draft, eval, iterate, and optimize trigger description. Includes a browser-based reviewer and quantitative benchmarking. |
| `trident-icons` | Design | Searches the @clubmed/trident-icons library (559 icons, 17 categories) by semantic description and generates ready-to-use React import code. Fetches the live catalog automatically. |
| `trident-ui-install` | Design | Automates the full setup of Trident UI in Vite and Next.js projects: detects project type and package manager, installs dependencies, configures Tailwind 4, creates components.json, and installs the design system (157 CSS variables, 25+ animations) via shadcn CLI. |
