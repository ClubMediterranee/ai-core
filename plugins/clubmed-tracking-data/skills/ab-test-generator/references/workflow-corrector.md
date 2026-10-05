# Workflow Corrector — correction de code AB Tasty en recette

## Quand utiliser ce mode

Le mode **Corrector** s'active quand un test a déjà été développé par AB Tasty et qu'en
recette, des écarts sont constatés entre le code livré et le brief. Il ne refait pas le
pipeline complet — il diagnostique, patche, et re-valide.

Ce n'est pas une itération créative (→ `workflow-iteration.md`). C'est une correction
chirurgicale sur du code existant avec un brief de référence.

---

## Inputs

| Input | Obligatoire | Format attendu |
|---|---|---|
| Code JS livré | ✅ | Bloc brut, sans commentaires AB Tasty |
| Code CSS livré | ✅ | Bloc brut |
| Brief textuel | ✅ | Description libre des écarts constatés OU brief original |
| URL de la page | ✅ | URL de recette ou de production |
| Maquette UX | ❌ | Image, Figma, PDF — seulement si disponible |

> Si la maquette est absente, AC1 déduit les attendus visuels du brief textuel.
> Si l'URL est inaccessible (login), noter comme risque mais continuer.

---

## Pipeline

```
Inputs reçus
  │
  ▼
AC0 Triage (Corrector détecté)
  │
  ▼
AC1 Diagnosis Agent
  → lecture code + brief (+ maquette si dispo)
  → scraping URL ciblé si sélecteur suspect (optionnel, sur décision AC1)
  → table des écarts : TYPE | ZONE | ATTENDU | OBSERVÉ | PRIORITÉ | SÉLECTEUR SUSPECT
  │
  ▼
AC2 Fix Patch Agent
  → corrections chirurgicales tracées vers chaque écart AC1
  → chaque fix marqué // FIX-[n] dans le code
  → règles non négociables A6 respectées (idempotence, scoping, IIFE, etc.)
  │
  ▼
A7 QA Webperf
  → re-audit du code corrigé
  → même grille que pour un build standard (references/qa-webperf.md)
  │
  ┌─ si fix touche logique / tracking / SPA ─┐
  ▼                                          ▼
A8 QA Playwright (optionnel)          (skippé sinon)
  │
  ▼
AC3 Diff Review Agent
  → tableau avant/après par écart
  → confirmation 100% couverture
  → notes d'implémentation AB Tasty
  → rollback si nécessaire
```

---

## AC1 — Diagnosis Agent

**Objectif** : produire une table exhaustive des écarts entre le code livré et le brief.

**Méthode** :
1. Lire le brief textuel et la maquette (si disponible) → extraire la liste des attendus.
2. Lire le code JS + CSS → extraire la liste de ce qui est implémenté.
3. Croiser les deux → identifier chaque écart.
4. Pour chaque sélecteur qui paraît fragile ou potentiellement mort, le signaler (mais ne
   pas lancer le scraping automatiquement — le noter comme "SÉLECTEUR À VÉRIFIER").

**Format de sortie — table des écarts** :

| # | TYPE | ZONE | ATTENDU | OBSERVÉ DANS LE CODE | PRIORITÉ | NOTE |
|---|---|---|---|---|---|---|
| 1 | DRIFT | CTA hero | Texte "Réserver maintenant" | Texte "Voir les offres" | HAUTE | — |
| 2 | BUG | Mobile | Sticky visible sous 768px | Observer borné mais jamais déconnecté | HAUTE | Risque perf |
| 3 | MISSING | Bandeau promo | Badge "-10%" sur l'image | Absent du code | MOYENNE | — |
| 4 | DRIFT | Couleur CTA | #E30613 (charte Rouge Club Med) | #FF0000 | BASSE | Charte |

**Types d'écarts** :
- `BUG` : code présent mais cassé ou risqué (sélecteur mort, logique inversée, MutationObserver
  non déconnecté, duplication non guardée, erreur JS silencieuse).
- `DRIFT` : code présent mais ne correspond pas au brief (mauvais wording, mauvaise couleur,
  mauvais device, mauvaise zone).
- `MISSING` : fonctionnalité attendue dans le brief, absente du code.

**Priorités** :
- `HAUTE` : bloquant pour la recette (la variation ne fait pas ce qu'elle promet).
- `MOYENNE` : non-conforme mais non bloquant (impact UX modéré).
- `BASSE` : amélioration, finition, charte.

**Profil** : ANALYTIQUE (0.5). Chaque ligne de la table est sourcée dans le code (numéro de
ligne ou pattern) ET dans le brief. Pas d'écart inventé, pas d'écart omis par complaisance.

---

## AC2 — Fix Patch Agent

**Objectif** : corriger chaque écart de la table AC1, chirurgicalement, sans réécrire ce
qui fonctionne.

**Méthode** :
1. Pour chaque écart, produire le patch minimal.
2. Marquer chaque modification dans le code : `// FIX-[n] — [description courte]`.
3. Respecter strictement les règles non négociables du build (SKILL.md §Étape 3) :
   idempotence, scoping `.abt-vN`, IIFE, zéro dépendance externe, fallbacks, anti-flicker
   si injection above-the-fold, MutationObserver borné + disconnect.
4. Ne pas toucher au code qui ne correspond à aucun écart AC1 — même si AC2 pense
   qu'il pourrait être amélioré. Les améliorations hors-scope sont notées en bas de
   livraison sous "Observations non corrigées (hors-scope brief)".

**Sortie** :
- `variation-corrected.css` (scopé, avec `// FIX-[n]` sur chaque patch)
- `variation-corrected.js` (idempotent, IIFE, avec `// FIX-[n]` sur chaque patch)
- Liste des fixes appliqués : `FIX-[n] → écart #[n] → ligne(s) modifiée(s)`

**Profil** : DÉTERMINISTE STRICT (0.1). Un seul patch par écart, le plus minimal et sûr.
Si un écart nécessite une réécriture structurelle (ex. logique cassée à la racine), le
signaler à l'utilisateur avant de patcher.

---

## AC3 — Diff Review Agent

**Objectif** : produire le rapport de clôture de la correction.

**Contenu** :

### 1. Tableau de couverture

| Écart AC1 # | TYPE | Statut | Fix appliqué |
|---|---|---|---|
| 1 | DRIFT | ✅ Corrigé | FIX-1 — L.14 variation.js |
| 2 | BUG | ✅ Corrigé | FIX-2 — L.31 variation.js |
| 3 | MISSING | ✅ Corrigé | FIX-3 — L.9 variation.css + L.47 variation.js |
| 4 | DRIFT | ✅ Corrigé | FIX-4 — L.3 variation.css |

### 2. Diff résumé (prose courte)

Un paragraphe max par écart : ce qui était, ce qui est maintenant, pourquoi c'est juste.

### 3. Observations hors-scope (optionnel)

Ce qu'AC2 a vu mais n'a pas touché (hors brief). L'utilisateur décide s'il veut
une itération supplémentaire.

### 4. Notes d'implémentation AB Tasty

Reprendre les instructions d'implémentation (où coller JS / CSS dans AB Tasty, ordre,
ciblage campagne) — identiques à la livraison standard.

### 5. Rollback

Rappel du snippet de cleanup (classe racine + `data-abt`) si le test doit être
désactivé en urgence.

**Profil** : JUGE (0.2). Vérifie que chaque écart de la table AC1 a bien son FIX
correspondant. Si un écart HAUTE priorité n'est pas couvert → bloque la livraison
et remonte à AC2.

---

## Gates Corrector

| Gate | Condition de passage | Sinon |
|---|---|---|
| GC1 Inputs | Code JS + CSS + brief + URL présents | Demander les manquants |
| GC2 Diagnosis | Table AC1 validée (au moins 1 écart, sinon signaler "aucun écart trouvé") | Arrêt — rien à corriger |
| GC3 Webperf | Verdict A7 ≠ FAIL sur le code corrigé | Retour AC2 (max 2 boucles) |
| GC4 Couverture | 100% des écarts HAUTE priorité couverts par un FIX | Retour AC2 |
| GC5 Anti-spirale | ≤ 5 rounds de patch AC2 cumulés sur ce test dans la session | Arrêt — proposer un restart from scratch (voir ci-dessous) |

### GC5 — Anti-spirale (plafond 5 rounds)

Un **round** = tout passage par AC2 qui produit un nouveau patch, que ce soit pour couvrir
la table AC1 initiale ou pour corriger une régression signalée après un round précédent.
Compte cumulativement sur le même test, même si l'utilisateur reformule sa demande entre-temps.

**Pourquoi** : le patching chirurgical répété (`// FIX-N` empilés) a déjà dégradé un résultat
au lieu de l'améliorer sur un test réel (24 rounds en une session, régressions détectées
plusieurs fixes plus tard sans revalidation visuelle systématique). Au-delà d'un certain
nombre de patches, les interactions non prévues entre fixes successifs coûtent plus cher à
diagnostiquer qu'un rebuild propre.

**Au round 5 sans convergence complète** (l'utilisateur signale encore un écart après le
5ᵉ patch) : **arrêter le patching**, ne pas lancer de 6ᵉ round automatiquement. Dire
explicitement à l'utilisateur :
- combien de rounds ont été faits et sur quoi,
- que la limite anti-spirale est atteinte,
- proposer soit (a) une réécriture propre à partir des dernières captures/attendus validés
  (Fast Build ou Production Grade depuis zéro), soit (b) continuer manuellement si
  l'utilisateur préfère assumer le risque — mais jamais enchaîner un 6ᵉ round sans cette
  confirmation explicite.

---

## Dossier de sortie

```
outputs/corrections/{nom-du-test}/
  ├── variation-corrected.js
  ├── variation-corrected.css
  ├── diagnosis-report.md     (table des écarts AC1)
  ├── diff-review.md          (rapport AC3)
  └── variation.spec.js       (si A8 activé)
```

Le nom du test est dérivé du brief ou de l'URL (ex. `homepage-hero-cta-fix`).

---

## Cas particuliers

**Aucun écart trouvé** : AC1 constate que le code est conforme au brief. Livraison
d'un rapport "Aucun écart — code conforme" + les observations hors-scope si AC2
a des suggestions d'amélioration webperf. L'utilisateur décide de la suite.

**Écart nécessitant une réécriture complète** : si AC2 constate que l'architecture
du code est fondamentalement incompatible avec le brief (ex. ciblage complètement faux,
logique inversée sur tout le JS), signaler à l'utilisateur que le mode Corrector
n'est plus adapté → proposer un Fast Build ou Production Grade depuis zéro.

**Maquette contradictoire avec le brief textuel** : AC1 signale la contradiction,
demande à l'utilisateur lequel fait référence avant de continuer.
