# Brief standardisé d'A/B test

> **V2** : ce fichier décrit comment *collecter* l'information en conversation (questions,
> brief minimum viable). L'artefact qui *fige* la demande est désormais l'**AB Test Task
> Contract** (`references/task-contract.md`), produit par le Scoping Agent (A1) et challengé
> par le CRO Strategy Agent (A2).

Le brief est le contrat. Un bon brief évite 80 % des allers-retours. Reformule toujours la
demande de l'utilisateur dans ce format, puis fais **valider** avant de coder.

## Format complet

```
# BRIEF AB TEST — [nom court du test]

## 1. Contexte
- URL cible : https://...
- Outil : AB Tasty | Kameleoon | VWO | Optimizely | autre
- Type : A/B | A/B/n | redirection | split URL | personnalisation

## 2. Hypothèse
"En [changement], on s'attend à [effet mesurable] parce que [raison/insight]."
Exemple : "En passant le CTA principal en orange et en le rendant collant au scroll,
on s'attend à +X% de clics car il devient plus visible sur les pages longues."

## 3. Audience & devices
- Devices : desktop | mobile | tablette | tous
- Segment : tous visiteurs | nouveaux | connectés | trafic payant | ...
- Pages : page unique | template | tout le site

## 4. Changements demandés
- [ ] Changement 1 (élément + nature : contenu / style / position / ajout / suppression)
- [ ] Changement 2
- ...

## 5. Métriques
- Primaire : (ex. clic CTA, taux d'ajout panier, conversion)
- Secondaires : ...

## 6. Contraintes
- Ne pas casser : tracking, formulaires, accessibilité (contraste, focus clavier), SEO
- Respecter la charte graphique du site
- Anti-flicker : oui / non (selon gestion native de l'outil)
- Autres : ...
```

## Brief minimum viable

Si l'utilisateur est pressé, ces 4 infos suffisent pour démarrer ; déduis le reste et
signale tes hypothèses :

1. **URL**
2. **Ce qu'on change** (en langage naturel)
3. **Devices** (sinon : tous)
4. **Outil** (sinon : AB Tasty)

## Comment mener le cadrage

- Si l'URL manque, demande-la en priorité : sans elle, pas de scraping ni de ciblage fiable.
- Si l'hypothèse manque, propose-en une à partir du changement demandé et fais valider.
- Ne pose jamais plus de 1 à 3 questions à la fois. Privilégie des questions à choix
  (devices ? outil ? un ou plusieurs éléments ?) plutôt que des questions ouvertes.
- Quand le brief est complet, affiche la fiche récapitulative et demande : « Je pars
  là-dessus ? » avant de générer.

## Exemple

**Demande utilisateur :** « Sur ma page produit, je veux tester un titre plus court et un
bouton "Ajouter au panier" plus gros et orange, surtout sur mobile. »

**Brief reformulé :**

```
# BRIEF AB TEST — Titre court + CTA panier renforcé (PDP)
## 1. Contexte
- URL : (à confirmer) page produit
- Outil : AB Tasty (par défaut)
- Type : A/B
## 2. Hypothèse
"En raccourcissant le titre produit et en agrandissant + colorant le CTA panier en orange,
on s'attend à +clics ajout panier, car l'action principale devient plus lisible et saillante,
surtout sur petit écran."
## 3. Audience & devices
- Devices : mobile en priorité + desktop
- Pages : template page produit
## 4. Changements
- [ ] Titre produit : version raccourcie (texte à fournir/à proposer)
- [ ] CTA "Ajouter au panier" : taille augmentée + couleur orange de la charte
## 5. Métriques
- Primaire : taux de clic "Ajouter au panier"
## 6. Contraintes
- Garder le tracking du bouton, respecter le contraste AA, suivre la charte
- Anti-flicker : oui
```

Puis : « Tu me confirmes l'URL et le nouveau libellé du titre, ou je te propose une version ? »
