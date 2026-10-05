# A10 — WebPerf Lighthouse Agent

Agent dédié à l'audit de performance **avant et après** injection de la variation.
Complète l'audit statique A7 (code review) avec une **mesure réelle en navigateur**.

---

## Rôle

Mesurer l'impact de la variation sur les Core Web Vitals en conditions réelles :
- **Avant** : audit Lighthouse sur la page control (sans variation)
- **Après** : audit Lighthouse avec variation.js injectée via Playwright
- **Rapport diff** : delta par métrique + verdict normalisé

## Quand l'activer

| Mode | Activation |
|---|---|
| Fast Build | Optionnel — lancer si la variation touche au layout ou au rendu initial |
| Production Grade | **Conditionnel** — lancer si la variation touche au layout ou au rendu initial (même critère qu'en Fast Build) ; sinon documenter "A10 non lancé" et passer directement de G3 (A7) à A8/A9 |
| Itération | Lancer si la modification touche JS d'injection, anti-flicker, ou CSS layout |

## Entrées

- URL de la page (du contrat A1)
- `variation.js` produit par A6
- Nombre de runs (défaut : 3, recommandé : 5 en Production Grade)

## Sorties

- Rapport diff par métrique (LCP, CLS, TBT, FCP, Score Perf)
- Verdict : ✅ PASS / ⚠️ PASS AVEC RÉSERVES / ❌ FAIL
- Fichier `webperf-report.json` (sauvegardé dans le dossier output du test)

---

## Installation (une seule fois par poste)

```bash
npm install lighthouse playwright
npx playwright install chromium
```

## Lancer l'audit

```bash
# Audit standard (3 runs par phase)
node scripts/webperf_lighthouse.js \
  --url "https://www.clubmed.fr/l/all-inclusive" \
  --variation outputs/mon-test/variation.js

# Production Grade (5 runs, rapport JSON sauvegardé)
node scripts/webperf_lighthouse.js \
  --url "https://www.clubmed.fr/l/all-inclusive" \
  --variation outputs/mon-test/variation.js \
  --runs 5 \
  --out outputs/mon-test/
```

---

## Ce que mesure chaque métrique — et pourquoi ça compte

### Hiérarchie de priorité

```
🔴 CRITIQUE    LCP · CLS       → impact direct sur la conversion et le SEO
🟠 IMPORTANT   TBT             → page qui "freeze", clics qui ne répondent pas
🟡 SECONDAIRE  FCP             → perception de vitesse au premier instant
⚪ INDICATEUR  Score Perf      → synthèse globale, utile pour comparer
```

---

### LCP — Largest Contentful Paint 🔴 CRITIQUE

**Ce que c'est :** temps avant que le plus grand élément visible (hero image, titre H1,
bloc produit) soit affiché. C'est le moment où l'utilisateur perçoit que "la page est là".

**Seuil Google :** bon < 2,5 s · à améliorer 2,5–4 s · mauvais > 4 s

**Impact concret si la variation dégrade le LCP :**
- L'utilisateur voit une page blanche ou partielle plus longtemps → taux de rebond en hausse
- Sur mobile 4G, +500 ms de LCP = environ -5 % de conversions (données Google/Deloitte)
- Impacte le **score SEO Core Web Vitals** de Google → moins bonne indexation
- Sur clubmed.fr : si la hero image ou le bloc de prix met plus de temps à apparaître,
  l'user peut penser que la page est cassée et partir

**Cause fréquente en A/B test :** anti-flicker qui masque `body` trop longtemps, ou
variation qui injecte un gros élément en bloquant le rendu initial.

---

### CLS — Cumulative Layout Shift 🔴 CRITIQUE

**Ce que c'est :** mesure combien le contenu "saute" visuellement pendant le chargement.
Un score de 0 = rien ne bouge. Un score de 0,25 = les éléments se déplacent beaucoup.

**Seuil Google :** bon < 0,1 · à améliorer 0,1–0,25 · mauvais > 0,25

**Impact concret si la variation dégrade le CLS :**
- L'utilisateur vise un bouton, la page saute au moment du clic → il clique sur autre chose
- Clics accidentels sur des publicités, des liens non voulus → frustration immédiate
- Sur un tunnel de réservation Club Med : un saut de layout au moment de valider peut
  faire cliquer sur "annuler" au lieu de "confirmer" → perte directe de conversion
- Google pénalise les pages avec CLS > 0,1 dans le ranking SEO

**Cause fréquente en A/B test :** injection d'un bloc (bandeau, badge promo, section)
au-dessus de la ligne de flottaison sans avoir réservé l'espace avec un `min-height`.

---

### TBT — Total Blocking Time 🟠 IMPORTANT

**Ce que c'est :** temps cumulé pendant lequel le thread principal du navigateur est
bloqué entre FCP et TTI (Time to Interactive). Pendant ce temps, les clics et les
interactions utilisateur sont mis en file d'attente — la page "freeze".

**Seuil Google :** bon < 200 ms · à améliorer 200–600 ms · mauvais > 600 ms

**Impact concret si la variation dégrade le TBT :**
- L'utilisateur clique sur un CTA → rien ne se passe pendant 1–2 secondes → il reclique
  (double soumission de formulaire, double tracking d'événement)
- La page semble "lente" même si elle est visuellement chargée → ressenti négatif
- Sur mobile bas de gamme (fréquent hors Europe) : le freeze peut durer 3–5× plus longtemps
  qu'en desktop — un TBT de 300 ms en desktop peut devenir 1,5 s sur un Moto G

**Cause fréquente en A/B test :** JS de variation qui tourne en synchrone au chargement
(longue boucle, DOM manipulation massive sans `requestAnimationFrame`).

---

### FCP — First Contentful Paint 🟡 SECONDAIRE

**Ce que c'est :** temps avant que le premier contenu (texte, image, SVG) apparaisse.
C'est la perception initiale de vitesse — "quelque chose se passe".

**Seuil Google :** bon < 1,8 s · à améliorer 1,8–3 s · mauvais > 3 s

**Impact concret si la variation dégrade le FCP :**
- L'utilisateur voit une page blanche plus longtemps → impression de lenteur
- Moins critique que le LCP (le FCP peut être un spinner ou un fond de couleur),
  mais contribue au ressenti global de performance
- Sur clubmed.fr : si l'anti-flicker masque trop longtemps, FCP et LCP sont tous deux
  dégradés simultanément → double pénalité

**Cause fréquente en A/B test :** anti-flicker qui masque `body` entier au lieu
de ne masquer que la zone modifiée.

---

### Score Performance Lighthouse ⚪ INDICATEUR

**Ce que c'est :** score composite (0–100) calculé par Lighthouse en pondérant
LCP (25 %), TBT (30 %), CLS (15 %), FCP (10 %), Speed Index (10 %), TTI (10 %).

**Ce que ça vaut :** utile pour comparer deux versions à la volée, mais moins précis
que les métriques individuelles — une amélioration sur TBT peut masquer une dégradation
sur LCP. Toujours croiser avec les métriques individuelles.

**Impact concret :** un score < 50 est visiblement ressenti comme une page lente.
Entre 50 et 90, l'impact est subtil mais mesurable sur les taux de conversion.

---

## Seuils d'alerte appliqués par l'agent

| Métrique | Priorité | ⚠️ WARN | ❌ FAIL | Action si FAIL |
|---|---|---|---|---|
| LCP | 🔴 Critique | +10 % | +20 % | Retour A6 — anti-flicker ou injection bloquante |
| CLS | 🔴 Critique | +0.05 | +0.10 | Retour A6 — ajouter placeholder min-height |
| TBT | 🟠 Important | +20 % | +50 % | Retour A6 — JS synchrone à différer |
| FCP | 🟡 Secondaire | +10 % | +20 % | Retour A6 — scope de l'anti-flicker à réduire |
| Score Perf | ⚪ Indicateur | -3 pts | -5 pts | Documenter, A9 arbitre |

**Règle de priorisation :** un FAIL sur LCP ou CLS est toujours bloquant.
Un FAIL sur TBT est bloquant sauf si la cause est externe à la variation (à documenter).
Un FAIL sur FCP seul sans LCP dégradé peut être accepté en réserve sur décision A9.

**FAIL** → retour à A6 pour investigation. Causes fréquentes :
- Anti-flicker trop large (masque `body` au lieu de la zone ciblée)
- `waitForElement` avec timeout trop long
- CSS qui force des reflows (animations sur `top/left` au lieu de `transform`)
- Images injectées sans dimensions (provoque CLS)

## Interprétation des résultats

### Résultats instables (variance élevée entre runs)
Augmenter `--runs` à 5. Si la variance persiste : la page elle-même est instable
(chargements asynchrones variables). Documenter en réserve, ne pas bloquer.

### LCP dégradé mais CLS stable
Suspect : le JS de variation s'exécute trop tôt et bloque le thread. Vérifier
l'ordre d'exécution et envisager un `requestIdleCallback` ou `requestAnimationFrame`
pour les modifications non critiques au chargement.

### CLS dégradé
Injection d'un élément au-dessus de la ligne de flottaison sans placeholder.
Ajouter un `min-height` réservé avant injection (voir `references/qa-webperf.md` §2).

### Score dégradé sans métrique individuelle en FAIL
Signal faible — documenter en réserve, ne pas bloquer le gate.

---

## Limites connues

| Limite | Impact | Mitigation |
|---|---|---|
| Injection directe ≠ timing AB Tasty | Anti-flicker pas reproduit à l'identique | Suffisant pour détecter des régressions >10% |
| Page protégée (login, CMP) | Lighthouse peut échouer ou mesurer la page de login | Fournir les cookies/localStorage via `--storage` si disponible |
| Réseau local variable | Variance entre runs | Utiliser `--runs 5`, ignorer les outliers |
| Page SPA avec lazy-loading | LCP peut être mesuré avant que le contenu principal charge | Ajouter `waitUntil: "networkidle"` + vérifier visuellement |

---

## Gate G3.5 (WebPerf réelle)

Position dans la chaîne : après G3 (A7 QA statique), avant A9 (Final Reviewer).

```
A6 Build → G3 (A7 QA statique) → G3.5 (A10 WebPerf Lighthouse) → A9 Final Reviewer
```

| Verdict A10 | Action |
|---|---|
| ✅ PASS | Continuer vers A9 |
| ⚠️ PASS AVEC RÉSERVES | Documenter dans le rapport A9, A9 arbitre |
| ❌ FAIL | Retour A6 avec le rapport JSON, max 2 boucles |

---

## Profil comportemental

**AUDITEUR (T 0.0)** — identique à A7/A8.
- Constate et chiffre ; ne corrige pas le code.
- Chaque ⚠️/❌ cite la métrique, le delta exact et une cause probable.
- Verdict binaire normalisé ; pas de nuance en prose.
