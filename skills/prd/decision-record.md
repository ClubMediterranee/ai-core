# Decision record — skill `prd`

> Les décisions **majeures et critiques** prises sur ce skill, pour les reviews : se souvenir et
> justifier. Une ligne par décision, triée par catégorie. Ce fichier n'est jamais chargé pendant
> une session PRD (absent des Bundled resources).
>
> **En français pour le moment** — exception explicite de la PM à la règle « docs skills en
> anglais » du CLAUDE.md. **Type** : *durable* (remise en cause = nouvelle décision) ou
> *temporaire* (probatoire — la colonne Comment dit ce qui déclencherait la révision).
> **Fondements** : méthode/étude à l'appui et/ou la mesure de campagne qui a motivé la décision.

## Gates & validation

| Décision (version) | Description | Raison — risques mitigés / supprimés | Fondements | Type | Comment |
|---|---|---|---|---|---|
| Gates = deux lignes fixes, machine tokens (1.6.0) | Le bloc de gate ne porte que `[A] Advanced Elicitation` / `[C] Validate → …`, jamais de checklist | Les checklists embarquées étaient traduites/altérées dans tous les runs observés ; ce que `[C]` exécute est le process de l'agente, pas un objet de review PM | Campagnes 2026-08 (traduction systématique observée) | durable | — |
| La confirmation naturelle valide un gate (1.7.0) | `[C]` **ou** une confirmation claire, donnée au bloc de gate qui est la dernière chose présentée, sans modification/réserve/question | Un PM réel répond « OK », pas `[C]` ; risque mitigé par les 3 conditions : l'accord donné à une question ne ferme jamais un step | Choix PM ; campagne v1.6.1 (3 runs fermés sur un accord donné à autre chose) | **temporaire** | Probatoire — « si KO lors des tests, on remettra le C littéral ». Revue à chaque campagne (v1.7.1 : 1 run sur 3 encore fautif au Step 1) |
| Write only after `[C]` ; la mémoire canonique est exempte pendant la dérivation (1.4-1.5) | Rien n'atteint le fichier PRD avant validation ; la mémoire prend les éléments parqués au fil de l'eau | Le PRD enregistre du travail validé, pas un brouillon ; une écriture anticipée fait du gate une chambre d'enregistrement | Campagnes (écritures hors gate = 1er échec observé : 7 → 2 → 5 selon versions) | durable | La répétition ×5 « Before [C]… » dans les steps est **délibérée** — ne pas « optimiser » |
| A WARN is not a pass — listé verbatim au gate (1.7.1-1.7.3) | La présentation du quality gate affiche chaque WARN restant ; corrigé ou arbitré par la PM | Un WARN que la PM n'a jamais vu n'est pas arbitré (run réel : WARN livré sans être montré) | Campagne v1.7.1 (run-3) | durable | — |
| §6/8/9 écrits au `[C]` du step qui repère l'item (1.7.2) | Jamais parqués jusqu'au Step 6, qui ne fait que clore les restes | Deux runs réels avaient lu la règle précédente en sens opposés ; un 3e bloqué au Step 6 | Débriefs des 3 runs v1.7.1 | durable | — |

## Dérivation & altitude

| Décision (version) | Description | Raison — risques mitigés / supprimés | Fondements | Type | Comment |
|---|---|---|---|---|---|
| La discipline cœur du skill est l'altitude (1.7.3) | Chaque fait à son niveau — but dans la journey, capacité dans le FUNC, condition dans son critère — énoncé une fois ; le document doit durer pour qui travaille dessus (dev qui spec, PM qui modifie une règle) | Une BR inline dans une journey crée de la dette ou un double effort à chaque évolution ; constaté sur prd03 (présélection encodée dans un pas) | Cockburn, *Writing Effective Use Cases* (2000) — niveaux de buts ; *Business Rules Manifesto* (BRG, 2003) — règles séparées des processus ; DRY (Hunt & Thomas, 1999) ; prd03 PR#100 | durable | L'échelle des mailles + test de placement vivent dans SKILL.md (en contexte du Step 0 à la reprise) |
| Park and Surface (1.7.3) | Tout input PM différé est parqué en mémoire canonique sous le bac du step consommateur, et la présentation le nomme | La PM ne doit jamais avoir « prompté pour rien » : un input invisible → re-prompt → frustration → abandon du skill ; différé/coupé/faux ont trois domiciles (cette règle / Name the Arbitrations / Challenge Pass) — rien ne disparaît en silence | Analyse PM sur prd03 ; mécanisme mesuré (le récap Sources classé top-3 aide par un producteur) | durable | — |
| Provenance plutôt que filtre (1.7.1) ; complétée : une source légitime l'existence, jamais la forme (1.7.3) | Dériver de tout (DRD, glossaire, autres PRDs), présenter avec la source, la PM garde ou coupe au gate ; ce qu'une maquette rend en composant entre comme la capacité qu'il sert | Rejeté : filtre amont (« mode react coûte que coûte ») — aurait aveuglé la dérivation ; risque résiduel constaté puis fermé : « sourcé » lu comme exemption d'altitude (prd03 : FUNCs découpés sur l'arbre de composants du DRD) | Campagne v1.7.1 : Q6 1/2/5 → 5/5/3 ; prd03 FUNC-005-009 | durable | — |
| Les capacités se découpent par capacité, jamais par conteneur (1.7.3) | Un `GIVEN` d'état de conteneur UI (« le layer est ouvert ») n'est pas un état du monde ; test : « the capability is no longer true if the mockup changes » | Trois onglets = un à trois capacités par le discriminant, jamais trois FUNCs parce que la maquette a trois onglets | prd03 (FUNC-006-009, un par onglet) | durable | Moitié lexicale au script (QG-2 WARN), moitié sémantique au Challenge Pass |
| Frontière FUNC = résultat observable autonome (1.2.0) | Un seul discriminant remplace contraintes de format et bornes numériques | Les bornes poussaient au découpage artificiel ; le discriminant tranche les fusions/scissions | Pratique use cases (Cockburn — « manage X ») | durable | — |
| Le nombre de journeys est une décision de lisibilité (1.3.0) | Invariant : la réorganisation ne change jamais l'ensemble des capacités révélées | Sépare le débat de forme du débat de périmètre | Patton, *User Story Mapping* (2014) — variations sous les activités | durable | Tension scission/fusion (#8) documentée, à designer avec la PM |
| LGM/DC importées, jamais dérivées (1.4.0) | Toute métrique sans ancre brief = tension loggée, jamais un ajout silencieux | Le brief reste la source de vérité du succès | REF-brief-contract ; pratique RE (ISO/IEC/IEEE 29148 — traçabilité) | durable | — |
| Un brief non validé est un signal, pas un mur (REF-brief-contract) | Nommer, demander, logger la tension, continuer si la PM le veut | La PM peut légitimement explorer avant validation formelle | — | durable | — |

## Langue

| Décision (version) | Description | Raison — risques mitigés / supprimés | Fondements | Type | Comment |
|---|---|---|---|---|---|
| Tokens vs shapes (1.6.0-1.7.0) | Ce que le script ou `spec` lit reste anglais figé (titres de sections, en-têtes de colonnes, `Acceptance criteria:`, GIVEN/WHEN/THEN, marqueurs) ; les patterns de titres FUNC sont des **formes** dont les mots suivent la langue de la PM | Un token traduit aveugle silencieusement le validateur ; un titre FUNC anglais dans un PRD français casse l'harmonie (3 PRDs réels constatés) | Campagnes v1.6.1/v1.7.0 | durable | — |
| Les labels de prose FUNC suivent la langue du document (1.7.3) | `Actor:` / `Capability:` / `Nominal scenario:` traduits (« Acteur : », « Capacité : », « Scénario nominal : ») | Vérifié : ni le validateur ni le skill `spec` ne les lisent — harmonisation à coût machine zéro ; rejeté : tout traduire (table d'alias par langue dans le validateur, casse des PRD existants) | grep exhaustif spec + validateur (2026-09) | durable | — |

## Ids & structure

| Décision (version) | Description | Raison — risques mitigés / supprimés | Fondements | Type | Comment |
|---|---|---|---|---|---|
| Les ids sont des identifiants, pas des rangs (1.2.0) | Jamais renuméroté ; un id retiré laisse un trou, normal et attendu | La cascade de renumérotation traverse §3, §5, les scénarios, les PERM — pour zéro contenu ; le validateur ne signale **volontairement pas** les trous | — | durable | Ne pas ajouter ce check (documenté dans le docstring du validateur) |
| Les bullets §4 dupliquent §5 délibérément (1.2.0) | Un FUNC liste ses critères avec leur description ; §5 est la source de vérité, le bullet réaligne sur divergence | Sans description, personne ne fait l'aller-retour sur 10 critères et les règles ne sont plus lues ; coût de propagation assumé | Exception DRY consciente ; `spec` compare verbatim | durable | — |
| En-tête Lagging Metrics à 3 colonnes accepté (1.5.0) | `ID/Metric/Threshold` toléré à côté de la forme à 4 colonnes | Les PRDs écrits avant `Baseline (T0)` parsent encore ; leurs cellules sont lues par des règles indépendantes de la position | — | **temporaire** | Héritage — à retirer quand les anciens PRDs auront migré |

## Instruments & retenue

| Décision (version) | Description | Raison — risques mitigés / supprimés | Fondements | Type | Comment |
|---|---|---|---|---|---|
| One check, one home (1.6.0) | Script / Challenge Pass / jugé : une règle, une définition, un domicile | Deux définitions de la même règle dérivent sans que personne ne voie laquelle le gate applique (rejeté : QG jugés paraphrasant les tables CP) | DRY appliqué aux contrôles ; dérive observée pré-1.6.0 | durable | — |
| Les définitions vivent dans l'échelle de SKILL.md ET dans leur REF, phrases-clés identiques (1.7.3) | L'échelle donne la ligne, la REF la méthode | Rejeté : fichier glossaire séparé — risque compaction (définition absente au Step 3-4), REFs non auto-portantes, une lecture de plus, pour un risque de dérive jamais observé en 9 versions | Analyse coût/risque 2026-09 | durable | La redite d'une ligne est assumée ; verbatim = anti-dérive |
| La grille de complexité est consultative | Le PM peut passer outre ; le validateur WARN, jamais ERROR — et dit qu'il ne compte que les FUNCs | Le script ne sait pas compter les personas (prose libre) ; un faux ERROR bloquerait à tort | — | durable | — |
| Lexique UI QG-2 en WARN (1.7.3) | Liste serrée EN+FR de composants non ambigus, §3 et §4 seulement | Une liste de mots peut sur-tirer : un lecteur arbitre ; le principe (tripwire lexical) est durable | prd03 (cas de contrôle positif : modale, layer, onglet) | **temporaire** (la liste) | La liste se calibre par campagne ; le principe reste |
| « claude » exclu de `AI_AUTHOR_RE` | Le garde anti-« IA en author » matche anthropic/noreply/copilot/gemini/chatgpt/openai, pas les prénoms | Claude est un prénom humain réel — un faux ERROR sur l'author d'une PM est pire que le trou | — | durable | — |
| Le validateur voyage avec sa suite de tests (1.4.0+) | `test_validate_prd.py` teste le validateur, jamais un PRD ; jamais chargé en run | Chaque évolution du script est verrouillée par 50+ cas mutation-vérifiés ; séparés, ils dériveraient | Pratique standard code+tests | durable | Question récurrente en review — le docstring du validateur le dit désormais |
