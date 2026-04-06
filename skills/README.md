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

| Skill | Category | Description |
|-------|----------|-------------|
| `a11y-audit` | Accessibility | Audits live pages using Playwright + axe-core. Verifies real contrast, dynamic content, and focus order on deployed pages via sitemap or URL list. |
| `a11y-web` | Accessibility | Audits and fixes RGAA 4.1.2 accessibility issues in any web framework (React, Vue, Svelte, Astro, Angular, Next.js, etc.). Proactive static analysis before deployment. |
| `agent-browser` | Automation | Browser automation CLI for AI agents. Navigate pages, fill forms, click buttons, take screenshots, extract data, handle auth, and test web apps using CDP-based Chrome/Chromium control. |
| `agent-creator` | Config | Guides the creation of Claude Code agents: subagents (hierarchical delegation) and multi-agent swarms (peer-to-peer coordination). Covers frontmatter, system prompt design, triggering examples, and tool/permission configuration. |
| `clean-code` | Code Quality | Applies Robert C. Martin's Clean Code principles to review, refactor, and improve code quality: naming, functions, comments, formatting, error handling, tests, and code smells detection. |
| `e2e-testing` | Testing | Reliable end-to-end test suites: Page Object Model, fixtures, network mocking, mobile/desktop split, locale-agnostic selectors, no hardcoded dates, visual regression, and accessibility testing. |
| `excalidraw` | Documentation | Generates Excalidraw diagrams from natural language descriptions. Supports flowcharts, system architecture, relationship diagrams, and mind maps. Outputs `.excalidraw` files. |
| `figma-generate-personal-token` | Design | Manages the full lifecycle of `FIGMA_TOKEN`: detects existing tokens, validates them via the Figma API, and auto-generates a new one via browser (auto-login with `FIGMA_USERNAME`/`FIGMA_PASSWORD`, or manual fallback). Persists the token to `.env`. |
| `git-commit` | Development | Analyses your diff and generates a standardized Conventional Commits message. Handles staging, type/scope detection, and commit execution. |
| `react-best-practices` | Development | 64 React and Next.js performance rules from Vercel Engineering, covering rendering, re-renders, server-side patterns, bundle optimization, and more. |
| `skill-creator` | Config | Guides the full lifecycle of a skill: draft, eval, iterate, and optimize trigger description. Includes a browser-based reviewer and quantitative benchmarking. |
| `trident-icons` | Design | Searches the @clubmed/trident-icons library (559 icons, 17 categories) by semantic description and generates ready-to-use React import code. Fetches the live catalog automatically. |
| `typescript-advanced-types` | Development | Reference guide for TypeScript's advanced type system: generics, conditional types, mapped types, template literals, utility types, and patterns like type-safe API clients, event emitters, builders, and discriminated unions. |
