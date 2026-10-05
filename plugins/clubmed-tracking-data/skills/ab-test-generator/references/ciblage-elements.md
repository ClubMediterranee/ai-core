# Ciblage automatique des éléments

Objectif : traduire le vocabulaire métier de l'utilisateur (« le titre », « le CTA », « la
bannière ») en **sélecteurs CSS robustes**, en s'appuyant sur le profil scrappé
(`elements.json`, `design.json`) et le HTML réel de la page.

## 1. Lire le profil scrappé

Après `scripts/scrape_site.py`, tu disposes de :

- **`design.json`** — tokens de charte : palette (avec rôles : primary, accent, danger, text,
  bg), familles et tailles de police, échelle d'espacement, rayons, ombres, styles de boutons,
  breakpoints détectés.
- **`elements.json`** — carte des éléments sémantiques détectés, chacun avec : rôle deviné
  (`title`, `cta_primary`, `nav`, `hero`, `price`, `form`, `image_hero`…), un **sélecteur
  recommandé**, des **sélecteurs de repli**, le texte courant, et la visibilité par device.
- **captures** desktop + mobile pour le contrôle visuel.

Croise toujours `elements.json` avec une lecture du HTML : le script propose, tu valides.

## 2. Mapping vocabulaire → élément

Quand l'utilisateur nomme un élément, mappe-le ainsi (par ordre de probabilité) :

| Ce que dit l'utilisateur | Cible probable |
|---|---|
| « le titre », « le H1 », « l'accroche » | premier `<h1>` visible, sinon plus gros texte du hero |
| « le sous-titre » | `<h2>`/`<p>` juste sous le H1 |
| « le CTA », « le bouton principal », « le bouton d'action » | bouton/lien le plus saillant au-dessus de la ligne de flottaison (couleur accent, taille) |
| « ajouter au panier », « acheter » | bouton dont le texte/`aria-label`/`data-*` matche l'intention e-commerce |
| « la bannière », « le bandeau » | élément pleine largeur en haut de page (promo, info) |
| « le hero », « la section principale » | premier bloc full-width avec titre + visuel + CTA |
| « le prix » | nœud contenant un motif monétaire (€, $, format prix) près du produit |
| « la nav », « le menu » | `<nav>` / `[role=navigation]` / `<header>` |
| « le formulaire » | `<form>` le plus proche de l'intention (newsletter, contact, checkout) |

En cas d'ambiguïté (plusieurs candidats), **montre les 2-3 candidats** (texte + sélecteur) et
demande lequel — ou utilise la capture pour trancher visuellement.

## 3. Hiérarchie de robustesse des sélecteurs

Choisis le sélecteur le plus **stable** disponible. Du meilleur au pire :

1. **ID stable** : `#add-to-cart` (si non généré dynamiquement).
2. **Attribut sémantique / data** : `[data-testid="cta-primary"]`, `[data-cta]`,
   `[name="email"]`, `[aria-label="Ajouter au panier"]`.
3. **Rôle + contexte** : `nav [role="button"]`, `header .logo`.
4. **Classe sémantique lisible** : `.product-title`, `.btn-primary` (pas hashée).
5. **Texte** (via JS, voir plus bas) : repérer par contenu quand rien d'autre n'est stable.
6. **À ÉVITER** : classes hashées (`.css-1a2b3c`, `.sc-xyz`), `:nth-child()` profonds,
   chemins descendants longs et fragiles.

> Règle : si le seul sélecteur dispo est fragile, signale-le dans la livraison et ajoute un
> **fallback** (ex. ciblage par texte en JS) pour que le test ne casse pas au prochain déploiement
> du site.

### Ciblage par texte (fallback robuste pour libellés)

Quand seul le texte est fiable (boutons sans data-attribute) :

```js
function findByText(selector, text) {
  return [...document.querySelectorAll(selector)]
    .find(el => el.textContent.trim().toLowerCase() === text.toLowerCase());
}
const cta = findByText('a, button', 'Ajouter au panier');
```

## 4. DOM dynamique : attendre l'élément

Beaucoup de sites rendent le contenu en JS (SPA, lazy-load). Ne suppose jamais que l'élément
est présent au chargement. Utilise un observateur avec timeout (présent dans
`assets/variation.js`) :

```js
function waitForElement(selector, { timeout = 5000 } = {}) {
  return new Promise((resolve, reject) => {
    const found = document.querySelector(selector);
    if (found) return resolve(found);
    const obs = new MutationObserver(() => {
      const el = document.querySelector(selector);
      if (el) { obs.disconnect(); resolve(el); }
    });
    obs.observe(document.documentElement, { childList: true, subtree: true });
    setTimeout(() => { obs.disconnect(); reject(new Error('timeout: ' + selector)); }, timeout);
  });
}
```

## 5. Multi-device : vérifier l'existence par device

Un sélecteur valide sur desktop peut viser un nœud absent/différent sur mobile (menus burger,
versions distinctes du même bloc). Le `elements.json` indique la visibilité par device.
Si l'élément diffère, prévois **un sélecteur par device** ou un sélecteur commun robuste, et
teste les deux captures. Voir `references/regles-ux.md` (multi-device).

## 6. Checklist de ciblage (avant de figer)

- [ ] Chaque changement a un sélecteur **recommandé** + au moins **un fallback**.
- [ ] Aucun sélecteur ne dépend d'une classe hashée seule.
- [ ] Les sélecteurs existent sur **tous les devices ciblés** (vérifié sur les captures).
- [ ] Les éléments à contenu dynamique passent par `waitForElement`.
- [ ] Les sélecteurs n'attrapent pas d'éléments parasites (tester `document.querySelectorAll`
      mentalement / via le snippet de preview).
