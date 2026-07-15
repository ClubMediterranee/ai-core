# Pattern: Accessibility checks

Opt-in, not a default. Use to assert a flow has no critical accessibility violations, via
`@axe-core/playwright`. Complements — does not replace — the dedicated `a11y-web` / `a11y-audit`
skills. Follows Club Med conventions: import from `./fixtures`.

```typescript
import { test, expect } from "./fixtures";
import AxeBuilder from "@axe-core/playwright";

test("search page has no a11y violations @desktop", async ({ page }) => {
  await page.goto("/");
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
});
```

**When to use:** the qualified intent asks for an accessibility gate on the flow. Scope with
`.include(...)` / `.exclude(...)` when only part of the page is in scope.
