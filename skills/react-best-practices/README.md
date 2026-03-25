# react-best-practices

Provides 64 performance optimization rules for React and Next.js, sourced from Vercel Engineering. Used when writing, reviewing, or refactoring React components and Next.js pages to ensure optimal patterns around rendering, data fetching, bundle size, and hydration.

## Usage

Trigger when working on React or Next.js code, especially for performance-sensitive tasks.

```
Review this component for performance issues
Implement data fetching for this Next.js page
Refactor this hook to avoid unnecessary re-renders
```

## Rule categories

| Category | Examples |
|----------|---------|
| **Rendering** | Hoist static JSX, avoid inline components, use transitions |
| **Re-renders** | Derived state, memo, deferred values, split hooks |
| **Server** | Parallel fetching, streaming, cache, auth actions |
| **Async** | Suspense boundaries, parallel awaits, defer non-blocking work |
| **Bundle** | Dynamic imports, barrel imports, conditional loading |
| **Client** | Passive event listeners, SWR dedup, localStorage schema |
| **JS perf** | Index maps, set/map lookups, cache function results |
| **Advanced** | Init-once patterns, event handler refs, useLatest |

## Source

Rules adapted from [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills/tree/main/skills/react-best-practices).
