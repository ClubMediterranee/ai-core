---
name: ref-citation-feature
description: >
  How a spec cites a transversal feature: the machine-readable comment, the §5 line naming the carried rules,
  the frontmatter entry, and why binding every variation point is what makes coverage derivable.
type: reference
---

# Citer une fonctionnalité transverse depuis une spec

Une fonctionnalité transverse est une **fonction** : ses règles en sont le corps, ses points de variation la signature.
Une spec qui la cite est un site d'appel — et comme tout appel, il doit **lier tous les paramètres**.

Sans cette contrainte, la fonctionnalité transverse devient une invitation à la cohérence. Avec elle, la couverture des
branches se **déduit** de l'ensemble des liaisons : plus aucune liste à maintenir, plus aucune
divergence silencieuse.

## Les quatre marques à poser

### 1. Le commentaire de liaison — lu par la machine

```
<!-- feature:reservation-service VAR-01=card VAR-02=half-day,day-by-day VAR-03=per-attendee -->
```

Invisible au rendu, indépendant de la langue, même idiome que les ancres `dc:` du skill `spec`.
Plusieurs valeurs pour un même point se séparent par une virgule, sans espace.

**Où le poser : dans le §5, immédiatement au-dessus de la ligne de citation** décrite plus bas. Les
deux marques disent la même chose à deux lecteurs — la machine et l'humain — et les séparer les
condamne à diverger. Aucune gate ne vérifie l'emplacement ; c'est précisément pour ça qu'il faut une
convention.

**Le slug doit égaler le nom du fichier** de la fonctionnalité transverse, sans son extension :
QG-S16 compare la déclaration du frontmatter au slug du commentaire par le *stem* du chemin. Un
`feature:reservation` pointant vers `reservation-service.md` lève une ERROR sur une citation par
ailleurs correcte.

Une citation qui omet un point de variation déclaré par la fonctionnalité transverse échoue **QG-S6** : elle ne dit pas
quelle branche la spec porte, donc elle ne compte pour aucune.

### 2. La ligne de §5 — lue par un humain

Le §5 obéit à une règle stricte du skill `spec` : **les règles métier y sont recopiées verbatim
depuis le PRD**, et la *seule* chose qu'on ait le droit d'y écrire soi-même est une règle impliquée
par le DRD — marquée `(implied by DRD)` pour qu'un relecteur distingue les provenances d'un coup
d'œil.

Notre ligne est une **troisième provenance** : ni le PRD, ni le DRD, mais un document normatif
externe. Elle porte donc son marqueur, dans la même forme — sans quoi elle ressemble à une règle
inventée, ce que la convention du §5 existe justement pour empêcher :

```markdown
**Créneaux — règles communes.** *(portées par une fonctionnalité transverse)* —
[reservation-service](dcx/booking-engine/docs/transversal-features/reservation-service.md) :
RULE-RSV-01, RULE-RSV-02. Liaisons : VAR-01 = card (une card par enfant),
VAR-02 = half-day et day-by-day selon la locale.
```

La ligne **s'ajoute**, elle ne remplace rien : retirer ou reformuler une BR verbatim casserait la
vérification de couverture du skill `spec`.

**Nommer les ids de règle est ce qui rend la liste des porteurs dérivable.** C'est la même discipline
que les tags de trace du §9 : sans l'id, on sait qu'une spec cite la fonctionnalité transverse, pas quelle règle elle
porte. Une règle que personne ne nomme échoue **QG-S5** — règle morte.

### 3. Le frontmatter — la déclaration

```yaml
transversal_features:
  - ../../transversal-features/reservation-service.md
related_specs:
  - childcare-section-cards.md
```

Un **champ dédié**, pas `related_specs`. Ce dernier désigne les specs sœurs d'un même PRD ; y glisser
une fonctionnalité transverse surchargerait son sens, et `validate_specs.py` traiterait le document
comme une spec voisine — ce qu'il n'est pas.

Le champ dédié ne casse rien : `validate_specs.py` vérifie la **présence** des clés requises et
**ignore les clés inconnues**. Une spec qui porte `transversal_features:` reste valide pour le skill
`spec`.

**Ce que la déclaration apporte, que le commentaire n'apporte pas :** elle est visible sans lire le
corps. On sait ce qu'une spec porte en listant les frontmatters, et la question « qui porte cette
fonctionnalité ? » se répond par un `grep` au lieu d'une lecture.

**Rattraper les specs déjà écrites.** Une spec rédigée avant l'existence de la fonctionnalité
transverse n'a aucune raison de porter le champ. C'est exactement ainsi qu'un porteur passe
inaperçu — le skill **propose donc d'ajouter le champ** quand il détecte une spec qui partage les
clés d'une fonctionnalité existante sans la déclarer.

**Attention à la convention de chemin** : ici, relatif **au fichier de spec** — c'est celle du skill
`spec`. Dans le **corps** des documents produits, les liens sont relatifs à la racine du repo. Les
deux règles coexistent parce qu'elles servent deux lecteurs différents : un validateur qui résout sur
disque, et un humain qui lit sur GitHub.

### 4. Le scénario de §9 — ce qui rend la branche testée

La règle est écrite **une fois** dans la fonctionnalité transverse ; elle est testée **dans chaque
spec porteuse**. Sans le tag, QG-S8 signale la branche comme non testée — c'est le trou que toute la
mécanique cherche à rendre visible, et c'est cette marque qui le comble.

#### D'abord chercher, écrire seulement ensuite

**Sur un corpus mature, le comportement est déjà testé.** Une spec écrite avant la fonctionnalité
transverse teste la même chose sous son id local — `@BR-013` plutôt que `@RULE-RSV-02`. Écrire un
second scénario produirait alors un doublon que personne n'a demandé.

**Chercher d'abord un scénario existant qui exerce la règle, et lui ajouter le tag `@RULE-`** sur sa
ligne de tags. C'est la voie à préférer : rien n'est inventé, rien n'est reformulé, et
`validate_specs.py` ne voit aucun changement — le tag n'est ni une catégorie ni une trace à ses yeux,
il l'ignore sans broncher.

```gherkin
@nominal-passing @FUNC-002 @BR-008 @BR-013 @ST-001 @RULE-RSV-02
```

**N'écrire un scénario neuf que si rien n'exerce la règle.** C'est le seul cas où le skill affirme un
comportement plutôt que d'en constater un, et c'est ce qui lui vaut la relecture la plus attentive du
gate 2.

#### Écrire un scénario neuf

Un scénario ajouté dans la fence `gherkin` du §9, tagué ainsi :

```gherkin
@alternative-passing @BR-029 @RULE-RSV-01
Scénario: Un transfert au stock épuisé reste visible et non sélectionnable
  Étant donné un transfert dont la disponibilité vaut "fully_booked"
  Quand la section Transfert s'affiche
  Alors l'option reste visible
  Et elle n'est pas sélectionnable
```

Quatre contraintes, toutes vérifiées par `validate_specs.py` — les respecter est ce qui garantit que
le diff de non-régression reste vide :

1. **Dans la fence ` ```gherkin ` existante** du §9. Ne jamais en ouvrir une seconde. Les tags vont
   sur **une ligne à eux, juste avant le `Scénario:`**, chaque tag commençant par `@` — un tag posé
   ailleurs, en fin de ligne de scénario ou en commentaire, n'est jamais lu, et la branche reste
   silencieusement non testée.
2. **Exactement un** tag de catégorie : `@nominal-passing`, `@nominal-non-passing`,
   `@alternative-passing`, `@alternative-non-passing` ou `@edge`. Ni zéro, ni deux.
3. **Au moins un** tag de trace `@FUNC-…`, `@BR-…`, `@ERR-…`, `@ACC-…`, `@PERM-…` ou `@ST-…`, dont
   l'id est **déjà couvert par la spec en §1–§7**. Un id inventé est une erreur bloquante.
4. **Le tag `@RULE-xxx-nn`** de la règle transverse. C'est lui, et lui seul, que QG-S8 cherche : il
   n'est pas un tag de trace au sens de `validate_specs.py`, qui l'ignore sans broncher.

**Ne transcrire que le comportement déjà validé.** L'énoncé du scénario reprend la règle de la
fonctionnalité transverse — celle que l'utilisateur a confirmée. Le skill n'a pas lu les DRD ; il
n'est pas en position d'inventer un comportement, seulement de vérifier celui qui est écrit. Le
`Étant donné` reste spécifique à la verticale, et c'est normal : ce qui est factorisé, c'est le
**comportement attendu**, pas le montage.

Un seul scénario peut lever plusieurs branches à la fois, dès lors que la spec les lie toutes.

## Rester dans le cadre du skill `spec` sans le charger

Il ne faut **pas** lire le skill `spec` en entier pour poser quatre marques — SKILL.md, huit steps et
trois références noieraient l'agent pour un gain nul. Ce qui compte tient en six règles, et elles
sont ici :

1. **Chemins de frontmatter relatifs au fichier de spec** (`../../transversal-features/…`), jamais à
   la racine du repo — c'est la convention que `validate_specs.py` résout.
2. **Ne rien retirer ni reformuler dans le §5.** Les BR sont le texte du PRD, au mot près.
3. **Marquer la provenance** de la ligne ajoutée, comme le fait `(implied by DRD)`.
4. **Ne toucher à aucune ancre** : `dc:clarify`, `dc:index`, `dc:handoff`, `at:tests`. Les deux
   validateurs matchent dessus.
5. **Au §9, on tague ou on ajoute — on ne réécrit jamais.** Un tag `@RULE-` peut être ajouté à la
   ligne de tags d'un scénario existant, et un scénario peut être ajouté dans la fence `gherkin`
   existante. Rien d'autre : aucun scénario n'est reformulé ni supprimé, aucun tag existant n'est
   retiré, l'ancre `at:tests` n'est pas touchée, la couverture des `ERR-xxx` n'est pas recalculée.
6. **Ne dupliquer ni renuméroter aucun titre de section.** Le §5 existe déjà : on écrit dedans.

La garantie ne vient pas de la lecture du skill, elle vient de la **vérification** : `validate_specs.py`
tourne avant et après l'édition, et **tout constat nouveau est bloquant** (étape 7).

En revanche, la relecture adversariale du skill `spec` (son étape 7.2) n'a **pas** à être rejouée :
elle relit le PRD, contrôle la couverture des FUNC et revérifie les preuves du §8 contre le MCP —
exactement ce que ce skill s'interdit de rouvrir, pour un coût sans rapport avec trois lignes
ajoutées.

## Ce que le skill fait, et ne fait pas

Il **propose** les quatre marques et, après confirmation, les applique par `Edit` chirurgical. Il ne
réécrit jamais une spec entière.

**Limite à annoncer avant d'appliquer** : une régénération ultérieure par le skill `spec` effacera la
citation, puisqu'il réécrit le fichier complet et ne connaît pas encore les fonctionnalités transverses. Le dire après
coup, c'est laisser quelqu'un découvrir la perte tout seul. Cela vaut aussi pour le scénario de §9 —
et une perte de test se remarque moins vite qu'une perte de citation.

