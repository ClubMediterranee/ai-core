---
applies-to: [write, review, harden]
enforcement: grep
---

# Rule: No hardcoded dates

Never write a literal date (`"2026-03-21"`, `"22 Mar 2026"`) in test code. Hardcoded dates
silently rot the suite — a date that is valid today is in the past next month. Compute every
date at runtime relative to `new Date()`, using the repo's `tests/utils/dates.ts` helpers
(`getFutureDate`, `formatDateISO`, `calculateChildBirthDate`, …).

```typescript
// ❌ Wrong — brittle, breaks over time
await page.fill('[data-testid="checkin"]', "2026-06-15");

// ✅ Correct — dynamic, relative to now
import { getFutureDate, formatDateISO } from "./utils/dates";
await page.fill('[data-testid="checkin"]', formatDateISO(getFutureDate(30)));
```

**Review action:** any hardcoded/literal date in a spec or util is a blocking finding.
