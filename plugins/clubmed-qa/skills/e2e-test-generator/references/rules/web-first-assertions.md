---
applies-to: [write, review, harden]
enforcement: grep
---

# Rule: Web-first assertions, no error-swallowing helpers

Prefer Playwright's **web-first assertions** — they auto-retry until the condition holds or the
timeout elapses, which is the primary defense against flakiness: `toHaveURL`, `toHaveTitle`,
`toBeVisible`, `toBeEnabled`, `toContainText` (with regex where text is involved).

Do **not** hand-roll boolean helpers that wrap a check in `try/catch` and return `false` on
error. They lose auto-retry and hide real failures behind a silent `false`.

```typescript
// ❌ Wrong — swallows errors, no retry, hides failures
async function isResortSelected(page: Page): Promise<boolean> {
  try {
    return (await page.locator("[data-name=Resort]").getAttribute("aria-pressed")) === "true";
  } catch {
    return false;
  }
}
expect(await isResortSelected(page)).toBe(true);

// ✅ Correct — web-first, auto-retrying, fails loudly
await expect(page.locator("[data-name=Resort]")).toHaveAttribute("aria-pressed", "true");
```

**Review action:** an error-swallowing boolean helper, or `expect(bool).toBe(true)` over a
hand-rolled check where a web-first assertion would work, is a blocking finding.
