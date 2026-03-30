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

| Skill | Description |
|-------|-------------|
| `git-commit` | Analyses your diff and generates a standardized Conventional Commits message. Handles staging, type/scope detection, and commit execution. |
| `excalidraw` | Generates Excalidraw diagrams from natural language descriptions. Supports flowcharts, system architecture, relationship diagrams, and mind maps. Outputs `.excalidraw` files. |
| `skill-creator` | Guides the full lifecycle of a skill: draft, eval, iterate, and optimize trigger description. Includes a browser-based reviewer and quantitative benchmarking. |
| `react-best-practices` | 64 React and Next.js performance rules from Vercel Engineering, covering rendering, re-renders, server-side patterns, bundle optimization, and more. |
| `clean-code` | Applies Robert C. Martin's Clean Code principles to review, refactor, and improve code quality: naming, functions, comments, formatting, error handling, tests, and code smells detection. |

