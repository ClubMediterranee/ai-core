<!-- TEMPLATE — retirer ce commentaire à l'instanciation (QG-S15 échoue tant qu'il est là).
     Un seul registre pour tout le projet, à {DOCS_ROOT}/SYNCHRO.md.
     Les blocs sync:auto sont régénérés à chaque passage ; tout le reste est préservé.

     CE QUE LA MACHINE LIT DANS CE FICHIER
     - Aucun [crochet] ne doit subsister : tout `[texte]` restant lève un WARN QG-S15.
     - Est une *entrée de registre* toute section `##` livrant au moins une clé entre backticks en
       première colonne d'un bloc sync:auto. Les sections structurelles ci-dessous — Points
       d'attention, Révisions éditoriales — n'en livrent pas et échappent donc à QG-S9, qui exige
       un champ « À aligner ».
     - Une entrée périmée se marque avec le mot **Obsolète** dans son titre, ou dans les 400
       premiers caractères de son corps. Sans ce mot, QG-S10 la signale en ERROR. -->
# Registre de synchronisation

Ce registre recense les clés partagées entre specs de **PRD différents** qui ne justifient pas — ou
pas encore — une fonctionnalité transverse : deux PRD porteurs, ou une clé éditoriale quel qu'en soit le nombre.

Les blocs `sync:auto` sont **dérivés** des specs : leur contenu se déduit du rapport du détecteur,
on n'y invente rien. C'est **le skill qui les réécrit** à chaque passage — en remplaçant tout ce qui
se trouve entre les deux marqueurs, jamais en insérant — et aucun script ne le fait à sa place. Les
champs rédigés en dessous sont **préservés**. C'est ce partage qui permet de rejouer le détecteur
sans écraser le travail d'analyse.

Une clé portée par **trois PRD ou plus**, et dont la règle est observable, sort d'ici pour devenir une
fonctionnalité transverse dans `transversal-features/`. Une clé éditoriale n'en sort jamais : deux specs affichant le même libellé
posent une question de cohérence ou de doublon, pas de comportement commun.

## Points d'attention

Ce que le détecteur n'a pas pu trancher seul. Sévérité en texte : **Blocking** / **Medium** / **Minor**.

C'est aussi **la destination des libellés non rédigés** — les clés dont le libellé vaut `TBD`,
`À définir` ou `TODO`. Le détecteur les exclut de toute comparaison, faute de quoi quatre clés
partageant « TBD par le PO » passeraient pour un doublon. Elles n'ont donc ni synchro ni
fonctionnalité transverse à rejoindre : sans cette ligne, elles sortent du rapport et disparaissent.
Nommer la conséquence, pas seulement la clé — un doublon réel restera invisible tant que le libellé
n'est pas écrit.

| # | Sévérité | Point | Impact | Résolution |
|---|---|---|---|---|
| 1 | **Medium** | [ex. un suffixe élidé sans forme canonique connue] | [ce que ça empêche] | [MCP clubmed_api, ou qui trancher] |

---

## [prdXX Nom] ↔ [prdYY Nom]

<!-- sync:auto généré le AAAA-MM-JJ -->
| Clé partagée | Type | Specs porteuses |
|---|---|---|
| `[METHODE /chemin]` | endpoint | [nom-de-spec](dcx/booking-engine/docs/specs/[prd-slug]/[spec].md) |
<!-- /sync:auto -->

**À aligner :** [Ce qui doit rester cohérent entre les deux. C'est le seul contenu qui compte
vraiment ici — une entrée sans ce champ ne dit rien de plus que « ces deux specs appellent le même
endpoint », ce que le détecteur sait déjà. QG-S9 avertit tant qu'il est vide.]

**Proposition de révision :** [Pour une clé éditoriale : dédoublonner, renommer l'une des deux, ou
confirmer que le partage est voulu. Laisser vide pour un endpoint.]

---

## Révisions éditoriales — même libellé, clés différentes

Deux clés portant le même texte. Ce n'est pas toujours un doublon : deux surfaces partagent
légitimement un mot, et le vocabulaire d'interface se duplique à dessein. La colonne Signal ordonne
la lecture, elle ne tranche pas.

Quand il faut trancher, **l'attestation décide** : un libellé attesté par un DRD Content Contract
l'emporte sur une clé encore à créer dans Directus.

<!-- sync:auto généré le AAAA-MM-JJ -->
| Libellé | Portée | Clés | Signal |
|---|---|---|---|
| «&nbsp;[texte]&nbsp;» | inter-PRD | `[clé.a]` · `[clé.b]` | [signal calculé] |
<!-- /sync:auto -->

**Décisions éditoriales :** [Clé retenue, clé abandonnée, et pourquoi. Une ligne par arbitrage rendu.
Les collisions laissées volontairement en l'état se notent ici aussi — sinon elles reviendront à
chaque passage et quelqu'un finira par les unifier à tort.]

**Décision :** [L'arbitrage rendu, avec sa date. Vide tant que rien n'est tranché.]

---

<!-- Une entrée dont la clé n'est plus portée par aucune spec est marquée **Obsolète** dans son
     titre — jamais supprimée : la décision qui l'accompagne garde sa valeur même quand la clé
     disparaît, et une entrée périmée qui se tait est indiscernable d'une entrée juste. -->
