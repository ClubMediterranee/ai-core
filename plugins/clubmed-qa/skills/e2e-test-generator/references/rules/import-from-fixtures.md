---
applies-to: [write, review, harden]
enforcement: grep
---

# Rule: Import from `./fixtures`, never from `@playwright/test`

Every spec file imports `test` and `expect` from the project's custom fixtures module, not
from Playwright directly. The custom fixtures inject per-page setup the whole suite depends on
(cookie-consent acceptance, newsletter/backdrop popup suppression). A spec that imports from
`@playwright/test` bypasses that setup and will behave differently — treat it as a defect.

```typescript
// ✅ Correct
import { test, expect } from "./fixtures";

// ❌ Wrong — bypasses consent + popup handling
import { test, expect } from "@playwright/test";
```

**Review action:** any spec importing `test`/`expect` from `@playwright/test` is a blocking finding.
