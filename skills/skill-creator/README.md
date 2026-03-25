# skill-creator

Guides you through the full lifecycle of a Claude Code skill: from capturing intent and writing a first draft, to running evaluations, reviewing outputs, iterating based on feedback, and optimizing the skill's trigger description.

## Usage

Trigger when you want to create a new skill, improve an existing one, or measure how well a skill performs.

```
Create a skill that generates weekly status reports from git log
Improve the excalidraw skill, it's not generating good layouts
Run evals on the git-commit skill
```

## What it does

1. **Draft** — interviews you to understand the skill's purpose, scope, and edge cases
2. **Test** — spawns parallel subagents to run the skill against realistic prompts, with baselines for comparison
3. **Review** — opens an eval viewer in the browser with qualitative outputs and quantitative benchmarks
4. **Iterate** — improves the skill based on your feedback, reruns, repeats
5. **Optimize** — runs a triggering optimization loop to tune the skill's `description` field for better activation accuracy

## Structure

```
skill-creator/
├── SKILL.md
├── agents/          # Grader, comparator, analyzer subagent instructions
├── references/      # JSON schemas for evals and benchmarks
├── scripts/         # Aggregation, packaging, and optimization scripts
├── assets/          # HTML templates for the eval reviewer
└── eval-viewer/     # Browser-based output and benchmark viewer
```
