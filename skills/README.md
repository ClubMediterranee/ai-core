# Skills

A skill is a reusable prompt module that Claude Code can invoke to perform a specific task.

| Name | Description | Model |
|------|-------------|-------|
| **git-commit** | Execute git commit with conventional commit message analysis, intelligent staging, and message generation. Auto-detects type/scope from changes, generates conventional commit messages from diff, and supports interactive overrides. | haiku |
| **excalidraw** | Generate Excalidraw diagrams from natural language descriptions. Supports flowcharts, relationship diagrams, mind maps, and system architecture diagrams. Outputs `.excalidraw` JSON files. | sonnet |
| **skill-creator** | Create new skills, modify and improve existing skills, and measure skill performance. Supports evals, benchmarking with variance analysis, and description optimization for triggering accuracy. | — |
| **a11y-web** | Audit and fix RGAA 4.1.2 accessibility issues in any HTML-outputting framework (React, Vue, Svelte, Astro, Angular, plain HTML, ERB, etc.). Activates proactively on any component/template work. Covers static analysis: images, colors, tables, links, mandatory elements, structure, forms, navigation landmarks. | sonnet |
| **a11y-audit** | Runtime RGAA 4.1.2 audit on live pages via Playwright + axe-core. Takes a sitemap URL or URL list, renders each page in Chromium, runs axe-core (WCAG 2.1 AA) and custom DOM checks, produces a consolidated report with per-page violations and global summary. Covers contrast ratios and rendered output that static analysis cannot reach. Requires Playwright + axe-core (see `scripts/setup.sh`). | sonnet |