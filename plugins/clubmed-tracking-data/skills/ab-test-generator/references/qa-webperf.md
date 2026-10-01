# QA Webperf / Flickering — grille d'audit (A7)

Audit **ligne à ligne** du code produit par A6, en profil AUDITEUR : constater, prouver,
renvoyer — jamais corriger soi-même. Commencer par le lint automatique :

```bash
python scripts/qa_check.py --css variation.css --js variation.js
```

Puis dérouler la grille manuelle ci-dessous. Chaque item reçoit ✅ / ⚠️ / ❌ avec la **preuve
dans le code** (ligne ou pattern cité) et le **correctif attendu** en une phrase.

## 1. Flickering & rendu initial

- [ ] Anti-flicker présent si la variation modifie du contenu visible au chargement.
- [ ] **Timeout de sécurité ≤ 3 s** sur le masquage (jamais de page masquée indéfiniment).
- [ ] Le masquage est **scopé à la zone modifiée** quand c'est possible (pas `body` entier
      pour un changement de CTA).
- [ ] Démasquage garanti dans tous les chemins (succès, sélecteur introuvable, exception —
      `finally` ou équivalent).
- [ ] Pas de contenu original visible puis remplacé (Flash Of Original Content).

## 2. CLS (Cumulative Layout Shift)

- [ ] Aucune injection au-dessus de la ligne de flottaison sans espace réservé
      (`min-height` / placeholder).
- [ ] Les changements de taille (police, padding, bannière) ne décalent pas le contenu
      sous la zone après le rendu initial.
- [ ] Images/médias injectés avec dimensions explicites.

## 3. Timing d'injection

- [ ] La variation s'exécute dès que sa cible existe (waitForElement), pas sur `load`.
- [ ] Pas de `setTimeout` arbitraire comme mécanisme d'attente.
- [ ] SPA : ré-exécution gérée au changement de route, avec guard d'idempotence.

## 4. Duplication & idempotence

- [ ] Guard d'exécution (`data-abt` / flag) vérifié **avant** toute modification.
- [ ] Réexécution simulée mentalement : aucun nœud dupliqué, aucun listener empilé.
- [ ] Les éléments injectés sont identifiables (attribut `data-abt`) pour le cleanup.

## 5. MutationObserver & polling

- [ ] Observer **borné** à un conteneur précis (jamais `document.body` avec
      `subtree: true` sans nécessité prouvée).
- [ ] **`disconnect()` systématique** dès la cible trouvée ou après timeout.
- [ ] Aucune boucle de polling sans condition d'arrêt + limite d'itérations.
- [ ] L'observer ne peut pas se re-déclencher sur ses propres mutations (boucle infinie).

## 6. Reflows & listeners

- [ ] Pas de lectures/écritures layout entrelacées dans une boucle
      (offsetHeight → style → offsetHeight = layout thrashing).
- [ ] Modifications DOM groupées (classe racine, fragment) plutôt qu'élément par élément.
- [ ] Listeners `scroll`/`resize`/`touchmove` : **passifs** et throttlés/debouncés.
- [ ] Délégation d'événements si cibles multiples ; pas de listener par item de liste.
- [ ] Aucun listener global ajouté sans nécessité, aucun sans possibilité de retrait.

## 7. CSS

- [ ] 100 % des règles scopées sous la classe racine `.abt-vN`.
- [ ] `!important` seulement si justifié par un conflit de spécificité documenté en commentaire.
- [ ] Animations sur `transform`/`opacity` uniquement (compositées) ; jamais sur
      `top/left/width/height/margin`.
- [ ] Pas de sélecteurs universels coûteux (`.abt-v1 * { … }`).

## 8. Mobile

- [ ] Poids du code raisonnable (< ~15 Ko JS+CSS non minifiés pour un test standard).
- [ ] Pas d'animation continue, pas d'observer permanent (batterie/CPU).
- [ ] Cibles tactiles ≥ 44 px, pas de scroll horizontal induit.
- [ ] Media queries alignées sur les breakpoints du `design.json`.

## 9. Compatibilité AB Tasty

- [ ] Code exécutable tel quel dans l'éditeur (IIFE, pas de `import`/`export`, pas de
      top-level `await`).
- [ ] Pas de dépendance à jQuery ni à une lib du site (sauf listée au contrat).
- [ ] JS et CSS collables dans leurs onglets respectifs, anti-flicker intégré (pas de fichier à part).
- [ ] Aucune pollution globale (`window.*`) hors éventuel namespace unique documenté.

## Verdict normalisé

```
QA WEBPERF — verdict : ✅ PASS | ⚠️ PASS AVEC RÉSERVES | ❌ FAIL
- ❌ bloquants : [item → preuve → correctif]
- ⚠️ réserves  : [item → preuve → risque accepté ?]
- ✅ points solides notables (max 3, sans complaisance)
```

- **FAIL** = au moins un ❌ dans les sections 1, 4, 5 ou 9 (flicker, duplication, boucle,
  incompatibilité plateforme). Retour à A6, max 2 boucles, puis escalade utilisateur.
- **PASS AVEC RÉSERVES** = ⚠️ uniquement ; les réserves sont arbitrées par A9 (Production
  Grade) ou affichées en tête de livraison (Fast Build).
