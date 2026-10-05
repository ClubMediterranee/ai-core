// =============================================================================
// TEMPLATE — variation.spec.js (QA Playwright Agent / A8)
// Adapter : TEST_URL, ROOT_CLASS, la table SELECTORS (copie exacte de la table A4),
// les assertions de contenu, et la section tracking selon le KPI du contrat.
// Exécution : npx playwright test variation.spec.js --reporter=list
// =============================================================================
const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

// --- Configuration (à adapter) -----------------------------------------------
const TEST_URL = 'https://exemple.com/page';           // URL du contrat
const ROOT_CLASS = 'abt-v1';                            // classe racine de la variation
const CSS_PATH = path.join(__dirname, 'variation.css');
const JS_PATH = path.join(__dirname, 'variation.js');

// Copie EXACTE de la table de ciblage A4 (sélecteurs recommandés)
const SELECTORS = {
  // cta: '[data-testid="add-to-cart"], .product-cta button', // exemple
};

const VIEWPORTS = [
  { name: 'desktop', viewport: { width: 1440, height: 900 }, isMobile: false },
  { name: 'mobile', viewport: { width: 390, height: 844 }, isMobile: true },
];

// --- Helpers ------------------------------------------------------------------
async function injectVariation(page) {
  await page.addStyleTag({ content: fs.readFileSync(CSS_PATH, 'utf8') });
  await page.addScriptTag({ content: fs.readFileSync(JS_PATH, 'utf8') });
}

function collectErrors(page, errors) {
  page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });
  page.on('pageerror', (err) => errors.push(String(err)));
}

// --- Tests par viewport ---------------------------------------------------------
for (const vp of VIEWPORTS) {
  test.describe(`[${vp.name}]`, () => {
    test.use({ viewport: vp.viewport, isMobile: vp.isMobile });

    test('1. la variation apparaît', async ({ page }) => {
      await page.goto(TEST_URL, { waitUntil: 'domcontentloaded' });
      await page.screenshot({ path: `before-${vp.name}.png`, fullPage: false });
      await injectVariation(page);
      await expect(page.locator(`.${ROOT_CLASS}`).first()).toBeVisible({ timeout: 5000 });
      // TODO assertions par changement du contrat, ex. :
      // await expect(page.locator(SELECTORS.cta).first()).toHaveText('Nouveau wording');
      await page.screenshot({ path: `after-${vp.name}.png`, fullPage: false });
    });

    test('2. pas de duplication en double injection', async ({ page }) => {
      await page.goto(TEST_URL, { waitUntil: 'domcontentloaded' });
      await injectVariation(page);
      await page.waitForSelector(`.${ROOT_CLASS}`, { timeout: 5000 });
      const before = await page.locator('[data-abt]').count();
      await page.addScriptTag({ content: fs.readFileSync(JS_PATH, 'utf8') }); // 2e injection
      await page.waitForTimeout(500);
      const after = await page.locator('[data-abt]').count();
      expect(after).toBe(before);
    });

    test('3. comportement au reload', async ({ page }) => {
      await page.goto(TEST_URL, { waitUntil: 'domcontentloaded' });
      await injectVariation(page);
      await page.reload({ waitUntil: 'domcontentloaded' });
      await injectVariation(page);
      await expect(page.locator(`.${ROOT_CLASS}`).first()).toBeVisible({ timeout: 5000 });
    });

    test('4. console propre pendant l\'injection', async ({ page }) => {
      const errors = [];
      collectErrors(page, errors);
      await page.goto(TEST_URL, { waitUntil: 'domcontentloaded' });
      const baseline = errors.length; // erreurs du site lui-même, hors périmètre
      await injectVariation(page);
      await page.waitForTimeout(1500);
      expect(errors.length, `Erreurs induites : ${errors.slice(baseline).join(' | ')}`)
        .toBe(baseline);
    });

    test('5. CTA cliquable', async ({ page }) => {
      test.skip(!SELECTORS.cta, 'Pas de CTA dans ce test');
      await page.goto(TEST_URL, { waitUntil: 'domcontentloaded' });
      await injectVariation(page);
      const cta = page.locator(SELECTORS.cta).first();
      await expect(cta).toBeVisible();
      await expect(cta).toBeEnabled();
      // TODO si navigation : await Promise.all([page.waitForURL(/…/), cta.click()]);
    });
  });
}

// --- Tracking (adapter au KPI primaire du contrat) -------------------------------
test('6. le tracking du KPI primaire se déclenche', async ({ page }) => {
  test.skip(!SELECTORS.cta, 'Adapter au KPI du contrat');
  await page.goto(TEST_URL, { waitUntil: 'domcontentloaded' });
  await injectVariation(page);
  await page.locator(SELECTORS.cta).first().click().catch(() => {});
  // Option A — dataLayer :
  const dl = await page.evaluate(() => (window.dataLayer || []).slice(-10));
  // TODO : expect(dl.some(e => e.event === 'nom_event_kpi')).toBe(true);
  // Option B — hit réseau : page.waitForRequest(r => r.url().includes('abtasty'|analytics))
  expect(Array.isArray(dl)).toBe(true); // placeholder — remplacer par l'assertion réelle
});

// --- SPA (activer uniquement si le contrat indique navigation dynamique) ---------
// test('7. ré-application après navigation SPA', async ({ page }) => { … });
