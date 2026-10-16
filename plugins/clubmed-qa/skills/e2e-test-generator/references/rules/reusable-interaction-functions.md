---
applies-to: [write, review, plan]
enforcement: judgment
---

# Rule: Small reusable interaction functions over monolithic tests

Never write large test blocks. Extract every meaningful interaction into a small, named,
reusable function (`searchDestination(page, "bali")`, `selectDates(page)`,
`addChildren(page, [7, 8])`). These functions live in shared utility files under `tests/utils/`
and are imported by the tests. A test body should read like a sequence of high-level steps, not
low-level Playwright calls.

Match the style already in the repo. The Club Med repos express these utilities as **plain
exported async functions** that take `page: Page` as the first argument (not class-based Page
Objects) — follow that convention so the codebase stays in one paradigm.

```typescript
// tests/utils/search.ts
import { Page } from "@playwright/test";

/**
 * Search for a destination by name.
 * @param page - Playwright page instance
 * @param destination - Destination name (e.g., "bali")
 */
export async function searchDestination(page: Page, destination: string): Promise<void> {
  await page.getByRole("searchbox").click();
  await page.getByRole("searchbox").fill(destination);

  const option = page.getByRole("option", { name: new RegExp(destination, "i") }).first();
  await option.waitFor({ state: "visible" });
  await option.click();
}
```

- One purpose per function, `Page` first argument, JSDoc on every exported util.
- Group by concern: `utils/navigation.ts`, `utils/search.ts`, `utils/calendar.ts`,
  `utils/guests.ts`, `utils/resort.ts`; pure logic with no `Page` in `utils/dates.ts`.
- See also `small-functions.md` (≤15-line functions, reuse before creating).

**Review action:** a monolithic test body with inline low-level Playwright calls, or a new
utility that departs from the repo's established style (e.g. a Page Object class where the repo
uses functional utils), is a finding.
