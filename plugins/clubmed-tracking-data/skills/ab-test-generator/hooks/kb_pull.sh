#!/bin/bash
# SessionStart hook — met à jour la Knowledgebase ClubMed (dcx/analytics-cro) au démarrage de Claude Code.
# Ne clone jamais automatiquement : si le dossier est absent, affiche la commande à lancer et
# continue sans bloquer la session. Silencieux si tout va bien, affiche un message uniquement
# en cas de mise à jour ou d'absence.

KB="${CLUBMED_KB:-$HOME/.clubmed/knowledge-base}"

if [ ! -d "$KB/.git" ]; then
    echo "{\"systemMessage\": \"ℹ️ Knowledgebase introuvable ($KB). Clone-la une fois avec : git clone https://github.com/ClubMediterranee/knowledge-base.git $KB — le skill ab-test-generator continue sans les leçons accumulées ni le design system Trident UI pour cette session.\"}"
    exit 0
fi

cd "$KB" || exit 0

git fetch origin main --quiet 2>/dev/null || exit 0

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    exit 0
fi

git pull origin main --quiet 2>/dev/null

echo '{"systemMessage": "✅ Knowledgebase mise à jour depuis GitHub (dcx/analytics-cro : leçons et design system à jour)"}'
