# Pattern: Parallel testing & sharding

Opt-in, for scaling a growing suite in CI. Not needed for a single new spec — reach for it when
the whole suite is slow enough that splitting it across CI machines pays off.

Playwright parallelizes across files by default (`fullyParallel: true`). Sharding splits the run
across N machines that each execute a slice:

```bash
# In CI, run each shard on its own machine, then merge the reports
npx playwright test --shard=1/4
npx playwright test --shard=2/4
npx playwright test --shard=3/4
npx playwright test --shard=4/4
```

Notes for this project:

- The repo already defines browser **projects** (chromium/firefox/webkit + a Pixel 5 mobile
  project routed by `@mobile` tags). Sharding is orthogonal — it splits the file set, projects
  split the engines. They compose.
- Prefer `--shard` on the CLI (per CI job) over hardcoding shard counts in
  `playwright.config.ts`, so the split follows the CI matrix.
- Keep tests independent (no shared state) — sharding assumes any file can run on any machine.
- Merge the per-shard blob reports into one HTML report at the end of the CI run.

When to use: the suite's wall-clock time in CI is the bottleneck. For authoring or hardening a
single flow, this pattern does not apply.
