# QA Playwright — génération et exécution des tests E2E (A8)

L'agent A8 produit un fichier `variation.spec.js` qui vérifie la variation **dans un vrai
navigateur**, en injectant le code de variation comme AB Tasty le ferait. Base : le template
`assets/playwright.spec.template.js` — le copier puis l'adapter, jamais réécrire de zéro.

## Principe d'injection

Les tests chargent la page originale puis injectent `variation.css` + `variation.js` via
`page.addStyleTag` / `page.addScriptTag`. C'est fidèle au comportement d'AB Tasty (exécution
post-chargement) et ça permet de tester **sans campagne active**.

## Couverture obligatoire

1. **Apparition** : la classe racine `.abt-vN` est posée et chaque changement du contrat est
   visible (texte, style, élément injecté) — assertions basées sur la table de ciblage A4,
   sélecteurs identiques.
2. **Non-duplication** : injecter le JS **deux fois**, vérifier qu'aucun nœud n'est dupliqué
   (count des éléments `data-abt` inchangé).
3. **Reload** : recharger, ré-injecter, revérifier l'apparition.
4. **Responsive** : mêmes assertions sur viewport desktop (1440×900) et mobile (390×844,
   `isMobile: true`) — plus tablette si le contrat la cible.
5. **Console propre** : aucun `console.error` ni `pageerror` bloquant pendant l'injection.
6. **CTA cliquables** : chaque CTA modifié est visible, activable (`toBeEnabled`), et le clic
   ne jette pas d'erreur ; si le CTA navigue, vérifier l'URL cible.
7. **Tracking** : intercepter les hits attendus du KPI primaire — requêtes réseau
   (`page.route`/`waitForRequest` sur le domaine AB Tasty ou analytics) et/ou pushes
   `dataLayer` (évaluer `window.dataLayer` après le clic). Si le tracking passe par le
   click-tracking natif AB Tasty, vérifier au minimum que le sélecteur du goal matche
   l'élément final.
8. **Screenshots** : avant injection et après, desktop + mobile, nommés
   `before-desktop.png`, `after-desktop.png`, etc. — ces captures de **couverture finale**
   restent pleine page (c'est une preuve livrée). Les captures **intermédiaires de mise au
   point** (rounds de diagnostic visuel pendant une itération/debug) doivent en revanche
   cibler uniquement la zone modifiée via `scripts/preview.js --clip <sélecteur>` plutôt que
   le viewport entier : moins de poids, moins à réanalyser en boucle de debug. Elles restent
   locales de toute façon (jamais committées dans `outputs/` — voir `.gitignore`).
9. **SPA (si applicable)** : naviguer via un lien interne (route change sans reload),
   vérifier que la variation se ré-applique sans duplication.

## Exécution

```bash
pip install playwright --break-system-packages -q   # si besoin
python -m playwright install chromium
npm init -y >/dev/null 2>&1 && npm i -D @playwright/test >/dev/null 2>&1
npx playwright test variation.spec.js --reporter=list
```

> **Environnement sans accès au domaine cible** (sandbox réseau restreinte, page derrière
> login) : ne pas simuler des résultats. Livrer le `.spec.js` prêt à lancer, la commande
> d'exécution, et la **checklist manuelle équivalente** (les 9 points ci-dessus reformulés
> en vérifications à la main). Marquer le gate G4 : « à exécuter côté client ».

## Rapport normalisé

```
QA PLAYWRIGHT — verdict : ✅ PASS | ❌ FAIL | ⏸ À EXÉCUTER CÔTÉ CLIENT
- Tests : X passés / Y au total
- Échecs : [test → cause probable → agent à qui renvoyer (A4 sélecteur ? A6 code ?)]
- Screenshots : chemins des fichiers
```

Un échec de sélecteur retourne à **A4**, un échec de comportement à **A6**. Ne jamais
« assouplir » un test pour le faire passer : le test décrit le contrat, pas le code.
