# Step 7 — Validate the generated specs

Once all specs are written (Step 6.8), you **must** validate them before reporting the work done. Validation has two layers: a deterministic script that checks the form (everything present and filled in), and an independent reviewer that checks the meaning.

## 7.1 — Run the deterministic validator (blocking)

Run the bundled Python script (stdlib only, no install needed). Its path is `scripts/validate_specs.py`, relative to this skill's directory:

```bash
python3 <skill-dir>/scripts/validate_specs.py {DOCS_ROOT}/specs/<prd-slug>/          # this run's folder
python3 <skill-dir>/scripts/validate_specs.py {DOCS_ROOT}/specs                      # every PRD folder (recursive)
```

What it checks — **form and completeness only**, never meaning:

- **Frontmatter** — required keys present and non-empty; `confidence` / `data_contract_confidence` valid buckets *and* single values (a list is an error); `status` known; `data_contract_sources` ⊆ api/directus; `date` YYYY-MM-DD (WARN); each `related_specs` entry resolves on disk (WARN).
- **Structure** — the 9 sections present, in order, **not duplicated**, and none empty; §5 carries at least one PRD id. Headings inside fenced code blocks are ignored, so a spec may quote the template without shadowing its own sections.
- **§8** — sub-sections found by their anchors **on a heading**: `dc:clarify` and `dc:index` (ERROR), `dc:handoff` (WARN — a spec with nothing unresolved needs no Handoff); the endpoint index has at least one data row. When `api` is a declared source: at least one curl/bash block, one TypeScript block, one 🟢/🟡/🔴 tier (WARN each) — a pure-editorial spec is exempt from those three.
- **§9** — anchor `at:tests`; Gherkin parsed **inside the fence only**; each scenario carries **exactly one** category tag and **at least one** trace tag; every traced id is one the spec actually covers (§1–§7); at least one passing scenario; **every `ERR-xxx` written as a rule in §5 has a non-passing scenario tagged with it**. WARN under three scenarios.
- **§6 assets** — every local image path resolves on disk, relative to the spec file (handles `%20`, spaces, `<…>` and titles).
- **`index.md` manifest** — in each PRD folder: every spec it lists exists, every sibling spec is listed (WARN otherwise).
- **Sizing** — WARN when §5 exceeds ~15 rules or §8 details more than ~5 endpoints (likely >2h for an AI — consider a split).

**Exit codes:** `0` clean · `1` at least one ERROR · `2` nothing to validate — a bad path, not a success.

How to react:
- **`✗ ERROR`** — **fix every error and re-run** until the script is clean. Do not report the specs as done while any ERROR remains.
- **`⚠ WARN`** — not auto-fixed. Read each one and decide: correct it, or confirm it is intentional. Surface unresolved warnings to the user rather than hiding them.

A file you name explicitly is always validated: a spec too broken to still look like a spec ERRORs — it is never silently skipped. Because detection is anchor-based, a fully localized spec validates cleanly.

## 7.2 — Independent adversarial review (subagent)

The script verifies **form**, not **meaning** — and you cannot objectively grade your own output. Dispatch an **independent reviewer subagent** (via `Task`, fresh context) whose job is to *refute*, not to praise. Give it the spec(s), the PRD path, the relevant DRD paths, and MCP access, and task it to check:

- **Coverage and fidelity** — every `FUNC-xxx` / `BR-xxx` / `ERR-xxx` in scope is covered by at least one spec (**nothing else checks this** — the script sees one file at a time and never reads the PRD); the Business Rules are the PRD's **verbatim** text, not a paraphrase; the User Story matches the scope. **Re-read the PRD one final time with the explicit goal of catching a requirement or attention point that did not surface during drafting.**
- **Acceptance tests hold (§9)** — each scenario's steps actually exercise the ids in its trace tags; the non-passing scenarios genuinely trigger their `ERR-xxx`; no scenario merely documents an implementation detail (that belongs in unit tests).
- **Evidence is real** — re-verify a sample of the `🟢 high` §8 entries against the MCP (`search_openapi` / `validate_route`) or the named DRD Content Contract row. A 🟢 whose evidence does not reproduce is downgraded; a 🟢 justified by an API scenario is invalid by construction.
- **No hallucinated endpoint, no leaked scenario** — every §8 path resolves to a real operation; no scenario id, title, prerequisites or channel gating appears anywhere; Directus appears only in the CMS translation-keys table.
- **Language consistency** — everything human-readable is in the user's language (`SKILL.md` § Language), including section titles and Gherkin keywords; machine tokens (anchors, tags, frontmatter enums, identifiers) are untranslated.

The reviewer returns a **structured findings list** (severity · spec · location · what is wrong · suggested fix). Default to "problem" when uncertain. Address every **Blocking** finding — re-resolve the entry, downgrade the confidence, or move it to a Point to clarify — then re-run 7.1. Do not report done while a Blocking finding stands.

## 7.3 — Confirm the feature flag, then report

1. **Confirm the feature flag** (scheduled from Step 5 §7). For each flag written as `(proposed — to confirm)`, ask the user whether the feature should be feature-flagged and, if so, to confirm or adjust the name. Applying the answer means **rewriting the whole spec file** — there is no partial-edit path (Step 6.8) — so **re-run 7.1** on every file you touched.
2. **Report, per spec** — overall §8 confidence, 🟢/🟡/🔴 counts, Points to clarify by severity, Developer Handoff count. List any accepted warnings and downgraded entries so the user knows what was consciously left open. This summary is produced **here only**.
