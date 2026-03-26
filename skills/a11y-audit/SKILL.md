---
name: a11y-audit
description: 'Audit RGAA 4.1.2 accessibility on live pages using a sitemap or URL list. Uses Playwright to render each page, injects axe-core for automated checks, and runs custom DOM queries for RGAA-specific criteria. Triggers on: "audit the site accessibility", "check a11y on production", "run RGAA audit", "accessibility audit from sitemap", "check deployed pages for WCAG", "audit live site", "run axe on the site", or when the user provides a sitemap URL or a list of URLs to audit. Complements a11y-web (static) with runtime checks: real contrast ratios, rendered landmarks, focus order, dynamic content.'
model: sonnet
allowed-tools: WebFetch, Write, Read, mcp__playwright__browser_navigate, mcp__playwright__browser_evaluate, mcp__playwright__browser_snapshot, mcp__playwright__browser_take_screenshot, mcp__playwright__browser_wait_for, mcp__playwright__browser_tabs, mcp__playwright__browser_install
version: 1.0.0
changelog:
  - version: 1.0.0
    date: 2026-03-26
    changes:
      - Initial release — runtime RGAA 4.1.2 audit via Playwright + axe-core
created-at: 2026-03-26
created-by: "Club Med Team <team@clubmed.com>"
---

# RGAA 4.1.2 Runtime Accessibility Auditor

Audit live pages for RGAA 4.1.2 compliance using Playwright and axe-core. Complements `a11y-web` (static code) with runtime checks that require a rendered browser environment: real contrast ratios, dynamic content, focus order, and more.

## When to Use This Skill

- User provides a **sitemap URL** (e.g., `https://site.com/sitemap.xml`)
- User provides a **list of URLs** to audit
- User wants to audit a **deployed site** (staging or production)
- User asks to "check a11y on production", "audit live pages", "run RGAA on the site"

For source code analysis, use `a11y-web` instead.

---

## Dependencies

This skill requires Playwright and axe-core. Verify they are available before running.

```bash
# Check Playwright
npx playwright --version

# Check axe-core (used via CDN injection — no local install needed)
# OR install locally:
npm install --save-dev axe-core
```

If Playwright is not installed, run the setup script:
```bash
bash skills/a11y-audit/scripts/setup.sh
```

The setup script installs Playwright and verifies the environment.
See `scripts/setup.sh` for details.

---

## Modes

### Single URL
Audit one page. User provides: `https://example.com/page`

### Sitemap Audit (default)
Fetch sitemap XML → extract URLs → audit each page in sequence.
User provides: `https://example.com/sitemap.xml`

### URL List
User provides a list of URLs (file or inline).

---

## Workflow

### Step 0 — Verify Playwright

```
# Ensure Playwright browser is available
mcp__playwright__browser_install   (if needed)
```

If browser install fails, report the error and stop. Do not proceed without a working browser.

### Step 1 — Get URL List

**From sitemap:**
```
WebFetch: GET [sitemap_url]
```
Parse the XML response to extract `<loc>` elements.

```javascript
// Sitemap parsing — extract URLs
const urls = xmlContent.match(/<loc>(.*?)<\/loc>/g)
  .map(loc => loc.replace(/<\/?loc>/g, '').trim());
```

For large sitemaps (> 50 URLs): audit the first 20 by default, or the N pages specified by the user. Large sitemaps may have nested sitemaps (`<sitemap>` elements) — follow them recursively up to one level.

**From URL list:** use as-is.

**From single URL:** wrap in array.

### Step 2 — For Each Page: Navigate and Audit

For each URL, execute Steps 2a–2e in sequence.

#### 2a — Navigate

```
browser_navigate: url
browser_wait_for: { state: "load" }
```

If navigation fails (timeout, 404, auth redirect), mark page as `[SKIP]` and continue.

#### 2b — Inject and Run axe-core

```javascript
// browser_evaluate — inject axe-core
const script = document.createElement('script');
script.src = 'https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js';
document.head.appendChild(script);
await new Promise((resolve, reject) => {
  script.onload = resolve;
  script.onerror = reject;
  setTimeout(reject, 5000);
});
```

```javascript
// browser_evaluate — run axe with WCAG 2.1 AA (covers most RGAA criteria)
const results = await axe.run(document, {
  runOnly: {
    type: 'tag',
    values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'best-practice']
  }
});
return {
  violations: results.violations,
  passes: results.passes.length,
  incomplete: results.incomplete.length
};
```

If axe-core CDN fails (e.g., network restrictions), try loading from local node_modules:
```javascript
// Fallback — inline axe-core from local install
// (only if npm install axe-core was run)
```

#### 2c — Custom DOM Queries (RGAA gaps in axe-core)

axe-core does not cover all RGAA criteria. Run these additional checks:

```javascript
// browser_evaluate — custom RGAA checks
const customChecks = {
  // RGAA 8.3 — lang attribute value
  langValue: document.documentElement.lang,

  // RGAA 9.1 — heading hierarchy
  headings: Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,h6'))
    .map(h => ({ level: parseInt(h.tagName[1]), text: h.textContent.trim().slice(0, 60) })),

  // RGAA 12.7 — skip link: first focusable element
  firstFocusable: (() => {
    const el = document.querySelector(
      'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    return el ? { tag: el.tagName, href: el.getAttribute('href'), text: el.textContent.trim().slice(0, 60) } : null;
  })(),

  // RGAA 12.6 — landmark presence
  landmarks: {
    main: !!document.querySelector('main, [role="main"]'),
    nav: document.querySelectorAll('nav, [role="navigation"]').length,
    header: !!document.querySelector('header, [role="banner"]'),
    footer: !!document.querySelector('footer, [role="contentinfo"]')
  },

  // RGAA 11.1 — inputs without labels
  unlabeledInputs: Array.from(
    document.querySelectorAll('input:not([type="hidden"]):not([aria-label]):not([aria-labelledby])')
  ).filter(input => {
    const id = input.id;
    return !id || !document.querySelector(`label[for="${id}"]`);
  }).map(i => ({ type: i.type, name: i.name, id: i.id })),

  // RGAA 8.5 — page title
  title: document.title,

  // RGAA 3.1 — inputs/spans with only color-based class names (heuristic)
  colorOnlyIndicators: Array.from(
    document.querySelectorAll('[class*="red"],[class*="green"],[class*="error"],[class*="success"]')
  ).filter(el => !el.textContent.trim()).length,

  // RGAA 5.4 — tables without caption
  tablesWithoutCaption: Array.from(document.querySelectorAll('table'))
    .filter(t => !t.querySelector('caption') && t.getAttribute('role') !== 'presentation')
    .length,

  // RGAA 1.1 — images without alt
  imgsWithoutAlt: Array.from(document.querySelectorAll('img:not([alt])'))
    .map(i => i.src.split('/').pop())
};
return customChecks;
```

#### 2d — Screenshot

```
browser_take_screenshot: { fullPage: false }
```

Save for reference in the report (optional, activated by `--screenshots` flag).

#### 2e — Get Accessibility Tree

```
browser_snapshot
```

Use to verify landmark structure and heading hierarchy in the rendered tree.

### Step 3 — Build Per-Page Report

For each page, produce a structured section:

```markdown
## Page: [URL]
Status: 200 OK | Audited at: YYYY-MM-DD HH:MM

### axe-core Violations
| RGAA | axe Rule | Severity | Element | Message |
|------|----------|----------|---------|---------|
| 3.2  | color-contrast | critical | `<p class="subtitle">` | Contrast ratio 2.8:1 (min 4.5:1) |
| 1.1  | image-alt | critical | `<img src="hero.jpg">` | Missing alt attribute |
| 12.7 | skip-link | moderate | — | No skip navigation link found |

### Custom RGAA Checks
- [PASS] RGAA 8.3 — lang="fr" ✓
- [FAIL] RGAA 9.1 — Heading hierarchy: h1 → h3 (h2 missing)
- [FAIL] RGAA 12.6 — No <main> landmark found
- [PASS] RGAA 12.7 — Skip link present: "Aller au contenu" → #main
- [FAIL] RGAA 11.1 — 2 unlabeled inputs: input[type=email], input[type=search]

### Summary
- axe-core violations: X (Y critical, Z serious, W moderate)
- Custom RGAA failures: N
- axe-core passes: P checks passed
- Incomplete (needs manual review): I
```

Severity mapping (axe-core → RGAA):
- `critical` → `[FAIL]`
- `serious` → `[FAIL]`
- `moderate` → `[WARN]`
- `minor` → `[WARN]`

### Step 4 — Global Summary Report

After all pages are audited, produce a consolidated report:

```markdown
# RGAA 4.1.2 Accessibility Audit Report
Site: [base URL]
Sitemap: [sitemap URL]
Date: YYYY-MM-DD
Pages audited: N / Total in sitemap

## Critical Issues (across all pages)
| RGAA | Issue | Occurrences | Pages affected |
|------|-------|-------------|----------------|
| 3.2  | Insufficient contrast | 47 | 12/20 pages |
| 1.1  | Missing alt on images | 23 | 8/20 pages |
| 12.6 | Missing <main> landmark | 3 | 2/20 pages |

## Per-Page Summary
| Page | Violations | Critical | Warnings | Status |
|------|-----------|----------|----------|--------|
| /home | 12 | 3 | 9 | ⚠ |
| /about | 0 | 0 | 0 | ✓ |
| /contact | 5 | 2 | 3 | ⚠ |

## Compliance Estimate
Estimated RGAA compliance rate: XX% (based on auditable criteria)

## Recommended Priority Actions
1. Fix contrast issues (affects X% of users, critical severity, XX occurrences)
2. Add alt text to images (XX occurrences on X pages)
3. Add <main> landmark to layout template (affects all pages)

## Limitations
- Interactive content (modals, tooltips, carousels) requires manual testing
- Authentication-protected pages were skipped
- Dynamic content loaded after interaction not audited
- Recommended: complement with manual screen reader testing (NVDA/JAWS/VoiceOver)

Reference: https://accessibilite.numerique.gouv.fr/methode/criteres-et-tests/
```

Save the report to a file:
```
Write: a11y-audit-report-YYYY-MM-DD.md
```

---

## axe-core → RGAA Mapping

| RGAA Criterion | axe-core Rule(s) |
|----------------|-----------------|
| 1.1 — Image alt | `image-alt`, `role-img-alt`, `input-image-alt` |
| 1.2 — Decorative images | `image-redundant-alt` |
| 3.2 — Contrast | `color-contrast`, `color-contrast-enhanced` |
| 6.1 — Link names | `link-name`, `duplicate-link` |
| 6.2 — Image links | `image-alt` (on img inside a) |
| 8.3 — HTML lang | `html-has-lang`, `html-lang-valid` |
| 8.4 — Lang valid | `html-lang-valid`, `valid-lang` |
| 8.5 — Page title | `document-title` |
| 9.1 — Headings | `heading-order`, `page-has-heading-one` |
| 11.1 — Form labels | `label`, `label-content-name-mismatch` |
| 11.2 — Placeholder | `label` (no-label), `placeholder-label-no-duplicate` (best-practice) |
| 11.5 — Fieldset | `radiogroup`, `checkboxgroup` (best-practice) |
| 12.1 — Multiple nav | — (custom check) |
| 12.6 — Landmarks | `landmark-one-main`, `region`, `landmark-unique` |
| 12.7 — Skip link | `skip-link` |
| 12.8 — Skip link functional | `skip-link` |

Criteria not covered by axe-core (custom checks handle these):
- RGAA 3.1 — Color-only information (heuristic only)
- RGAA 9.1 — Heading level skip detection
- RGAA 12.6 — Multiple nav without aria-label

---

## Limitations

| What cannot be audited automatically | Why |
|--------------------------------------|-----|
| Authentication-protected pages | Requires login — provide session cookies if needed |
| Dynamic content (modals, live regions) | Requires interaction to trigger |
| PDF / Office documents | Not browser-renderable |
| Video captions (RGAA topic 4) | Requires human review |
| Touch target sizes | Requires device-specific testing |
| Screen reader announcements | Requires real AT (NVDA, JAWS, VoiceOver) |

For thorough RGAA compliance, complement this audit with:
1. `a11y-web` — static source code analysis
2. Manual screen reader walkthrough (NVDA/Firefox, VoiceOver/Safari)
3. Keyboard-only navigation test

---

## Reference

Official RGAA 4.1.2: https://accessibilite.numerique.gouv.fr/methode/criteres-et-tests/
axe-core rules: https://dequeuniversity.com/rules/axe/
Playwright docs: https://playwright.dev/docs/api/class-page
