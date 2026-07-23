---
name: ref-acceptance-criteria
description: >
  Methodological reference for deriving and validating functional acceptance
  criteria: BR (Business Rules), ST (State & Transitions),
  PERM (Permissions), ERR (Error Scenarios). Covers derivation rules,
  formats, and validation criteria.
type: reference
---

# Acceptance Criteria — Methodological Reference

Acceptance criteria are the specific conditions a feature must meet for its development to be considered complete and shippable. Key characteristics: testable and binary (pass/fail), written from the user's or system's perspective, and linked to one or more functional blocks (FUNCs).

---

## AC Types

### Business Rules (BR-XXX)

**Definition:** Core business rules that govern how the organization or domain operates. They reflect legal constraints, internal policies, or invariant business logic — including market/country-specific variants.

**Rules:**
- Testable in binary (passes / fails) — no subjective language
- Cross-cutting: a BR may apply to multiple FUNCs
- Numbered independently from FUNCs

**Format:**
```
BR-001 : [Condition] → [Expected behavior]
Variants : [FR] / [DE] if applicable
```

**Example:**
```
BR-001 : Cart total is < [threshold] € → standard shipping fee applied
Variants : [FR] 25 € / [DE] 30 €

BR-002 : A promo code is applied → the discount cannot exceed the cart total
         (minimum amount charged: 0 €)

BR-003 : An item is out of stock → it cannot be added to the cart
```

---

### States & Transitions (ST-XXX)

**Definition:** The lifecycle of a business object — the states it can be in, and the conditions that trigger transitions between states.

**Derivation:** only when a journey involves an object with an identifiable lifecycle (order, cart, profile…). **Do not force** if no lifecycle exists.

**Rules:**
- Tied to a specific entity (order, cart, user, etc.)
- Define what is possible or impossible depending on the current state

**Format:**
```
ST-001 : [Object]
  States : [state A] | [state B] | [state C]
  Allowed transitions : [A → B] | [B → C]
  Blocked transitions : [C → A] — [reason]
```

**Example:**
```
ST-001 : Order
  States : cart | awaiting_payment | confirmed | in_preparation
         | shipped | delivered | cancelled | returned
  Allowed transitions :
    cart → awaiting_payment (user validates checkout)
    awaiting_payment → confirmed (payment accepted)
    confirmed → in_preparation (warehouse picks up the order)
    in_preparation → shipped (handed to carrier)
    shipped → delivered (delivery confirmed)
    confirmed → cancelled (cancellation before preparation starts)
    delivered → returned (return requested within the legal window)
  Blocked transitions :
    cancelled → confirmed — a cancelled order cannot be reactivated
    shipped → cancelled — cancellation not possible once shipped
```

---

### Permissions (PERM-XXX)

**Definition:** Access restriction on an action based on the actor's role or the current context.

**Derivation:** only when a journey or a BR involves an explicit access restriction. **Do not force** if no restriction exists.

**Rules:**
- Based on roles or attributes
- Cross-cutting: a PERM may apply to multiple FUNCs

**Format:**
```
PERM-001 : [Actor] can [action] if [condition]
         : [Actor] cannot [action] if [opposite condition]
```

**Example:**
```
PERM-001 : Logged-in user can save a delivery address if they have an active account
         : Guest (not logged in) cannot save a delivery address

PERM-002 : User can apply a promo code
           if the code is valid, not expired, and not already used on this account
         : User cannot apply a promo code
           if the code has already been redeemed on this account or is expired
```

---

### Error Scenarios (ERR-XXX)

**Definition:** Expected product behavior in response to a failure — invalid user action, business rule or state constraint violation, or technical failure.

**Rules:**
- Preserve the user's state — an error must never cause the user to lose their work.

**Format:**
```
ERR-001 : [Condition that triggers the failure]
  Expected behavior : [What the product must do]
```

**Example:**
```
ERR-001 : Payment is declined by the bank
  Expected behavior : the cart and delivery information are preserved;
  an explicit error message is displayed; the user can retry
  or choose a different payment method

ERR-002 : An item goes out of stock at confirmation time
          (stock depleted between adding to cart and checkout)
  Expected behavior : the order is not created; the cart is updated
  with the item removed; the user is notified before resuming checkout

ERR-003 : The delivery address is outside the delivery zone
  Expected behavior : carrier selection is blocked;
  a message indicates the covered zones; the cart is preserved
```

---

## Challenge Pass

See `REF-challenge-pass.md` — section "Challenge Pass — Acceptance Criteria".

---

## Validation Criteria

A pool of acceptance criteria is valid if:

1. Every **BR** describes an observable product behavior without naming a technical mechanism or design detail
2. Every **BR** is binary-testable (precise condition, no subjective language)
3. **ST-XXX** are derived only for objects with an identifiable lifecycle in the journeys
4. **PERM-XXX** are derived only for restrictions identified in the journeys or BRs
5. Every **ERR-XXX** referenced in a FUNC is defined in the acceptance criteria
6. Country/language variants are annotated inline on the relevant BR, not created as separate BRs *(this criterion is not covered by a dedicated QG check — it falls under validation by this REF)*
7. No BR or ERR is duplicated per FUNC — a BR/ERR is defined once and referenced by multiple FUNCs when applicable
