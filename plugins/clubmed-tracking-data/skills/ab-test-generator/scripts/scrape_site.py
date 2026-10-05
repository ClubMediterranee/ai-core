#!/usr/bin/env python3
"""
scrape_site.py — Extrait la charte de design + une carte des éléments d'une page web,
pour alimenter la génération d'A/B tests qui respectent le design du site.

Dépendances :
    pip install playwright --break-system-packages
    python -m playwright install chromium

Usage :
    python scrape_site.py "https://exemple.com/page" --out ./abtest_profile
    python scrape_site.py "https://exemple.com" --mobile-width 390 --desktop-width 1366

Sorties (dans --out) :
    design.json    — tokens de charte (couleurs, typo, espacements, boutons, breakpoints)
    elements.json  — éléments sémantiques détectés + sélecteurs robustes
    desktop.png    — capture desktop
    mobile.png     — capture mobile

Le script PROPOSE ; l'humain/Claude valide en croisant avec le HTML réel et les captures.
"""
import argparse
import json
import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit(
        "Playwright manquant. Installer :\n"
        "  pip install playwright --break-system-packages\n"
        "  python -m playwright install chromium"
    )

# ── JS exécuté dans la page pour extraire la charte ───────────────────────────
DESIGN_JS = r"""
() => {
  const px = v => parseFloat(v) || 0;
  const seen = (m, k) => { m[k] = (m[k] || 0) + 1; };

  const colorCount = {}, bgCount = {}, fontCount = {}, sizeCount = {}, radiusCount = {};
  const buttons = [];

  const all = document.querySelectorAll('*');
  for (const el of all) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    const cs = getComputedStyle(el);
    if (cs.color) seen(colorCount, cs.color);
    if (cs.backgroundColor && cs.backgroundColor !== 'rgba(0, 0, 0, 0)') seen(bgCount, cs.backgroundColor);
    if (cs.fontFamily) seen(fontCount, cs.fontFamily.split(',')[0].replace(/["']/g, '').trim());
    if (cs.fontSize) seen(sizeCount, cs.fontSize);
    if (px(cs.borderTopLeftRadius) > 0) seen(radiusCount, cs.borderTopLeftRadius);

    const tag = el.tagName.toLowerCase();
    const role = el.getAttribute('role');
    const isBtn = tag === 'button' || (tag === 'a' && (px(cs.paddingTop) > 4)) || role === 'button';
    if (isBtn && buttons.length < 12) {
      buttons.push({
        text: (el.textContent || '').trim().slice(0, 40),
        bg: cs.backgroundColor, color: cs.color,
        radius: cs.borderTopLeftRadius, padding: cs.padding,
        fontSize: cs.fontSize, fontWeight: cs.fontWeight,
      });
    }
  }

  const top = (m, n = 6) => Object.entries(m).sort((a, b) => b[1] - a[1]).slice(0, n).map(e => e[0]);

  // breakpoints depuis les media queries des feuilles de style
  const breakpoints = new Set();
  for (const sheet of document.styleSheets) {
    let rules; try { rules = sheet.cssRules; } catch (e) { continue; }
    if (!rules) continue;
    for (const rule of rules) {
      if (rule.media && rule.conditionText) {
        const m = rule.conditionText.match(/(\d+)px/g);
        if (m) m.forEach(x => breakpoints.add(parseInt(x)));
      }
    }
  }

  return {
    colors: { text: top(colorCount), background: top(bgCount) },
    typography: { families: top(fontCount), sizes: top(sizeCount, 8) },
    radius: top(radiusCount, 4),
    buttons,
    breakpoints: [...breakpoints].sort((a, b) => a - b),
  };
}
"""

# ── JS pour repérer les éléments sémantiques + sélecteurs robustes ────────────
ELEMENTS_JS = r"""
() => {
  const robustSelector = (el) => {
    if (!el) return null;
    // 1. id stable (pas hashé)
    if (el.id && !/[0-9a-f]{6,}/.test(el.id)) return '#' + CSS.escape(el.id);
    // 2. data-* / name / aria-label
    for (const a of ['data-testid','data-test','data-cy','data-qa','name']) {
      const v = el.getAttribute(a);
      if (v) return `[${a}="${v}"]`;
    }
    const aria = el.getAttribute('aria-label');
    if (aria) return `${el.tagName.toLowerCase()}[aria-label="${aria}"]`;
    // 3. classe sémantique lisible (non hashée)
    const cls = [...el.classList].find(c => c.length > 2 && !/[0-9a-f]{5,}/.test(c) && !/^css-/.test(c) && !/^sc-/.test(c));
    if (cls) return `${el.tagName.toLowerCase()}.${CSS.escape(cls)}`;
    // 4. tag + role
    const role = el.getAttribute('role');
    if (role) return `${el.tagName.toLowerCase()}[role="${role}"]`;
    return el.tagName.toLowerCase();
  };

  const fallbacks = (el) => {
    const fb = [];
    const txt = (el.textContent || '').trim().slice(0, 30);
    if (txt) fb.push({ type: 'text', value: txt });
    const cls = [...el.classList].find(c => /[0-9a-f]{5,}/.test(c) || /^css-/.test(c));
    if (cls) fb.push({ type: 'hashed-class-AVOID', value: '.' + cls });
    return fb;
  };

  const visible = (el) => {
    if (!el) return false;
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none';
  };

  const out = [];
  const push = (role, el) => {
    if (!el) return;
    out.push({
      role,
      selector: robustSelector(el),
      fallbacks: fallbacks(el),
      text: (el.textContent || '').trim().slice(0, 80),
      visible: visible(el),
      tag: el.tagName.toLowerCase(),
    });
  };

  // Titre principal
  push('title', document.querySelector('h1'));
  // Sous-titre
  const h1 = document.querySelector('h1');
  if (h1) {
    let sib = h1.nextElementSibling;
    if (sib && /^(h2|p)$/i.test(sib.tagName)) push('subtitle', sib);
  }
  // CTA principal : bouton/lien le plus "saillant" en haut de page
  const candidates = [...document.querySelectorAll('button, a[href]')].filter(visible).filter(el => {
    const r = el.getBoundingClientRect();
    return r.top < (window.innerHeight * 1.5) && r.width > 60 && r.height > 24;
  });
  candidates.sort((a, b) => (b.getBoundingClientRect().width * b.getBoundingClientRect().height)
                          - (a.getBoundingClientRect().width * a.getBoundingClientRect().height));
  if (candidates[0]) push('cta_primary', candidates[0]);

  // CTA e-commerce par intention
  const cart = [...document.querySelectorAll('button, a')].find(el => {
    const t = ((el.textContent || '') + ' ' + (el.getAttribute('aria-label') || '')).toLowerCase();
    return /panier|cart|acheter|buy|ajouter|add to/.test(t);
  });
  if (cart) push('cta_cart', cart);

  // Nav
  push('nav', document.querySelector('nav, [role="navigation"], header'));
  // Hero (premier grand bloc full-width)
  const hero = [...document.querySelectorAll('section, header, div')].find(el => {
    const r = el.getBoundingClientRect();
    return r.top < 50 && r.width > window.innerWidth * 0.9 && r.height > 200;
  });
  push('hero', hero);
  // Prix (motif monétaire)
  const price = [...document.querySelectorAll('*')].find(el => {
    if (el.children.length > 0) return false;
    return /(\d+[.,]\d{2})\s*(€|\$|£)|(\€|\$|\£)\s*\d/.test(el.textContent || '');
  });
  push('price', price);
  // Formulaire
  push('form', document.querySelector('form'));

  return out.filter(o => o.selector);
}
"""


def scrape(url, out_dir, desktop_w, mobile_w):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # ── Desktop ──
        ctx = browser.new_context(viewport={"width": desktop_w, "height": 900},
                                  user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                                              "Chrome/120.0 Safari/537.36"))
        page = ctx.new_page()
        page.goto(url, wait_until="networkidle", timeout=45000)
        page.wait_for_timeout(1500)

        design = page.evaluate(DESIGN_JS)
        elements_desktop = page.evaluate(ELEMENTS_JS)
        page.screenshot(path=str(out / "desktop.png"), full_page=False)
        ctx.close()

        # ── Mobile ──
        mctx = browser.new_context(viewport={"width": mobile_w, "height": 844},
                                   is_mobile=True, has_touch=True,
                                   user_agent=("Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                                               "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                                               "Version/16.0 Mobile/15E148 Safari/604.1"))
        mpage = mctx.new_page()
        mpage.goto(url, wait_until="networkidle", timeout=45000)
        mpage.wait_for_timeout(1500)
        elements_mobile = mpage.evaluate(ELEMENTS_JS)
        mpage.screenshot(path=str(out / "mobile.png"), full_page=False)
        mctx.close()

        browser.close()

    # Fusionner la visibilité par device dans la carte d'éléments
    by_role_mobile = {e["role"]: e for e in elements_mobile}
    for e in elements_desktop:
        m = by_role_mobile.get(e["role"])
        e["visible_desktop"] = e.pop("visible", None)
        e["visible_mobile"] = (m or {}).get("visible")
        e["selector_mobile"] = (m or {}).get("selector") if (m and m.get("selector") != e["selector"]) else None

    design_path = out / "design.json"
    elements_path = out / "elements.json"
    design_path.write_text(json.dumps({"url": url, **design}, indent=2, ensure_ascii=False))
    elements_path.write_text(json.dumps({"url": url, "elements": elements_desktop}, indent=2, ensure_ascii=False))

    print(f"[ok] design   → {design_path}")
    print(f"[ok] elements → {elements_path}  ({len(elements_desktop)} éléments)")
    print(f"[ok] captures → {out/'desktop.png'} , {out/'mobile.png'}")
    print("\nÉléments détectés :")
    for e in elements_desktop:
        print(f"  - {e['role']:<12} {e['selector']:<35} \"{(e['text'] or '')[:30]}\"")


def main():
    ap = argparse.ArgumentParser(description="Scrape charte + éléments d'une page pour A/B test")
    ap.add_argument("url")
    ap.add_argument("--out", default="./abtest_profile")
    ap.add_argument("--desktop-width", type=int, default=1366)
    ap.add_argument("--mobile-width", type=int, default=390)
    args = ap.parse_args()
    try:
        scrape(args.url, args.out, args.desktop_width, args.mobile_width)
    except Exception as e:
        print(f"[erreur] scraping impossible : {e}", file=sys.stderr)
        print("Vérifier l'accès réseau au domaine, ou fournir HTML/captures manuellement.",
              file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
