#!/usr/bin/env node
/**
 * webperf_lighthouse.js — Audit Lighthouse avant/après injection de variation
 *
 * Usage :
 *   node scripts/webperf_lighthouse.js --url <URL> --variation <path/to/variation.js>
 *   node scripts/webperf_lighthouse.js --url <URL> --variation variation.js --runs 3 --out ./
 *
 * Dépendances (installer une fois) :
 *   npm install lighthouse playwright
 *   npx playwright install chromium
 *   sudo apt-get install -y libnspr4 libnss3 libatk1.0-0t64 libatk-bridge2.0-0t64 libcups2t64 libdrm2 libgbm1 libasound2t64
 *
 * Codes de sortie : 0 = PASS · 1 = WARN · 2 = FAIL
 */

const lighthouse  = require("lighthouse").default;
const { chromium } = require("playwright");
const fs   = require("fs");
const path = require("path");
const net  = require("net");

// ── Seuils d'alerte ──────────────────────────────────────────────────────────
const THRESHOLDS = {
  lcp:   { warn: 0.10, fail: 0.20, unit: "ms",  label: "LCP" },
  cls:   { warn: 0.05, fail: 0.10, unit: "abs",  label: "CLS" },
  tbt:   { warn: 0.20, fail: 0.50, unit: "ms",  label: "TBT" },
  fcp:   { warn: 0.10, fail: 0.20, unit: "ms",  label: "FCP" },
  score: { warn: -3,   fail: -5,   unit: "pts",  label: "Score Perf" },
};

// ── Trouver un port libre ─────────────────────────────────────────────────────
function getFreePort() {
  return new Promise((resolve, reject) => {
    const srv = net.createServer();
    srv.listen(0, "127.0.0.1", () => {
      const port = srv.address().port;
      srv.close(() => resolve(port));
    });
    srv.on("error", reject);
  });
}

// ── Extraire les métriques du rapport Lighthouse ─────────────────────────────
function extractMetrics(lhResult) {
  const a = lhResult.lhr.audits;
  return {
    lcp:   a["largest-contentful-paint"]?.numericValue ?? 0,
    cls:   a["cumulative-layout-shift"]?.numericValue  ?? 0,
    tbt:   a["total-blocking-time"]?.numericValue      ?? 0,
    fcp:   a["first-contentful-paint"]?.numericValue   ?? 0,
    score: Math.round((lhResult.lhr.categories?.performance?.score ?? 0) * 100),
  };
}

// ── Moyenne sur N métriques ───────────────────────────────────────────────────
function avgMetrics(list) {
  const keys = Object.keys(list[0]);
  const result = {};
  for (const k of keys) {
    const val = list.reduce((s, m) => s + m[k], 0) / list.length;
    result[k] = k === "score" ? Math.round(val) : val;
  }
  return result;
}

// ── Un run Lighthouse via Playwright (port de debug partagé) ─────────────────
async function oneRun(url, variationCode) {
  const port = await getFreePort();

  const browser = await chromium.launch({
    args: [
      `--remote-debugging-port=${port}`,
      "--no-sandbox",
      "--disable-setuid-sandbox",
    ],
    headless: true,
  });

  try {
    // Si variation : ouvrir la page et injecter avant l'audit
    if (variationCode) {
      const page = await browser.newPage();
      await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
      await page.addScriptTag({ content: variationCode });
      await page.waitForTimeout(1500);
      await page.close();
    }

    const result = await lighthouse(url, {
      port,
      output: "json",
      logLevel: "error",
      onlyCategories: ["performance"],
      formFactor: "desktop",
      screenEmulation: { disabled: true },
      disableStorageReset: !!variationCode,
    });

    return extractMetrics(result);
  } finally {
    await browser.close();
  }
}

// ── N runs avec moyenne ───────────────────────────────────────────────────────
async function auditPhase(url, variationCode, runs, label) {
  const results = [];
  for (let i = 0; i < runs; i++) {
    process.stdout.write(`  ${label} run ${i + 1}/${runs} … `);
    const m = await oneRun(url, variationCode);
    results.push(m);
    console.log(`LCP ${Math.round(m.lcp)} ms · CLS ${m.cls.toFixed(3)} · Score ${m.score}`);
    if (i < runs - 1) await new Promise((r) => setTimeout(r, 2000));
  }
  return avgMetrics(results);
}

// ── Comparer control vs variation ────────────────────────────────────────────
function compare(control, variation) {
  const findings = [];
  let exitCode = 0;

  for (const [key, cfg] of Object.entries(THRESHOLDS)) {
    const before = control[key];
    const after  = variation[key];
    const delta  = after - before;
    const pct    = before !== 0 ? delta / Math.abs(before) : 0;

    let status = "✅ PASS";
    if (cfg.unit === "abs") {
      if (delta >= cfg.fail)      { status = "❌ FAIL";  exitCode = Math.max(exitCode, 2); }
      else if (delta >= cfg.warn) { status = "⚠️  WARN"; exitCode = Math.max(exitCode, 1); }
    } else if (cfg.unit === "pts") {
      if (delta <= cfg.fail)      { status = "❌ FAIL";  exitCode = Math.max(exitCode, 2); }
      else if (delta <= cfg.warn) { status = "⚠️  WARN"; exitCode = Math.max(exitCode, 1); }
    } else {
      if (pct >= cfg.fail)        { status = "❌ FAIL";  exitCode = Math.max(exitCode, 2); }
      else if (pct >= cfg.warn)   { status = "⚠️  WARN"; exitCode = Math.max(exitCode, 1); }
    }

    const sign = delta >= 0 ? "+" : "";
    const fmtDelta = cfg.unit === "ms"
      ? `${sign}${Math.round(delta)} ms (${sign}${(pct * 100).toFixed(1)} %)`
      : cfg.unit === "abs"
      ? `${sign}${delta.toFixed(3)}`
      : `${sign}${delta.toFixed(1)} pts`;

    findings.push({
      metric: cfg.label,
      before: cfg.unit === "ms"  ? `${Math.round(before)} ms`
            : cfg.unit === "pts" ? `${before}/100`
            : before.toFixed(3),
      after:  cfg.unit === "ms"  ? `${Math.round(after)} ms`
            : cfg.unit === "pts" ? `${after}/100`
            : after.toFixed(3),
      delta: fmtDelta,
      status,
    });
  }

  return { findings, exitCode };
}

// ── Affichage du rapport ──────────────────────────────────────────────────────
function printReport(url, variationPath, findings, exitCode, runs) {
  const verdict = exitCode === 0 ? "✅ PASS"
                : exitCode === 1 ? "⚠️  PASS AVEC RÉSERVES"
                : "❌ FAIL";

  console.log("\n" + "═".repeat(70));
  console.log("  RAPPORT WEBPERF LIGHTHOUSE — Avant / Après variation");
  console.log("═".repeat(70));
  console.log(`  URL       : ${url}`);
  console.log(`  Variation : ${path.basename(variationPath)}`);
  console.log(`  Runs      : ${runs} par phase`);
  console.log("─".repeat(70));
  console.log(
    `  ${"Métrique".padEnd(20)} ${"Avant".padEnd(12)} ${"Après".padEnd(12)} ${"Δ".padEnd(22)} Statut`
  );
  console.log("─".repeat(70));
  for (const f of findings) {
    console.log(
      `  ${f.metric.padEnd(20)} ${f.before.padEnd(12)} ${f.after.padEnd(12)} ${f.delta.padEnd(22)} ${f.status}`
    );
  }
  console.log("─".repeat(70));
  console.log(`  Verdict : ${verdict}`);
  console.log("═".repeat(70));
  console.log(`
  Seuils & impact utilisateur :
    LCP  ⚠️ +10 %  ❌ +20 %  → page perçue lente, rebond en hausse, SEO pénalisé
    CLS  ⚠️ +0.05  ❌ +0.10  → layout qui saute, clics accidentels, frustration
    TBT  ⚠️ +20 %  ❌ +50 %  → page qui freeze, clics ignorés
    FCP  ⚠️ +10 %  ❌ +20 %  → page blanche prolongée, impression de lenteur
    Score⚠️ -3 pts ❌ -5 pts → indicateur global Lighthouse
  `);
}

// ── Sauvegarde JSON ───────────────────────────────────────────────────────────
function saveJson(outDir, url, variationPath, control, variation, findings, exitCode, runs) {
  if (!outDir) return;
  fs.mkdirSync(outDir, { recursive: true });
  const report = {
    timestamp: new Date().toISOString(),
    url, variationPath, runs, control, variation, findings,
    verdict: exitCode === 0 ? "PASS" : exitCode === 1 ? "PASS_AVEC_RESERVES" : "FAIL",
  };
  const file = path.join(outDir, "webperf-report.json");
  fs.writeFileSync(file, JSON.stringify(report, null, 2));
  console.log(`  Rapport JSON → ${file}\n`);
}

// ── CLI ───────────────────────────────────────────────────────────────────────
async function main() {
  const args = process.argv.slice(2);
  const get  = (f) => { const i = args.indexOf(f); return i !== -1 ? args[i + 1] : null; };

  const url           = get("--url");
  const variationPath = get("--variation");
  const runs          = parseInt(get("--runs") || "3", 10);
  const outDir        = get("--out");

  if (!url || !variationPath) {
    console.error("Usage : node webperf_lighthouse.js --url <URL> --variation <path> [--runs 3] [--out <dir>]");
    process.exit(1);
  }
  if (!fs.existsSync(variationPath)) {
    console.error(`Fichier introuvable : ${variationPath}`);
    process.exit(1);
  }

  const variationCode = fs.readFileSync(variationPath, "utf8");

  console.log(`\n⏳ Phase CONTROL (${runs} runs) …`);
  const control = await auditPhase(url, null, runs, "control");

  console.log(`\n⏳ Phase VARIATION (${runs} runs) …`);
  const variation = await auditPhase(url, variationCode, runs, "variation");

  const { findings, exitCode } = compare(control, variation);
  printReport(url, variationPath, findings, exitCode, runs);
  saveJson(outDir, url, variationPath, control, variation, findings, exitCode, runs);

  process.exit(exitCode);
}

main().catch((err) => {
  console.error("\nErreur :", err.message);
  process.exit(2);
});
