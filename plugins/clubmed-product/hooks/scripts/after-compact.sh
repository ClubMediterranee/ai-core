#!/usr/bin/env bash
# SessionStart hook, matcher `compact`: re-anchor a prd session after the context was summarised.
#
# A compaction drops the files the agent had read. The state of a PRD in progress lives on disk —
# the PRD itself (its `## Parked` block first), the project record under record/, the skill and
# the current step's reference — so what matters is that they are read again before anything
# else. This script prints that instruction first (Claude Code adds its stdout to the context
# right after the compaction), then lists, best effort and bounded, the PRDs in progress it can
# see. It never fails the session: exit 0 whatever happens, and never more than a few seconds.

cat <<'EOF'
Context was compacted. If a PRD session is in progress, before anything else:
re-read the prd skill (SKILL.md), the PRD being written — its "## Parked" block first —,
the project record under record/, and the reference of the current step.
Nothing reaches a numbered section or the record before the PM's [C]; a "## Parked" row is
written as soon as an item is parked. The gate recap of the last presentation is what [C] writes.
EOF

# best effort: the docs root may be the cwd or a sibling repository. Only `prd/` folders are
# searched, four levels deep, skipping dependency and VCS trees — never the whole home directory.
prds=$(find . ../*/docs -maxdepth 4 -type f -path '*/prd/prd[0-9]*.md' \
         -not -path '*/node_modules/*' -not -path '*/.git/*' 2>/dev/null \
       | xargs -I{} grep -l '^status: in-progress' {} 2>/dev/null \
       | while IFS= read -r f; do (cd "$(dirname "$f")" && printf '%s/%s\n' "$(pwd -P)" "$(basename "$f")"); done \
       | sort -u | head -5)

if [ -n "$prds" ]; then
  printf 'PRDs in progress found:\n%s\n' "$prds"
fi
exit 0
