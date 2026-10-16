---
applies-to: [harden]
enforcement: runtime
---

# Rule: Code quality gate

Before any test is considered done, all three must pass with **zero** errors:

```bash
npm run typecheck   # tsc --noEmit
npm run lint        # eslint . (zero warnings, zero eslint-disable)
npm run format      # prettier --check .
```

No type errors, no lint violations, no formatting drift. This is a gate, not a suggestion —
a test that fails any of the three is not finished, regardless of whether it passes at runtime.
Fix the code (never suppress the rule; see `no-eslint-disable.md`) and re-run until green.

**Harden action:** `gatePassed` is true only when all three commands exit 0 with clean output.
