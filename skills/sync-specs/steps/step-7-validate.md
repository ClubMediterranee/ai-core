# Step 7 — Validate, report, publish

```bash
python3 <skill-dir>/scripts/validate_sync.py \
  --specs {DOCS_ROOT}/specs --features {DOCS_ROOT}/transversal-features \
  --register {DOCS_ROOT}/SYNCHRO.md --repo-root <repo-root>
```

Fix every `✗ ERROR` and re-run until clean. Read each `⚠ WARN` and decide: correct it, or tell the
user why it is intentional — `refs/REF-quality-gates.md` says which ones matter most and why.

## Prove you broke nothing

Diff against the baseline captured at Step 3:

```bash
python3 <spec-skill-dir>/scripts/validate_specs.py {DOCS_ROOT}/specs > /tmp/specs-after.txt
diff /tmp/specs-before.txt /tmp/specs-after.txt
```

**Any finding that appears is blocking.** Comparing matters: the corpus already carries pre-existing
warnings, and reading the exit code alone would let a new one hide among them. The diff also covers
the per-PRD manifests, since `validate_specs.py` checks them on both runs.

Do **not** re-run the `spec` skill's adversarial reviewer (Step 7.2) — see
`refs/REF-citation-feature.md`.

## Report, then publish

Report: transversal features created, carriers attached, register entries touched, specs modified,
and the warnings consciously left open.

Then offer to send the work with the **`github-publish`** skill. Unlike `prd` and `spec`, which
create documents, this skill **modifies documents already reviewed by other people** — they need a
pull request to be read by the specs' owners, not a commit that lands unseen.
