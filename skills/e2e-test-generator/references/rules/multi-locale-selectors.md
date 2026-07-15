---
applies-to: [write, review]
enforcement: judgment
---

# Rule: Multi-locale selectors

The application runs in a multi-locale environment (FR/EN and more). Never hardcode a
single-language label. Use one of:

1. `getByRole` with a **regex name covering all supported locales**, case-insensitive:
   `getByRole("button", { name: /select dates|dates de séjour/i })`.
2. Locale-independent selectors: `data-testid`, `data-cs-override-id`, `data-name`, CSS,
   or DOM structure.

```typescript
// ❌ Wrong — breaks in every other locale
await page.getByText("Select dates").click();

// ✅ Correct — regex across locales
await page.getByRole("button", { name: /select dates|dates de séjour/i }).click();

// ✅ Also correct — locale-independent attribute
await page.locator('[data-testid="date-picker-trigger"]').click();
```

**Review action:** a single-locale text selector is a blocking finding.
