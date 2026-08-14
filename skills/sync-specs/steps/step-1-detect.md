# Step 1 — Detect

## First, check you still read specs the way `spec` writes them

```bash
python3 <skill-dir>/scripts/check_spec_drift.py {DOCS_ROOT}/specs
```

The detector **copies** two regexes and four parsers from `validate_specs.py` rather than importing
them. A copy that has drifted raises nothing — it simply makes the detector see a different document
than the one `spec` validated, and a quality gate becomes quietly wrong. It has happened twice.

Run it here, not later: a drifted `sections()` falsifies the whole detection, and Step 7 would be too
late to learn it. **Stop on exit 1** and align first — `ADHERENCES-spec.md` says what depends on what.
Exit 2 means `spec` was not found, which also blocks Steps 3 and 7.

## Then detect

**Ask what to compare.** Either the whole corpus — a periodic audit — or the specs of one PRD against
all the others (`--focus <prd-slug>`, matched against each spec's `prd_source`), the natural
follow-up to a `spec` run. Default to the whole corpus if the user has no preference.

In both cases the detector reads **every spec** under `{DOCS_ROOT}/specs/` — focus filters the
*report*, never the corpus, because a collision has two sides and dropping one makes it invisible
rather than shorter.

```bash
python3 <skill-dir>/scripts/sync_specs.py {DOCS_ROOT}/specs \
  --features {DOCS_ROOT}/transversal-features \
  --register {DOCS_ROOT}/SYNCHRO.md \
  --repo-root <repo-root> \
  [--focus prd07-food-and-drinks]
```

Always pass `--features` and `--register`, even when they do not exist yet: the report then states
which sources it consulted and whether each was present, instead of leaving you to guess whether
"nothing covered" means "nothing found" or "nothing looked at".

Read `refs/REF-join-keys.md` for what the detector joins on and what it deliberately refuses to join
on. The two classification rules it applies, which you need at Step 3:

- **2 distinct PRDs** carrying a key → register entry;
- **≥ 3 distinct PRDs** carrying an *endpoint* → transversal feature candidate;
- a CMS key stays in the register **whatever the count**, and a key shared inside a single PRD is
  ignored — `spec` already owns that case.

**On an elided endpoint** (`POST …/cart/services`) the detector refuses to guess, and the two cases
are not equivalent: matching **no** full path still joins on the suffix (Medium), matching
**several** does not join at all (Blocking). Read `refs/REF-endpoint-resolution.md` and resolve via
the `clubmed_api` MCP. If the MCP is not connected, say so at Step 3 **with the count** — a silent
degradation is worse than a blocked one.
