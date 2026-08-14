# Adhérences avec le skill `spec`

`sync-specs` s'exécute **sur les specs produites par `spec`** et réutilise ses conventions. Ce
document liste ce qui est adhérent, où, et ce qui casse si `spec` change.

À lire **avant toute modification du skill `spec`**, et à relire après.

## Échelle de criticité

| | Nature | Pourquoi ce rang |
|---|---|---|
| 🔴 **Critique** | Casse **silencieuse** — une gate se trompe sans erreur d'exécution | Le run paraît propre et le résultat est faux. Les deux incidents connus sont de ce type |
| 🟠 **Élevé** | Casse **bruyante** — le script échoue, une commande ne résout pas | Immédiatement visible, donc corrigeable |
| 🟡 **Moyen** | Dérive **documentaire** — le texte devient faux, rien ne casse | Coûte une confusion de lecteur, pas un livrable faux |

---

## A. Code exécuté

| Adhérence | Où dans `sync-specs` | Impact si modif côté `spec` | Criticité |
|---|---|---|---|
| `<spec-skill-dir>/scripts/validate_specs.py` lancé deux fois (baseline et après écriture) | `steps/step-3`, `steps/step-7` | Chemin cassé → **le diff de non-régression ne peut plus être produit**, l'étape 7 ne prouve plus rien | 🟠 |
| Résolution `<spec-skill-dir>` = `../spec` | `SKILL.md`, section des ressources | Déplacement ou distribution séparée de `spec` → même effet | 🟠 |
| Sortie textuelle de `validate_specs.py` comparée par `diff` | `steps/step-7` | Changement de format de sortie → **diff faussement non vide**, tout run bloque | 🟠 |

---

## B. Code copié, jamais importé

Six éléments recopiés depuis `validate_specs.py`. **Aucun test ne compare les deux implémentations.**

| Élément | Rôle dans `sync-specs` | État vérifié le 13/08/2026 | Criticité |
|---|---|---|---|
| `ID_RE` | Ids cités par une spec (QG-S5) | Identique à l'octet | 🔴 |
| `TRACE_RE` | Tags de trace du §9 (QG-S8) | Identique à l'octet | 🔴 |
| `mask_fences` | Neutralise les blocs de code avant de chercher les titres | Texte divergent, **résultats identiques** sur 24 specs | 🔴 |
| `parse_frontmatter` | Lit `prd_source`, `status`, `transversal_features` | idem | 🔴 |
| `sections` | Découpe §1–§9 — **base de toute la détection** | Signature différente (3-uplet vs dict), **résultats identiques** | 🔴 |
| `gherkin_scenarios` | Parse les scénarios du §9 | idem | 🔴 |

**Pourquoi 🔴 partout** : une divergence ne lève aucune erreur. Elle change ce que le détecteur *voit*,
donc ce que les gates concluent.

### Incidents déjà survenus

| Symptôme observé | Cause | Correctif |
|---|---|---|
| QG-S5 signalait « règle morte » sur **toutes** les règles | `ID_RE` ne connaît pas le préfixe `RULE-`, absent de son alternance | Union avec `RULE_ID_RE` dans `Spec.ids` |
| QG-S8 signalait « branche non testée » sur **toutes** les branches, quel que soit le nombre de scénarios | `TRACE_RE` ne connaît pas `RULE-` → le tag cherché n'était jamais collecté | Union avec `RULE_ID_RE` dans `traced_ids` |

Même schéma les deux fois : une alternance de préfixes copiée de `spec`, antérieure aux
fonctionnalités transverses, qui rend une gate **définitivement fausse** sans rien casser.

### Contrôle d'équivalence — automatisé

```bash
python3 scripts/check_spec_drift.py {DOCS_ROOT}/specs [--spec-skill-dir ../spec]
```

Lancé à **l'étape 1, avant le détecteur** : un parseur qui a dérivé fausse toute la détection, et
l'apprendre à l'étape 7 serait trop tard. Il vérifie les deux regex à l'octet, les quatre parseurs
par équivalence de résultat sur le corpus, et les deux listes documentées ci-dessous.

Exit 1 = divergence, exit 2 = `spec` introuvable — qui bloque aussi le diff de non-régression des
étapes 3 et 7.

---

## C. Conventions citées noir sur blanc

| Convention `spec` | Où dans `sync-specs` | Impact si modif | Criticité |
|---|---|---|---|
| **Les 5 tags de catégorie** gherkin (`@nominal-passing`…) | `refs/REF-citation-feature.md`, en clair — **comparé au code par `check_spec_drift.py`** | Un tag renommé ou ajouté → la 4ᵉ marque écrite est **rejetée par `validate_specs.py`**, diff non vide, run bloqué | 🔴 |
| **Les 6 préfixes de trace** `@FUNC/BR/ERR/ACC/PERM/ST` | Deux copies (prose + `ID_RE`/`TRACE_RE`), **tenues alignées par `check_spec_drift.py`** | Les deux copies dérivent indépendamment | 🔴 |
| Ancres `dc:index`, `dc:clarify`, `dc:handoff` | 4, 1 et 1 fichiers | Renommage → le détecteur ne trouve plus le §8, **zéro clé détectée** | 🔴 |
| Ancre `at:tests` | 2 fichiers | Renommage → §9 introuvable, QG-S8 toujours au rouge | 🔴 |
| Clé de frontmatter `prd_source` | 4 fichiers | Renommage → **la dimension de jointure disparaît**, plus aucun seuil PRD calculable (QG-S13) | 🔴 |
| Clé `related_specs` | 4 fichiers | Sens modifié → l'argument qui justifie un champ dédié tombe | 🟡 |
| §5 recopié verbatim du PRD + marqueur `(implied by DRD)` | `refs/REF-citation-feature.md` | Convention changée → la ligne de §5 posée par `sync-specs` devient non conforme | 🟡 |
| Convention de chemin du frontmatter (relatif au fichier de spec) | `SKILL.md` §Paths, `REF-citation-feature.md` §3 | Changement → `transversal_features:` ne résout plus | 🟠 |
| **« l'étape 7.2 de `spec` »**, désignée par son numéro | `refs/REF-citation-feature.md` | Renumérotation de `spec` → renvoi muet vers une étape qui n'existe plus | 🟡 |

---

## D. Comportements de `spec` non contractuels

Trois adhérences reposent sur des effets de bord, **non documentés côté `spec`**.

| Comportement | Ce qu'il permet | Impact s'il change | Criticité |
|---|---|---|---|
| `validate_specs.py` vérifie la **présence** des clés de frontmatter et **ignore les inconnues** | La déclaration `transversal_features:` | Passage en validation stricte → **toutes les specs citées deviennent invalides** | 🔴 |
| Un tag `@RULE-…` n'est ni une catégorie ni une trace → **ignoré sans broncher** | La 4ᵉ marque (scénario §9 tagué) | Validation stricte des tags → toute spec citée en erreur | 🔴 |
| `check_manifest` compare **tout** nom de `.md` du manifeste au contenu du dossier | Justifie l'interdiction de toucher aux `index.md` | Assouplissement → l'interdiction devient inutile ; durcissement → elle devient insuffisante | 🟡 |

---

## Index inverse — « je modifie X dans `spec` »

| Ce que je change dans `spec` | Ce que je vérifie dans `sync-specs` |
|---|---|
| Une ancre `dc:*` ou `at:tests` | Détection du §8 et du §9 : relancer le détecteur, vérifier que le nombre de clés est inchangé |
| Un préfixe d'id, ou ajout d'un nouveau | `ID_RE` et `TRACE_RE` dans `sync_specs.py`, **et** la liste en prose de `REF-citation-feature.md` |
| Un tag de catégorie gherkin | La liste en clair de `REF-citation-feature.md`, contrainte n°2 de la 4ᵉ marque |
| `sections`, `mask_fences`, `parse_frontmatter`, `gherkin_scenarios` | Rejouer le contrôle d'équivalence (§B) |
| Une clé de frontmatter | `prd_source` (jointure) et `related_specs` (argument du champ dédié) |
| La validation du frontmatter (présence → strict) | **Bloquant** : `transversal_features:` doit être ajouté aux clés admises de `spec` |
| La numérotation des étapes | Le renvoi à « l'étape 7.2 » dans `REF-citation-feature.md` |
| Le format de sortie de `validate_specs.py` | Le diff de non-régression de l'étape 7 |
| `check_manifest` | L'interdiction de toucher aux `index.md` (`steps/step-6`) |

---

## Le sens de la dépendance

`sync-specs` → `spec` uniquement. `spec` n'a **aucune** connaissance de `sync-specs`, ce qui a deux
conséquences à connaître :

1. Une **régénération** par `spec` réécrit le fichier entier et **efface les quatre marques** —
   citation et scénario de §9 compris. À annoncer avant d'appliquer (`steps/step-3`).
2. Les adhérences de la section D ne sont pas des contrats mais des coïncidences. Les transformer en
   contrats suppose d'apprendre les fonctionnalités transverses à `spec` — chantier non engagé.
