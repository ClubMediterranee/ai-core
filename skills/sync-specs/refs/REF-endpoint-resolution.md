---
name: ref-endpoint-resolution
description: >
  Lifting an elided-endpoint ambiguity with the clubmed_api MCP — when to do it, how, and what to
  do when the MCP is not connected.
type: reference
---

# Résoudre une forme élidée

## Le partage des rôles

Le détecteur est **hors-ligne et déterministe**. Il joint ce qu'il peut joindre sans rien deviner,
et signale le reste en Point d'attention. C'est le même partage que dans le skill `spec` : le script
vérifie la forme, le MCP résout, les Points d'attention portent ce qui reste ouvert.

Ce partage n'est pas cosmétique. Un script qui appellerait le réseau ne serait plus rejouable en CI,
plus reproductible, et échouerait quand le MCP est absent — pour un gain qui ne concerne qu'une
minorité de cas.

## Les deux signalements

**Blocking — le suffixe correspond à plusieurs chemins complets.**
La clé est **exclue de la jointure**. Deviner reviendrait à relier deux specs sans rapport, ce qui
est bien pire qu'un trou visible : un faux positif se propage en fonctionnalité transverse, en citations, en tests.

**Medium — le suffixe ne correspond à aucun chemin complet connu.**
La jointure se fait sur le suffixe seul, ce qui est correct : deux specs qui écrivent toutes deux la
forme élidée doivent se rencontrer. Mais la route canonique reste inconnue, donc le §8 des porteurs
est incomplet.

## Résoudre avec le MCP

Si `clubmed_api` est connecté :

1. `search_openapi` avec le suffixe (`cart/services`) pour retrouver les opérations candidates.
2. `validate_route` sur chaque candidate retenue pour confirmer qu'elle existe bien.
3. Retenir la route qui correspond au **besoin exprimé** par la spec — la colonne « Rôle » de son
   index d'endpoints le dit. Deux routes proches ne servent pas le même besoin ; c'est cette colonne
   qui tranche, pas la ressemblance du chemin.

Écrire ensuite la **forme canonique** dans la spec propriétaire, et remplacer la forme élidée. La
prochaine exécution du détecteur joindra sans ambiguïté, et le Point d'attention disparaîtra de
lui-même — c'est le signe que la résolution a bien été faite au bon endroit.

## Si le MCP n'est pas connecté

**Le dire, et le chiffrer.** Pas de blocage — contrairement au skill `spec`, celui-ci n'a pas de
porte dure, parce que la jointure elle-même n'a besoin d'aucun réseau. Mais une dégradation
silencieuse est pire qu'un blocage : personne ne sait qu'il manque quelque chose.

À l'étape de proposition, annoncer :

> *N ambiguïtés d'endpoint n'ont pas pu être levées : le MCP `clubmed_api` n'est pas connecté.*

Puis porter chaque Point d'attention **tel quel** dans le registre ou la fonctionnalité transverse concernée, avec sa
sévérité. Une ambiguïté visible coûte beaucoup moins cher qu'une jointure fausse et muette, et elle
permet à quelqu'un d'autre de la résoudre plus tard sans refaire l'analyse.

## Ce qu'il ne faut pas faire

- **Choisir la route la plus courte** ou « la plus probable ». Le détecteur refuse justement de
  hiérarchiser des candidates ; le faire à la main sans preuve reproduit l'erreur qu'il évite.
- **Éditer la spec sans preuve.** Une route écrite sans `validate_route` est une hypothèse déguisée
  en fait : si elle doit être posée quand même, elle va en Point d'attention, pas dans l'index.
- **Élider davantage** pour faire coïncider deux formes. Cela masque l'ambiguïté au lieu de la
  résoudre, et la prochaine exécution ne signalera plus rien.
