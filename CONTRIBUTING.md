# Contribuer à ai-core

Bienvenue dans la Guilde IA Club Med. Ce guide explique comment contribuer au référentiel `ai-core`.

## Prérequis

- [Claude Code](https://claude.ai/code) installé et configuré
- Accès au dépôt (voir #guilde-ia sur Slack)

## Workflow

1. Créez une branche depuis `main`
   ```bash
   git checkout -b feat/mon-skill
   ```
2. Ajoutez votre contribution dans le bon répertoire (voir [Structure](#structure))
3. Commitez en suivant les [conventions de commit](#commits)
4. Soumettez une Pull Request avec une description claire

## Structure

| Répertoire   | Contenu                                      |
| ------------ | -------------------------------------------- |
| `skills/`    | Skills Claude Code (commandes `/`)           |
| `agents/`    | Agents spécialisés                           |
| `docs/`      | Documentation, tutoriels, bonnes pratiques   |
| `benchmarks/`| Évaluations et comparatifs de modèles/outils |

## Ajouter un skill

Chaque skill est un dossier `skills/<nom>/` contenant un fichier `SKILL.md` avec le frontmatter suivant :

```yaml
---
name: nom-du-skill
description: 'Description courte utilisée par Claude pour déclencher le skill'
model: haiku          # haiku | sonnet | opus
allowed-tools: Bash   # outils autorisés
version: 1.0.0
changelog:
  - version: 1.0.0
    date: YYYY-MM-DD
    changes:
      - Initial release
created-at: YYYY-MM-DD
created-by: "Prénom Nom <email@clubmed.com>"
---
```

## Ajouter un agent

Chaque agent est un dossier `agents/<nom>/` contenant un fichier `AGENT.md` décrivant son rôle, ses outils et ses instructions système.

## Commits

Les commits suivent la convention [Conventional Commits](https://www.conventionalcommits.org/) :

```
<type>(scope): <description en anglais>
```

Types courants : `feat`, `fix`, `docs`, `chore`, `refactor`

Utilisez le skill `/git-commit` pour générer automatiquement le message.

## Questions

Posez vos questions sur **#guilde-ia** (Slack) ou contactez [jeremy.wallez@clubmed.com](mailto:jeremy.wallez@clubmed.com).
