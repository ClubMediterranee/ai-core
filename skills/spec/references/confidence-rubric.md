# Confidence rubric — §8 Data Contract

Every entry in the §8 Data Contract carries a confidence level. This rubric defines the three
buckets and the evidence each requires. The point is simple: **a `high` entry is something a
developer can build on without re-checking; a `low` entry is a lead, not a fact.**

**The bucket is the granularity — never attach a numeric percentage or a progress bar.** A
`90%` implies a precision the sources do not provide; it would be fabricated. Display exactly
`🟢 high` / `🟡 medium` / `🔴 low` plus the evidence string.

---

## Per-entry confidence

### `high` — resolved with evidence
The entry is confirmed against a live source, and the proof is recorded.

- **API entry:** a matching operation returned by `search_openapi` / `suggest_openapi_operations`,
  **and** the exact response field path is visible in the operation's response shape.
  Strongest evidence: a passing `validate_route` (`is_valid: true`) for a concrete request.
- **Editorial entry:** a **DRD Content Contract** row that gives the real label text and format
  (the documentary source of truth for editorial copy). **API scenarios are never evidence** —
  they are the API team's documentation used to *discover* routes and expose neither a field
  path nor a CMS key.
- **Evidence string is mandatory.** Record the resolving MCP call (the operation id, or
  `validate_route → is_valid: true`) or the DRD component + "Content Contract". No evidence →
  not `high`.

### `medium` — found but incomplete
The source is identified but something is unconfirmed.

- Operation matches but the **response field path** is ambiguous, or a **required parameter**
  is unclear.
- The operation is identified but its **request body schema** is not exposed by the MCP.
- A label is grounded by the DRD but its **Directus key name** is still a proposal.
- Record what is missing so the developer knows the residual risk.

### `low` — inferred only
Not found in any connected source; carried over from a guess or derived from the UI.

- Directus translation keys with no DRD grounding.
- API fields whose path could not be located in any operation.

**Note on DRD-grounded editorial keys — attest the label, not the key name.** A DRD Content
Contract confirms the **label text, format, and i18n behaviour** — it never confirms the
**Directus key name** (the DRD does not carry keys). So:
- A key whose **label** is grounded by the DRD but whose **name** is inferred earns at most
  `medium` (🟡), with the evidence string **`label from drd:<Component>, key name inferred`**.
  It is **not** `low` (the label is real), but it is **not** `high` either (the key is a guess).
- It reaches `high` (🟢) only when the **key name itself** is confirmed against Directus (a CMS
  collection that exposes that exact key). The MCP does not serve Directus, so in practice this
  requires someone checking the CMS — expect editorial keys to sit at 🟡.
- A key with no DRD label falls to `low`/Handoff.
- **Every `low` entry goes to the Developer Handoff** and is labeled as a best-guess.

---

## Overall §8 confidence (`data_contract_confidence`)

Compute the data-contract confidence as the **worst-case bucket across the critical entries** —
structural endpoints and keys shared across multiple specs. This is a different rule from the
spec's own `confidence` (a checklist over PRD/DRD source quality, in `steps/step-5-compose-body.md`);
the two are scored independently and must not be conflated:

- **`high`** — all critical entries resolved `high`, no unresolved structural endpoint.
- **`medium`** — ≥1 critical entry at `medium`, or ≥1 non-critical entry unresolved.
- **`low`** — ≥1 critical endpoint/key unresolved, or the API/editorial source itself was
  unavailable for a critical family.

A single non-critical `low` editorial label (e.g. a static message routed to Developer Handoff)
does **not** drag the whole §8 to `low` — only critical entries drive the overall bucket.

This value populates the spec's `data_contract_confidence` frontmatter field. It is scored
**independently** of the spec's own `confidence` (which reflects PRD/DRD source quality).

---

## What counts as "critical"

- Endpoints that structure the feature's data flow (the read that populates the screen,
  the write that mutates the cart/booking).
- Keys or fields shared across sibling specs (listed in the spec's `related_specs`).
- Anything a business rule depends on for state (availability, stock, price, age eligibility).

Static copy, decorative labels, and single-surface messages are **non-critical** — resolve
them when possible, hand them off when not, but do not let them dominate the overall score.
