# Pattern: Debugging failing / flaky tests

Opt-in tooling, mainly for the **harden** phase. When a spec fails or flakes across the repeated
runs, use these to find the real cause before touching the test — distinguish a genuine product
bug from a test-quality issue (never weaken an assertion just to make it pass).

## Reproduce and observe

```bash
# Watch the run in a real browser
npx playwright test path/to.spec.ts --headed

# Step through with the inspector
npx playwright test path/to.spec.ts --debug

# Open the trace of a failed run (config already sets trace: on-first-retry)
npx playwright show-trace test-results/**/trace.zip
```

## Narrow down where it breaks

```typescript
import { test } from "./fixtures";

// Group steps so the report and trace show exactly which one failed
test("should complete the booking flow @desktop", async ({ page }) => {
  await test.step("search a destination", async () => {
    await searchDestination(page, "bali");
  });

  await test.step("select dates", async () => {
    await selectAvailableDates(page);
  });
});

// Pause execution and open the inspector at a suspect point (remove before commit)
await page.pause();
```

## Turning findings into a fix

- **Flake at a specific step** → the wait signal is wrong. Replace any implicit timing
  assumption with a web-first assertion or `waitFor({ state })` (see `rules/ban-waitfortimeout`).
- **Selector not found intermittently** → it was not properly grounded; re-check the flow-map
  (see `rules/grounded-selectors`).
- **Consistent failure that looks correct** → likely a real product bug. Surface it as a
  finding; do not soften the assertion.

`page.pause()`, `page.screenshot()`, and `--headed` are debugging aids only — never leave them
in the committed spec (see `rules/no-repo-pollution`).
