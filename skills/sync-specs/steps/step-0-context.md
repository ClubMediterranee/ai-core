# Step 0 — Context

**`{DOCS_ROOT}`** — the docs tree, containing `prd/`, `drd/` and `specs/`. It often lives in a
sibling repo, not under the cwd; ask if it is not obvious. **Repo root** — the `knowledge-base`
checkout that contains it, via `git rev-parse --show-toplevel` from inside the tree. It is what makes
the body links relative.

**Take the repo's pulse while you are there** — `git status --short` on `{DOCS_ROOT}`. Step 3 needs
it to know which carriers can be edited, but knowing it now costs nothing and changes how you read
the detector's output: a spec modified and uncommitted may not say what its last commit says.

**Read the existing material before analysing anything.** Load every transversal feature under
`{DOCS_ROOT}/transversal-features/` and the register `{DOCS_ROOT}/SYNCHRO.md`, and note the keys they
already cover. Skipping this is how a second run proposes again what the first one extracted. Neither
existing means this is a first run — create `transversal-features/` at Step 4 when you need it.
