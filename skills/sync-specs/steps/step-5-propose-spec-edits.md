# Step 5 — Propose the spec edits 🙋

The second gate. It settles a different question from the first: Step 3 asked whether a mechanism
deserves a document; this one asks whether to **operate on specs someone else already wrote and
reviewed**. Different risk, different reviewer — which is why it is its own gate and not a formality.

**When this gate merges into Step 3.** It exists because the rule ids did not exist yet. When the run
creates **no new identifier** — attaching a carrier to an existing feature, or a register entry alone
— the ids are already there, the edits were formulable at Step 3, and there is nothing left to
confirm. Present them at Step 3 and go straight to Step 6.

## What to present

Read `refs/REF-citation-feature.md` for the syntax, then show, **per spec**, the exact before/after
of each of the four marks:

1. the `transversal_features:` line added to the **frontmatter**;
2. the **binding comment**, with every variation point bound to a real value;
3. the **§5 line**, naming the rule ids carried and its provenance marker;
4. the **§9 scenario** that tests the branch, with its four tag constraints.

Exact text, not a description of it. This is the last moment where a wrong rule id or a mis-bound
axis costs nothing to fix — and the binding values are machine-parsed, so a stray comma inside a
value silently becomes two values.

**The §9 scenario deserves the closest reading of the four.** The other three are transcription; this
one asserts a behaviour. The skill has not read the DRDs, so it only ever transcribes a rule you
already confirmed at gate 1 — but a rule that reads well in the abstract can be wrong for one
vertical. If a scenario looks off, dropping it costs one QG-S8 warning; keeping a false test costs
more.

Re-run `git status --short` on the specs concerned. Step 3 checked them, but Step 4 wrote to the
repo in between and time has passed — a carrier that was clean can have moved.

**Wait for confirmation.**
