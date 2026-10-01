# AB Test Task Contract

Le contrat est le **gate G1** : aucun code n'est généré tant qu'il n'existe pas. Il remplace
le brief libre par un artefact structuré, versionné avec le test, et relu par A2 avant
validation. Le brief conversationnel (`references/brief-standard.md`) reste la méthode pour
*collecter* l'information ; le contrat est la méthode pour la *figer*.

Tout champ déduit plutôt que fourni est suffixé `(hypothèse)`. Les champs inconnus restent
`À CONFIRMER` — jamais inventés.

## Format complet (Production Grade)

```
# AB TEST TASK CONTRACT — [nom court] — [date] — v1

## 1. Contexte
- Client / projet :
- Contexte business (pourquoi ce test, pourquoi maintenant) :
- Tests déjà menés sur cette zone (résultats connus) :

## 2. Cible
- URL(s) / template :
- Pays / langue (impact wording, longueurs de texte, formats prix) :
- Devices : desktop | mobile | tablette | tous
- Audience / segment :
- Part de trafic allouée :

## 3. Objectif & mesure
- Objectif business :
- Hypothèse CRO : "En [X], on s'attend à [Y mesurable] parce que [Z insight]."
- KPI primaire (+ comment il est tracké dans AB Tasty : click / page / custom event / transaction) :
- KPI secondaires :
- Garde-fous (métriques qui ne doivent PAS se dégrader : rebond, revenu/visite, vitesse) :
- Testabilité : trafic page/mois ≈ … | taux de base ≈ … | MDE visé ≈ … | durée estimée ≈ …

## 4. Mécanique envisagée
- Description fonctionnelle de la variation :
- Éléments touchés (langage métier) :
- Comportements dynamiques (sticky, scroll, apparition conditionnelle…) :

## 5. Contraintes UX
- Charte : à respecter strictement | marges de liberté :
- Accessibilité : AA minimum (non négociable)
- Wording imposé / interdit :

## 6. Contraintes techniques & environnement
- Outil : AB Tasty (défaut) | autre
- Anti-flicker : géré nativement | snippet requis
- SPA / navigation dynamique (pushState) : oui / non
- CMP / consentement : le test dépend-il du consentement ? bandeau susceptible de
  masquer/décaler la zone ?
- Autres scripts tiers sur la zone (chat, reviews, personnalisation) :
- Tests A/B concurrents sur la page ou l'audience :
- Interdits : toucher au tracking existant, au SEO (pas de cloaking), aux formulaires…

## 7. Inputs manquants
- [ ] … (chaque item = une question à poser ou une hypothèse assumée)

## 8. Risques
- Techniques (sélecteurs fragiles, DOM dynamique, flicker…) :
- Business (brand, juridique prix/promo, collision de tests…) :
- Statistiques (trafic insuffisant, KPI trop bas dans le funnel…) :

## 9. Plan d'exécution
- Mode : Fast Build | Production Grade
- Agents activés : A1 → … → A9
- Gates applicables : G1 … G5
```

## Contrat minimal (Fast Build)

```
# CONTRAT MINIMAL — [nom court]
- URL :                          - Devices :
- Changement(s) :                - Outil : AB Tasty
- Hypothèse (1 ligne) :          - KPI primaire :
- Contraintes connues :          - Hypothèses assumées : …
Gates : G1 (tacite), G2, G3.
```

En Fast Build : remplis-le toi-même depuis le message utilisateur, affiche-le, pose **au plus
une** question (la plus bloquante — en général l'URL ou le device), et considère la validation
tacite si l'utilisateur répond sans objection.

## Règles de validation (G1)

- **Production Grade** : le contrat complet est affiché et l'utilisateur valide explicitement
  (« Je pars là-dessus ? »). L'avis A2 (GO / GO AVEC RÉSERVES / NO-GO) est affiché avec.
- Un NO-GO d'A2 n'interdit pas de continuer : l'utilisateur peut passer outre, mais le
  NO-GO et sa raison restent inscrits au contrat et rappelés dans la livraison finale.
- Toute itération ultérieure qui change l'hypothèse, le KPI ou la cible → nouvelle version
  du contrat (v2, v3…), pas un patch silencieux.
