---
applies-to: [write, review, harden]
enforcement: grep
---

# Rule: No ESLint suppression

Never use `eslint-disable`, `eslint-disable-next-line`, `eslint-disable-line`, or any other
form of rule suppression. If a lint rule fires, fix the underlying code — the rule is almost
always pointing at a real issue (an unused variable, an unsafe `any`, a floating promise).
Silencing it hides the problem and normalizes suppression for the next author.

```typescript
// ❌ Wrong
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const data: any = await response.json();

// ✅ Correct — type it properly
interface UsersResponse { users: { id: number; name: string }[] }
const data = (await response.json()) as UsersResponse;
```

**Review action:** any `eslint-disable` in authored code is a blocking finding.
