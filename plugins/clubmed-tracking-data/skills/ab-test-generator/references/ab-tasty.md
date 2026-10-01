# AB Tasty (et outils similaires) : conventions & anti-flicker

Ce skill vise une compatibilité « AB Tasty friendly » mais le code reste portable vers
Kameleoon, VWO, Optimizely Web, etc. Les principes sont communs ; seules quelques conventions
diffèrent.

## 1. Où va le code

Dans AB Tasty, une variation d'un test « éditeur de code » se compose typiquement de :

- un onglet **CSS** (styles de la variation) ;
- un onglet **JavaScript** (logique d'application) ;
- éventuellement un réglage **anti-flicker** global au niveau du compte/campagne.

Le skill produit donc **CSS et JS séparés**. Ne jamais mélanger : pas de `element.style.x` pour
ce qui relève du CSS, pas de `<style>` injecté depuis le JS sauf nécessité (ex. styles
calculés dynamiquement).

## 2. Structure JS recommandée

Le JS d'une variation doit être :

- **Idempotent** : réexécutable sans dupliquer d'effet (AB Tasty peut ré-appliquer la variation
  sur navigation SPA). Garde un flag.
- **Défensif** : attendre les éléments (DOM dynamique), ne pas planter si un sélecteur manque.
- **Scopé & traçable** : poser une classe racine `abt-vN` sur `<html>` ou `<body>` ; toutes les
  modifs sont attribuables à la variation → cleanup et rollback triviaux.

Squelette (voir `assets/variation.js` pour la version complète) :

```js
(function () {
  var VARIATION = 'abt-v1';
  if (document.documentElement.classList.contains(VARIATION)) return; // idempotence
  document.documentElement.classList.add(VARIATION);

  function apply() {
    // waitForElement(...).then(el => { ... })
  }

  if (document.readyState !== 'loading') apply();
  else document.addEventListener('DOMContentLoaded', apply);
})();
```

## 3. CSS scopé

Toujours préfixer par la classe racine pour éviter les collisions et permettre un retrait
propre :

```css
/* Variation 1 — changements de style */
html.abt-v1 .product-title { font-size: 1.5rem; line-height: 1.2; }
html.abt-v1 .btn-primary {
  background: var(--brand-accent, #ff6a00);
  /* dériver les couleurs du design.json, pas au hasard */
}
```

- Évite `!important` ; ne l'utilise qu'en dernier recours contre une règle inline du site, et
  documente pourquoi.
- Reprends les **tokens de la charte** (`design.json`) : couleurs, rayons, ombres, typo. Un test
  qui respecte la charte performe mieux et passe la design critique.

## 4. Gestion du flicker (FOOC / flash of original content)

Le flicker = l'utilisateur voit brièvement la version originale avant que la variation
s'applique. C'est l'ennemi n°1 de la crédibilité d'un test.

**Ordre de préférence pour le gérer :**

1. **Anti-flicker natif de l'outil** : si AB Tasty (ou autre) gère le masquage natif, l'activer
   et NE PAS ajouter de snippet maison (double masquage = page blanche trop longue).
2. **Anti-flicker intégré dans variation.js/variation.css** (si pas de gestion native — cas
   par défaut) : masqué en tête d'IIFE, retiré à la fin de `apply()` (tous les chemins), avec
   **timeout de sécurité** pour ne jamais laisser la page masquée si le JS échoue. Voir
   `assets/variation.js` (bloc `AFL_ID`) et `assets/variation.css` (`.abt-v1-hide`).
3. **Minimiser la surface masquée** : masquer uniquement les conteneurs modifiés plutôt que
   toute la page, pour réduire la perception de lenteur.

**Règles anti-flicker :**

- Toujours un **timeout** (≈ 3-4 s max) qui ré-affiche coûte que coûte.
- Étant intégré dans la variation (et non plus en code global de la campagne), il se déclenche
  seulement quand AB Tasty exécute le JS — pas avant. Risque résiduel : si AB Tasty tarde à
  déclencher la variation, un flicker bref peut rester visible (jamais une casse fonctionnelle,
  juste un défaut visuel). Si le contrat exige un masquage garanti dès le `<head>` (page très
  sensible au flicker, above-the-fold), signaler l'option de repasser en snippet séparé en code
  global de campagne.
- Privilégier `visibility:hidden`/`opacity:0` à `display:none` pour préserver le layout et
  limiter les reflows.
- Ne jamais masquer indéfiniment : un échec JS ne doit pas casser la page.

## 5. Tracking & non-régression

- Ne supprime/remplace pas un élément qui porte un **listener de tracking** sans réattacher
  l'équivalent. Préfère **modifier** le nœud existant plutôt que le **recréer**.
- Si tu dois remplacer un bouton, conserve ses `id`, `data-*`, `aria-*` et handlers, ou
  duplique-les sur le nouveau nœud.
- Vérifie que les sélecteurs des outils analytics ne dépendent pas de ce que tu modifies.

## 6. Portage vers d'autres outils

Le code généré fonctionne tel quel dans la plupart des éditeurs de code. Différences à garder
en tête :

- **Kameleoon / VWO / Optimizely** : même découpage CSS/JS ; chacun a son réglage anti-flicker
  natif — privilégier le natif quand il existe.
- **SPA / navigation interne** : si l'outil ré-exécute la variation sur changement de route,
  l'idempotence (flag) évite les doublons. Pour réappliquer après une navigation client, écouter
  les événements de l'app ou observer le DOM.
