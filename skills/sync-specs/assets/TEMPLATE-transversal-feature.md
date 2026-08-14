<!-- TEMPLATE — retirer ce commentaire à l'instanciation (QG-S15 échoue tant qu'il est là).
     Aucun [crochet] ne doit subsister après instanciation : tout `[texte]` restant lève un WARN
     QG-S15, y compris dans le frontmatter.
     Un fichier par mécanisme partagé, dans {DOCS_ROOT}/transversal-features/<slug>.md.
     Les libellés se traduisent ; les ancres, les préfixes d'id et les clés de frontmatter, non. -->
---
id: TF-[nn]
title: "[Nom du mécanisme partagé]"
status: draft
owner: "[Prénom Nom]"
date: AAAA-MM-JJ
---

# [Nom du mécanisme partagé]

#### 1. Portée et preuve d'entrée

[Une ou deux phrases : quel comportement cette fonctionnalité transverse fige, et ce qu'elle ne couvre pas.]

Cette fonctionnalité transverse a été ouverte parce que les clés ci-dessous sont portées par au moins trois PRD
distincts. Elles sont la preuve d'entrée, pas une liste d'endpoints à implémenter — le contrat de
données de chaque porteur reste dans son §8.

<!-- sync:keys -->
| Clé | Type |
|---|---|
| `[METHODE /chemin]` | endpoint |
<!-- /sync:keys -->

**FUNC servis :** [FUNC-xxx de chaque porteur que ce mécanisme sert — ce qui situe la fonctionnalité transverse dans le
découpage fonctionnel des PRD sans la scinder artificiellement par FUNC.]

#### 2. Points d'attention

Ce qui reste ouvert et doit être tranché, par l'`owner` du frontmatter.

Sévérité, au même sens que celui donné aux endpoints élidés par le détecteur :
**Blocking** — le comportement est indéterminé, aucun porteur ne peut implémenter juste ;
**Medium** — le comportement est déterminé mais une variante n'est pas attestée ;
**Minor** — formulation ou présentation.

| # | Sévérité | Point | Impact | Résolution |
|---|---|---|---|---|
| 1 | **Blocking** | [la question qui change le comportement] | [ce qui casse si non résolu] | [qui tranche, où] |

#### 3. Règles

Chaque règle porte un id `RULE-<ID>-nn`. Une spec qui porte une règle **la nomme dans son §5** —
c'est ce qui rend la liste des porteurs dérivable au lieu d'être tenue à la main.

Écrire chaque règle de façon **observable** : un utilisateur doit pouvoir constater l'incohérence si
deux porteurs la traitent différemment. Une règle qu'aucun utilisateur ne peut voir est de la
factorisation de code, et n'a pas sa place ici.

**RULE-XXX-01** — [énoncé normatif, indépendant de tout service particulier]

**RULE-XXX-02** — [énoncé normatif]

#### 4. Points de variation

Les paramètres de la fonctionnalité transverse. C'est ce qui la distingue d'une règle uniforme : le comportement est
commun, ces axes-là varient **légitimement**. Une divergence qui n'entre dans aucun axe est un défaut
de spec, pas une variante.

Une spec qui cite la fonctionnalité transverse doit **lier chaque point de variation** — la couverture des branches se
déduit alors de l'ensemble des liaisons, sans qu'aucune liste ne soit maintenue.

| Point | Valeurs autorisées | Champ §8 qui le porte | Qui décide |
|---|---|---|---|
| **VAR-01** | [valeur-a], [valeur-b] | `[champ du contrat de données]` | [le produit / le resort / l'API] |
| **VAR-02** | [valeur-a], [valeur-b], [valeur-c] | `[champ]` | [qui] |

La colonne **Valeurs autorisées est lue par la machine** : `validate_sync.py` la découpe sur les
virgules et les barres obliques pour vérifier que chaque branche est portée et testée. Chaque valeur
est donc un **jeton nu**, sans ponctuation interne ni parenthèse explicative — `per-attendee`, pas
`par participant (un par enfant éligible)`. Une virgule à l'intérieur d'une valeur en crée deux, et
QG-S7 signale ensuite des branches que personne n'a déclarées.

La colonne **Champ §8** est ce qui distingue un axe d'une impression : elle nomme le champ du contrat
de données des porteurs sur lequel la variation se lit. Un axe qu'aucun champ ne porte reste
possible — une locale, une règle resort — mais il doit alors être justifié, et QG-S17 le signale.

**Son en-tête est porteur** : `validate_sync.py` localise cette colonne par le mot `§8`, `Champ` ou
`Field` dans la ligne d'en-tête, jamais par son rang. La renommer « Où l'axe se lit » viderait les
quatre champs et ferait tirer QG-S17 partout, sans que rien n'indique pourquoi. Le libellé se
traduit, à condition de garder l'un de ces trois mots.

Il n'existe pas de valeur « sans objet ». Un axe bien posé est **total** : chaque porteur a une
valeur, même quand elle vaut « imposé », « tous » ou « aucun ». Un porteur qui n'a rien à lier
signale soit un axe mal posé, soit un porteur qui n'appartient pas à cette fonctionnalité.

#### 5. Porteurs

Table **dérivée** : son contenu se déduit entièrement des citations trouvées dans les specs — ne
rien y inventer. C'est **le skill qui la réécrit** à chaque passage, en remplaçant tout ce qui se
trouve entre les deux marqueurs ; aucun script ne le fait à sa place. QG-S4 la compare ensuite aux
citations réellement présentes.

La colonne `Liaisons` reprend la syntaxe du commentaire de liaison, points de variation séparés
par ` · ` :

<!-- sync:auto -->
| Spec | Liaisons |
|---|---|
| [nom-de-spec](dcx/booking-engine/docs/specs/[prd-slug]/[spec].md) | `VAR-01=full-stay,per-day` · `VAR-02=all` · `VAR-03=none` |
<!-- /sync:auto -->

#### 6. Tests

**Aucun test ici.** Une fonctionnalité transverse est agnostique du service : un scénario n'y aurait ni acteur, ni
écran, ni jeu de données, donc rien à jouer en recette.

Les tests vivent dans les specs porteuses, où le montage est concret. La règle s'écrit une fois ici,
elle est testée autant de fois qu'il y a de porteurs — par un scénario du §9 **tagué avec son id de
règle**. Le plus souvent le scénario existe déjà sous un id local : on lui ajoute le tag plutôt que
d'écrire un doublon. QG-S8 signale toute branche liée qu'aucun scénario n'exerce, ce qui fait de ces
tags la carte de couverture : une verticale absente s'y voit.
