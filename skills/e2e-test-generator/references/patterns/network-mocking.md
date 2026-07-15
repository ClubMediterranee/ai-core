# Pattern: Network mocking & interception

Opt-in, not a default. Use when a scenario must exercise a state the live site will not
reliably produce — an API error or a specific payload — or when it would otherwise trigger a
**forbidden action** captured during qualification (e.g. a real payment). Mock the call instead
of firing it for real. Follows Club Med conventions: import from `./fixtures`, multi-locale
regex selectors.

```typescript
import { test, expect } from "./fixtures";

// Force an error state the live backend won't give you on demand
test("should show an error when the offers API fails @desktop", async ({ page }) => {
  await page.route("**/api/offers**", (route) =>
    route.fulfill({ status: 500, contentType: "application/json", body: "{}" }),
  );
  await page.goto("/");
  await expect(page.getByText(/error|erreur/i)).toBeVisible();
});

// Mock a third-party service to avoid a forbidden real transaction
test("should confirm booking with mocked payment @desktop", async ({ page }) => {
  await page.route("**/payment/**", (route) =>
    route.fulfill({ status: 200, body: JSON.stringify({ status: "succeeded" }) }),
  );
  // ... drive the confirmation flow against the mock
});
```

**When to use:** reproducing failure/edge states; honoring a forbidden-action constraint by
mocking rather than triggering. **Do not** mock away the very behavior under test.
