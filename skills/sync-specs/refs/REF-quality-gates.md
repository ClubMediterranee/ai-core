---
name: ref-quality-gates
description: >
  The quality gates on the documents sync-specs produces — which are scripted, which stay with the
  model, and why a transversal feature without tests needs them more than any other artifact.
type: reference
---

# Quality gates

## Pourquoi elles existent

Le script existe **parce que le modèle ne peut pas se noter lui-même**. Une porte où l'auteur est
aussi le juge dérive, silencieusement, et le document paraît conforme longtemps après avoir cessé de
l'être.

Ici, l'enjeu est plus fort qu'ailleurs : **une fonctionnalité transverse ne porte aucun test d'acceptation**, par
construction. Rien ne casse quand elle devient fausse : une règle périmée y survit indéfiniment,
sans qu'aucune recette ne s'en aperçoive.

Les gates ci-dessous **sont** le signal qui manque.

## Scriptées — `validate_sync.py`

| Gate | Objet | Niveau |
|---|---|---|
| QG-S1 | Frontmatter de fonctionnalité transverse complet, `status` dans l'énumération, `date` ISO | ERROR |
| QG-S2 | Ancres `sync:auto` et `sync:keys` présentes et appariées | ERROR |
| QG-S3 | Liens du corps relatifs au repo et résolvant sur disque | ERROR |
| QG-S4 | Table des porteurs non vide et cohérente avec les citations réellement trouvées | ERROR |
| QG-S5 | Règle nommée par aucune spec porteuse — règle morte | ERROR |
| QG-S6 | Citation ne liant pas tous les `VAR-nn` déclarés | ERROR |
| QG-S7 | Valeur de `VAR-nn` liée par aucune spec — branche non portée | WARN |
| QG-S8 | Valeur liée mais aucun scénario §9 tagué avec une règle de la fonctionnalité transverse — branche non testée | WARN |
| QG-S9 | Entrée de registre dont « À aligner » est vide | WARN |
| QG-S10 | Clé de registre disparue des specs, entrée non marquée obsolète | ERROR |
| QG-S11 | Fonctionnalité transverse dont la preuve d'entrée n'est faite que de clés CMS | ERROR |
| QG-S12 | Fonctionnalité transverse de moins de deux règles — le registre la porte mieux | WARN |
| QG-S13 | `prd_source` d'une spec ne résout pas — le PRD est la dimension de jointure | ERROR |
| QG-S14 | Tous les porteurs d'une fonctionnalité transverse en `status: draft` | WARN |
| QG-S15 | Restes de template : commentaire d'instanciation (ERROR), `[placeholder]` (WARN) | ERROR/WARN |
| QG-S16 | Déclaration `transversal_features:` et liaisons en commentaire qui ne concordent pas | ERROR |
| QG-S17 | `VAR-nn` ne nommant aucun champ du §8 — un axe que le contrat de données ne porte pas | WARN |

## Portées par le détecteur, pas par le validateur

Deux contrôles éditoriaux vivent dans `sync_specs.py` et non ici, parce qu'ils portent sur les
**specs** et non sur les documents produits — les attraper à l'étape 1 évite de proposer quoi que ce
soit sur une base fausse.

| Contrôle | Objet | Niveau |
|---|---|---|
| Divergence de libellé | même clé CMS, libellés différents — une clé rend un seul texte | ERROR |
| Divergence d'attestation | même clé, classe de source différente (`drd` vs `directus`) | WARN |
| Libellé non rédigé | `TBD`, `À définir`, `TODO` — exclu de toute comparaison | WARN |

## Laissées au modèle

Aucun script ne peut les rendre, et prétendre le contraire produirait une conformité de façade.

**L'observabilité d'une règle.** Un utilisateur remarquerait-il l'incohérence en utilisant deux
verticales ? C'est le critère qui sépare une règle produit d'une factorisation de code. Voir
`REF-extraction-criteria.md`.

**La granularité d'une fonctionnalité transverse.** Couvre-t-elle exactement un mécanisme ? QG-S12 n'attrape que le cas
dégénéré — une seule règle. Une fonctionnalité transverse de six règles qui en mélange deux passe toutes les gates.

**La pertinence du champ « À aligner ».** QG-S9 vérifie qu'il est rempli, pas qu'il dit quelque
chose. « Vérifier la cohérence » remplit la case et n'apprend rien à personne.

**La justesse d'une proposition de révision CMS.** Le détecteur classe une collision de libellé en
« même élément à deux emplacements », « surfaces différentes » ou « vocabulaire d'interface », à
partir de la seule forme des clés. Ce signal ordonne la lecture, il ne décide pas : seul quelqu'un
qui connaît les deux surfaces sait si elles devront un jour dire deux choses différentes. Unifier à
tort est plus coûteux que le doublon — il faudra rescinder.

## Comment réagir

**`✗ ERROR`** — corriger et relancer jusqu'à ce que ce soit propre. Ne pas rapporter le travail
comme fait tant qu'une erreur subsiste.

**`⚠ WARN`** — lire chacun et décider : corriger, ou confirmer que c'est intentionnel et le dire à
l'utilisateur. Deux méritent une attention particulière, parce qu'ils décrivent la mort lente d'une
fonctionnalité transverse plutôt qu'un défaut de forme :

- **QG-S7, branche non portée** — un point de variation déclaré que personne n'utilise. Soit la
  valeur est de trop, soit un porteur manque.
- **QG-S8, branche non testée** — une branche portée mais qu'aucun scénario n'exerce. C'est le trou
  dans la raquette que toute la mécanique cherche à rendre visible : la règle est écrite, elle est
  citée, et rien ne la vérifie. **Elle se lève dans le run** : la quatrième marque de citation est un
  scénario de §9 tagué avec l'id de règle (`REF-citation-feature.md`). Un WARN QG-S8 qui subsiste
  après écriture est donc un choix, pas une fatalité — dire lequel.
- **QG-S17, axe non ancré** — un point de variation qu'aucun champ du §8 ne porte. La gate est en
  WARN parce qu'un axe légitimement produit — une locale, une règle resort — n'a effectivement aucun
  champ. Mais c'est aussi la signature d'un axe lu dans le §5 seul, donc deviné : le §8 est le seul
  endroit où la variation est observable, et il a déjà été confronté à l'API par le skill `spec`.

## Non-régression

`sync-specs` ne modifie jamais la structure d'une spec — seulement son frontmatter, une ligne de §5
et un commentaire. Pour le prouver, on **compare** deux exécutions du validateur du skill `spec` :
une capturée à l'étape 3, avant toute modification, une à l'étape 7 après écriture.

```bash
diff /tmp/specs-before.txt /tmp/specs-after.txt
```

**Tout constat qui apparaît est bloquant.** Lire le seul code de sortie ne suffit pas : le corpus
porte déjà des avertissements préexistants, et un nouveau s'y cacherait sans être vu. C'est
pourquoi le baseline se capture à l'étape 3 — après l'étape 6, il est trop tard.
