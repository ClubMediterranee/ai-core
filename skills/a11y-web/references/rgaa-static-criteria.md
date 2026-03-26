# RGAA 4.1.2 — Static Web Criteria Reference

Full details for each criterion covered by the `a11y-web` skill.
Applies to all HTML-outputting frameworks: React, Vue, Svelte, Astro, Angular, plain HTML, ERB, Nunjucks, Handlebars, etc.
Official source: https://accessibilite.numerique.gouv.fr/methode/criteres-et-tests/

## Framework Syntax Quick Reference

| Attribute | HTML / Vue / Svelte / Astro | React (JSX) |
|-----------|----------------------------|-------------|
| Label association | `for="id"` | `htmlFor="id"` |
| CSS class | `class="..."` | `className="..."` |
| Autocomplete | `autocomplete="email"` | `autoComplete="email"` |
| ARIA attributes | `aria-label`, `aria-hidden` | identical |

All RGAA criteria in this file target the **rendered HTML output**. Examples use plain HTML syntax unless noted otherwise.

## Table of Contents

1. [Topic 1 — Images](#topic-1--images)
2. [Topic 3 — Colors](#topic-3--colors)
3. [Topic 5 — Tables](#topic-5--tables)
4. [Topic 6 — Links](#topic-6--links)
5. [Topic 8 — Mandatory Elements](#topic-8--mandatory-elements)
6. [Topic 9 — Information Structure](#topic-9--information-structure)
7. [Topic 10 — Information Presentation](#topic-10--information-presentation)
8. [Topic 11 — Forms](#topic-11--forms)
9. [Topic 12 — Navigation](#topic-12--navigation)
10. [Quick Fix Lookup Table](#quick-fix-lookup-table)

---

## Topic 1 — Images

### RGAA 1.1 — Informative Image Must Have an Accessible Name

Every `<img>` conveying information must have a non-empty `alt` attribute.
Every informative `<svg>` must have an accessible name via `aria-label`, `aria-labelledby`, or an inner `<title>` element with `role="img"` on the `<svg>`.

**Fails:**
```jsx
<img src="chart.png" />                       // no alt
<svg viewBox="0 0 100 100"></svg>             // no accessible name
```

**Passes:**
```jsx
<img src="chart.png" alt="Bar chart: revenue grew 12% in Q3" />

<svg aria-label="Bar chart: revenue grew 12%" role="img" viewBox="0 0 100 100">
  <title>Bar chart: revenue grew 12%</title>
</svg>
```

**Grep pattern:** `<img(?![^>]*\balt=)`

---

### RGAA 1.2 — Decorative Image Must Be Hidden from Assistive Technologies

A decorative image adds no information beyond surrounding text. Screen readers must ignore it.

Required for `<img>`: `alt=""` (always) + `aria-hidden="true"` OR `role="presentation"`.
Required for `<svg>`: `aria-hidden="true" focusable="false"`.

**Fails:**
```jsx
<img src="divider.svg" alt="" />              // alt="" alone is not enough
<img src="star.png" alt="star icon" />        // describes shape, not information
```

**Passes:**
```jsx
<img src="divider.svg" alt="" aria-hidden="true" />
<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24">{/* ... */}</svg>
```

---

### RGAA 1.6 / 1.7 — Complex Images Need Extended Descriptions

Charts, diagrams, maps, and infographics require both a short `alt` and a detailed text alternative.

Options:
- `<figure>` + `<figcaption>` (preferred)
- `aria-describedby` pointing to a visible or visually-hidden `<p>` or `<details>`
- Adjacent text description

```jsx
<figure>
  <img
    src="revenue-chart.png"
    alt="Revenue chart Q1–Q4 2025"
    aria-describedby="chart-desc"
  />
  <figcaption id="chart-desc">
    Q1: 1.2M€, Q2: 1.5M€, Q3: 1.8M€, Q4: 2.1M€ — consistent 25% quarterly growth.
  </figcaption>
</figure>
```

---

## Topic 3 — Colors

### RGAA 3.1 — Information Not Conveyed by Color Alone

Any information communicated by color must also be available via text, icon, pattern, or shape.

**Fails:**
```jsx
// Red/green only — color is the only signal
<span style={{ color: status === 'error' ? 'red' : 'green' }}>
  {message}
</span>
```

**Passes:**
```jsx
<span style={{ color: status === 'error' ? 'red' : 'green' }}>
  {status === 'error' ? '✗ Error: ' : '✓ '}{message}
</span>
// Or use role="alert" for errors, distinct icons, or text labels
```

**Note:** Cannot be fully verified statically. Flag `style={{ color: ... }}` for manual review.

---

### RGAA 3.2 — Sufficient Contrast Ratio

- Normal text (< 18pt or < 14pt bold): minimum **4.5:1**
- Large text (≥ 18pt or ≥ 14pt bold): minimum **3:1**
- UI components and graphic elements (borders, icons): minimum **3:1**

**Cannot be verified statically.** Always add a `[MANUAL]` note. Recommended tools:
- Chrome DevTools → Accessibility → Contrast
- [axe-core](https://github.com/dequelabs/axe-core)
- [Lighthouse](https://developer.chrome.com/docs/lighthouse/) accessibility audit
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)

---

## Topic 5 — Tables

### RGAA 5.3 — Layout Tables Must Have role="presentation"

A `<table>` used for layout must declare `role="presentation"` to suppress table semantics for assistive technologies.

**Fails:**
```jsx
<table>  {/* layout table, no role */}
  <tr><td>Logo</td><td>Nav</td></tr>
</table>
```

**Passes:**
```jsx
<table role="presentation">
  <tr><td>Logo</td><td>Nav</td></tr>
</table>
```

**Best practice:** Replace layout tables with CSS Flexbox or Grid entirely.

---

### RGAA 5.4 — Data Tables Must Have a Caption

Every data `<table>` must have a `<caption>` as its first child, describing the table's purpose.

**Fails:**
```jsx
<table>
  <thead><tr><th>Name</th><th>Price</th></tr></thead>
```

**Passes:**
```jsx
<table>
  <caption>Hotel rates by season — 2025</caption>
  <thead>...</thead>
```

---

### RGAA 5.6 / 5.7 — Table Headers Must Use th with scope

- Column headers: `<th scope="col">`
- Row headers: `<th scope="row">`
- Complex tables with merged cells: use `id` + `headers` attributes

**Fails:**
```jsx
<tr><td>Name</td><td>Value</td></tr>  // headers as td
<th>Name</th>                          // no scope
```

**Passes:**
```jsx
<thead>
  <tr>
    <th scope="col">Hotel</th>
    <th scope="col">Rate</th>
  </tr>
</thead>
<tbody>
  <tr>
    <th scope="row">Punta Cana</th>
    <td>1 200€</td>
  </tr>
</tbody>
```

**Grep pattern:** `<th(?![^>]*\bscope=)`

---

## Topic 6 — Links

### RGAA 6.1 — Links Must Have an Accessible Name

A link's accessible name is derived from (priority order):
1. `aria-label` attribute
2. `aria-labelledby` pointing to another element
3. Text content of the `<a>`
4. `alt` of an `<img>` inside the link

The name must describe the **destination or action**, not the visual appearance.

**Fails:**
```jsx
<a href="/report">Click here</a>
<a href="/report">Read more</a>
<a href="/report"></a>
<a href="/report"><img src="arrow.png" alt="" /></a>  // empty alt = no accessible name
```

**Passes:**
```jsx
<a href="/report">Download Q3 2025 financial report (PDF)</a>
<a href="/report" aria-label="Read more: Paris resort expansion">Read more</a>
<a href="/home"><img src="logo.png" alt="Club Med — return to homepage" /></a>
```

---

### RGAA 6.2 — Image Links Must Have Alt Text Describing the Destination

When an `<img>` is the sole content of an `<a>`, `alt` becomes the link's accessible name. It must describe the **destination**, not the image.

**Fails:**
```jsx
<a href="/"><img src="logo.png" alt="logo" /></a>   // describes appearance
<a href="/"><img src="logo.png" alt="" /></a>         // no accessible name
```

**Passes:**
```jsx
<a href="/"><img src="logo.png" alt="Club Med — Accueil" /></a>
```

---

## Topic 8 — Mandatory Elements

### RGAA 8.1 — Character Encoding

The document must declare UTF-8 encoding. In React projects, this is in `public/index.html` or root `index.html`.

```html
<meta charset="UTF-8" />
```

---

### RGAA 8.3 / 8.4 — Document Language

The `<html>` element must have a valid `lang` attribute (BCP 47 language tag).

```html
<html lang="fr">    <!-- French -->
<html lang="en">    <!-- English -->
<html lang="fr-FR"> <!-- French (France) -->
```

For sections in a different language, use `lang` on the containing element:
```jsx
<p lang="en">Welcome to Club Med</p>
```

**Grep pattern:** `<html(?![^>]*\blang=)`

---

### RGAA 8.5 / 8.6 — Page Title

Each page must have a `<title>` that is non-empty and descriptive.
Recommended format: `"Page Name — Site Name"`.

```jsx
// Next.js App Router
export const metadata = { title: 'Resort Details — Club Med' };

// Next.js Pages Router
import Head from 'next/head';
<Head><title>Resort Details — Club Med</title></Head>

// react-helmet
import { Helmet } from 'react-helmet';
<Helmet><title>Resort Details — Club Med</title></Helmet>

// Plain index.html
<title>Home — Club Med</title>
```

---

## Topic 9 — Information Structure

### RGAA 9.1 — Heading Hierarchy

Rules:
- Exactly **one** `<h1>` per page, naming the main content
- No skipped levels (e.g., h1 → h3 without h2)
- Do not use headings for visual styling — use CSS classes instead

**Fails:**
```jsx
<h1>Welcome</h1>
<h3>Our Services</h3>   // skipped h2
<h2>Contact</h2>
```

**Passes:**
```jsx
<h1>Welcome to Club Med</h1>
  <h2>Our Resorts</h2>
    <h3>Caribbean</h3>
    <h3>Mediterranean</h3>
  <h2>Contact Us</h2>
```

---

### RGAA 9.3 — Lists Must Use Semantic List Elements

Enumerations must use `<ul>`, `<ol>`, or `<dl>`. Do not simulate lists with `<div>` or `<p>`.

**Fails:**
```jsx
<div className="list">
  <div className="list-item">Item 1</div>
  <div className="list-item">Item 2</div>
</div>
```

**Passes:**
```jsx
<ul>
  <li>Item 1</li>
  <li>Item 2</li>
</ul>

// Key-value pairs
<dl>
  <dt>Check-in</dt><dd>From 15:00</dd>
  <dt>Check-out</dt><dd>Until 12:00</dd>
</dl>
```

---

### RGAA 9.4 — Quotations Must Use Semantic Quote Elements

- Block quotes: `<blockquote>` with optional `<cite>`
- Inline quotes: `<q>` (browser renders language-appropriate quote marks)

**Fails:**
```jsx
<p>"The best holiday of my life." — Marie D.</p>
```

**Passes:**
```jsx
<blockquote>
  <p>The best holiday of my life.</p>
  <footer>— <cite>Marie D., verified guest</cite></footer>
</blockquote>

<p>Our guests say <q>the food is exceptional</q> every year.</p>
```

---

## Topic 10 — Information Presentation

### RGAA 10.1 — Information Not Conveyed by Shape, Size, or Position Alone

Any visually-communicated information (via shape, size, or position) must also be available in text.

**Example failure:** "Click the round button to confirm" — shape is the only identifier.

**Cannot be verified statically.** Always `[MANUAL]`.

---

### RGAA 10.4 — Text Must Be Resizable to 200% Without Loss of Content

Use relative units (`rem`, `em`, `%`) for font sizes. Avoid fixed heights that could clip enlarged text.

```css
/* Avoid */
font-size: 14px;
height: 40px;

/* Prefer */
font-size: 0.875rem;
min-height: 2.5em;
```

**Cannot be verified in JSX alone** — requires CSS review. `[MANUAL]`.

---

### Semantic Emphasis Elements

| Element | Semantic meaning | Use case |
|---------|-----------------|----------|
| `<strong>` | Strong importance | Warnings, critical info |
| `<em>` | Stress emphasis | Tone, nuance in text |
| `<b>` | None (presentational) | Stylistic only — prefer CSS |
| `<i>` | None (presentational) | Technical terms, foreign words — prefer CSS |

```jsx
// Avoid when meaning is intended
<i>Warning: this action is irreversible</i>

// Prefer
<strong>Warning: this action is irreversible</strong>
```

---

## Topic 11 — Forms

### RGAA 11.1 — Every Form Field Must Have a Label

Each `<input>` (except `type="hidden"`), `<select>`, and `<textarea>` must have an associated label via:
- `<label htmlFor="id">` with matching `id` on the field
- Wrapping `<label>` (implicit association)
- `aria-label` attribute
- `aria-labelledby` pointing to a label element

**Fails:**
```html
<input type="text" placeholder="Enter your name" />   <!-- placeholder is not a label -->
<label>Name</label>
<input type="text" id="name" />                        <!-- label not linked -->
```

**Passes — HTML / Vue / Svelte / Astro:**
```html
<label for="name">Full name</label>
<input id="name" type="text" name="name" />

<!-- Wrapping label (implicit association) -->
<label>Full name <input type="text" name="name" /></label>

<!-- aria-label for icon-only inputs -->
<input type="search" aria-label="Search resorts" />
```

**Passes — React (JSX):**
```jsx
<label htmlFor="name">Full name</label>
<input id="name" type="text" name="name" />
```

---

### RGAA 11.2 — Placeholder Is Not a Substitute for a Label

`placeholder` text disappears on focus and has low contrast by default. It must never be the only label.

```jsx
// Correct — label + optional placeholder for hint
<label htmlFor="email">Email address</label>
<input
  id="email"
  type="email"
  placeholder="you@example.com"
  autoComplete="email"
/>
```

---

### RGAA 11.5 / 11.6 — Radio and Checkbox Groups Need fieldset + legend

When multiple radio buttons or checkboxes answer the same question, wrap them in `<fieldset>` with a `<legend>`.

**Fails:**
```jsx
<div>
  <label><input type="radio" name="size" value="S" /> Small</label>
  <label><input type="radio" name="size" value="M" /> Medium</label>
</div>
```

**Passes:**
```jsx
<fieldset>
  <legend>Choose your room size</legend>
  <label><input type="radio" name="size" value="S" /> Small</label>
  <label><input type="radio" name="size" value="M" /> Medium</label>
  <label><input type="radio" name="size" value="L" /> Large</label>
</fieldset>
```

---

### RGAA 11.10 — Required Fields Must Be Indicated

Required fields must be indicated:
- Visually (text or symbol like `*`)
- Programmatically with `required` and/or `aria-required="true"`
- With an explanation of the convention at the start of the form

```jsx
<p><span aria-hidden="true">*</span> Required fields</p>

<label htmlFor="email">
  Email address <span aria-hidden="true">*</span>
</label>
<input
  id="email"
  type="email"
  required
  aria-required="true"
/>
```

---

### RGAA 11.13 — Autocomplete for Personal Data Fields

Fields collecting personal data must have the `autoComplete` attribute to assist users with cognitive disabilities.

| Field | autoComplete value |
|-------|-------------------|
| Full name | `name` |
| First name | `given-name` |
| Last name | `family-name` |
| Email | `email` |
| Phone | `tel` |
| Address | `street-address` |
| Postal code | `postal-code` |
| Country | `country` |
| Credit card | `cc-number` |
| Birthday | `bday` |

```html
<!-- HTML / Vue / Svelte / Astro -->
<input type="email" id="email" autocomplete="email" />
<input type="tel" id="phone" autocomplete="tel" />
<input type="text" id="firstname" autocomplete="given-name" />
```

```jsx
{/* React (JSX) — camelCase */}
<input type="email" id="email" autoComplete="email" />
<input type="tel" id="phone" autoComplete="tel" />
<input type="text" id="firstname" autoComplete="given-name" />
```

---

## Topic 12 — Navigation

### RGAA 12.6 — Landmark Roles / HTML5 Sectioning Elements

| HTML element | Implicit ARIA role | Purpose |
|---|---|---|
| `<header>` | `banner` | Site header (not inside article/section) |
| `<nav>` | `navigation` | Navigation menus |
| `<main>` | `main` | Primary content (unique per page) |
| `<footer>` | `contentinfo` | Site footer (not inside article/section) |
| `<aside>` | `complementary` | Sidebar or related content |

```jsx
<header>
  <nav aria-label="Main navigation">...</nav>
</header>
<main id="main-content">
  <h1>Page title</h1>
  {/* page content */}
</main>
<aside aria-label="Related articles">...</aside>
<footer>...</footer>
```

Multiple `<nav>` elements must each have a unique `aria-label`:
```jsx
<nav aria-label="Main navigation">...</nav>
<nav aria-label="Footer links">...</nav>
<nav aria-label="Breadcrumb">...</nav>
```

---

### RGAA 12.7 / 12.8 — Skip Links

A "skip to content" link must be the **first focusable element** in the DOM. It must become visible when focused (do not use `display:none` or `visibility:hidden`).

```jsx
// In App.tsx or layout — MUST be first element in DOM
<a href="#main-content" className="skip-link">
  Skip to main content
</a>
```

```css
/* CSS — accessible hide: visible on focus only */
.skip-link {
  position: absolute;
  left: -9999px;
  top: auto;
  width: 1px;
  height: 1px;
  overflow: hidden;
}
.skip-link:focus {
  position: fixed;
  top: 0;
  left: 0;
  width: auto;
  height: auto;
  padding: 0.5rem 1rem;
  background: #000;
  color: #fff;
  z-index: 9999;
  overflow: visible;
}
```

---

### RGAA 12.4 — Breadcrumb Navigation

On multi-page sites, a breadcrumb trail is expected by RGAA validators. Use `aria-current="page"` on the current page item.

```jsx
<nav aria-label="Breadcrumb">
  <ol>
    <li><a href="/">Home</a></li>
    <li><a href="/resorts">Resorts</a></li>
    <li aria-current="page">Punta Cana</li>
  </ol>
</nav>
```

---

## Quick Fix Lookup Table

| Violation detected | Fix |
|-------------------|-----|
| `<img>` no alt | Add `alt="description"` |
| Decorative `<img>` | Add `alt="" aria-hidden="true"` |
| `<svg>` no name | Add `aria-label="..."` + `role="img"` + `<title>` child |
| Decorative `<svg>` | Add `aria-hidden="true" focusable="false"` |
| Complex image no desc | Wrap in `<figure>` + `<figcaption id="...">` + `aria-describedby` |
| Empty link | Add text content or `aria-label` |
| Ambiguous link text | Add `aria-label="[destination]"` |
| Image link empty alt | Add `alt="[destination description]"` |
| `<table>` no caption | Add `<caption>` as first child |
| `<th>` no scope | Add `scope="col"` or `scope="row"` |
| Layout table no role | Add `role="presentation"` (or replace with flexbox/grid) |
| Input no label | Add `<label htmlFor="id">` + matching `id` on input |
| Placeholder-only label | Add a `<label>` in addition to `placeholder` |
| Radio/checkbox no fieldset | Wrap in `<fieldset><legend>...</legend>` |
| Required not indicated | Add `required aria-required="true"` + visible `*` + explanation |
| Personal field no autocomplete | Add `autoComplete="[value]"` |
| `<html>` no `lang` | Add `lang="fr"` (or appropriate language) |
| No `<title>` | Add via `<Helmet>`, Next.js `Head`, or `metadata` |
| No `<meta charset>` | Add `<meta charset="UTF-8" />` in `index.html` |
| No `<main>` landmark | Add `<main id="main-content">` wrapping page content |
| No skip link | Add `<a href="#main-content">Skip to main content</a>` as first DOM element |
| Multiple `<nav>` unlabeled | Add distinct `aria-label` to each `<nav>` |
| Heading level skipped | Restructure headings; never skip levels |
| `<b>` / `<i>` for meaning | Replace with `<strong>` / `<em>` |
| List not using `<ul>`/`<ol>` | Replace `<div>` list with `<ul><li>` |
| Block quote as `<p>` | Replace with `<blockquote>` |

---

## Resources

- Official RGAA 4.1.2: https://accessibilite.numerique.gouv.fr/methode/criteres-et-tests/
- WCAG 2.1 Quick Reference: https://www.w3.org/WAI/WCAG21/quickref/
- ARIA Authoring Practices Guide: https://www.w3.org/WAI/ARIA/apg/
- axe-core (runtime testing): https://github.com/dequelabs/axe-core
- @axe-core/react: https://github.com/dequelabs/axe-core-npm/tree/develop/packages/react
- React accessibility docs: https://react.dev/learn/accessibility
- WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
