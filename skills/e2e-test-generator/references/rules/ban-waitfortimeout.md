---
applies-to: [write, review, harden]
enforcement: grep
---

# Rule: No `waitForTimeout`

Fixed sleeps (`page.waitForTimeout(500)`) are flake generators: too short and the test races
the app, too long and the suite crawls. They encode a guess about timing instead of waiting on
the actual condition. Ban them.

Use instead:
- Web-first assertions that auto-wait: `await expect(locator).toBeVisible()`.
- `locator.waitFor({ state: "visible" | "attached" })` before interacting.
- `page.waitForLoadState("networkidle")` / `page.waitForURL(...)` after navigation.
- `page.waitForResponse(...)` when gating on a specific API call.

```typescript
// ❌ Wrong
await page.waitForTimeout(500);
await page.getByRole("button", { name: /continue|continuer/i }).click();

// ✅ Correct
const button = page.getByRole("button", { name: /continue|continuer/i });
await button.waitFor({ state: "visible" });
await button.click();
```

**Review action:** any `waitForTimeout(` in authored code is a blocking finding.
