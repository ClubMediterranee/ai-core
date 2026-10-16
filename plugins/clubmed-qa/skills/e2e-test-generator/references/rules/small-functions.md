---
applies-to: [write, review, plan]
enforcement: judgment
---

# Rule: Small, reusable functions over monolithic tests

Extract every meaningful interaction into a small, named, reusable function
(`searchDestination(page, "bali")`, `selectAvailableDates(page)`, `addChildren(page, [7, 8])`).
No function exceeds ~15 lines; if it does, split it further. A test body should read as a
sequence of high-level steps, not a wall of low-level Playwright calls.

## Reuse before you write

Reusing existing project code is mandatory, not a nicety. Before creating any new util:

1. **Read** the existing `tests/utils/*` and `tests/*.spec.ts` to learn the helpers and idioms
   already present.
2. **Grep** for an equivalent by concept and by interaction verb (`search`, `calendar`,
   `guest`, `date`, `navigat`, …). If a suitable helper exists, **import and reuse it** — never
   write a near-duplicate.
3. **Extend** the relevant concern file (`utils/search.ts`, `utils/calendar.ts`, …) instead of
   adding a redundant new one.
4. **Match the surrounding style**: import path, JSDoc form, function granularity, selector
   strategy. New code must read like the code already in the repo.

Only add a brand-new util when the interaction is genuinely missing, and say why an existing one
did not fit.

```typescript
// ✅ Test body reads as intent, not mechanics
test("should search a destination and open the date picker @desktop", async ({ page }) => {
  await page.goto("/");
  await searchDestination(page, "bali");
  await openDatePicker(page);
  await expect(page.getByRole("button", { name: /select dates|dates de séjour/i })).toBeVisible();
});
```

**Review action:** a monolithic test body, a >15-line function, or a duplicated interaction
that should reuse an existing util (a near-copy of a helper already in `tests/utils/`) is a
finding.
