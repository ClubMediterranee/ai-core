---
name: agent-creator
description: This skill should be used when the user asks to "create an agent", "add an agent", "write a subagent", "multi-agent", "agent swarm", "coordinator agent", "worker agent", "agent frontmatter", "when to use description", "agent examples", "agent tools", "agent colors", "autonomous agent", "agents that communicate", "parallel agents", or needs guidance on agent structure, system prompts, triggering conditions, subagent orchestration, or multi-agent swarm development for Claude Code.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
version: 1.1.0
changelog:
  - version: 1.1.0
    date: 2026-03-31
    changes:
      - Add Multi-Agent Swarm (Type B) — coordinator/worker pattern with session messaging
      - Add full official subagent frontmatter fields (permissionMode, maxTurns, effort, isolation, etc.)
      - Add project metadata standard (created-at, created-by, credits) on all agent files
      - Add intent qualification workflow before creating any agent
      - Add dynamic skills discovery — suggest relevant pre-loaded skills based on agent domain
  - version: 1.0.0
    date: 2026-03-31
    changes:
      - Initial release
credits: https://github.com/anthropics/claude-code
created-at: 2026-03-31
created-by: "Jeremy Wallez <jeremy.wallez@clubmed.com>"
---

# Agent Creator for Claude Code

## Overview

Two distinct agent types in Claude Code:

| Type | Official Name | Communication | Use When |
|------|--------------|---------------|----------|
| A | **Subagent** | Hierarchical (parent spawns child) | Autonomous task, delegated by an orchestrator |
| B | **Multi-Agent Swarm** | Peer-to-peer via sessions (tmux) | Coordinated agents that message each other |

---

## Step 0: Qualify the User's Intent

Before writing any agent, ask these questions:

1. **What task** should the agent handle?
2. **Where** will it live?
   - Project: `.claude/agents/` (shared with all project users)
   - Global: `~/.claude/agents/` (personal, all projects)
   - Plugin-bundled: `skills/my-skill/agents/` (ships with a skill)
3. **Does it need to communicate** with other running Claude Code sessions?
   - No → **Type A: Subagent**
   - Yes → **Type B: Multi-Agent Swarm**
4. **Permissions**: Should it run commands, edit files, or be read-only?
5. **Should it run in background** or block the current session?

---

## Frontmatter Standard

Every agent file must include **project metadata** (required by this project) **and** agent configuration fields.

### Project Metadata (required on all agents)

```yaml
created-at: YYYY-MM-DD
created-by: "Firstname Lastname <email@example.com>"
credits: https://...   # Optional — only if derived from external work
```

Always ask the user for their first name, last name, and email before writing the file. Never guess or skip `created-by`.

### Agent Configuration Fields

| Field | Required | Values | Notes |
|-------|----------|--------|-------|
| `name` | Yes | `lowercase-hyphens` | 3–50 chars, start/end alphanumeric |
| `description` | Yes | Text + `<example>` blocks | Primary triggering mechanism |
| `model` | No | `inherit`, `sonnet`, `opus`, `haiku`, full model ID | Default: `inherit` |
| `color` | No | `blue` `cyan` `green` `yellow` `magenta` `red` | UI identifier |
| `tools` | No | Array of tool names | Omit = all tools |
| `disallowedTools` | No | Array of tool names | Explicitly deny |
| `permissionMode` | No | `default` `acceptEdits` `dontAsk` `bypassPermissions` `plan` | Override permission prompts |
| `maxTurns` | No | Integer | Cap agentic turns |
| `background` | No | `true`/`false` | Run without blocking current session |
| `effort` | No | `low` `medium` `high` `max` | Reasoning effort level |
| `isolation` | No | `worktree` | Isolated git worktree environment |
| `memory` | No | `user` `project` `local` | Persistent memory scope |
| `skills` | No | Array of skill paths | Pre-loaded skills at startup |

**Color guide:** blue/cyan = analysis · green = generation · yellow = validation · red = security · magenta = creative/refactoring

### Pre-loading Skills (`skills` field)

When creating an agent, suggest pre-loading relevant skills from the project. Skills give the agent additional domain expertise at startup.

**Discover available skills dynamically** — before suggesting anything, scan the project:

```
1. Glob: **/SKILL.md (search both skills/ and .claude/skills/, wherever they live)
2. For each result, read the `name` and `description` fields from the frontmatter
3. Based on the agent's domain, propose the relevant ones
```

Then ask the user: *"Should this agent have any skills pre-loaded?"* and show only the ones that match the agent's responsibilities.

**Example frontmatter with skills:**
```yaml
skills:
  - skills/react-best-practices
  - skills/typescript-advanced-types
```

---

## Type A: Subagent

A standalone agent spawned hierarchically. An orchestrator (Claude or another agent) delegates a task to it.

### File Template

```markdown
---
created-at: YYYY-MM-DD
created-by: "Firstname Lastname <email@example.com>"

name: my-agent
description: Use this agent when [conditions]. Examples:

<example>
Context: [Situation]
user: "[Request]"
assistant: "[Response using this agent]"
<commentary>
[Why this agent triggers here]
</commentary>
</example>

model: inherit
color: blue
tools: ["Read", "Grep", "Glob"]
---

You are [role] specializing in [domain].

**Your Core Responsibilities:**
1. [Primary responsibility]
2. [Secondary responsibility]

**Process:**
1. [Step 1]
2. [Step 2]

**Output Format:**
[What to produce and how to structure it]
```

### Invocation

```
# Natural language — Claude decides
Use the my-agent subagent to analyze the codebase

# @-mention — forces this specific agent for one task
@"my-agent (agent)" check the auth module
```

### Restricting Which Subagents an Orchestrator Can Spawn

In an orchestrator agent's frontmatter, limit spawnable subagents:

```yaml
tools: Agent(worker, researcher), Read, Bash
```

### Description Best Practices

The `description` field is the sole triggering mechanism. Include 2–4 `<example>` blocks covering:
- Explicit request (user directly asks)
- Proactive triggering (agent activates after relevant work)
- Variations in phrasing

See `references/triggering-examples.md` for the full guide.

### System Prompt Design

Write in second person (`You are...`, `You will...`). See `references/system-prompt-design.md` for complete patterns (Analysis, Generation, Validation, Orchestration) with structure templates and edge case guidance.

---

## Type B: Multi-Agent Swarm

Multiple Claude Code sessions coordinating via shared state. Each session runs independently and notifies a coordinator when idle.

### When to Use

- Tasks that can be parallelized (multiple PRs, multiple services, multiple modules)
- Workflows requiring specialized agents for different phases
- Long-running work exceeding a single session's context
- Independent tasks with explicit dependencies

### Architecture

```
Coordinator session (e.g. "team-leader")
    ├── Worker session A ("auth-agent")    → works on Task 3.5
    ├── Worker session B ("db-agent")      → works on Task 4.2
    └── Worker session C ("api-agent")     → works on Task 5.1
         ↕ communicate via tmux send-keys
```

### State File

Each worker session reads `.claude/multi-agent-swarm.local.md` to know its task and coordinator:

```yaml
---
agent_name: auth-agent
task_number: 3.5
pr_number: TBD
coordinator_session: team-leader
enabled: true
dependencies: ["Task 3.4"]
additional_instructions: "Use JWT, not sessions"
---

# Task Assignment: Implement Authentication

## Requirements
- JWT token generation and validation
- Refresh token flow

## Success Criteria
- Auth endpoints pass all tests
- PR created and CI green

## Coordination
Depends on Task 3.4 (user model).
Report status to coordinator session 'team-leader'.
```

### State File Fields

| Field | Required | Description |
|-------|----------|-------------|
| `agent_name` | Yes | Identifier for this agent in the swarm |
| `task_number` | Yes | Task ordering (e.g. `3.5`) |
| `coordinator_session` | Yes | tmux session name of the coordinator |
| `enabled` | Yes | `true`/`false` — agent skips its hook if false |
| `pr_number` | No | Associated PR number |
| `dependencies` | No | Task IDs that must complete first |
| `additional_instructions` | No | Per-agent override instructions |

### Idle Notification Hook

Add a `Stop` hook to each worker's `.claude/settings.json` that calls a notify script on idle. See `examples/complete-agent-examples.md` → Example 5 for the full `settings.json` block and `notify-coordinator.sh` script.

### Coordinator System Prompt Pattern

```
You are the coordinator of a multi-agent swarm managing parallel development tasks.

**Your Core Responsibilities:**
1. Assign tasks to worker agents via their tmux sessions
2. Track task dependencies — only assign a task when its dependencies are complete
3. Handle worker notifications (agents message you when idle)
4. Consolidate completed work into a final report

**Coordination Process:**
1. Maintain a backlog of pending tasks with their dependencies
2. When a worker becomes idle: identify the next unblocked task and assign it
3. To assign a task: tmux send-keys -t <session> "<task description>" Enter
4. When all tasks complete: produce a summary of all PRs and outcomes

**State:** Track which tasks are pending/in-progress/done, and which session owns each.
```

### Full Swarm Example

See `examples/complete-agent-examples.md` → "Example 5: Multi-Agent Swarm".

---

---

## Quick Reference

### Which type?

```
Does the agent need to message other running Claude Code sessions?
├── No  → Type A: Subagent
│         .claude/agents/my-agent.md
└── Yes → Type B: Multi-Agent Swarm
          .claude/multi-agent-swarm.local.md
```

### Minimal Subagent

```yaml
---
created-at: 2026-03-31
created-by: "Name <email>"
name: my-agent
description: Use this agent when... Examples: <example>...</example>
model: inherit
---
You are an agent that does X.
1. Step one
2. Step two
Output: [what to produce]
```

### Reference Files

- `references/system-prompt-design.md` — Patterns for Analysis, Generation, Validation, Orchestration agents
- `references/triggering-examples.md` — Writing `<example>` blocks for reliable triggering
- `references/agent-creation-system-prompt.md` — AI-assisted agent generation prompt

### Example Files

- `examples/complete-agent-examples.md` — Production-ready templates (subagents + swarm)
- `examples/agent-creation-prompt.md` — AI-assisted generation workflow

