---
name: ref-extraction-criteria
description: >
  Register or transversal feature: the two conditions for extracting a shared rule, why editorial keys never
  qualify, and how to size a transversal feature so it covers exactly one mechanism.
type: reference
---

# Registre ou fonctionnalité transverse

## La table de décision

| Clé partagée | 2 PRD | ≥ 3 PRD |
|---|---|---|
| **Endpoint** (comportement) | registre | **fonctionnalité transverse**, si la règle est observable |
| **Clé CMS** (libellé) | registre + proposition de révision | registre + proposition de révision |
| dans un seul PRD | ignoré | ignoré |

## Les deux conditions pour une fonctionnalité transverse

### 1. La règle doit être observable

**Un utilisateur remarquerait-il l'incohérence en utilisant deux verticales ?**

C'est le critère qui sépare une règle produit d'une factorisation de code. Il se teste par l'exemple :

- « la journée complète exclut les demi-journées » — si les activités faisaient l'inverse du
  childcare, l'utilisateur le verrait. **Observable, donc fonctionnalité transverse.**
- « le créneau est identifié par une clé composite date-slot » — aucun utilisateur ne verra jamais
  cette clé. **Non observable : c'est du dev, ça ne va ni en fonctionnalité transverse ni au registre.**

Ce jugement vous appartient. Aucun script ne peut le rendre, et c'est précisément pour ça que le
critère est écrit ici plutôt qu'encodé dans une gate.

#### Le test : réénoncer la règle sans un seul terme d'API

C'est ce qui tranche, et c'est vérifiable :

> **Réécrire la règle sans nommer d'endpoint, de champ, de verbe HTTP ni de payload. Si elle dit
> encore quelque chose qu'un utilisateur pourrait remarquer, c'est une règle. Si elle devient vide ou
> intraduisible, c'est de la plomberie.**

| Formulation d'origine | Réénoncée sans API | Verdict |
|---|---|---|
| « l'écriture envoie la liste complète des services, obtenue en relisant les existants » | « ajouter un service d'une verticale ne fait disparaître aucun service d'une autre » | **règle** — un utilisateur voit sa garderie disparaître |
| « les trois verticales appellent le même endpoint de panier » | *(rien ne subsiste)* | plomberie |
| « le créneau est identifié par une clé composite date-slot » | *(intraduisible)* | ni l'un ni l'autre : c'est du dev |

Le test a un bénéfice au-delà du classement : il **corrige la formulation**. Une règle rédigée en
vocabulaire d'API, dans un document qui se veut agnostique du service, est déjà un défaut — et c'est
le même geste qui la classe et qui la répare.

#### Plomberie et observabilité ne s'opposent pas

L'anti-pattern « plomberie prise pour une règle » (`REF-challenge-pass.md`) et le critère
d'observabilité **portent sur deux objets différents** : le premier sur la **clé**, le second sur la
**règle**. Ils ne peuvent donc pas se contredire, et quand ils semblent le faire, c'est la règle qui
décide — la clé n'est que la preuve d'entrée.

Un endpoint de panier appelé par tout le funnel **est** de la plomberie **en tant qu'endpoint**. Cela
ne dit rien de ce qu'on en tire : s'il existe une règle observable à son sujet, on extrait cette
règle, pas l'endpoint. S'il n'en existe aucune, l'anti-pattern s'applique, et le partage va au
registre.

**La liste d'exemples de l'anti-pattern illustre le cas fréquent ; elle ne classe pas.** C'est sa
définition qui classe : *« le partage est réel mais n'implique aucun comportement que l'utilisateur
puisse comparer »*.

### 2. Au moins trois porteurs

Deux, c'est une coïncidence ; trois, c'est un motif. À deux porteurs, la synchro se documente au
registre — sans le coût d'un document de plus à maintenir. Le seuil se compte en **PRD distincts**,
pas en specs : quatre specs du même PRD qui partagent une clé, c'est un cas que le skill `spec` gère
déjà.

## Pourquoi une clé éditoriale ne devient jamais une fonctionnalité transverse

Deux specs qui affichent le même libellé ne partagent pas un comportement — elles partagent un mot.
La question posée est « est-ce voulu, ou est-ce un doublon à dédoublonner ? », et sa réponse est une
proposition de révision, pas un contrat normatif.

Une fonctionnalité transverse est réservée aux **features**. QG-S11 échoue sur une fonctionnalité transverse dont la preuve d'entrée ne
contient que des clés CMS.

## Granularité : une fonctionnalité transverse = un mécanisme

Plusieurs mécanismes identifiés → **autant de fonctionnalités transverses**. Un document fourre-tout
perd la propriété qui fait la valeur de la fonctionnalité transverse : pouvoir dire « ce
comportement-là est le même partout ».

L'unité naturelle est **la machine d'états partagée**, ou le groupe d'endpoints qui la sert. Une
fonctionnalité transverse **liste les FUNC qu'elle sert**, ce qui la situe dans le découpage
fonctionnel des PRD sans la scinder artificiellement.

**Pourquoi pas une fonctionnalité transverse par FUNC.** Le précédent est dans les specs elles-mêmes :
une spec regroupe couramment plusieurs FUNC *parce qu'ils partagent un même état et un même
composant*. Découper strictement par FUNC produirait autant de fonctionnalités transverses citant
toutes la même machine d'états — exactement la duplication que l'extraction est censée retirer.

**Le garde-fou inverse.** Une fonctionnalité transverse d'une seule règle est du bruit : le registre la porte mieux.
QG-S12 avertit.

### Le test : un mécanisme, ou deux ?

Deux clés portées par les mêmes PRD ne forment pas forcément un mécanisme. C'est la décision la plus
structurante du skill, et deux documents au lieu d'un passent exactement les mêmes gates — rien ne
rattrape l'erreur après coup.

**Le test se pose règle par règle : peut-on énoncer cette règle en ne nommant qu'une seule des
clés ?**

- **Oui pour toutes** → deux mécanismes, deux documents. Chaque règle vit d'un seul côté ; les
  regrouper ne factorise rien, ça juxtapose.
- **Au moins une a besoin des deux** → un seul. Exemple : « la lecture renvoie `fully_booked`,
  l'écriture ne doit pas le perdre » — cette règle n'existe qu'au point de contact. C'est la signature
  d'une machine d'états partagée.

C'est le pendant exact du test d'observabilité : il ne se raisonne pas dans l'abstrait, il se vérifie
sur chaque règle qu'on vient de rédiger.

**Le rapport du détecteur ordonne la lecture, il ne tranche pas.** Il compare les ensembles de specs
porteuses : identiques, c'est l'indice fort d'un mécanisme unique ; différents, c'est soit deux
mécanismes, soit un porteur manquant — et il faut savoir lequel avant d'appliquer le test.

**Le test de granularité qui se vérifie.** Les points de variation le tranchent mieux que l'intuition :
un porteur qui n'a rien à lier sur un axe signale soit un axe mal posé, soit **deux mécanismes
mélangés** dans un même document. La règle et son garde-fou sont à l'étape 3.

## Ce qui reste au registre même à trois porteurs

- une clé éditoriale, toujours ;
- une clé dont la règle n'est pas observable ;
- un endpoint d'infrastructure — authentification, tracking, un endpoint de panier appelé par tout
  le funnel — **dont on ne tire aucune règle observable**. C'est la condition qui compte, pas la
  forme de l'endpoint : le même endpoint de panier sort du registre dès qu'une règle observable s'y
  attache. Le test de réénonciation ci-dessus tranche ; voir aussi l'anti-pattern « plomberie prise
  pour une règle » dans `REF-challenge-pass.md`.
