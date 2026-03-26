# a11y-audit — Dependencies

## Required

| Dependency | Version | Purpose | Install |
|-----------|---------|---------|---------|
| **Playwright** (Chromium) | ≥ 1.40 | Browser automation — render pages, evaluate JS, take screenshots | `npm install --save-dev @playwright/test && npx playwright install chromium` |
| **axe-core** | ≥ 4.9 | WCAG 2.1 AA automated rules engine — covers ~57% of RGAA criteria | CDN (primary) or `npm install --save-dev axe-core` |
| **Node.js** | ≥ 18 LTS | Runtime for npm/npx | https://nodejs.org |

## Quick Setup

```bash
bash skills/a11y-audit/scripts/setup.sh
```

Or manually:

```bash
npm install --save-dev @playwright/test axe-core
npx playwright install chromium
```

## axe-core Loading Strategy

The skill loads axe-core in priority order:

1. **CDN injection** (default — no local install needed):
   ```javascript
   // Injected into page via browser_evaluate
   https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js
   ```

2. **Local fallback** (for offline/restricted environments):
   ```javascript
   // If CDN fails, read local file and inject as inline script
   node_modules/axe-core/axe.min.js
   ```

3. **Inline from read** (last resort):
   ```
   Read: node_modules/axe-core/axe.min.js
   → Pass content as inline <script> via browser_evaluate
   ```

## MCP Requirements

This skill requires the **Playwright MCP server** to be configured in Claude Code settings.

Verify it is active:
```bash
# In Claude Code settings.json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```

If the Playwright MCP is not available, the skill will report an error and suggest using `a11y-web` for static analysis instead.

## Version Pinning

For reproducible audits, pin versions in package.json:

```json
{
  "devDependencies": {
    "@playwright/test": "^1.44.0",
    "axe-core": "^4.10.2"
  }
}
```

## Upgrade Notes

- **axe-core** releases frequently — newer versions add rules and fix false positives. Pin to a version for stable CI audits.
- **Playwright** Chromium updates may change rendering and affect contrast calculations. Note the browser version in audit reports.

## No-Install Environments

If neither CDN nor local axe-core is available, the skill falls back to **custom DOM checks only** (RGAA topics 8, 9, 11, 12) and marks all axe-core-dependent criteria as `[MANUAL]`.
