# Step 3 — Propose the mechanism 🙋

The first of two gates. This one settles a **product** question: does this shared mechanism deserve a
normative document, and what does it say? The exact edits to the carrier specs are Step 5's business —
they cannot even be written yet, because the rule ids do not exist until Step 4.

**Read `refs/REF-extraction-criteria.md` before drafting anything** — two judgements are yours alone,
and both decide what you write: whether the shared rule is **observable** (would a user notice the
inconsistency using two verticals?) and whether a transversal feature covers **exactly one**
mechanism. Applied after the fact, they only make you throw work away.

## Where the rules come from

The detector outputs **keys, not rules**. Drafting them is yours, and it is the most expensive part of
the run. Two sections of each carrier spec, and they answer different questions:

- **§5 Business Rules — what the rule is.** Read every carrier's, and synthesise the normative
  statement they have in common, service-agnostic.
- **§8 Data Contract — what varies.** The payload shape is where the axes are visible, and it has
  already been validated against the API by `spec`, which makes it the most trustworthy evidence in
  the document.

## Naming the variation points

Variation points are the axes on which the common behaviour legitimately differs between carriers.
They are the feature's signature: every carrier will have to bind each of them.

For each axis, **name the §8 field that carries it** and the value that field takes for each carrier.
An axis you cannot attach to any field is not an axis, it is an impression.

> `schedules[].attendees[]` → childcare binds one attendee per card, transfer binds all of them.

**There is no `n/a`.** A well-framed axis is *total*: every carrier has a value, even when that value
is "imposed", "all" or "none". A carrier with nothing to bind does not reveal a special case — either
the axis is mis-framed, or that carrier does not belong to this feature.

The guard-rail is only worth what the check behind it is worth, because "none" is "not applicable"
under another name. What makes it honest: **"none" is a legitimate value only when the field exists
for that carrier and you can say why it does not constrain anything.** For transfer,
`[].age_in_months` is genuinely present and genuinely unconstraining — that is verifiable, and it is
what separates a bound axis from a ticked box.

`assets/TEMPLATE-transversal-feature.md` shows the shape you are filling. Note that the **values
column is machine-parsed** — split on commas and slashes — so each value is a bare token. A value
written as prose with a comma inside it silently becomes two, and QG-S7 then reports branches nobody
ever declared.

## Which carriers to cite

The detector lists every spec holding the key — often nine for one endpoint. Citing all of them is
noise; citing one is a gap. **One carrier per PRD**, the one that actually exercises the mechanism
(reads *and* writes, rather than merely displaying a value the mechanism produced). The PRD is the
join dimension, so one carrier per PRD is what makes the coverage table say something.

When two specs of the same PRD both exercise it, cite the one whose §5 carries the rule; the other is
a sibling and `spec` already keeps them aligned.

## Degraded cases

Each one names its **consequence**, not just its obstacle.

**A carrier with uncommitted changes.** Run `git status --short` on every spec you intend to edit.
Step 6 edits by surgical `Edit`: if the file moved between read and write the edit fails or lands in
the wrong place, and with nothing committed there is no point to return to. Propose, in this order:

1. **Commit what is in flight** — it is the user's work, not the skill's. The commit separates two
   intents in the history and becomes the safety net.
2. Re-run the skill.
3. Send everything at Step 7.

Do not propose opening a PR on uncommitted changes: a PR compares commits, so it cannot carry them.

**The threshold falling below 3 PRDs.** When the blocked carrier is the only one from its PRD,
dropping it changes the deliverable's **nature**, not its size. Say exactly that:

> `transfer-add-on.md` has uncommitted changes. It is the **only carrier from PRD04**, so the third
> PRD that justifies the extraction. Without it the proposal becomes **a register entry rather than a
> transversal feature**.

**An axis a carrier cannot bind** — reframe the axis, or drop the carrier. Never `n/a`.

## Capture the baseline

Before anything is modified — Step 7 compares against it, and by then the specs have changed:

```bash
python3 <spec-skill-dir>/scripts/validate_specs.py {DOCS_ROOT}/specs > /tmp/specs-before.txt
```

Any writable path works; only the two captures need to match.

## Present

Run the Challenge Pass (`refs/REF-challenge-pass.md`), then present:

1. **Transversal features to create** — one per mechanism, with the evidence keys, the rules, the
   variation points **with their §8 field**, and the carrier specs.
2. **Carriers to attach** to an existing transversal feature or register entry.
3. **Register entries** to create or update. For the editorial revisions, detail only the candidates
   worth acting on; **count** the ones the detector classified "probablement légitime" or "vocabulaire
   d'interface" rather than listing them. When a unification is right, say **which key survives** — a
   label grounded in a DRD Content Contract outranks one still to create in Directus.
4. **Unwritten labels** — the keys the detector excluded from comparison (`TBD`, `À définir`).
   They join no synchro and no feature, so they belong in the register's *Points d'attention*, with
   the consequence named: a real duplicate stays invisible until the label is written.
5. **Which specs will be modified and why** — the list and the reason, *not* the exact text. Naming
   the rules before they have ids produces a sketch, and a sketch is not something to confirm.

Say plainly that **a later regeneration by the `spec` skill will drop the citations** — it rewrites
whole files and does not know about transversal features yet.

**Wait for confirmation.**
