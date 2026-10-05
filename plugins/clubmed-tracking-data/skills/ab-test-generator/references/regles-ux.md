# Règles UX & multi-device

Un test d'A/B testing modifie une interface vue par de vrais utilisateurs. Respecter ces
règles évite de dégrader l'expérience (et de fausser le test).

## 1. Règles UX à respecter

**Hiérarchie & lisibilité**
- Une seule action principale par écran : ne crée pas deux CTA qui se concurrencent.
- Préserve la hiérarchie visuelle (titre > sous-titre > corps > légende). Si tu agrandis un
  élément, vérifie qu'il ne casse pas l'ordre de lecture.
- Garde des longueurs de ligne lisibles (≈ 45-75 caractères pour le corps de texte).

**Contraste & accessibilité (ne jamais régresser)**
- Contraste texte/fond conforme **WCAG AA** : ≥ 4.5:1 (texte normal), ≥ 3:1 (grand texte/UI).
  Avant de changer une couleur, vérifie le ratio contre le nouveau fond.
- Conserve un **focus clavier visible** sur les éléments interactifs.
- Conserve les attributs d'accessibilité (`aria-label`, `alt`, `role`) des éléments modifiés.
- Cibles tactiles ≥ 44×44 px sur mobile.
- Respecte `prefers-reduced-motion` si tu ajoutes des animations.

**Cohérence avec la charte**
- Dérive couleurs, typo, rayons, ombres, espacements des tokens du `design.json`. Un orange
  « accent » du test doit être l'orange de la marque, pas un orange arbitraire.
- Réutilise les composants/styles existants plutôt que d'en inventer (un bouton de test doit
  ressembler aux boutons du site, en mieux).

**Clarté du copywriting (si tu touches au texte)**
- Verbe d'action explicite sur les CTA (« Ajouter au panier », pas « Valider »).
- Cohérence du libellé sur tout le parcours (le bouton « Publier » mène à un toast « Publié »).
- Pas de jargon technique côté utilisateur. Spécifique > malin.

**Non-régression fonctionnelle**
- Ne casse pas les formulaires, le tracking, le responsive, le SEO (titres, contenu indexé).
- Modifie plutôt que recrée, pour préserver listeners et attributs (cf. `ab-tasty.md`).

## 2. Multi-device natif

Le test doit être pensé pour **tous les devices ciblés dès la génération**, pas adapté après coup.

**Breakpoints**
- Récupère les breakpoints réels depuis `design.json` (le scraper détecte les media queries du
  site). À défaut, repères courants : mobile < 768px, tablette 768-1024px, desktop ≥ 1024px.
- Gère les variantes responsive **en CSS** (media queries) plutôt qu'avec des branches JS sur
  la largeur d'écran (plus robuste, pas de reflow au resize).

```css
html.abt-v1 .btn-primary { font-size: 1rem; }
@media (max-width: 767px) {
  html.abt-v1 .btn-primary { font-size: 1.125rem; width: 100%; } /* CTA pleine largeur mobile */
}
```

**Éléments différents selon le device**
- Le même contenu peut avoir deux nœuds distincts (ex. nav desktop vs menu burger mobile). Vérifie
  dans `elements.json` la visibilité par device.
- Si l'élément diffère, prévois un sélecteur par device ou un sélecteur commun robuste, et teste
  les deux captures (`desktop.png`, `mobile.png`).

**Contrôles spécifiques mobile**
- Cibles tactiles suffisantes (≥ 44px), espacement entre éléments cliquables.
- Pas d'effet `:hover` comme seul moyen d'interaction (pas de hover au doigt).
- Attention au clavier virtuel qui pousse le layout sur les formulaires.
- Vérifie que les modifications ne provoquent pas de scroll horizontal.

**Checklist multi-device avant livraison**
- [ ] Sélecteurs valides sur desktop **et** mobile (et tablette si ciblée).
- [ ] Pas de débordement horizontal introduit.
- [ ] CTA et cibles tactiles ≥ 44px sur mobile.
- [ ] Contraste AA respecté sur chaque fond/device.
- [ ] Rendu vérifié sur les deux captures.
