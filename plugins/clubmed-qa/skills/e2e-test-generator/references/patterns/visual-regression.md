# Pattern: Visual regression

Opt-in, not a default. Use for pages or components where layout correctness is the point of the
test (a redesigned card, a pricing block). Follows Club Med conventions: import from
`./fixtures`.

```typescript
import { test, expect } from "./fixtures";

test("resort card layout is stable @desktop", async ({ page }) => {
  await page.goto("/");
  const card = page.getByRole("article").first();
  await expect(card).toHaveScreenshot("resort-card.png", { maxDiffPixels: 100 });
});
```

**Caution:** snapshot assertions are brittle across locales and dynamic content. Prefer
element-scoped screenshots over `fullPage` on a live, content-varying site, mask dynamic
regions, and commit baselines deliberately.
