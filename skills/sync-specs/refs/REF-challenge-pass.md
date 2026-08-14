---
name: ref-challenge-pass
description: >
  Challenge Pass protocol for sync-specs: the automatic anti-pattern filter applied before every
  presentation of a proposal (fonctionnalité transverses, register entries, citations).
type: reference
---

# Challenge Pass — protocole

Un **filtre automatique**, pas une étape de dialogue. Il s'applique avant toute présentation, que la
proposition vienne du détecteur ou de l'utilisateur.

**Comportement :**
- anti-pattern détecté → le nommer + proposer la version corrigée ;
- aucun → continuer en silence, sans commentaire ;
- plusieurs dans la même passe → les grouper en un seul message (ce sont des filtres parallèles, pas
  des questions successives).

Le détecteur trouve des **clés partagées**. Il ne sait pas si un partage signale une règle commune —
et la plupart du temps, il n'en signale pas. Ce filtre est ce qui empêche un rapport brut de devenir
une pile de fonctionnalité transverses qui ne servent à rien.

---

## Anti-patterns

| Anti-pattern | À quoi ça ressemble | Correction |
|---|---|---|
| **Plomberie prise pour une règle** | La clé partagée est de l'infrastructure : authentification, tracking, rafraîchissement de proposition, un endpoint de panier appelé par tout le funnel. Le partage est réel mais n'implique aucun comportement que l'utilisateur puisse comparer. **Ces exemples illustrent, ils ne classent pas** — c'est la seconde phrase qui décide. | Reclasser en entrée de registre. Ne pas ouvrir de fonctionnalité transverse. **Sauf si** une règle observable s'attache à cette clé : on extrait alors la règle, pas l'endpoint. Trancher par le test de réénonciation sans terme d'API (`REF-extraction-criteria.md`). |
| **Fonctionnalité transverse fourre-tout** | Une fonctionnalité transverse couvre plusieurs mécanismes qui ne partagent ni machine d'états ni groupe d'endpoints — souvent parce qu'ils sont apparus dans le même rapport. | Scinder : une fonctionnalité transverse par mécanisme. La proximité dans un rapport n'est pas une parenté. |
| **Clé CMS déguisée en feature** | Un libellé partagé remonte comme candidat à factorisation. | Reclasser en registre + proposition de révision. Une fonctionnalité transverse est pour un comportement, pas pour un mot. |
| **Règle non observable** | La règle proposée ne se verrait pas en utilisant deux verticales — une clé technique, une forme de payload, un ordre d'appel. | Ni fonctionnalité transverse ni registre : c'est de la factorisation dev, elle se traite dans le code. |
| **Doublon de fonctionnalité transverse existante** | Le mécanisme est déjà couvert par une fonctionnalité transverse en place, sous un titre différent. | Rattacher le porteur à la fonctionnalité transverse existante. Dédoublonner **par clé**, jamais par titre : un titre dérive au fil des relectures. |
| **Fonctionnalité transverse sur porteurs `draft`** | Tous les porteurs sont en `status: draft` — la fonctionnalité transverse fige des règles qui peuvent encore bouger. | Proposer quand même, mais **le dire** : c'est une base mouvante, et une fonctionnalité transverse réécrite trois fois perd son autorité. |
| **Extraction prématurée** | Deux porteurs seulement, mais la tentation d'anticiper le troisième. | Registre. Deux, c'est une coïncidence ; la fonctionnalité transverse attend le motif. |
| **Reformulation qui tranche** | La reformulation proposée pour une synchro décide en fait d'un arbitrage produit (quel libellé gagne, quelle spec porte la règle). | Séparer : proposer la reformulation **et** signaler l'arbitrage comme une question, sans le résoudre à la place du PO. |
| **Libellé générique pris pour un doublon** | Deux clés portent « Add-ons », « Learn more », « Validate » — et la proposition suggère de n'en garder qu'une. | Ne rien unifier. C'est du vocabulaire d'interface : une seule clé coupleraient des surfaces sans rapport, et la première demande de nuance obligerait à la rescinder. |
| **Même mot, deux surfaces** | `…remote.childcare` et `…section.childcare.title` disent tous deux « Club enfants », donc on propose de fusionner. | Ne pas fusionner. Le jour où la section devient « Votre club enfants » et la remote reste « Club enfants », il faut deux clés — et les avoir fusionnées coûtera plus cher que le doublon. |
| **Unification sans propriétaire** | On propose de garder une clé sur deux sans dire laquelle fait foi. | Trancher par l'attestation : une clé dont le libellé est attesté par un DRD l'emporte sur une clé encore à créer dans Directus. Si les deux sont attestées, c'est un arbitrage éditorial — le poser en question. |

---

## Ce que le filtre ne fait pas

Il ne juge pas la **qualité** d'une règle une fois qu'elle est légitimement extraite — c'est le
travail de la relecture, et des gates de `validate_sync.py` pour ce qui est vérifiable.

Il ne remplace pas non plus le critère d'observabilité de `REF-extraction-criteria.md` : le filtre
attrape les cas où la proposition est manifestement mal classée, le critère tranche les cas où elle
est plausible.
