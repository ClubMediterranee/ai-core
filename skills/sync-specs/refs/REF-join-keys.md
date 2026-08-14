---
name: ref-join-keys
description: >
  What the detector joins specs on, what it deliberately refuses to join on, and how an endpoint is
  normalised so two writings of the same route meet.
type: reference
---

# Clés de jointure

## Le principe

On ne compare pas des documents, **on les joint sur leurs clés**. Comparer les PRD deux à deux, c'est
un jugement par paire sur de la prose : le coût croît au carré, et la précision baisse. Joindre les
specs sur leurs endpoints, c'est une jointure sur un index — et un index n'oublie pas.

C'est aussi pourquoi la jointure se fait au niveau **spec** et pas PRD. Un PRD dit « l'utilisateur
ajoute un créneau de garderie » : aucune clé. Une spec nomme `GET /v0/additional_services` dans son
§8. La différence n'est pas de rigueur, elle est de nature.

## Ce qui est une clé

| Clé | Où | Ce qu'un partage signale |
|---|---|---|
| **Endpoint** | §8, table sous `<!-- dc:index -->` et titres des blocs de détail | deux specs agissent sur la même ressource — candidat comportement |
| **Clé CMS** | §8, colonne 1 de la table éditoriale | deux specs rendent le même texte — leurs libellés doivent être identiques |
| **Libellé CMS** | §8, colonne 2 de la même table | deux clés disent la même chose — factorisation peut-être manquante |

Le détecteur les distingue **par la forme de la valeur**, jamais par le libellé de la sous-section :
`📝 CMS Keys` devient `📝 Clés CMS` dans une spec française, mais `childcare.slot.morning` garde sa
forme dans toutes les langues. Une clé pointée est un endpoint, une clé pointillée est éditoriale.

## L'axe éditorial a deux sens, et ils ne se valent pas

Joindre sur la **clé** ne voit qu'une moitié du problème. L'autre moitié — deux clés différentes pour
le même texte — est **en pratique la plus fréquente**, et un détecteur qui ne regarde que les clés y
est aveugle par construction.

### Même clé, libellés différents → défaut

Une clé rend **un** texte. Deux specs qui lui donnent deux libellés se contredisent : l'une des deux
est fausse, et le rendu final sera l'un ou l'autre selon qui écrit en dernier dans Directus. C'est un
**ERROR** du détecteur, pas un candidat soumis au jugement — il n'y a rien à arbitrer.

Même chose, en plus doux, pour l'**attestation** : la colonne Source est du texte libre, donc seule
sa **classe** est comparable — `drd` (libellé attesté par un Content Contract), `directus` (à créer),
ou autre. Deux specs qui divergent de classe sur une même clé sortent en WARN : l'une s'appuie sur
une preuve, l'autre sur une proposition, et c'est la première qui fait foi. Comparer les phrases
elles-mêmes ne produirait que du bruit.

### Même libellé, clés différentes → question

Ici le détecteur **ne conclut jamais**. Trois situations se ressemblent dans les données et ne se
traitent pas pareil :

| Situation | Exemple réel | À faire |
|---|---|---|
| **Même élément, deux emplacements** | `nbe.paiement.remote.participants` et `nbe.participants.remote.participants` — c'est la même remote, BR-005 | unifier |
| **Même mot, deux surfaces** | `nbe.dashboard.remote.childcare` et `nbe.dashboard.section.childcare.title` | **ne pas unifier** — le jour où la section devient « Votre club enfants », il faut deux clés |
| **Vocabulaire d'interface** | « Add-ons », « Learn more », « Validate » | laisser — unifier coupleraient des surfaces sans rapport |

Le détecteur calcule un **signal** à partir de la forme des clés, et rien de plus :

- clés de même longueur ne différant que par **un seul segment** → « même élément à deux
  emplacements », candidat sérieux ;
- longueurs différentes, ou plusieurs segments qui diffèrent → « surfaces différentes,
  probablement légitime » ;
- libellé porté par **trois clés ou plus** → « vocabulaire d'interface probable ».

Ces signaux ordonnent la lecture ; ils ne décident pas. Le Challenge Pass et le jugement humain font
le reste.

### Libellé non rédigé

Un libellé encore à écrire — `TBD`, `À définir`, `TODO` — est **exclu de la comparaison** et remonte
en WARN. Quatre clés partageant « TBD par le PO » ne disent pas la même chose : elles ne disent rien
encore, et les compter comme un doublon fabriquerait une factorisation sur du vide.

## Et quand une nomenclature de clés existera ?

Une convention de nommage réduira les divergences accidentelles — deux personnes nommant
différemment la même chose. Elle ne supprimera pas le besoin : deux clés **conformes** peuvent
parfaitement désigner le même texte. La jointure sur la valeur reste le seul moyen de le voir.

## Ce qui n'est délibérément pas une clé

**Les ids de machine d'états (`ST-xxx`).** Ils sont numérotés par spec : `ST-001` dans la spec
childcare et `ST-001` dans la spec activités désignent deux machines différentes. Les joindre
produirait des faux positifs systématiques. Un mécanisme partagé se détecte par ses **endpoints** ;
la machine d'états commune est une preuve que vous ajoutez à la main en confirmant la fonctionnalité transverse.

**Les ids de règle (`BR-xxx`, `FUNC-xxx`).** Même raison : locaux à leur PRD.

**Le partage à l'intérieur d'un seul PRD.** Le skill `spec` le gère déjà avec `related_specs` et la
règle de la spec propriétaire. Le re-signaler serait du bruit, et le bruit fait ignorer le rapport.

## Normalisation d'un endpoint

Le §8 autorise deux écritures de la même route :

```
POST /v1/customers/{customer_id}/bookings/{booking_id}/cart/services      forme complète
POST …/cart/services                                                       forme élidée
```

Sans normalisation, elles ne se rencontrent jamais — et le détecteur rate exactement ce qu'il est
censé trouver. Le script applique donc :

1. méthode en majuscules, séparée du chemin ;
2. schéma et hôte retirés ;
3. `{customer_id}` et `{id}` réduits au même marqueur `{}` — le nom du paramètre n'est pas la route ;
4. slashes multiples réduits, slash final retiré ;
5. élision détectée sur `…` ou `...` en tête.

## Résolution d'une forme élidée

Un suffixe élidé est comparé aux chemins complets vus dans les autres specs :

| Correspondances | Décision | Pourquoi |
|---|---|---|
| exactement 1 | jointure sur le chemin complet | sans ambiguïté |
| 0 | jointure sur le suffixe seul, **Point d'attention Medium** | deux specs qui écrivent toutes deux la forme élidée doivent quand même se rencontrer |
| ≥ 2 | **aucune jointure**, Point d'attention **Blocking** | deviner ici, c'est relier deux specs sans rapport — plus coûteux que de signaler |

Le cas à zéro correspondance mérite l'attention : c'est celui où **aucune** spec ne connaît la forme
canonique. La jointure se fait alors sur le suffixe, ce qui est juste, mais la route reste inconnue —
d'où le Point d'attention, et l'étape de résolution par le MCP décrite dans
`REF-endpoint-resolution.md`.
