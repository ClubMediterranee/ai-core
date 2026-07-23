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
| `api-patterns` | API | API design principles and decision-making. REST vs GraphQL vs tRPC selection, response formats, versioning, pagination. |
| `api-security-best-practices` | API | Implement secure API design patterns including authentication, authorization, input validation, rate limiting, and protection against common API vulnerabilities. |
| `async-python-patterns` | Python | Comprehensive guidance for implementing asynchronous Python applications using asyncio, concurrent programming patterns, and async/await. |
| `backend-security-coder` | Security | Expert in secure backend coding practices specializing in input validation, authentication, and API security. |
| `clean-code` | Code Quality | Applies Robert C. Martin's Clean Code principles to review, refactor, and improve code quality: naming, functions, comments, formatting, error handling, tests, and code smells detection. |
| `container-security-hardening` | Infrastructure | Harden Docker/container images and runtime deployments with secure base images, non-root users, CVE scanning, SBOM/signing, seccomp/AppArmor, and Kubernetes pod security controls. |
| `database-migration` | Database | Master database schema and data migrations across ORMs (Sequelize, TypeORM, Prisma), including rollback strategies and zero-downtime deployments. |
| `django-pro` | Python | Master Django 5.x with async views, DRF, Celery, and Django Channels. Build scalable web applications with proper architecture, testing, and deployment. |
| `e2e-test-generator` | Testing | Orchestrates robust Playwright/TypeScript E2E test generation for Club Med B2C sites via 5 scoped subagents: ground selectors on the live site (flow-map contract), plan scenarios, author, prove non-flakiness by repeated cross-browser runs, and review with independent critics. |
| `error-handling-patterns` | Development | Build resilient applications with robust error handling strategies that gracefully handle failures and provide excellent debugging experiences. |
| `excalidraw` | Documentation | Generates Excalidraw diagrams from natural language descriptions. Supports flowcharts, system architecture, relationship diagrams, and mind maps. Outputs `.excalidraw` files. |
| `fastapi-pro` | Python | Build high-performance async APIs with FastAPI, SQLAlchemy 2.0, and Pydantic V2. Master microservices, WebSockets, and modern Python async patterns. |
| `figma-authentication` | Design | Manages the complete lifecycle of `FIGMA_TOKEN`: detects, validates, auto-generates via browser (auto-login or manual fallback), and persists to `.claude/settings.local.json`. Token is auto-injected by Claude Code — no export needed. |
| `figma-client` | Design | Figma REST client — fetches node metadata, auto-layout with css_hints, INSTANCE hierarchy with variants and visual signatures, texts, image fills, icon SVGs, hidden layers, carousel signals, list item shapes, and prototype interactions. |
| `git-commit` | Development | Analyses your diff and generates a standardized Conventional Commits message. Handles staging, type/scope detection, and commit execution. |
| `git-push-branch` | Development | Pushes the current branch under a speaking name derived from the last conventional commit (`<type>/<scope>-<description>`). Refuses to push the default branch — carves a feature branch first. Sets upstream with `-u`. Hidden from the command menu. |
| `git-rebase-branch` | Development | Rebases the current branch onto the latest default branch (detected dynamically from `origin/HEAD` — main, develop, etc.), attempting safe automatic conflict resolution and asking to arbitrate genuine conflicts. Never rebases the default branch — carves a feature branch first. Hidden from the command menu. |
| `github-authentication` | Development | Manages the complete lifecycle of `GITHUB_TOKEN`: detects, validates, auto-generates a classic PAT via browser (manual login primary, best-effort auto-login), and persists to the user-global `~/.claude/settings.json` — generated once, valid in every repository, outside every git work tree. Unblocks the GitHub MCP server. Uses the Playwright MCP. Hidden from the command menu. |
| `github-cancel` | Development | Abandons the work in progress: closes its pull request (or turns it into a draft), drops the local branch, and returns to a clean base. Always confirms first, naming what is lost. Never deletes the remote branch, so a closed PR stays reopenable. Refuses on merged PRs. |
| `github-my-prs` | Development | Shows where you stand: current work, your pull requests with actionable status, review comments inline, and the way back into work you left behind — resuming restores the branch without you ever naming it. |
| `github-new` | Development | Moves on to something else: returns to a clean, up-to-date base branch. Asks what to do with anything unpublished first, since work left only on a local branch cannot be found again through `github-my-prs`. Never stashes, never deletes. |
| `github-open-pr` | Development | Opens a GitHub pull request for the current branch via the GitHub MCP. Derives owner/repo from the remote, current branch as head, default branch as base, and builds title/body from the commits. Falls back to `github-authentication` if the token is missing. Hidden from the command menu. |
| `github-publish` | Development | End-to-end "send my work to GitHub": commits as a Conventional Commit, then opens a PR for new work or adds to the PR already open for it, and asks whether to keep going or move on. Composes `git-commit`, `git-rebase-branch`, `git-push-branch`, and `github-open-pr`. Never pushes to main. |
| `github-update` | Development | Brings you up to date, choosing the method from your situation: pull on a clean base, rebase for work never sent, GitHub-side update for work already sent so published history is never rewritten. Detects a merged PR and offers a return to a clean base. |
| `jira-fetch` | Project Management | Fetches a Jira ticket and writes its full structured content to `.jira/<KEY>/`. Extracts all standard fields, all custom fields, attachments, and linked assets (Figma URLs, images, files). Supports MCP and CLI methods. |
| `graphql` | API | GraphQL schema design, resolvers, DataLoader for N+1 prevention, federation, and client integration. Covers security controls against malicious queries. |
| `java-pro` | Java | Master Java 21+ with modern features like virtual threads, pattern matching, and Spring Boot 3.x. Expert in the latest Java ecosystem including GraalVM, Project Loom, and cloud-native patterns. |
| `k8s-security-policies` | Infrastructure | Comprehensive guide for implementing NetworkPolicy, PodSecurityPolicy, RBAC, and Pod Security Standards in Kubernetes. |
| `nextjs-best-practices` | React / Next.js | Next.js App Router principles. Server Components, data fetching, routing patterns. |
| `nodejs-best-practices` | Node.js | Node.js development principles and decision-making. Framework selection, async patterns, security, and architecture. |
| `observability-patterns` | Observability | Build production-ready monitoring, logging, and tracing systems. Implements comprehensive observability strategies, SLI/SLO management, and incident response workflows. |
| `postgresql-optimization` | Database | PostgreSQL database optimization workflow for query tuning, indexing strategies, performance analysis, and production database management. |
| `prisma-expert` | Database | Expert in Prisma ORM with deep knowledge of schema design, migrations, query optimization, relations modeling, and database operations. |
| `react-best-practices` | React / Next.js | 64 React and Next.js performance rules from Vercel Engineering, covering rendering, re-renders, server-side patterns, bundle optimization, and more. |
| `react-component-performance` | React / Next.js | Diagnose slow React components and suggest targeted performance fixes. |
| `react-patterns` | React / Next.js | Modern React patterns and principles. Hooks, composition, performance, TypeScript best practices. |
| `security-scanning-security-hardening` | Security | Coordinate multi-layer security scanning and hardening across application, infrastructure, and compliance controls. |
| `security-scanning-security-sast` | Security | Static Application Security Testing (SAST) for code vulnerability analysis across multiple languages and frameworks. |
| `prd` | Product | Guides a PM through writing a PRD from a validated brief. Sequential steps (scope, journeys, FUNCs, ACs, metrics, complexity) with step gates, challenge pass, advanced elicitation, and a 12-check quality gate before saving. |
| `spec` | Product | Generates developer-ready specs from a PRD. Reads docs/specs/prd/, cross-references DRDs, and produces structured markdown specs with user stories, business rules, Figma links, feature flags, a live-resolved §8 Data Contract (real endpoints, field paths, per-entry confidence, points to clarify, Developer Handoff) resolved via the clubmed_api MCP, and §9 standard-Gherkin acceptance tests traceable to FUNC/BR/ERR. |
| `skill-creator` | Config | Guides the full lifecycle of a skill: draft, eval, iterate, and optimize trigger description. Includes a browser-based reviewer and quantitative benchmarking. |
| `terraform-specialist` | Infrastructure | Expert Terraform/OpenTofu specialist mastering advanced IaC automation, state management, and enterprise infrastructure patterns. |
| `testing-patterns` | Testing | Jest testing patterns, factory functions, mocking strategies, and TDD workflow. |
| `tracking-plan` | Data | GA4 tracking-plan engine. From a Figma link and/or a URL, infers the trackable moments (clicks, impressions, ecommerce, page views) and produces a validated, tool-agnostic `plan.json` inspired by the existing Club Med plan. Rendering and publishing are separate skills that consume the plan. |
| `trident-icons` | Design | Searches the @clubmed/trident-icons library (559 icons, 17 categories) by semantic description and generates ready-to-use React import code. Fetches the live catalog automatically. |
| `trident-ui-install` | Design | Automates the full setup of Trident UI in Vite and Next.js projects: detects project type and package manager, installs dependencies, configures Tailwind 4, creates components.json, and installs the design system (157 CSS variables, 25+ animations) via shadcn CLI. |
| `typescript-advanced-types` | TypeScript | Reference guide for TypeScript's advanced type system: generics, conditional types, mapped types, template literals, utility types, and patterns like type-safe API clients, event emitters, builders, and discriminated unions. |
| `typescript-expert` | TypeScript | TypeScript and JavaScript expert with deep knowledge of type-level programming, performance optimization, monorepo management, migration strategies, and modern tooling. |
