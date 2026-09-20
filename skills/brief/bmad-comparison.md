# Skill `brief` et méthode BMAD — analyse comparée

> Pour les mainteneur·es. Jamais chargé en session. En français, même exception explicite que
> `decision-record.md`.
>
> **Sources.** BMAD : `bmad-code-org/BMAD-METHOD@main`, lu le 19/09/2026 — `skills/bmad-product-brief/`
> (`SKILL.md`, `assets/brief-template.md`, `customize.toml`), `skills/bmad/scripts/memlog.py`,
> `skills/bmad-advanced-elicitation/`, `skills/bmad-forge-idea/`, `skills/bmad-prfaq/`.
> Nous : skill `brief` v1.0.0 → v1.2.0, et les essais à blanc des 18 et 20/09/2026 (PM simulée,
> Sonnet) — les chiffres cités en viennent.

## 1. Deux objets différents

| | BMAD `product-brief` | Notre `brief` |
|---|---|---|
| Ce que c'est | Un document de pitch et d'alignement, 1 à 2 pages, forme libre | Un contrat d'espace problème, lu par `/prd`, à structure figée |
| Contenu | Problème, **solution, différenciation, vision**, cibles, succès, périmètre | Outcomes, preuves gradées, persona, key problem, opportunités, tensions — **aucune solution** |
| Conduite | Un fichier de 11,5 Ko, une posture de coach, **ni steps ni gates** ; deux modes (rapide / coaching) | Cinq steps à gates, écriture après validation, trois références de méthode |
| Mémoire | Journal plat append-only (`.memlog.md`) + `addendum.md` | Aucune : le fichier du brief est le seul état (v1.2.0) ; ce qui appartient à l'aval va en §7 *Parked* |
| Réussit quand | La personne est fière de son brief et peut le présenter | `/prd` peut bâtir dessus sans résoudre le mauvais problème |

La comparaison vaut donc pour les **pratiques**, pas pour le résultat : on ne juge pas leur brief
sur nos critères, ni l'inverse.

## 2. Nos partis pris — pourquoi, ce qu'ils apportent, ce qu'ils coûtent

| Parti pris | Pourquoi | Avantages | Inconvénients |
|---|---|---|---|
| **Pas de solution dans le brief** | Le brief est ce contre quoi une solution sera jugée ; si elle y figure, elle se juge elle-même. Une PM arrive presque toujours avec une solution (essai 1 : « je veux une wishlist ») : c'est le biais que le skill existe pour casser | Le problème est formulé indépendamment de la réponse ; plusieurs solutions restent possibles pour `/prd` ; la PM voit ce que sa solution doit prouver. Essai 1 : la wishlist est devenue « une solution candidate d'OPP-001, parmi d'autres » | Frustrant pour une PM qui a déjà décidé ; le brief ne peut pas servir de pitch ; il faut un domicile visible pour la solution, sinon elle semble jetée — d'où §7 *Parked*, hors engagement, qui a son propre risque : la solution figure physiquement dans le document et peut être lue comme du périmètre ; une solution imposée par contrat rend le skill inutile — cas d'exclusion de la description |
| **Processus à gates** | Une validation explicite par artefact empêche de bâtir une persona sur des signaux non confirmés, et rend la session reprenable et évaluable. Hérité du `prd`, où quatre campagnes ont montré qu'une progression passive produit des documents « validés » que personne n'a validés | Reproductible ; évaluable (on peut contrôler qu'un gate a été présenté et ce qui a été écrit quand) ; reprise exacte après interruption ; la PM sait toujours où elle en est | Des tours en plus : 10 à 16 par session, quand BMAD peut livrer en 3 ou 4 ; rigidité ressentie ; la mécanique d'écriture coûte de la latence (essais : 77 à 105 s par réponse en moyenne) ; deux comportements à tenir sous pression (ne pas prendre un accord à une question pour le gate) |
| **Preuves typées et gradées, confiance calculée** | Un brief vaut ce que valent ses preuves ; sans gradation, un on-dit et une mesure se lisent pareil | La confiance ne dépend pas de l'assurance de la PM ; le plan de validation découle du niveau ; `/prd` sait sur quoi il bâtit | Plus lourd à remplir ; peut paraître procédurier sur une petite évolution ; demande à l'agente de déclasser ce que dit la PM, donc une posture ferme |
| **Écriture après validation seulement** | Le fichier enregistre du travail validé, pas un brouillon (décision durable du `prd`) | Le fichier ne contient jamais de non-validé ; pas de nettoyage en fin de session | Un step interrompu avant son gate est à refaire ; BMAD, qui écrit en continu, ne perd rien |
| **Le fichier du brief est le seul état** (v1.2.0) | La mémoire canonique coûtait un tiers à la moitié des écritures, doublonnait le brief et créait deux sources de vérité, pour une valeur propre faible | Un seul fichier à écrire, à lire, à reprendre ; la PM voit tout ; rien à synchroniser | Pas de reprise en cours de step ; le pourquoi d'un choix secondaire n'est gardé que s'il est dans le brief ; diverge du `prd`, qui garde sa mémoire |
| **L'agente ne pose jamais `validated`** | `validated` doit vouloir dire « une personne a relu et accepté » | Statut fiable pour `/prd` | Un geste manuel avant chaque `/prd` |
| **Un cadre, pas un script** | Des questions scriptées font réciter et coûtent le même nombre de tours que les inputs soient riches ou vides | L'agente dérive, confronte, s'adapte ; tours divisés par 2,2 contre l'ancien skill scripté (16 contre 35) | Moins prévisible qu'un script ; repose sur la qualité du modèle ; exige des garde-fous (trois classes de contenu) pour que la liberté ne corrompe pas les preuves |

## 3. Appliqué depuis BMAD — et pourquoi

| Pratique BMAD | Ce que nous en avons fait (v1.1.0) | Pourquoi |
|---|---|---|
| « Read what exists first; ask only what is missing » · questions **consolidées** du mode rapide | *Derive first, then close the gaps in one move* : tout dérivable → présentation et gate en un message ; trous indépendants → **une** question groupée | Essai 1 : Step 1 a pris 4 tours en questions successives. Converge avec le contrôle de suffisance du `prd` |
| *Brain dump* d'ouverture, puis « anything else? », avant de creuser | Step 0 : vider la tête de la PM **avant** de montrer le moindre cadrage | Un cadrage montré d'abord ancre ce dont elle se souvient ; or les signaux ne se dérivent pas, ils ne sont souvent que dans sa tête |
| « Ease as the brief firms up » (calibrer la pression) | *Challenge the framing* : « la plupart des présentations n'en portent aucune » ; une rivale qui ne change pas l'artefact n'est pas dite | Essai 2 : lecture rivale donnée sur un problème en confiance `High` — elle était devenue une rubrique |
| Intention **Validate** | Intention *Validate* : les trois mouvements du quality gate sur un brief existant, constats avec leurs lignes, offre d'amendment | Presque gratuit (le quality gate existe) ; sert les briefs historiques et les revues |
| Relecture finale par sous-agents indépendants | Mouvement B du quality gate confié à un sous-agent qui ne reçoit que le fichier et le Challenge Pass | Essai 1, débrief : « je n'ai pas relu le fichier en entier » ; leçon du `prd` : un gate jugé par l'auteur dérive |
| `forge-idea` : trois issues valides, dont *Killed* et *Clearer* | **Verdict de maturité** à la clôture : prêt pour `/prd`, ou pas encore et quoi collecter | Essai 1 : l'issue honnête était « allez chercher les 3 tickets » ; le brief le disait en tension mais annonçait quand même « pour `/prd` » |
| « Surface what is unknown alongside what is known » | États légitimes `Not established`, plancher différé, opportunité différée | Les agentes ont improvisé faute de règle (cause racine inconnue, PM qui ne tranche pas) |
| `forge-idea` : « praise is noise » · « do not assume the user's terms are precise » | Phrase de posture ; ligne *Fuzzy term* du Challenge Pass | Essai 1 : la tension T-01 venait d'un terme flou (« conversion ») |
| Catalogue de 59 méthodes d'élicitation | Quatre patterns ajoutés à `[A]` : recadrer la question, inversion, effet de second ordre, triangulation des sources | Diversifie `[A]` sans coût de tour. Leur **menu** n'est pas repris (§5) |
| « 1–2 pages, le reste en addendum » | Consigne souple de longueur dans le modèle (résumé en dix lignes, impact d'une tension en une phrase) | Nos briefs d'essai : 12 à 14 Ko, dont du verbiage dans les tensions |
| Écritures peu nombreuses (esprit du memlog) | Un seul `Write` de création, puis aussi peu d'éditions que possible, jamais de réécriture du fichier ; **plus de mémoire séparée** (v1.2.0) | Essais : 36 éditions dont 24 sur la mémoire (v1.0.0), puis réécritures du fichier entier et 6 à 10 écritures de mémoire (v1.1.0) ; validations de 100 à 254 s (v1.0.0), 134 à 246 s (v1.1.0), 62 à 211 s (v1.2.0) |
| `addendum.md` : garder visible ce que la personne apporte et qui appartient à l'aval | **§7 *Parked*** dans le brief, hors engagement : `Item · Kind · For · Origin` | Même intention — rien de ce que dit la PM ne se perd, et elle voit où c'est passé — sans fichier ni écriture de plus |
| Orientation de la personne à l'ouverture (« greet the user », modes annoncés) | Step 0 s'ouvre sur six lignes : espace problème, chemin, validations, livrable | La PM ne savait ni où elle était ni pourquoi sa solution était mise de côté (demande PM du 20/09) |

## 4. Candidat à une itération — et pourquoi pas maintenant

| Pratique BMAD | Intérêt | Pourquoi plus tard | Ce qui déclencherait l'itération |
|---|---|---|---|
| **`addendum.md` séparé**, à la place de §7 | Le brief resterait sans aucune solution, même parquée ; l'aval lit un fichier dédié | Un fichier et des écritures de plus ; un nom à faire ignorer par la liste de briefs du `prd` ; la PM a choisi §7 pour la simplicité | Si §7 est lu comme du périmètre par des lecteur·rices, ou si `/prd` s'ancre sur les solutions parquées |
| **Journal append-only** (`.memlog.md`) | Reprise en cours de step, audit chronologique des décisions, écritures bon marché | Exige un script et Bash ; la mémoire vient d'être supprimée pour sa lourdeur — y revenir demanderait une preuve de besoin | Si des sessions interrompues en plein step deviennent fréquentes et coûteuses |
| **Calibrer la profondeur aux enjeux** (« right-size to purpose ») | Frugalité là où elle est légitime (petite évolution) | Moins reproductible, plus dur à évaluer ; c'est sur les « petites » évolutions que passent les mauvaises features | Mesuré en v1.2.0 : 13 tours sur une évolution incrémentale — à décider |
| **Recherche web en sous-agent** pour vérifier un benchmark | « Tous nos concurrents l'ont » deviendrait un fait vérifié, en parallèle, sans tour en plus | Coût, permission d'outil ; un benchmark reste `Weak` dans notre grille, donc gain limité | Une demande de PM, ou un brief `Market` dont le benchmark est la preuve principale |
| **Mode headless** avec statut JSON | Évals et intégration continue (valider les briefs d'un dépôt) | Contredit l'humain dans la boucle pour la création | Pour l'intention *Validate* seulement, quand `validate_brief.py` existera |
| **Surface de personnalisation** (`customize.toml` : sources internes, envois Confluence, gabarit) | Brancher les outils d'une équipe sans forker le skill | Infrastructure (résolveur, `uv`) prématurée pour une seule équipe | Une deuxième équipe utilisatrice aux besoins différents |

## 5. Mis de côté — et pourquoi

| Pratique BMAD | Pourquoi nous ne la reprenons pas |
|---|---|
| **Solution, différenciation et vision dans le brief** | C'est leur définition du brief. La nôtre exclut la solution (§2) ; ces contenus appartiennent au PRD ou à un document de pitch |
| **Absence de steps et de gates** | Latence faible et liberté maximale, mais ni reproductible ni évaluable, et aucune garantie de couverture (rien n'oblige à traiter le damage control). Incompatible avec un protocole d'évaluation et un contrat lu par `/prd`. Nous en gardons la leçon : **les critères, pas la chorégraphie** — les débriefs citent comme utiles les modèles (trois classes, échelle, Challenge Pass), jamais les procédures |
| ***Fast path* : tout le brief rédigé, puis revue** | Contredit « rien dans le fichier avant `[C]` » (décision durable, fondée sur des campagnes) et supprime la confrontation step par step qui fait la valeur du brief ; deux modes doublent la surface d'évaluation. Sa moitié utile — questions consolidées — est appliquée |
| **Persistance temps réel du brouillon** (`status: draft` écrit en continu) | Même raison : notre fichier ne contient que du validé. Leur filet de sécurité est le memlog ; le nôtre, le fichier lui-même, rempli section par section à chaque gate |
| **Menu d'élicitation** (cinq méthodes proposées, la personne choisit, boucle Apply / Reject) | Des tours en plus, et la campagne `prd` a montré que demander à la PM « que veux-tu creuser ? » est l'échec type : `[A]` est le travail de l'agente |
| **Personas simulées** (`party-mode`, voix de `forge-idea`), commandes « attack / defend this » | Party Mode a été retiré du brief : optionnel, coûteux, déclenché par la PM — donc absent quand elle est le plus sûre d'elle. *Challenge the framing* agit sans être demandé, dans la présentation |
| **« You will not do the thinking for them »** comme règle générale | Nous dérivons ce qui est dérivable d'une source : c'est plus frugal, et BMAD lui-même fait l'inverse dès que la personne bloque (« a concrete proposal is easier to accept, reject, or revise »). Nous en gardons la moitié juste : **les signaux et les décisions structurantes ne se dérivent jamais** |
| **Gabarit « a starting structure, not a contract »** | Nos titres, colonnes et valeurs sont des tokens lus par `/prd` et, demain, par un validateur |
| **Envois externes en fin de session** (Confluence, Slack) | Suppose des outils MCP pré-autorisés, que nous avons retirés (le joker couvrait aussi l'écriture) |
