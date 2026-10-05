#!/usr/bin/env node
/**
 * preview.js — Aperçu live d'une variation A/B sur le vrai site
 *
 * Usage :
 *   node scripts/preview.js --url <URL> --js <variation.js> [--css <variation.css>]
 *   node scripts/preview.js --url https://www.clubmed.fr/o/offre-de-derniere-minute \
 *                           --js outputs/ab-tests/cta-hover-effect/variation.js \
 *                           --css outputs/ab-tests/cta-hover-effect/variation.css \
 *                           --out outputs/ab-tests/cta-hover-effect/
 *
 * Options :
 *   --url   URL cible (obligatoire)
 *   --js    Chemin vers variation.js (obligatoire)
 *   --css   Chemin vers variation.css (optionnel)
 *   --out   Dossier de sortie pour les screenshots (défaut : dossier courant)
 *   --wait  Délai en ms avant screenshot après injection (défaut : 3000)
 *   --keep  Garde le navigateur ouvert pour inspection manuelle (flag, pas de valeur)
 *   --clip  Sélecteur CSS de la zone modifiée : restreint les screenshots à cette zone
 *           au lieu du viewport entier. À utiliser pour les captures de mise au point/
 *           debug (moins de poids, moins de contexte à recharger en itération). Les
 *           captures de couverture finale (before/after) restent pleine page : ne pas
 *           passer --clip pour celles-ci. Fallback silencieux en pleine page si le
 *           sélecteur est introuvable.
 *
 * Ce que fait ce script :
 *   1. Ouvre un vrai navigateur Chromium (headed) sur l'URL cible
 *   2. Ferme automatiquement le bandeau cookie si présent
 *   3. Prend un screenshot "control" (sans variation)
 *   4. Injecte le CSS puis le JS de la variation
 *   5. Attend le délai --wait
 *   6. Prend un screenshot "variation" (avec hover simulé sur la première card)
 *   7. Affiche les chemins des screenshots dans le terminal
 *   8. Si --keep : laisse le navigateur ouvert pour inspecter manuellement
 *
 * Dépendances (installer une fois dans le dossier du test) :
 *   npm install playwright
 *   npx playwright install chromium
 */

const { chromium } = require("playwright");
const fs   = require("fs");
const path = require("path");

// ── Parsing des arguments ────────────────────────────────────────────────────
const args = process.argv.slice(2);
function getArg(flag, defaultVal) {
  const i = args.indexOf(flag);
  if (i === -1) return defaultVal;
  return args[i + 1];
}
const hasFlag = (flag) => args.includes(flag);

const url        = getArg("--url",  null);
const jsPath     = getArg("--js",   null);
const cssPath    = getArg("--css",  null);
const outDir     = getArg("--out",  ".");
const wait       = parseInt(getArg("--wait", "3000"), 10);
const keep       = hasFlag("--keep");
const clipSelector = getArg("--clip", null);

if (!url || !jsPath) {
  console.error("Usage: node scripts/preview.js --url <URL> --js <variation.js> [--css <variation.css>] [--out <dir>] [--wait <ms>] [--keep] [--clip <selector>]");
  process.exit(1);
}

const jsCode  = fs.readFileSync(path.resolve(jsPath), "utf8");
const cssCode = cssPath ? fs.readFileSync(path.resolve(cssPath), "utf8") : null;

if (!fs.existsSync(outDir)) { fs.mkdirSync(outDir, { recursive: true }); }

const timestamp  = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
const shotBefore = path.join(outDir, `preview-control-${timestamp}.png`);
const shotAfter  = path.join(outDir, `preview-variation-${timestamp}.png`);

// ── Helpers ──────────────────────────────────────────────────────────────────
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function log(msg) { console.log(`[preview] ${msg}`); }

async function takeScreenshot(page, filePath) {
  if (clipSelector) {
    try {
      const el = page.locator(clipSelector).first();
      if (await el.isVisible({ timeout: 1500 })) {
        await el.screenshot({ path: filePath });
        return;
      }
    } catch (_) { /* sélecteur absent, fallback pleine page ci-dessous */ }
    log(`--clip "${clipSelector}" introuvable, fallback pleine page.`);
  }
  await page.screenshot({ path: filePath, fullPage: false });
}

// ── Main ─────────────────────────────────────────────────────────────────────
(async () => {
  log(`Ouverture de : ${url}`);
  log(`Variation JS : ${jsPath}`);
  if (cssCode) log(`Variation CSS : ${cssPath}`);

  const browser = await chromium.launch({
    headless: false,
    args: ["--start-maximized"],
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    locale: "fr-FR",
  });

  const page = await context.newPage();

  // Charger la page
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
  await sleep(2000); // laisser les scripts asynchrones se charger

  // Fermer le bandeau cookie automatiquement (patterns courants Club Med / Axeptio)
  const cookieSelectors = [
    'button:has-text("Continuer sans accepter")',
    'button:has-text("Tout refuser")',
    'button:has-text("Accepter et continuer")',
    '[data-testid="cookie-reject"]',
    '#axeptio_btn_dismiss',
    '.axeptio-close',
  ];
  for (const sel of cookieSelectors) {
    try {
      const btn = page.locator(sel).first();
      if (await btn.isVisible({ timeout: 1500 })) {
        await btn.click();
        log(`Bandeau cookie fermé via : ${sel}`);
        await sleep(1000);
        break;
      }
    } catch (_) { /* sélecteur absent, on continue */ }
  }

  // Screenshot CONTROL (avant variation)
  await takeScreenshot(page, shotBefore);
  log(`Screenshot control : ${shotBefore}`);

  // Injecter le CSS via une balise <style>
  if (cssCode) {
    await page.evaluate((css) => {
      const style = document.createElement("style");
      style.setAttribute("data-abt-preview", "css");
      style.textContent = css;
      document.head.appendChild(style);
    }, cssCode);
    log("CSS injecté.");
  }

  // Injecter et exécuter le JS
  await page.evaluate((js) => {
    const script = document.createElement("script");
    script.textContent = js;
    document.head.appendChild(script);
  }, jsCode);
  log(`JS injecté. Attente de ${wait}ms...`);

  await sleep(wait);

  // Simuler le hover sur la première card instrumentée par la variation
  try {
    // Cherche d'abord une card instrumentée (.abt-card), sinon fallback sur le premier article
    const cardSelector = ".abt-card, section#offer-products article";
    const firstCard = page.locator(cardSelector).first();
    if (await firstCard.isVisible({ timeout: 2000 })) {
      // Scroll natif pour amener la card en haut du viewport avec marge
      await page.evaluate((sel) => {
        const el = document.querySelector(sel);
        if (!el) return;
        const top = el.getBoundingClientRect().top + window.scrollY - 80;
        window.scrollTo({ top, behavior: "instant" });
      }, cardSelector);
      await sleep(300);
      await firstCard.hover({ position: { x: 10, y: 10 } });
      await sleep(500); // laisser la transition CSS se terminer (180ms + marge)
      log("Hover simulé sur la première card instrumentée.");
    }
  } catch (_) {
    log("Hover non simulé (card introuvable — screenshot sans hover).");
  }

  // Screenshot VARIATION (après injection + hover)
  await takeScreenshot(page, shotAfter);
  log(`Screenshot variation : ${shotAfter}`);

  log("─".repeat(60));
  log("RÉSUMÉ");
  log(`  Control   → ${shotBefore}`);
  log(`  Variation → ${shotAfter}`);
  log("─".repeat(60));

  if (keep) {
    log("Mode --keep actif : navigateur ouvert. Ctrl+C pour quitter.");
    await new Promise(() => {}); // attente infinie
  } else {
    await browser.close();
    log("Navigateur fermé. Preview terminé.");
  }
})().catch((err) => {
  console.error("[preview] Erreur :", err.message);
  process.exit(1);
});
