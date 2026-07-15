---
applies-to: [write, review, plan]
enforcement: judgment
---

# Rule: Separate desktop and mobile tests

Every scenario splits into **two distinct test functions** — one desktop, one mobile. Never
branch on viewport inside a test body with `if (isMobile)` or `test.skip()`; that hides intent
and creates two code paths in one test.

Route by tag: title each test `should … @desktop` or `should … @mobile`. The Playwright
project config picks the right engine via `grep` / `grepInvert` (desktop projects invert
`@mobile`; the mobile project greps `@mobile`).

```typescript
test.describe("Destination page navigation", () => {
  test.describe("Desktop", () => {
    test("should navigate to Destinations from the menu @desktop", async ({ page }) => {
      // desktop path
    });
  });

  test.describe("Mobile", () => {
    test("should load Destinations directly @mobile", async ({ page }) => {
      // mobile path
    });
  });
});
```

**Review action:** `if (isMobile)` / `test.skip()` viewport branching inside a test body, or a
missing `@desktop`/`@mobile` tag, is a blocking finding.
