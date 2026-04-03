---
name: a11y-web
description: 'Audit and fix RGAA 4.1.2 accessibility issues in any web framework that outputs HTML: React, Vue, Svelte, Astro, Angular, Next.js, Nuxt, SvelteKit, plain HTML, Handlebars, ERB, Nunjucks, and similar. Activates proactively whenever a developer writes, modifies, generates, or refactors any component or template — even without explicit mention of accessibility. Triggers on: "create a component", "add a form", "refactor this header", "add a data table", "add a nav", "build a layout", "audit accessibility", "check a11y", "RGAA", "is this accessible", "make WCAG compliant", "fix accessibility issues", or any request to write/review .jsx/.tsx/.vue/.svelte/.astro/.html files. Covers static code only: images alt text, colors, tables, links, mandatory elements, information structure, forms, navigation landmarks.'
model: sonnet
allowed-tools: Read, Edit, Glob, Grep
version: 1.0.0
changelog:
  - version: 1.0.0
    date: 2026-03-26
    changes:
      - Initial release — framework-agnostic, covers RGAA 4.1.2 topics 1, 3, 5, 6, 8, 9, 10, 11, 12
created-at: 2026-03-26
created-by: "Emmanuel ERNEST <emmanuel.ernest@clubmed.com>"
---

# RGAA 4.1.2 Accessibility Auditor — Framework Agnostic

Audit and fix accessibility issues in any web framework that renders HTML, following RGAA 4.1.2 (aligned with WCAG 2.1 AA). Static analysis only — no runtime behavior.

## When to Use This Skill

Activate whenever:
- A developer **writes or modifies** a component or template (even without mentioning a11y)
- A developer asks to "review", "audit", or "check" a component
- A developer generates new component code from scratch
- Any `.jsx`, `.tsx`, `.vue`, `.svelte`, `.astro`, `.html`, `.htm`, `.erb`, `.njk`, `.hbs` file is in scope

The goal is accessibility by default, not as an afterthought.

---

## Framework Syntax Differences

RGAA criteria are about the **HTML output**, not the framework syntax. Keep these differences in mind when writing fixes:

| Concept | React/JSX | Vue / Svelte / Astro / HTML |
|---------|-----------|----------------------------|
| Label association | `htmlFor="id"` | `for="id"` |
| CSS class | `className="..."` | `class="..."` |
| Autocomplete | `autoComplete="..."` | `autocomplete="..."` |
| ARIA attributes | `aria-label`, `aria-hidden` | same in all frameworks |
| Event handlers | irrelevant (static only) | irrelevant (static only) |

When reporting a fix, always use the syntax of the framework being audited.

---

## Modes

### Audit Mode (default for review/check requests)
Scan files, report violations grouped by RGAA topic with severity, suggest fixes — do not apply them.

### Fix Mode (for generate/write/create requests)
Build accessible code from the start, or apply fixes directly to existing files using Edit.

**How to determine mode:**
- "review", "check", "audit", "report" → Audit Mode
- "fix", "make accessible", "apply", "generate", "create", "write" → Fix Mode
- Writing new code from scratch → Fix Mode (build correctly from the start)

---

## Workflow

### Step 1 — Identify Scope and Detect Framework

```
# Discover component/template files
Glob: src/**/*.{jsx,tsx}        # React
Glob: src/**/*.vue               # Vue
Glob: src/**/*.svelte            # Svelte
Glob: src/**/*.astro             # Astro
Glob: **/*.{html,htm}           # Plain HTML / Angular templates
Glob: **/*.{erb,njk,hbs}        # Server-side templates

# Root layout / app shell — check for Topic 8 and landmarks
Glob: src/App.{jsx,tsx,vue,svelte}
Glob: src/app/layout.{jsx,tsx}  # Next.js App Router
Glob: src/routes/+layout.svelte # SvelteKit
Glob: src/layouts/*.{astro,html,vue}
```

**Detect framework** by file extension and package.json presence:
- `.jsx`/`.tsx` → React / Next.js / Remix
- `.vue` → Vue / Nuxt
- `.svelte` → Svelte / SvelteKit
- `.astro` → Astro
- `.html` + Angular signals → Angular

Use the detected framework to format all fix suggestions with correct syntax.

### Step 2 — Per-Topic Scan

Run checks in order. Collect all violations before reporting. For full criterion text and examples per framework, read `references/rgaa-static-criteria.md`.

#### Topic 1 — Images

```
# 1.1 img without alt attribute
Pattern: <img(?![^>]*\balt=)
Files: *.{jsx,tsx,vue,svelte,astro,html,htm,erb,njk,hbs}

# 1.2 Decorative img: alt="" but missing aria-hidden="true" or role="presentation"
Pattern: alt=""
→ On same element, verify aria-hidden="true" OR role="presentation" is present

# 1.1 SVG without accessible name
Pattern: <svg(?![^>]*aria-label)(?![^>]*aria-labelledby)
→ Check if a <title> child exists inside the SVG block

# 1.6/1.7 Complex images (charts, infographics)
Pattern: <img
→ Flag imgs appearing to be charts/diagrams without aria-describedby or figcaption
```

#### Topic 3 — Colors

```
# 3.1 Color-only information
Pattern: style=.*color
→ Flag for manual review: verify information is not conveyed by color alone
```

Always add a `[MANUAL]` note for RGAA 3.2 (contrast ratios — requires rendered output).

#### Topic 5 — Tables

```
# 5.3 Layout table without role="presentation"
Pattern: <table(?![^>]*role=)

# 5.4 Table without <caption>
Pattern: <table
→ Check for <caption> as first child

# 5.6/5.7 th without scope
Pattern: <th(?![^>]*\bscope=)
```

#### Topic 6 — Links

```
# 6.1 Empty link text
Pattern: <a\b[^>]*>\s*</a>

# 6.1 Ambiguous link text (case-insensitive)
Pattern: >click here<|>read more<|>learn more<|>here<

# 6.2 Image link: verify img has non-empty alt
Pattern: <a\b[^>]*><img
→ Verify the img has a non-empty alt describing the destination
```

#### Topic 8 — Mandatory Elements

```
# 8.3/8.4 html element without lang
Pattern: <html(?![^>]*\blang=)
Files: **/*.{html,htm,jsx,tsx,vue,svelte,astro}

# 8.5/8.6 Page title
Pattern: <title          → in HTML files, verify non-empty
Pattern: <Helmet|<Head   → React / Next.js
Pattern: <svelte:head    → SvelteKit
Pattern: <head>          → Astro/Vue layouts
→ Check for <title> inside

# 8.1 Charset
Pattern: <meta\s+charset
Files: **/*.{html,htm}
```

#### Topic 9 — Information Structure

```
# 9.1 Heading inventory
Pattern: <h[1-6]
→ Count h1 occurrences (flag if 0 or >1 in main layout)
→ List all levels found; flag skipped levels

# 9.3 Presentational elements
Pattern: <b>|<i>
→ Suggest <strong>/<em> if semantic meaning is intended
```

#### Topic 10 — Information Presentation

Cannot verify statically. Always add:
- `[MANUAL]` for RGAA 10.1 (shape/size/position-only information)
- `[MANUAL]` for RGAA 10.4 (text resize to 200%)

#### Topic 11 — Forms

```
# 11.1 Input/select/textarea without label
Pattern: <input(?![^>]*type="hidden")(?![^>]*aria-label)(?![^>]*aria-labelledby)
Pattern: <select(?![^>]*aria-label)(?![^>]*aria-labelledby)
Pattern: <textarea(?![^>]*aria-label)(?![^>]*aria-labelledby)
→ Cross-check: does a <label for/htmlFor="id"> exist with matching id?

# 11.2 Placeholder without label
Pattern: placeholder=
→ Verify a <label> also exists for the same field

# 11.5/11.6 Radio/checkbox without fieldset+legend
Pattern: type="radio"|type="checkbox"
→ Check for wrapping <fieldset> with <legend>

# 11.10 Required field not indicated
Pattern: required
→ Verify visible text/symbol AND aria-required="true"

# 11.13 Personal data fields without autocomplete
Pattern: type="email"|type="tel"|name="email"|name="phone"|name="firstname"|name="lastname"
→ Verify autocomplete / autoComplete attribute present
```

#### Topic 12 — Navigation

```
# 12.6 Landmark presence
Pattern: <main
Pattern: <nav
Pattern: <header
Pattern: <footer
→ Flag if absent from app/layout component

# 12.6 Multiple nav without accessible name
Pattern: <nav(?![^>]*aria-label)(?![^>]*aria-labelledby)
→ Flag if more than one <nav> found without labels

# 12.7/12.8 Skip link
Pattern: skip|eviter|aller.au.contenu   (case-insensitive)
→ Flag if absent, pointing to #main-content
```

### Step 3 — Report (Audit Mode)

```
## RGAA Accessibility Audit — [filename or "Project"]
Framework: [React | Vue | Svelte | Astro | HTML | ...]
Date: YYYY-MM-DD

### Topic 1 — Images
[FAIL] RGAA 1.1 — src/components/Hero.tsx:14
  <img src="..." /> is missing an alt attribute.
  Fix: alt="Descriptive text" (informative) or alt="" aria-hidden="true" (decorative)

### Topic 3 — Colors
[MANUAL] RGAA 3.2 — Contrast ratios cannot be verified statically.
  Action: Run axe-core, Lighthouse, or check via DevTools > Accessibility.

---
Summary: X violations (Y FAIL, Z WARN, W MANUAL)
Reference: https://accessibilite.numerique.gouv.fr/methode/criteres-et-tests/
```

Severity:
- `[FAIL]` — Definite violation detectable in static code
- `[WARN]` — Likely violation; context verification needed
- `[MANUAL]` — Requires runtime or visual verification

### Step 4 — Apply Fixes (Fix Mode)

For each `[FAIL]` and `[WARN]`, apply the fix with Edit using the **correct syntax for the detected framework**. After editing, re-run the relevant Grep check to confirm.

---

## Quick-Reference Fix Patterns

Syntax shown as: `HTML / Vue / Svelte / Astro` first, then `React (JSX)` variant if different.

### Images
```html
<!-- Informative image — all frameworks -->
<img src="chart.png" alt="Bar chart: revenue grew 12% in Q3" />

<!-- Decorative image — all frameworks -->
<img src="divider.svg" alt="" aria-hidden="true" />

<!-- Informative SVG — all frameworks -->
<svg aria-label="Bar chart: revenue grew 12%" role="img" viewBox="0 0 100 100">
  <title>Bar chart: revenue grew 12%</title>
</svg>

<!-- Decorative SVG — all frameworks -->
<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24">...</svg>
```

### Links
```html
<!-- Ambiguous text — HTML/Vue/Svelte/Astro -->
<a href="/article/123" aria-label="Read full article: Paris Resort Review">Read more</a>

<!-- Image link — all frameworks -->
<a href="/home"><img src="logo.png" alt="Club Med — Home" /></a>
```

### Forms — HTML / Vue / Svelte / Astro
```html
<label for="email">Email address</label>
<input id="email" type="email" name="email" autocomplete="email" />

<!-- Required field -->
<label for="name">Full name <span aria-hidden="true">*</span></label>
<input id="name" type="text" required aria-required="true" />

<!-- Radio group -->
<fieldset>
  <legend>Preferred contact method</legend>
  <label><input type="radio" name="contact" value="email" /> Email</label>
  <label><input type="radio" name="contact" value="phone" /> Phone</label>
</fieldset>
```

### Forms — React (JSX differences)
```jsx
// React uses htmlFor and autoComplete (camelCase)
<label htmlFor="email">Email address</label>
<input id="email" type="email" name="email" autoComplete="email" />

<label htmlFor="name">Full name <span aria-hidden="true">*</span></label>
<input id="name" type="text" required aria-required="true" />
```

### Navigation landmarks — all frameworks
```html
<!-- First element in DOM -->
<a href="#main-content" class="skip-link">Skip to main content</a>

<header>
  <nav aria-label="Main navigation">...</nav>
</header>
<main id="main-content">
  <h1>Page title</h1>
</main>
<aside aria-label="Related resources">...</aside>
<footer>...</footer>

<!-- Multiple navs — each needs a unique aria-label -->
<nav aria-label="Main navigation">...</nav>
<nav aria-label="Footer links">...</nav>
```

### Tables — all frameworks
```html
<table>
  <caption>Hotel rates by season — 2025</caption>
  <thead>
    <tr>
      <th scope="col">Hotel</th>
      <th scope="col">Low season</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">Punta Cana</th>
      <td>1 200€</td>
    </tr>
  </tbody>
</table>
```

### Mandatory elements — title management per framework
```html
<!-- Plain HTML -->
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <title>Page Title — Site Name</title>
  </head>
```
```jsx
// React — Next.js App Router
export const metadata = { title: 'Page Title — Site Name' };

// React — Next.js Pages Router / react-helmet
<Head><title>Page Title — Site Name</title></Head>
```
```html
<!-- Vue / Nuxt -->
<Head><Title>Page Title — Site Name</Title></Head>
```
```svelte
<!-- SvelteKit -->
<svelte:head><title>Page Title — Site Name</title></svelte:head>
```
```astro
<!-- Astro -->
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <title>Page Title — Site Name</title>
  </head>
```

---

## Limitations (Static Analysis)

| Criterion | Why it needs manual review |
|-----------|---------------------------|
| RGAA 3.1 | Color-only info requires visual inspection |
| RGAA 3.2 | Contrast ratios require rendered colors |
| RGAA 10.1 | Shape/position-only info requires visual review |
| RGAA 10.4 | Text resize to 200% requires browser interaction |
| RGAA 12.4 | Breadcrumb presence requires site-level context |

For runtime analysis, recommend: `axe-core`, Lighthouse, browser DevTools Accessibility panel, or Storybook a11y addon.

---

## Reference

Full criterion details, examples per framework, and fix patterns:
→ `references/rgaa-static-criteria.md`

Official RGAA 4.1.2 specification:
→ https://accessibilite.numerique.gouv.fr/methode/criteres-et-tests/
