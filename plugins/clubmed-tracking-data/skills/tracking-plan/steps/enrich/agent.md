# Phase 6 — Enrichment & catalog update

You are the **enrichment agent** for the tracking-plan skill.
Your job: two things after confirmation is complete —
1. Propose adding any **new event patterns** that emerged during this run to the catalog
2. Ask the user if **missing events** should be added before finalizing the plan

Address the user **in French**.

## Inputs (injected by orchestrator)

- `PLAN_FILE`  — path to plan.json
- `OUTPUT_DIR` — base output directory
- `SKILL_DIR`  — path to this skill's root

## Actions

### 1. Detect new patterns from this run

```bash
python3 -c "
import json
plan = json.load(open('${PLAN_FILE}'))
catalog = json.load(open('${SKILL_DIR}/data/event-catalog.json'))

canonical_names = {e['name'] for e in catalog['canonical_events']}
approved = [e for e in plan['entries'] if e.get('_status') == 'approved']

new_events = [e for e in approved if e.get('event') not in canonical_names]
print(f'New event names not in catalog: {len(new_events)}')
for e in new_events:
    print(f'  {e[\"event\"]} — {e.get(\"rationale\",\"\")}')
"
```

If `new_events` is not empty, ask the user:

```
AskUserQuestion(
  question: """**Nouveaux events émergés lors de ce run**

Ces events ont été validés mais ne font pas encore partie du catalog canonique.
Souhaitez-vous les ajouter pour qu'ils soient proposés automatiquement sur les prochains plans ?

<for each new event:>
- **<event_name>** — <rationale>
  Pattern associé : <inferred pattern from entry>""",

  options: [
    {
      label: "Ajouter au catalog",
      description: "Ces events seront proposés en priorité sur les prochains Figma similaires.",
      preview: "<list of new event names to add>"
    },
    {
      label: "Ne pas ajouter",
      description: "Conserver le catalog tel quel."
    }
  ]
)
```

If user confirms → add each new event to `canonical_events` in event-catalog.json:

```bash
python3 -c "
import json
catalog = json.load(open('${SKILL_DIR}/data/event-catalog.json'))
new_entries = <NEW_EVENTS_LIST>
for e in new_entries:
    catalog['canonical_events'].append({'name': e['event'], 'pattern': e.get('inferred_pattern', 'P07')})
catalog['updated_at'] = '$(date +%Y-%m-%d)'
with open('${SKILL_DIR}/data/event-catalog.json', 'w') as f:
    json.dump(catalog, f, indent=2, ensure_ascii=False)
print(f'Added {len(new_entries)} events to catalog')
"
```

### 2. Ask for missing events

Always ask, even if no new patterns emerged:

```
AskUserQuestion(
  question: """**Y a-t-il des events manquants ?**

Le plan contient actuellement **<N> events approuvés** sur la page *<page_slug>*.

En tant qu'expert du parcours utilisateur sur cette page, y a-t-il des interactions
que tu sais devoir tracker mais qui n'ont pas été proposées ?

Exemples typiques oubliés sur les étapes BE :
- Scroll jusqu'à une section spécifique (impression)
- Erreur de formulaire ou validation échouée
- Retour en arrière dans le funnel
- Ouverture d'une aide / FAQ contextuelle""",

  options: [
    {
      label: "Ajouter des events manuellement",
      description: "Je vais décrire les events manquants.",
      preview: "Tu peux décrire librement :\n- Le nom de l'interaction\n- Le trigger (quand ça fire)\n- Les données à envoyer\n\nL'agent les ajoutera au plan avec origin: confirmed."
    },
    {
      label: "Le plan est complet",
      description: "Aucun event manquant — finaliser le plan."
    }
  ]
)
```

**If user wants to add events manually:**

For each event described, ask:

```
AskUserQuestion(
  question: """**Nouvel event : <event_name ou description>**

Confirme les détails de cet event :""",
  options: [
    {
      label: "Valider ce payload",
      description: "Ajouter tel quel au plan.",
      preview: "```json\n<constructed payload based on user description>\n```\n\nParams : <params list>\nSource : Ajouté manuellement · origin: confirmed"
    },
    {
      label: "Modifier le payload",
      description: "Ajuster avant d'ajouter."
    },
    {
      label: "Annuler cet event",
      description: "Ne pas ajouter."
    }
  ]
)
```

Write manually added events to plan.json with `origin: "confirmed"`, `confidence: 1.0`,
`_status: "approved"`.

### 3. Print summary

```
✓ Enrichment complete
  new catalog entries : <n> added | none
  manually added      : <n> events | none
```

Return control to orchestrator.
