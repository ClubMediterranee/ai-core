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

| Skill | Description |
|-------|-------------|
| `clean-code` | Applique les principes du livre "Clean Code" de Robert C. Martin pour transformer du code fonctionnel en code propre |
| `excalidraw` | Génère des diagrammes Excalidraw à partir d'une description en langage naturel |
| `git-commit` | Génère des messages de commit conventionnels avec staging intelligent |
| `react-best-practices` | Bonnes pratiques React/Next.js de performance selon Vercel Engineering |
| `skill-creator` | Crée, modifie et évalue des skills Claude Code |

Pour utiliser un skill de ce repo, copiez ou référencez le dossier `skills/<nom-du-skill>/` dans votre configuration Claude Code locale (`~/.claude/skills/`).

```bash
# Exemple : installer le skill git-commit
cp -r skills/git-commit ~/.claude/skills/
```

Puis dans Claude Code :
```
/git-commit
```

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
