---
name: ab-test-generator
description: >
  Chaîne de production multi-agent d'A/B tests prête pour AB Tasty (compatible Kameleoon,
  VWO, Optimizely) à partir d'un brief CRO en langage naturel. Utilise ce skill dès qu'on
  parle d'A/B test, AB test, test A/B, "variation", "variante", "expérimentation", "CRO",
  "AB Tasty", "anti-flicker", "flickering", "task contract", "test contract", "QA Playwright",
  "webperf", ou qu'on demande de modifier un élément de page (titre, CTA, bouton, bannière,
  hero, prix…) pour tester une hypothèse — même sans le mot "A/B". Couvre : cadrage
  obligatoire en AB Test Task Contract, challenge de l'hypothèse et des KPI (testabilité
  statistique), scraping + audit UX de la page, ciblage DOM robuste avec fallbacks,
  génération JS+CSS séparés, double QA (webperf/flickering + tests Playwright), review
  finale avec quality gates, 4 modes : Fast Build, Production Grade, Mockup (maquettes de
  présentation) et Corrector (diagnostic + correction chirurgicale de code livré en recette),
  rollback, itération et historique des versions.
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, Agent, AskUserQuestion, TaskCreate, TaskUpdate, TaskList, WebFetch
version: 1.0.0
changelog:
  - version: 1.0.0
    date: 2026-10-01
    changes:
      - Migration vers le plugin clubmed-tracking-data (ai-core) — leçons et design system déplacés vers la Knowledgebase (dcx/cro/docs/)
created-at: 2026-10-01
created-by: "Floran Garrido <floran.garrido.ext@clubmed.com>"
---

# AB Test Generator V2 — chaîne de production multi-agent

## Démarrage de session — message obligatoire

**Dès que ce skill est chargé, avant toute chose :**

1. Résous le chemin de la Knowledgebase locale :
   ```bash
   KB="${CLUBMED_KB:-$HOME/.clubmed/knowledge-base}"
   ```
2. Si `$KB` n'existe pas, affiche :
   > Knowledgebase introuvable (`$KB`). Clone-la une fois avec :
   > `git clone https://github.com/ClubMediterranee/knowledge-base.git ~/.clubmed/knowledge-base`
   > Je continue sans les leçons accumulées ni le design system Trident UI pour cette session.

   Et continue sans bloquer — les leçons sont un accélérateur, pas une dépendance dure.
3. Si `$KB` existe, exécute (obligatoire — ne pas afficher les commandes brutes) :
   ```bash
   git -C "$KB" log -1 --format="%ci"
   grep -rh "^### " "$KB/dcx/cro/docs/lessons-learned/" | wc -l
   ```
4. Affiche la ligne suivante avec les valeurs réelles obtenues :

> Skill AB Test Generator V2 chargé — Knowledgebase à jour du **[RÉSULTAT commande 1]**, **[RÉSULTAT commande 2]** leçons Club Med intégrées, design system Trident UI chargé. Prêt.

Exemple attendu : `Skill AB Test Generator V2 chargé — Knowledgebase à jour du 2026-10-01 09:12:00 +0200, 14 leçons Club Med intégrées, design system Trident UI chargé. Prêt.`

---

Ce skill ne « génère pas du code » : il fait tourner une **chaîne de production d'A/B tests**
composée d'agents spécialisés, chacun avec un rôle, des entrées/sorties contractuelles et un
**profil de température** propre. L'orchestrateur (toi, en lisant ce fichier) route la demande,
incarne les agents dans l'ordre, applique les **quality gates**, et ne livre jamais un test
qui n'a pas passé les gates de son mode.

## Vue d'ensemble

```
                            ┌─────────────── ORCHESTRATEUR (A0) ───────────────┐
                            │  triage Fast Build / Production Grade + routing  │
                            └──────────────────────┬───────────────────────────┘
                                                   ▼
  A1 Scoping ──► A2 CRO Strategy ──► A3 Page Intelligence ──► A4 DOM & Targeting
  (contract)      (challenge)          (scraping + UX)          (sélecteurs)
                                                   │
                                                   ▼
              A5 UX/UI Design ──► A6 Front-End Build
               (rendu, wording)     (JS + CSS AB Tasty)
                                          │
                          ┌───────────────┼───────────────┐
                          ▼               ▼               ▼
                    A7 QA Webperf   A10 Lighthouse   A8 QA Playwright
                    (audit code)    (--runs 1)        (tests E2E)
                          │               │               │
                          └───────────────┴───────────────┘
                                          │
                                          ▼
                                  A9 Final Reviewer
                                  (arbitrage, gates)
```

**QA en parallèle (Production Grade)** : A7, A10 et A8 sont lancés simultanément
dès que A6 a écrit les fichiers sur disque. Gain estimé : ~8-10min.

**Règle d'or : chaque agent est incarné séquentiellement, avec son profil comportemental,
et produit son artefact de sortie avant de passer la main.** Les rôles détaillés, les
entrées/sorties et les prompts d'incarnation sont dans **`references/agents.md`** — lis-le
dès qu'un agent entre en scène.

## Températures : réel vs simulé

Un skill ne règle pas la température du modèle. Deux régimes :

1. **Simulé (défaut, dans cette conversation)** : chaque agent a un *profil comportemental*
   qui reproduit l'effet d'une température (nombre d'options générées, tolérance à la
   créativité, format de sortie contraint). Les profils sont dans `references/agents.md`
   et doivent être appliqués à la lettre.
2. **Réel (orchestration externe)** : si le workflow est porté vers l'API Anthropic,
   Claude Code (subagents) ou un artifact "Claudeception", utilise la table de mapping :

| Agent | T réelle | Profil simulé |
|---|---|---|
| A1 Scoping | 0.2 | DÉTERMINISTE |
| A2 CRO Strategy | 0.5 | ANALYTIQUE |
| A3 Page Intelligence | 0.4 | ANALYTIQUE |
| A4 DOM & Targeting | 0.1 | DÉTERMINISTE STRICT |
| A5 UX/UI Design | 0.7 | CRÉATIF CADRÉ |
| A6 Front-End Build | 0.1 | DÉTERMINISTE STRICT |
| A7 QA Webperf | 0.0 | AUDITEUR |
| A8 QA Playwright | 0.0 | AUDITEUR |
| A9 Final Reviewer | 0.2 | JUGE (raisonnement long, sortie froide) |
| A10 WebPerf Lighthouse | 0.0 | AUDITEUR |
| AC1 Diagnosis | 0.5 | ANALYTIQUE |
| AC2 Fix Patch | 0.1 | DÉTERMINISTE STRICT |
| AC3 Diff Review | 0.2 | JUGE |

---

## Étape 0 — Triage (A0 Orchestrateur)

Avant tout, classe la demande :

- **Fast Build** : changement simple (1–3 éléments), pas de client final exigeant, l'utilisateur
  veut du code vite, ou dit "rapide", "quick", "juste un petit test".
- **Production Grade** : test client, mécanique complexe (sticky, injection de section,
  formulaire), enjeu business explicite, ou l'utilisateur dit "prod", "client", "sérieux",
  "complet". **En cas de doute → Production Grade.**
- **Mockup Mode** : l'objectif est une maquette visuelle pour présentation (roadmap, pitch,
  exploration créative), ou l'utilisateur dit "maquette", "mockup", "roadmap", "présentation",
  "concept". Le code produit est quand même **production-ready côté webperf** (idempotent,
  scopé, sans flickering, sans CLS) pour pouvoir être réutilisé si l'idée est validée — seule
  la batterie de QA formelle et les tests Playwright sont skippés.
- **Corrector** : un test a déjà été développé par AB Tasty et des écarts sont constatés en
  recette. Ce mode ne s'active **que sur signal explicite** : l'utilisateur dit "mode corrector"
  ou "mode correction", OU fournit du code JS/CSS **externe** (livré par AB Tasty, pas généré
  dans cette conversation) en précisant qu'il vient de recette. Les mots seuls comme "corriger",
  "bug", "écart", "pas conforme" ne suffisent pas — ils peuvent apparaître dans une itération
  normale. En cas de doute → demander à l'utilisateur s'il veut le mode Corrector ou une
  itération classique. Inputs obligatoires : code JS + CSS brut, brief textuel, URL.
  Input optionnel : maquette UX. → `references/workflow-corrector.md`.
- **Itération / rollback / critique** : la demande porte sur un test existant de la
  conversation → `references/workflow-iteration.md`, pas de re-cadrage complet.

Annonce le mode choisi en une ligne et laisse l'utilisateur le changer.

---

## Étape 1 — Cadrage obligatoire : l'AB Test Task Contract (A1 + A2)

**Aucun code n'est généré sans contrat.** C'est le gate G1.

- **A1 Scoping Agent** transforme le brief en **AB Test Task Contract** (format complet dans
  **`references/task-contract.md`**) : contexte, page, pays/langue, device, objectif business,
  hypothèse, KPI primaire/secondaires, mécanique, contraintes UX/techniques, environnement
  (CMP, SPA, tests concurrents), inputs manquants, risques, agents à activer.
- **A2 CRO Strategy Agent** challenge le contrat : hypothèse falsifiable ? KPI mesurable dans
  AB Tasty ? **Testabilité statistique** (trafic, MDE, durée estimée) ? Risques de collision
  avec d'autres tests ? Il peut reformuler l'hypothèse et rétrograder/upgrader le KPI primaire,
  en justifiant.

En **Fast Build**, le contrat existe quand même mais en version courte (section "Contrat
minimal" de `task-contract.md`), auto-rempli avec hypothèses affichées ; validation utilisateur
en une question. En **Production Grade**, le contrat complet est affiché et **validé
explicitement** avant de continuer.

---

## Étape 2 — Connaissance de la page (A3 + A4)

- **A3 Page Intelligence Agent** : scrape la page avec `scripts/scrape_site.py` (charte,
  éléments, captures desktop/mobile) puis produit un **audit UX express** de la zone touchée
  (hiérarchie, densité, friction, cohérence charte). Lecture : `references/ciblage-elements.md`.

```bash
pip install playwright --break-system-packages -q
python -m playwright install chromium
python scripts/scrape_site.py "https://exemple.com/page" --out /home/claude/abtest_profile
```

> Si le scraping échoue (réseau restreint, login), demande HTML/captures/sélecteurs et
> continue sans bloquer — mais note-le comme risque dans le contrat.

- **A4 DOM & Targeting Agent** : fige les **sélecteurs robustes** (stables > fragiles),
  un **fallback par cible**, la **zone d'injection**, et la stratégie pour DOM dynamique
  (`waitForElement`, SPA/`pushState`, MutationObserver borné). Sortie : table de ciblage
  (cible → sélecteur → fallback → device → dynamique O/N). C'est le gate G2 : chaque
  sélecteur doit exister sur chaque device ciblé et être unique.

---

## Étape 3 — Design & build (A5 + A6)

- **A5 UX/UI Design Agent** (profil créatif cadré) : wording, hiérarchie visuelle, états
  (hover, focus, disabled), responsive, accessibilité AA. En Production Grade il propose
  **2 pistes** et recommande ; en Fast Build, une seule. Contraintes : `references/regles-ux.md`
  + charte du `design.json` + design system Trident UI
  (`$CLUBMED_KB/dcx/cro/docs/design-system-trident-ui.md`).
- **A6 Front-End Build Agent** (déterministe strict) : génère le code selon
  `references/ab-tasty.md` et les templates `assets/variation.css` / `assets/variation.js`.

Règles non négociables du build :

- JS et CSS **toujours séparés** ; le CSS fait tout ce que le CSS peut faire.
- **Vanilla JS**, zéro dépendance externe, zéro pollution globale (IIFE, pas de `var` global).
- **Idempotent** : guard anti-duplication (`data-abt` / flag), réexécutable sans doublon.
- **Wrapper/classe racine unique** de variation (`.abt-vN`), CSS entièrement scopé.
- Sélecteurs avec fallbacks, échec silencieux loggé (pas d'erreur console bloquante).
- Anti-flicker **intégré dans variation.js/variation.css** (pas de fichier séparé) avec
  **timeout de sécurité 3 s**, prévention CLS (réserver l'espace, pas d'injection
  layout-shifting au-dessus de la ligne de flottaison). Voir `assets/variation.js`/`.css`.
- MutationObserver **ciblé, borné et déconnecté** ; jamais de polling infini.
- Responsive via media queries (breakpoints du `design.json`), pas de branches JS device.
- Notes d'implémentation + rollback en fin de livraison.

---

## Étape 4 — Double QA (A7 + A8)

### A7 — QA Webperf / Flickering (gate G3)

Audit ligne à ligne du code : flickering, CLS, injection tardive, duplication,
MutationObserver non déconnecté, polling, reflows synchrones (lectures/écritures layout
entrelacées), listeners coûteux non délégués/non passifs, CSS non scopé, animations
non compositées, impact mobile, compatibilité AB Tasty. Grille complète et verdict
normalisé : **`references/qa-webperf.md`**. Lancer aussi le lint automatique :

```bash
python scripts/qa_check.py --css variation.css --js variation.js
```

Verdict : ✅ PASS / ⚠️ PASS AVEC RÉSERVES / ❌ FAIL. Un FAIL retourne à A6 (max 2 boucles,
ensuite escalade à l'utilisateur avec le blocage expliqué).

### A10 — WebPerf Lighthouse (gate G3.5, Production Grade — conditionnel)

Mesure réelle de l'impact de la variation sur les Core Web Vitals via Playwright + Lighthouse.
Audit en deux phases : page **control** (sans variation) puis page **variation** (variation.js
injectée). Rapport diff sur LCP, CLS, TBT, FCP, Score Perf. Documentation complète et seuils :
**`references/webperf-lighthouse.md`**.

**Activation, y compris en Production Grade** : lancer uniquement si la variation touche le
layout ou le rendu initial — nouvel élément injecté au-dessus de la ligne de flottaison,
changement de dimensions/police affectant le flux, JS s'exécutant tôt dans le chargement,
anti-flicker masquant une zone visible au chargement. **Ne pas lancer** pour un changement
de texte, de couleur, ou tout ce qui ne modifie ni les dimensions ni le timing d'affichage —
dans ce cas, documenter dans la livraison "A10 non lancé : changement sans impact plausible
sur le rendu initial (texte/couleur uniquement)". En cas de doute sur l'impact rendu → lancer
A10 (coût d'un run navigateur, contre le risque de livrer une régression de performance).

```bash
node scripts/webperf_lighthouse.js \
  --url "https://www.clubmed.fr/l/ma-page" \
  --variation outputs/mon-test/variation.js \
  --runs 3 \
  --out outputs/mon-test/
```

Verdict : ✅ PASS / ⚠️ PASS AVEC RÉSERVES / ❌ FAIL. Un FAIL retourne à A6. Position dans la
chaîne : après G3 (A7), avant A8 et A9.

### A8 — QA Playwright (gate G4, Production Grade)

Génère un fichier de tests Playwright depuis le template
**`assets/playwright.spec.template.js`**, adapté au test : apparition de la variation,
non-duplication (double injection simulée), reload, viewports desktop/mobile, erreurs
console, CTA cliquables, **déclenchement du tracking** (interception réseau/dataLayer),
screenshots avant/après, navigation SPA si applicable. Méthode et exécution :
**`references/qa-playwright.md`**. Si l'environnement ne permet pas d'exécuter les tests
(réseau), livre le fichier `.spec.js` prêt à lancer + la checklist manuelle équivalente,
et marque G4 « à exécuter côté client ».

---

## Étape 5 — Final review & livraison (A9)

**A9 Final Reviewer** (raisonnement approfondi, sortie froide) : relit contrat + code + les
deux rapports QA, arbitre les réserves, vérifie la cohérence bout à bout (le code fait-il ce
que le contrat promet ?), attribue une **note /10** et bloque sous **8/10** (gate G5) : retour
à l'agent fautif avec instructions précises, max 2 boucles.

Format de livraison :

1. **AB Test Task Contract** (version finale)
2. **Verdict Final Reviewer** (note /10 + arbitrages)
3. **Bloc CSS** (scopé `.abt-vN`, anti-flicker intégré si requis)
4. **Bloc JS** (idempotent, anti-flicker intégré si requis)
5. **Rapports QA** (A7 coché + A10 si activé + A8 : résultats ou spec à exécuter)
6. **Tests Playwright** (`variation.spec.js`, Production Grade)
7. **Notes d'implémentation AB Tasty** (où coller quoi, ordre, ciblage campagne)
8. **Preview sur le vrai site** (exécution automatique de `preview.js` après G5 validé)
9. **Rollback / kill switch** (cleanup mécanique via la classe racine)

La section Preview (8) est une **exécution automatique**, pas une commande à copier-coller.
Dès que A9 valide (note ≥ 8/10), lancer via Bash :

```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/preview.js" \
  --url {URL du contrat} \
  --js outputs/ab-tests/{nom-du-test}/variation.js \
  --css outputs/ab-tests/{nom-du-test}/variation.css \
  --out outputs/ab-tests/{nom-du-test}/ \
  --keep
```

Annoncer à l'utilisateur : "Le navigateur s'ouvre sur le vrai site avec la variation active —
survole les éléments ciblés pour voir l'effet. Ctrl+C dans le terminal pour fermer."

Fichiers séparés (`variation.css`, `variation.js`, `variation.spec.js`) si l'utilisateur
travaille en fichiers ; sinon blocs de code.

---

## Les trois workflows

### Fast Build
1. A0 triage → 2. A1 contrat minimal (1 question max) → 3. A3 scraping léger (ou HTML fourni)
→ 4. A4 ciblage → 5. A5 une piste UX → 6. A6 build → 7. A7 QA webperf + `qa_check.py`
→ 8. livraison avec checklist QA cochée + rollback. **Gates : G1 (allégé), G2, G3.**
A10 optionnel en Fast Build (lancer si la variation touche au layout ou au rendu initial).

**Dossier de sortie Fast Build : `outputs/ab-tests/{nom-du-test}/`**

### Production Grade
1. A0 triage → 2. A1 contrat complet → 3. A2 challenge CRO + testabilité → **validation
utilisateur** → 4. A3 scraping + audit UX → 5. A4 table de ciblage → 6. A5 deux pistes UX
→ 7. A6 build → 8. **[PARALLELE] A7 QA webperf + A10 WebPerf Lighthouse (si applicable,
voir critère ci-dessous) + A8 QA Playwright** → 9. A9 final review (note /10)
→ 10. livraison complète + checklist de mise en production.
**Gates : G1→G5, tous. G3.5 uniquement si A10 activé.**

> **A10 conditionnel même en Production Grade** : ne lancer Lighthouse que si la variation
> touche le layout/rendu initial (critère détaillé à la section A10 ci-dessus). Un changement
> de texte/couleur seul ne le déclenche pas — documenter "A10 non lancé" dans la livraison
> à la place. Ça évite un agent complet (navigateur + rapport détaillé relu par A9) sur les
> tests qui n'en ont pas besoin.
>
> **Parallélisation QA (gain ~8-10min)** : dès que A6 livre les fichiers sur disque,
> lancer A7 (+ A10 si activé) et A8 simultanément via des Bash en arrière-plan. Ils sont
> indépendants : A7 audite le code statiquement, A10 lance Lighthouse, A8 génère et exécute
> les tests Playwright. A9 attend les verdicts disponibles avant de conclure.
>
> A10 (si activé) : passer `--runs 1` au lieu de `--runs 3` (variabilité prod rend les runs
> multiples peu significatifs sur des pages à fort bruit réseau — 1 run suffit pour confirmer
> l'absence de dégradation). Gain ~4min supplémentaires.

**Dossier de sortie Production Grade : `outputs/ab-tests/{nom-du-test}/`**

### Mockup Mode
Pipeline allégé pour maquettes de présentation (roadmap, pitch, exploration créative).
Le code est **production-ready côté webperf** — si l'idée est validée, le code est réutilisable
sans refonte. Seules la batterie de QA formelle (A7 script, A10 Lighthouse, A8 Playwright)
et la review finale (A9) sont skippées.

1. A0 triage → 2. A1 contrat minimal (contexte + hypothèse visuelle, 0 question bloquante)
→ 3. A3 scraping page + lecture Trident UI si composant concerné
→ 4. A4 ciblage allégé (zones d'injection identifiées, pas de table de fallbacks exhaustive)
→ 5. A5 **2 pistes visuelles** (plus de créativité, objectif = inspirer)
→ 6. A6 build avec **standards webperf intégrés** : IIFE + polling borné (300ms × 20 = 6s max)
   + guard idempotence (`data-abt-{variation}`) + styles **100% inline** (`el.style.setProperty`)
   + animations via `<style>` injecté uniquement si keyframes nécessaires + pas de CLS
   + anti-flicker si injection above-the-fold + MutationObserver borné si SPA
→ 7. A6 auto-revue webperf inline (vérification ligne à ligne sans script)
→ 8. Livraison : **`console.js`** unique par piste, prêt console ET AB Tasty + checklist "passage en prod".

**Gates Mockup : G1 (allégé), G2 (zones seulement), G3 inline (auto-revue A6).**

Livraison Mockup — format :
1. **Contexte** (hypothèse visuelle + page cible)
2. **Piste(s) UX** (A5 — description + choix recommandé)
3. **`console-piste-a.js`** (et `console-piste-b.js` si 2 pistes) — un seul fichier par piste,
   tout en inline, exécutable en console F12 ET collable tel quel dans l'onglet JS d'AB Tasty.
   Pas de CSS séparé en Mockup Mode — les styles sont en inline dans le JS (contournement C2).
4. **Checklist "passage en prod"** (ce qui reste à faire : QA formelle, Playwright, Lighthouse)

> **Pas de HTML preview, pas de CSS séparé en Mockup.** Un seul fichier IIFE par piste :
> console F12 pour la démo, onglet JS AB Tasty pour la prod — même code, zéro réécriture.
> Appris sur clubmed.fr : le CSS global écrase les classes injectées, donc tout en inline.

**Dossier de sortie Mockup Mode : `outputs/maquettes/{nom-du-test}/`**

> **Règle d'or Mockup** : le code doit tenir la route techniquement dès la maquette.
> Un stakeholder qui valide l'idée ne devrait pas découvrir des problèmes de perf ou de
> flickering en passant en prod. A6 internalise la rigueur webperf même sans A7/A10.

### Corrector Mode

Pipeline de correction de code AB Tasty livré en recette. Pas de re-cadrage CRO, pas
de build from scratch — diagnostic des écarts, patch chirurgical, re-QA.

1. AC0 triage (Corrector détecté) → vérification des inputs obligatoires (JS + CSS + brief + URL)
→ 2. AC1 Diagnosis : table des écarts BUG / DRIFT / MISSING avec priorité HAUTE / MOYENNE / BASSE
→ 3. AC2 Fix Patch : corrections chirurgicales tracées `// FIX-[n]`, règles A6 respectées
→ 4. A7 QA Webperf : re-audit du code corrigé (obligatoire)
→ 5. A8 QA Playwright : optionnel — activé si le fix touche la logique, le tracking ou une SPA
→ 6. AC3 Diff Review : tableau de couverture + diff résumé + notes d'implémentation + rollback.
**Gates : GC1→GC4.**

Livraison Corrector — format :
1. **Table des écarts** (AC1 — BUG / DRIFT / MISSING, priorité, source dans le code)
2. **`variation-corrected.js`** (fixes marqués `// FIX-[n]`)
3. **`variation-corrected.css`** (fixes marqués `// FIX-[n]`)
4. **Rapport A7** (verdict webperf sur le code corrigé)
5. **Tests Playwright** (`variation.spec.js` — si A8 activé)
6. **Diff Review AC3** (tableau de couverture + diff résumé)
7. **Notes d'implémentation AB Tasty**
8. **Rollback / kill switch**

> Si un écart nécessite une réécriture structurelle complète (logique fondamentalement
> incompatible avec le brief), AC2 le signale avant de patcher et propose de basculer
> en Fast Build ou Production Grade.

**Dossier de sortie Corrector : `outputs/corrections/{nom-du-test}/`**

### Quality gates (récapitulatif)

| Gate | Mode | Condition de passage | Sinon |
|---|---|---|---|
| G1 Contrat | Fast + Prod + Mockup | Contrat validé (explicite en Prod, tacite en Fast/Mockup) | Pas de code |
| G2 Ciblage | Fast + Prod + Mockup | Sélecteurs/zones identifiés par device | Retour A4 |
| G3 Webperf | Fast + Prod | Verdict A7 ≠ FAIL | Retour A6 (max 2) |
| G3 inline | Mockup | Auto-revue A6 ligne à ligne | Retour A6 |
| G3.5 Lighthouse | Prod only, **si A10 activé** (variation touche layout/rendu initial) | Verdict A10 ≠ FAIL | Retour A6 (max 2) |
| G4 Playwright | Prod only | Tests verts ou spec livrée + checklist | Retour A6 |
| G5 Review | Prod only | Note A9 ≥ 8/10 | Retour agent fautif (max 2) |
| GC1 Inputs | Corrector | JS + CSS + brief + URL présents | Demander les manquants |
| GC2 Diagnosis | Corrector | Table AC1 produite (≥ 1 écart ou "aucun écart") | Arrêt |
| GC3 Webperf | Corrector | Verdict A7 ≠ FAIL sur code corrigé | Retour AC2 (max 2) |
| GC4 Couverture | Corrector | 100% écarts HAUTE priorité couverts | Retour AC2 |
| GC5 Anti-spirale | Corrector | ≤ 5 rounds de patch AC2 cumulés | Arrêt, proposer restart from scratch |

---

## Itération, rollback, critique

Comme en V1 : chaque modification part de la **dernière version** (historique V1/V2/V3 +
changelog), le rollback est mécanique grâce au scoping, la design critique confronte à la
charte. Procédures : `references/workflow-iteration.md` et `references/qa-checklist.md`.
**La QA rejouée est proportionnée au delta** (grille de triage cosmétique/structurel dans
`workflow-iteration.md` §3) — un ajustement cosmétique ne redéclenche pas A7/A8/A9 en entier.

---

## Knowledgebase — leçons & design system

Les leçons accumulées (`lessons-learned/`) et le design system Trident UI
(`design-system-trident-ui.md`) ne vivent plus dans ce plugin : ils sont partagés entre équipes
via le repo `knowledge-base`, sous `dcx/cro/docs/`.

- **Chemin local attendu** : `${CLUBMED_KB:-$HOME/.clubmed/knowledge-base}`.
- **Première utilisation sur une machine** : si ce dossier est absent, le hook `SessionStart`
  affiche la commande de clone (voir message d'absence ci-dessus) — jamais de clone automatique
  silencieux d'un repo d'entreprise.
- **Mise à jour** : un hook `SessionStart` (`hooks/kb_pull.sh`) pull silencieusement la
  Knowledgebase à chaque démarrage si elle existe déjà.
- **Contribution** : en fin de session, si une leçon nouvelle et généralisable a été identifiée,
  un hook `Stop` (`hooks/lessons_pr.py`) l'ajoute à la Knowledgebase via une branche dédiée et
  ouvre/complète une pull request — jamais de push direct sur `main`. Pas de nouvelle leçon à
  chaque session : c'est attendu et normal.

---

## Fichiers de référence

Lecture au moment du besoin (progressive disclosure) :

| Fichier | Quand |
|---|---|
| `references/agents.md` | Dès qu'un agent est incarné — rôles, I/O, profils T + renvoi vers les leçons Club Med (Knowledgebase) à appliquer |
| `references/task-contract.md` | Étape 1 — formats de contrat complet et minimal |
| `references/brief-standard.md` | Cadrage conversationnel (questions, MVB) |
| `references/ciblage-elements.md` | Étape 2 — scraping + sélecteurs |
| `references/ab-tasty.md` | Étape 3 — conventions plateforme + flicker |
| `references/regles-ux.md` | Étape 3 — règles UX + multi-device |
| `references/qa-webperf.md` | Étape 4 — grille d'audit A7 |
| `references/qa-playwright.md` | Étape 4 — génération/exécution des tests A8 |
| `references/qa-checklist.md` | QA manuelle + design critique |
| `references/workflow-iteration.md` | Itération, historique, rollback |
| `references/workflow-corrector.md` | Mode Corrector — diagnostic, patch, re-QA |

Scripts : `scripts/scrape_site.py`, `scripts/qa_check.py`.
Templates : `assets/variation.css`, `assets/variation.js` (anti-flicker intégré),
`assets/playwright.spec.template.js`.
