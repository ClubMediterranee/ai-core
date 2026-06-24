# Plugins

A plugin is a curated collection of skills bundled for a specific role or stack. Instead of installing skills one by one, you install a plugin and get everything your team needs in one command.

## Installation

**Step 1 — Register the Club Med marketplace** (once globally, on your machine):

```bash
claude plugin marketplace add ClubMediterranee/ai-core
```

**Step 2 — Install the plugin for your project** (per project, scoped to the repo):

```bash
claude plugin install clubmed-frontend@clubmed --scope project        # React / Next.js / TypeScript
claude plugin install clubmed-backend-node@clubmed --scope project    # Node.js / API / PostgreSQL
claude plugin install clubmed-backend-python@clubmed --scope project  # Django / FastAPI / Python
claude plugin install clubmed-backend-java@clubmed --scope project    # Java 21+ / Spring Boot
claude plugin install clubmed-infra@clubmed --scope project           # Terraform / Kubernetes / Security
claude plugin install clubmed-data@clubmed --scope project            # GA4 tracking plans / analytics
claude plugin install clubmed-product@clubmed --scope project         # Spec generation / PRD / Product
```

Skills become available immediately as slash commands in Claude Code.

## Updating

First refresh the marketplace to pull the latest plugin definitions:

```bash
claude plugin marketplace update
```

Then update each installed plugin:

```bash
claude plugin update clubmed-frontend@clubmed --scope project
claude plugin update clubmed-backend-node@clubmed --scope project
claude plugin update clubmed-backend-python@clubmed --scope project
claude plugin update clubmed-backend-java@clubmed --scope project
claude plugin update clubmed-infra@clubmed --scope project
claude plugin update clubmed-data@clubmed --scope project
claude plugin update clubmed-product@clubmed --scope project
```

---

## Available Plugins

### `clubmed-frontend` — Club Med Frontend

> Skills for frontend developers: React, Next.js, GraphQL, TypeScript, testing, and design tools.

**Keywords:** `react` · `nextjs` · `graphql` · `typescript` · `testing` · `figma` · `design`

| Skill | Description |
|-------|-------------|
| `react-best-practices` | 64 React and Next.js performance rules from Vercel Engineering — rendering, re-renders, server-side patterns, bundle optimization. |
| `react-patterns` | Modern React patterns: hooks, composition, context, lazy loading, and component architecture. |
| `react-component-performance` | Diagnose and fix slow React components: memoization, virtualization, code splitting, profiling. |
| `nextjs-best-practices` | Next.js App Router principles — Server Components, data fetching, routing patterns, and caching. |
| `graphql` | GraphQL schema design, resolver patterns, query security (depth/complexity limits), and client-side best practices. |
| `typescript-expert` | TypeScript and JavaScript deep expertise: type-level programming, monorepo management, migration strategies, and modern tooling. |
| `typescript-advanced-types` | Advanced TypeScript type system: generics, conditional types, mapped types, template literals, and utility types. |
| `testing-patterns` | Jest testing patterns, factory functions, mocking strategies, and TDD red-green-refactor workflow. |
| `clean-code` | Robert C. Martin's Clean Code principles: naming, functions, formatting, error handling, and code smells. |
| `excalidraw` | Generates Excalidraw diagrams from natural language — flowcharts, system architecture, mind maps. |
| `figma-generate-personal-token` | Manages `FIGMA_TOKEN` lifecycle: detect, validate, auto-generate, and persist. |
| `jira-fetch` | Fetches a Jira ticket and writes its full structured content to `.jira/<KEY>/`. Extracts all fields, custom fields, attachments, and Figma URLs. |

---

### `clubmed-backend-node` — Club Med Backend Node.js

> Skills for Node.js backend developers: API design, security, databases, observability, and testing.

**Keywords:** `nodejs` · `api` · `security` · `postgresql` · `prisma` · `observability` · `testing`

| Skill | Description |
|-------|-------------|
| `nodejs-best-practices` | Node.js architecture principles: framework selection, async patterns, security, and project structure. |
| `api-patterns` | REST vs GraphQL vs tRPC selection, response formats, versioning, pagination, and API design decisions. |
| `api-security-best-practices` | Secure API design: authentication, authorization, input validation, rate limiting, and OWASP API top 10. |
| `backend-security-coder` | Secure backend coding: input validation, authentication, session management, and injection prevention. |
| `postgresql-optimization` | PostgreSQL query tuning, indexing strategies, EXPLAIN ANALYZE, connection pooling, and production management. |
| `prisma-expert` | Prisma ORM: schema design, migrations, query optimization, relations modeling, and raw queries. |
| `database-migration` | Schema and data migrations across ORMs (Sequelize, TypeORM, Prisma) with rollback and zero-downtime strategies. |
| `error-handling-patterns` | Resilient error handling: structured errors, retries, circuit breakers, and debugging experiences. |
| `observability-patterns` | Production-ready monitoring, logging, tracing, SLI/SLO management, and incident response. |
| `testing-patterns` | Jest testing patterns, factory functions, mocking strategies, and TDD workflow. |
| `clean-code` | Robert C. Martin's Clean Code principles applied to backend code. |
| `excalidraw` | Generates Excalidraw diagrams from natural language descriptions. |

---

### `clubmed-backend-python` — Club Med Backend Python

> Skills for Python backend developers: Django, FastAPI, async patterns, API design, security, and databases.

**Keywords:** `python` · `django` · `fastapi` · `async` · `api` · `security` · `postgresql`

| Skill | Description |
|-------|-------------|
| `django-pro` | Django 5.x: async views, DRF, Celery, Django Channels, scalable architecture, testing, and deployment. |
| `fastapi-pro` | FastAPI with SQLAlchemy 2.0 and Pydantic V2: microservices, WebSockets, and async patterns. |
| `async-python-patterns` | Python asyncio, concurrent programming, and async/await for high-performance non-blocking systems. |
| `api-patterns` | REST vs GraphQL vs tRPC selection, response formats, versioning, pagination, and API design decisions. |
| `api-security-best-practices` | Secure API design: authentication, authorization, input validation, rate limiting, and OWASP API top 10. |
| `backend-security-coder` | Secure backend coding: input validation, authentication, session management, and injection prevention. |
| `postgresql-optimization` | PostgreSQL query tuning, indexing strategies, EXPLAIN ANALYZE, connection pooling, and production management. |
| `database-migration` | Schema and data migrations with rollback and zero-downtime strategies. |
| `error-handling-patterns` | Resilient error handling: structured errors, retries, circuit breakers, and debugging experiences. |
| `observability-patterns` | Production-ready monitoring, logging, tracing, SLI/SLO management, and incident response. |
| `clean-code` | Robert C. Martin's Clean Code principles applied to Python code. |
| `excalidraw` | Generates Excalidraw diagrams from natural language descriptions. |

---

### `clubmed-backend-java` — Club Med Backend Java

> Skills for Java backend developers: Java 21+, Spring Boot, API design, security, and databases.

**Keywords:** `java` · `spring-boot` · `api` · `security` · `postgresql` · `observability`

| Skill | Description |
|-------|-------------|
| `java-pro` | Java 21+ with virtual threads, pattern matching, and Spring Boot 3.x. GraalVM, Project Loom, and cloud-native patterns. |
| `api-patterns` | REST vs GraphQL vs tRPC selection, response formats, versioning, pagination, and API design decisions. |
| `api-security-best-practices` | Secure API design: authentication, authorization, input validation, rate limiting, and OWASP API top 10. |
| `backend-security-coder` | Secure backend coding: input validation, authentication, session management, and injection prevention. |
| `postgresql-optimization` | PostgreSQL query tuning, indexing strategies, EXPLAIN ANALYZE, connection pooling, and production management. |
| `database-migration` | Schema and data migrations with rollback and zero-downtime strategies. |
| `error-handling-patterns` | Resilient error handling: structured errors, retries, circuit breakers, and debugging experiences. |
| `observability-patterns` | Production-ready monitoring, logging, tracing, SLI/SLO management, and incident response. |
| `clean-code` | Robert C. Martin's Clean Code principles applied to Java code. |
| `excalidraw` | Generates Excalidraw diagrams from natural language descriptions. |

---

### `clubmed-infra` — Club Med Infrastructure

> Skills for infrastructure and platform engineers: Terraform, Kubernetes, container security, and security scanning.

**Keywords:** `terraform` · `kubernetes` · `docker` · `security` · `observability` · `iac`

| Skill | Description |
|-------|-------------|
| `terraform-specialist` | Advanced Terraform/OpenTofu: state management, modules, workspaces, CI/CD integration, and enterprise IaC patterns. |
| `container-security-hardening` | Docker/container hardening: secure base images, non-root users, CVE scanning, SBOM, seccomp, and AppArmor. |
| `k8s-security-policies` | Kubernetes security: NetworkPolicy, RBAC, PodSecurityPolicy, Pod Security Standards, and admission controllers. |
| `security-scanning-security-hardening` | Multi-layer security hardening across application, infrastructure, and compliance controls. |
| `security-scanning-security-sast` | Static Application Security Testing (SAST) for vulnerability analysis across languages and frameworks. |
| `observability-patterns` | Production-ready monitoring, logging, tracing, SLI/SLO management, and incident response. |
| `clean-code` | Robert C. Martin's Clean Code principles for infrastructure-as-code. |
| `excalidraw` | Generates Excalidraw diagrams from natural language descriptions. |

---

### `clubmed-data` — Club Med Data & Tracking

> Skills for the data / analytics team: build GA4 tracking plans from a Figma link or a URL, inspired by the existing Club Med plan.

**Keywords:** `tracking` · `ga4` · `analytics` · `gtm` · `tracking-plan` · `figma` · `data`

| Skill | Description |
|-------|-------------|
| `tracking-plan` | GA4 tracking-plan engine. From a Figma link and/or a URL, infers the trackable moments (clicks, impressions, ecommerce, page views) and produces a validated, tool-agnostic `plan.json`. Rendering (Excel/Confluence/Markdown) and publishing are separate skills that consume the plan. |
| `figma-client` | Figma REST client — fetches node metadata, interactions, instances, hidden layers, and semantic hints. Feeds the Figma inference path. |
| `figma-authentication` | Manages the `FIGMA_TOKEN` lifecycle: detect, validate, auto-generate, and persist. Dependency of `figma-client`. |

---

### `clubmed-product` — Club Med Product

> Skills for product managers and product owners: spec generation from PRDs, user story enrichment, and developer-ready documentation.

**Keywords:** `product` · `spec` · `prd` · `user-story` · `documentation`

| Skill | Description |
|-------|-------------|
| `spec` | Generates developer-ready specs (enriched user stories) from a PRD document. Reads `docs/specs/prd/`, cross-references `docs/specs/drd/` design files, and produces structured markdown specs in `docs/specs/`. Each spec covers one independently implementable unit sized for an AI developer to complete in under 2 hours. |

---

## Plugin vs Skill

| | Plugin | Skill |
|---|--------|-------|
| **What it is** | Curated bundle for a role/stack | Single-purpose slash command |
| **Install** | `claude plugin install <name>@clubmed` | Install individually |
| **Best for** | Onboarding a team or setting up a project | Adding one specific capability |

You can mix both: install a plugin for your core stack, then add individual skills for cross-cutting concerns (e.g. `a11y-web`, `e2e-testing`).
