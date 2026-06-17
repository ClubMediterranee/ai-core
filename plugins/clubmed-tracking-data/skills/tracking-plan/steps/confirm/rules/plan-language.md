# Rule — Plan language

- All `plan.json` content (descriptions, rationales, trigger text, open questions) MUST
  be written in **English**.
- `detail_click` slugs are **language-independent stable IDs** — snake_case, no
  localised words. Use `criterias_when` not `criteres_quand`; `validate_step` not
  `valider_etape`.
- Address the user during confirmation (step 04) in **their language** (detect from their
  messages).
- Error messages and print outputs may be in the user's language.
- The `open-questions.md` file is in English.

**Why:** Plans are consumed by developers and analytics teams across locales. Localised
slugs break dashboards when the UI language changes. Stable English IDs are durable.
