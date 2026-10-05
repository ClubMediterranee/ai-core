# Itération, historique & rollback

## 1. Mémoire de la conversation

Le skill garde en tête, au fil de la conversation, l'**état courant du test** :

- le **brief** validé,
- le **profil** scrappé (charte + éléments),
- la **version courante** du code (CSS/JS/anti-flicker),
- l'**historique** des versions (changelog).

Chaque nouvelle demande de l'utilisateur s'interprète **par rapport à cet état**, pas comme une
requête isolée. « Rajoute aussi… », « finalement plutôt… », « remets comme avant » se résolvent
en se référant à la dernière version connue.

## 2. Historique des codes (versioning)

Tiens un historique simple : V1, V2, V3… Pour chaque version, garde un **changelog** d'une
ligne par changement.

```
HISTORIQUE — Test "Titre court + CTA panier"
V1 — Titre raccourci + CTA orange agrandi (base)
V2 — V1 + CTA collant au scroll sur mobile
V3 — V2 ; couleur CTA assombrie (#e85d00) pour passer le contraste AA
```

À chaque itération : pars de la version courante → applique le delta → incrémente → ajoute la
ligne de changelog → relance la QA. Si l'utilisateur veut revenir à une version antérieure,
ressors le code de cette version depuis l'historique.

> Si l'utilisateur travaille avec des fichiers, tu peux matérialiser l'historique en
> `variation.v1.css`, `variation.v2.css`, etc. Sinon, garde-le dans la conversation et ressers
> n'importe quelle version sur demande.

## 3. Itération : appliquer un delta

Quand l'utilisateur demande une modification :

1. **Identifie le delta** : qu'est-ce qui change par rapport à la version courante ? (ajout d'un
   élément, modification d'un style existant, retrait d'un changement).
2. **Réutilise** le ciblage et la structure existants ; ne régénère pas tout from scratch.
3. **Mode dev** : mets à jour le mini-changelog en tête des blocs.
4. **Re-QA proportionnée au delta** (voir grille ci-dessous) : ne pas rejouer toute la chaîne
   QA pour un ajustement mineur — chaque itération inutilement lourde recharge tout
   l'historique de la conversation (code + rapports précédents), ce qui fait grimper le coût
   des sessions longues.
5. **Livre** la nouvelle version + le diff résumé (« ce qui change depuis V2 »).

### Quelle QA rejouer selon le type de delta

| Type de delta | Exemples | QA à rejouer |
|---|---|---|
| **Cosmétique** | couleur, texte, espacement, taille de police, ordre visuel — pas de nouveau sélecteur, pas de nouvelle logique DOM/tracking | `qa_check.py` (lint auto, quelques secondes) + vérification visuelle manuelle. Pas de nouvel A7 en prose, pas de A8/A9. |
| **Structurel** | nouveau sélecteur, nouvelle logique JS, élément interactif ajouté, changement de ciblage DOM, changement affectant le tracking | A7 complet obligatoire ; A8/A9 seulement si Production Grade **et** que le delta touche tracking/SPA/logique — pas pour un simple ajustement visuel même en Production Grade. |

Exemple cosmétique — « passe le CTA en orange plus foncé » : delta = 1 propriété CSS,
`qa_check.py` + vérif visuelle suffisent, pas de re-A7/A8/A9.

Exemple structurel — « ajoute un badge "Livraison offerte" sous le prix » : delta = +1
élément avec nouveau ciblage ; conserve V2, ajoute le ciblage du prix, insère le badge en
CSS+JS, passe en V3, A7 complet, livre avec le diff.

## 4. Mode dev vs livraison

- **Mode dev** : commentaires riches (cible, hypothèse, sélecteurs, changelog), snippet de
  preview (bookmarklet/console) pour tester sans déployer.
- **Livraison** : code épuré, commentaires utiles seulement, prêt à coller dans l'outil.

Snippet de preview (à fournir en mode dev) : encapsule le CSS dans un `<style>` injecté et le JS
exécuté, à coller dans la console du navigateur sur la page cible pour visualiser la variation
en local avant déploiement.

```js
// Preview locale — coller dans la console sur la page cible
(function(){
  var css = `/* … coller le CSS de la variation … */`;
  var s = document.createElement('style'); s.id = 'abt-preview'; s.textContent = css;
  document.head.appendChild(s);
  /* … coller le JS de la variation … */
})();
```

Pour retirer la preview : supprimer `#abt-preview` et recharger la page.

## 5. Rollback / cleanup (mode [R])

Comme tout est **scopé par la classe racine** `abt-vN` et **traçable**, retirer un test est
mécanique.

**Procédure de cleanup :**
1. Retirer la classe racine `abt-vN` de `<html>`/`<body>` → tout le CSS scopé cesse de
   s'appliquer.
2. Restaurer le contenu original des nœuds dont le **texte/HTML** a été modifié (d'où l'intérêt
   de sauvegarder l'original avant de l'écraser — voir `assets/variation.js`).
3. Retirer les nœuds **ajoutés** par la variation (badges, bannières injectées) : les marquer
   d'un `data-abt="v1"` à la création rend leur suppression triviale.
4. Désactiver l'**anti-flicker** global de la campagne.
5. Vérifier qu'aucun résidu ne subsiste (`document.querySelectorAll('[data-abt]')` vide, classe
   racine absente).

Snippet de cleanup type :

```js
(function () {
  var V = 'abt-v1';
  document.documentElement.classList.remove(V);
  document.querySelectorAll('[data-abt="' + V + '"]').forEach(function (n) { n.remove(); });
  // restaurer les contenus sauvegardés si nécessaire (cf. dataset.abtOriginal)
})();
```

Conseil structurel à appliquer dès la génération pour que le rollback soit gratuit :
- marquer tout élément **ajouté** avec `data-abt="vN"` ;
- avant d'**écraser** un texte/HTML, le sauvegarder dans `el.dataset.abtOriginal`.
