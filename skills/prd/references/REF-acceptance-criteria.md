---
name: ref-acceptance-criteria
description: >
  Methodological reference for deriving and validating functional acceptance
  criteria: BR (Business Rules), ST (State & Transitions), PERM (Permissions),
  ERR (Error Scenarios), CL/CB (Constraints). Covers derivation rules, BR
  atomicity signals, thematic grouping, the referencing convention used inside
  FUNCs, and validation criteria.
type: reference
---

# Acceptance Criteria — Methodological Reference

Acceptance criteria are the specific conditions a feature must meet for its development to be considered complete and shippable. Key characteristics: testable and binary (pass/fail), written from the user's or system's perspective, and linked to one or more functional blocks (FUNCs).

---

## Derivation

Start from the **ERR candidates** parked in the canonical memory at Step 2, then derive the rules the
journeys and the FUNCs imply.

**Watch for the re-cut signal while writing the BRs.** This is the step where the real structure of
the feature surfaces — not a scan to run, a signal to notice:

- two FUNCs share the same state machine (ST-XXX) and one cannot be demonstrated without the other;
- a FUNC has no `WHEN/THEN` scenario that holds without another FUNC as a prerequisite.

Signal present → propose the merge, or the reclassification into a BR, **before** validating the
step. Signal absent → carry on silently. The same discriminant is stated in
`REF-functional-blocks.md`; this is simply a second moment to observe it.

---

## AC Types

### Business Rules (BR-XXX)

**Definition:** Core business rules that govern how the organization or domain operates. They reflect legal constraints, internal policies, or invariant business logic — including market/country-specific variants.

**Rules:**
- Testable in binary (passes / fails) — no subjective language
- Cross-cutting: a BR may apply to multiple FUNCs
- Numbered independently from FUNCs
- **Opens with a recap** — a short bold label naming *the case handled*, followed by a colon, then
  the rule itself. "Adult selection quota", not "You cannot go over". The recap is what lets a
  reader scan thirty rules to find the one covering their subject. When two rules cover the same
  subject for different actors, the distinction goes into the recap after an em dash.

**Three atomicity signals:**

| Signal | Expected result |
|---|---|
| The body of a BR references another BR ("see BR-XXX", "aligned with BR-XXX") | Rewrite the rule so it stands alone. If an object's state is involved, cite ST-XXX instead |
| One BR holds N mutually exclusive conditions producing N distinct observable behaviours | N BRs |
| A BR re-enumerates an object's states while an ST-XXX is defined for that object | Point to ST-XXX — one source of truth. For instance "the CTA reflects the current state (ST-XXX)" instead of listing each state and its rendering |

The third signal is what keeps ST and BR from drifting apart: a state added to ST-XXX must not have
to be propagated by hand into every rule that mentions it.

**Format** — one row of the §5 *Business Rules* table:

```
| ID | Rule | Applies to |
|----|------|-----------|
| BR-001 | **[Recap — the case handled]:** [condition] → [expected behavior] | FUNC-001 |
```

Country variants go **inline in the `Rule` cell, without brackets**: a bracketed token reads as an
unreplaced placeholder, and a dedicated column would displace `Applies to`, which the validator reads
as the last cell of the row.

**Example:**

```
| ID | Rule | Applies to |
|----|------|-----------|
| BR-001 | **Standard shipping threshold:** cart total is below the free-shipping floor → standard shipping fee applied. Variants : FR 25 € / DE 30 € | FUNC-002 |
| BR-002 | **Discount ceiling:** a promo code is applied → the discount cannot exceed the cart total (minimum amount charged: 0 €) | FUNC-003 |
| BR-003 | **Out-of-stock item:** an item is out of stock → it cannot be added to the cart | FUNC-001 |
```

#### Grouping past ~10 rules

Beyond roughly ten BRs a flat table stops being scannable. Group the rules into thematic
sub-sections **by business domain** — eligibility, pricing, availability, data entry — using `####`
headings under `### Business Rules`.

Two constraints on the grouping:

- **Never group by FUNC.** A BR is cross-cutting by definition; filing it under one FUNC forces
  either duplication or an arbitrary choice.
- **`####`, never `###` or `##`.** `###` is taken by the four AC types, and `##` would break the
  document's section structure.

The count is only a proxy — the real trigger is "several distinct business domains now coexist". A
PRD with twelve homogeneous rules on a single domain gains nothing from being split in two.
Whatever the grouping, **an entry is recognised by its id prefix, never by which table it sits in**.

---

### States & Transitions (ST-XXX)

**Definition:** The lifecycle of a business object — the states it can be in, and the conditions that trigger transitions between states.

**Derivation:** only when a journey involves an object with an identifiable lifecycle (order, cart, profile…). **Do not force** if no lifecycle exists.

**Rules:**
- Tied to a specific entity (order, cart, user, etc.)
- Define what is possible or impossible depending on the current state

**Format** — one row of the §5 *States & Transitions* table. Separate the items of a list with `/`:
a bare `|` inside a cell is read as a column break, and an escaped `\|` survives the validator but
not the reader.

```
| ID | Object | States | Allowed transitions | Blocked transitions |
|----|--------|--------|---------------------|---------------------|
| ST-001 | [Object] | [state A] / [state B] / [state C] | [A → B] / [B → C] | [C → A] — [reason] |
```

**Example:**

```
| ID | Object | States | Allowed transitions | Blocked transitions |
|----|--------|--------|---------------------|---------------------|
| ST-001 | Order | cart / awaiting_payment / confirmed / in_preparation / shipped / delivered / cancelled / returned | cart → awaiting_payment (user validates checkout) / awaiting_payment → confirmed (payment accepted) / confirmed → in_preparation (warehouse picks up the order) / in_preparation → shipped (handed to carrier) / shipped → delivered (delivery confirmed) / confirmed → cancelled (cancellation before preparation starts) / delivered → returned (return requested within the legal window) | cancelled → confirmed — a cancelled order cannot be reactivated / shipped → cancelled — cancellation not possible once shipped |
```

A row this wide is the honest shape of a lifecycle: the table is scanned by `ID` and `Object`, and
read in full only for the object under discussion.

---

### Permissions (PERM-XXX)

**Definition:** Access restriction on an action based on the actor's role or the current context.

**Derivation:** only when a journey or a BR involves an explicit access restriction. **Do not force** if no restriction exists.

**Rules:**
- Based on roles or attributes
- Cross-cutting: a PERM may apply to multiple FUNCs

**Format** — one row of the §5 *Permissions* table:

```
| ID | Actor | Action | Allowed condition | Blocked condition |
|----|-------|--------|-------------------|-------------------|
| PERM-001 | [Actor] | [Action] | [condition allowing the action] | [condition blocking it] |
```

**Example:**

```
| ID | Actor | Action | Allowed condition | Blocked condition |
|----|-------|--------|-------------------|-------------------|
| PERM-001 | Logged-in user | Save a delivery address | the account is active | the visitor is a guest, not logged in |
| PERM-002 | User | Apply a promo code | the code is valid, not expired, and not already used on this account | the code has already been redeemed on this account, or is expired |
```

---

### Error Scenarios (ERR-XXX)

**Definition:** Expected product behavior in response to a failure — invalid user action, business rule or state constraint violation, or technical failure.

**Rules:**
- Preserve the user's state — an error must never cause the user to lose their work.

**Format** — one row of the §5 *Error Scenarios* table:

```
| ID | Failure mode | Expected behavior |
|----|--------------|-------------------|
| ERR-001 | [Condition that triggers the failure] | [What the product must do] |
```

**Example:**

```
| ID | Failure mode | Expected behavior |
|----|--------------|-------------------|
| ERR-001 | Payment is declined by the bank | the cart and delivery information are preserved; an explicit error message is displayed; the user can retry or choose a different payment method |
| ERR-002 | An item goes out of stock at confirmation time (stock depleted between adding to cart and checkout) | the order is not created; the cart is updated with the item removed; the user is notified before resuming checkout |
| ERR-003 | The delivery address is outside the delivery zone | carrier selection is blocked; a message indicates the covered zones; the cart is preserved |
```

---

### Constraints (CB-XXX, CL-XXX)

**Definition:** Conditions this PRD **inherits** rather than defines. `CB` for business constraints
— a dependency on another PRD, on an existing platform behaviour, on an entry point owned
elsewhere. `CL` for legal and compliance constraints — what a locale or a regulation imposes.

They differ from a BR in direction: a BR is a rule this PRD *decides*, a constraint is a boundary
this PRD *accepts*. They live in the PRD's optional Constraints section, as bullets grouped under
`### Business` and `### Legal / Compliance`, and a FUNC or a BR may reference them like any other
id.

**Derivation:** only when the constraint actually shapes a FUNC or a BR of this PRD. A generic
disclaimer that constrains nothing is noise — the same test as an out-of-scope item: it has to be
*ambiguously in scope* to be worth writing down.

---

## Referencing acceptance criteria from a FUNC

A FUNC lists its acceptance criteria **with their description**, not with bare identifiers:

```
**Acceptance criteria:**

- **BR-010** — **Validation blocking:** at click on the validation CTA, navigation to the Payment
  step is blocked in two cases: […]
- **ST-001** — Form field — states: empty / in_progress / valid / in_error
- **PERM-008** — Logged-in user : Edit a registered companion's information
- **ERR-001** — Field validation error (invalid email format, invalid phone, inconsistent date)
```

**Why.** A FUNC is read to find out what it requires. With bare ids, that means a round trip to the
Acceptance Criteria section for each one — on a FUNC citing ten, nobody does it, and the rules stop
being read.

**The invariant.** Every `- **ID** — text` bullet is **textually identical** to what the definition
of `ID` produces in the Acceptance Criteria section. **That section is the source of truth: where
the two differ, the bullet is wrong.** This duplication is deliberate and it has a price — any
change to a rule must be propagated into every FUNC that cites it. The `spec` skill downstream
copies business rules verbatim and compares the texts, so two divergent versions of one rule make
the PRD and its specs impossible to reconcile. `scripts/validate_prd.py` enforces the invariant.

**Linearisation, per type.** The tables do not all have the same shape, so the expected description
is:

| Type | Source | Expected description |
|---|---|---|
| `BR` | `\| ID \| Rule \| Applies to \|` | the `Rule` column, verbatim |
| `ERR` | `\| ID \| Failure mode \| Expected behavior \|` | the `Failure mode` column |
| `PERM` | `\| ID \| Actor \| Action \| … \|` | `Actor` + ` : ` + `Action` |
| `ST` | `\| ID \| Object \| States \| … \|` | `Object` + ` — states: ` + `States`, state separator normalised to `/` |
| `CB` / `CL` | bullet in the Constraints section | the bullet text |

For `ST` and `PERM` the description is a **deliberate reduction**: those tables carry four or five
columns that do not linearise readably. The Acceptance Criteria section remains the complete
definition — the bullet identifies the rule, it does not replace it. For `BR` and `ERR` the text is
verbatim and must stay so.

---

## Challenge Pass

See `REF-challenge-pass.md` — section "Challenge Pass — Acceptance Criteria".

---

## Validation Criteria

A pool of acceptance criteria is valid if:

1. Every **BR** describes an observable product behavior without naming a technical mechanism or design detail
2. Every **BR** is binary-testable (precise condition, no subjective language)
3. Every **BR** opens with a recap naming the case handled, and **stands alone** — no BR references another BR in its body
4. No **BR** re-enumerates the states of an object for which an **ST-XXX** exists
5. **ST-XXX** are derived only for objects with an identifiable lifecycle in the journeys
6. **PERM-XXX** are derived only for restrictions identified in the journeys or BRs
7. Every **ERR-XXX** referenced in a FUNC is defined in the acceptance criteria
8. Every criterion is defined **once**, in the Acceptance Criteria section, and referenced from the FUNCs that need it. The FUNC bullet repeats the description for readability — it is a copy of the definition, never a second definition, and the Acceptance Criteria section wins on any divergence
9. Country/language variants are annotated inline in the BR's `Rule` cell, without brackets, and never created as separate BRs *(this criterion is not covered by a dedicated QG check — it falls under validation by this REF)*
10. Beyond ~10 BRs, the rules are grouped into `####` thematic sub-sections by business domain, never by FUNC
