# Step 1 — Resolve the docs root and identify the PRD

## 1.0 — Resolve the docs root (do this first)

The docs tree is **not** assumed to live under the current working directory — it often sits in a
sibling repository. Establish `{DOCS_ROOT}` before anything else, and use it in every later step
instead of a bare relative path. The expected layout:

```
{DOCS_ROOT}/
├── prd/          ← PRD sources (read-only)
├── drd/          ← DRD sources (read-only)
├── …             ← other analysis material (briefs, glossary, context.md)
└── specs/        ← OUTPUT — one folder per PRD, written by this skill only
```

1. Search for a `prd/` directory **that actually contains `.md` files**: in the cwd, then in
   sibling repositories / parent directories (e.g. `docs/prd/`, `../*/docs/prd/`). **Ignore empty
   scaffolds** (a `prd/` with no `.md` is not a candidate) and **deduplicate the cwd** from the
   sibling matches.
2. **Exactly one candidate** → its parent is `{DOCS_ROOT}`; state it once and move on.
3. **Several candidates, or none** → ask the user which docs root to use. Do not guess.

**Legacy layout:** if the PRDs are found under `…/specs/prd/` (old tree where sources and output
were mixed), tell the user and propose migrating (`prd/`, `drd/` and the other sources move up
beside `specs/`; `specs/` becomes output-only). If they decline, keep working: `{DOCS_ROOT}` is the
parent of that `specs/`, with `prd/` = `specs/prd/` and `drd/` = `specs/drd/`, and the output still
goes to `specs/<prd-slug>/`.

## 1.1 — Identify the PRD and fix its slug

**If the user provided a path:** read that file directly.

**If no path was given:** list all `.md` files in `{DOCS_ROOT}/prd/` and ask the user which one to
process. Example output:

```
Available PRDs:
1. {DOCS_ROOT}/prd/PRD00 - Booking engine Foundations.md
2. {DOCS_ROOT}/prd/PRD01 - All-inclusive details in Ticket price.md
...
Which PRD would you like to turn into specs?
```

**Derive the PRD slug** — the kebab-case of the PRD filename (`PRD04 - Transport & Transfer
booking.md` → `prd04-transport-transfer-booking`). It names the output folder
`{DOCS_ROOT}/specs/<prd-slug>/` where every spec and the `index.md` manifest of this run are
written. If that folder **already exists**, this run is an **update** — Step 6.8's re-run policy
applies (diff and ask before touching anything).

## 1.2 — Author

**Ask once at the start:** "What is your name? (It will be used as the `author` field in all specs)" — unless the user's identity is already clear from context. The `author` is the **person running the skill** (the spec author) — **not** the PRD's own `author` frontmatter, which belongs to whoever wrote the PRD and must not be copied here.
