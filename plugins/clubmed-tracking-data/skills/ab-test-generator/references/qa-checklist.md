# QA checklist & design critique

## 1. QA automatique (avant chaque livraison)

Une partie est vérifiable par script (`scripts/qa_check.py`), le reste à la main.

### Vérifications automatisées — `scripts/qa_check.py`

```bash
python scripts/qa_check.py --css variation.css --js variation.js
```

Le script signale notamment :
- **Sélecteurs fragiles** (classes hashées type `.css-xxxx`, `:nth-child` profonds).
- **`!important`** non justifié dans le CSS.
- **Anti-flicker** : absence de garde-fou / timeout si masquage détecté.
- **Idempotence** : absence du flag de variation dans le JS.
- **CSS non scopé** : règles sans préfixe de classe racine.
- **Syntaxe** : erreurs JS/CSS basiques.

### Vérifications manuelles (checklist)

**Ciblage**
- [ ] Chaque cible a un sélecteur recommandé + un fallback.
- [ ] Aucun sélecteur ne capture d'éléments parasites.
- [ ] Éléments dynamiques gérés par `waitForElement`.

**Rendu & charte**
- [ ] Couleurs/typo/espacements dérivés du `design.json` (pas de valeurs arbitraires).
- [ ] La variation ressemble à un évolution naturelle du site, pas à une greffe.
- [ ] Pas de FOUC/flicker perceptible (anti-flicker OK, timeout présent).

**Multi-device**
- [ ] OK sur desktop + mobile (+ tablette si ciblée), captures vérifiées.
- [ ] Pas de scroll horizontal, cibles tactiles ≥ 44px.

**Accessibilité**
- [ ] Contraste AA (≥ 4.5:1 texte, ≥ 3:1 grand texte/UI).
- [ ] Focus clavier visible, attributs aria/alt préservés.

**Non-régression**
- [ ] Tracking/listeners conservés sur les éléments modifiés.
- [ ] Formulaires, navigation, liens fonctionnels.
- [ ] JS idempotent (réexécution sans doublon).

**Rollback**
- [ ] Tout est scopé par la classe racine → cleanup trivial.
- [ ] Le contenu original peut être restauré (sauvegardé si remplacé).

### Rapport de QA

En tête de livraison, présente la checklist cochée. Exemple :

```
QA — Variation V1
[OK] Ciblage : 2/2 cibles avec fallback
[OK] Charte : couleurs dérivées de design.json
[OK] Anti-flicker : snippet + timeout 3s
[OK] Multi-device : desktop + mobile vérifiés
[!]  Accessibilité : contraste CTA 4.1:1 < 4.5 → fond assombri proposé
[OK] Rollback : scopé .abt-v1
```

Ne masque jamais un point rouge : signale-le et propose un correctif.

## 2. Design critique (mode [C])

Quand l'utilisateur demande un avis design, endosse le rôle de **directeur artistique** et
confronte la variation à la charte scrappée + aux règles UX. Évalue par axes :

**Hiérarchie** — l'œil va-t-il au bon endroit en premier ? L'action principale est-elle la plus
saillante sans écraser le reste ?

**Cohérence** — couleurs, typo, rayons, ombres, densité : la variation parle-t-elle la même
langue visuelle que le site ? Repère le moindre token « inventé ».

**Contraste & lisibilité** — ratios suffisants ? Tailles de texte confortables sur mobile ?

**Densité & espacement** — la modification respecte-t-elle le rythme vertical et les marges du
site, ou crée-t-elle un point de tension ?

**Accessibilité** — focus, cibles tactiles, alternatives textuelles préservées ?

**Risque vs récompense** — le changement est-il assez fort pour bouger la métrique, sans
dégrader l'expérience ni introduire de friction ?

Pour chaque axe : un constat, puis un **ajustement concret et justifié** (« passe le padding de
8px à 12px pour aligner sur l'échelle d'espacement du site et aérer le CTA »). Évite les avis
vagues ; sois spécifique et actionnable. Conclus par les 1-2 changements à plus fort impact.
