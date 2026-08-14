# Step 6 — Apply the citations

Surgical `Edit`, never a rewrite, and **stop on any uncommitted change** — the confirmation you got
at Step 5 was for a file in the state you read it.

Four marks, four jobs — `refs/REF-citation-feature.md` has the syntax:

1. `transversal_features:` in the **frontmatter** — the declaration, greppable without reading the
   body. Propose adding the key when it is absent: a spec written before the feature existed has no
   reason to carry it, and that is exactly how a carrier goes unrecorded.
2. the **binding comment** — which branch this spec carries. Not binding every variation point fails
   QG-S6; declaring without binding, or binding without declaring, fails QG-S16.
3. the **§5 line** naming the rules carried, with its provenance marker. Without the ids, QG-S5
   reports those rules as dead.
4. the **§9 scenario** tagged with the rule id — what makes the branch tested rather than merely
   carried. Without it, QG-S8 reports every bound branch as untested.

Marks 3 and 4 **add**; they never replace. Removing or rewording a verbatim BR would break the `spec`
skill's own coverage check, and touching an existing scenario would break the non-regression diff.

**Do not touch** `index.md`. `spec`'s `check_manifest` matches every `.md` filename appearing in a
manifest against the folder's contents, so a link to a transversal feature — which lives outside the
folder — raises a warning that the Step 7 diff then treats as blocking. The frontmatter declaration
already answers "who carries what", by `grep`.
