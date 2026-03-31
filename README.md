# ai-core

Référentiel central de la **Guilde IA Club Med** — configurations Claude Code, skills, agents, documentation, tutoriels et benchmarks partagés entre les équipes.

## Objectif

Centraliser les ressources d'IA générative utilisées au quotidien par les développeurs Club Med :
- Standardiser les pratiques autour de Claude Code
- Partager skills et agents réutilisables entre projets
- Documenter les bonnes pratiques, retours d'expérience et benchmarks
- Accélérer l'onboarding des nouveaux membres de la guilde

## Structure

```
ai-core/
├── skills/          # Skills Claude Code réutilisables
├── agents/          # Agents spécialisés
├── docs/            # Documentation, tutoriels, guides
└── benchmarks/      # Évaluations et comparatifs de modèles/outils
```

## Prérequis

- [Claude Code](https://claude.ai/code) installé et configuré
- Accès au compte Anthropic de la guilde (voir #guilde-ia sur Slack)

## Utilisation

### Skills

Les skills sont des commandes slash (`/`) invocables directement dans Claude Code.

Voir [`skills/README.md`](skills/README.md) pour la liste complète et les instructions d'installation.

### Agents

Les agents se trouvent dans `agents/` et s'utilisent via la commande `/agent` de Claude Code.

### Documentation

La documentation est disponible dans `docs/` — tutoriels, guides de bonnes pratiques, benchmarks et retours d'expérience.

## Contribuer

1. Créez une branche à partir de `main`
2. Ajoutez votre skill / agent / doc dans le bon répertoire
3. Respectez les conventions de nommage existantes
4. Soumettez une PR avec une description claire

> Les commits suivent la convention [Conventional Commits](https://www.conventionalcommits.org/).

## Mainteneurs

Guilde IA Club Med — [jeremy.wallez@clubmed.com](mailto:jeremy.wallez@clubmed.com)
