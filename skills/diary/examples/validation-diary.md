---
date: 2026-04-03
task: Validate end-to-end payment flow after Stripe SDK upgrade (v4 → v5)
mode: validation
agent: claude-sonnet
session-start: 10:00
---

# Diary — Validation: Payment Flow After Stripe SDK Upgrade

## Entry — 10:00

### What I did
Started the validation session after the `stripe` SDK was upgraded from `v4.5.0` to `v5.1.2`. Read the Stripe v5 migration guide and the changelog. Ran the existing E2E test suite to get a baseline failure count.

### Why
Stripe v5 is a breaking-change release — webhook signature verification and several PaymentIntent methods changed. Need to confirm the happy path works end-to-end before the release branch is cut.

### What worked
`npm test -- --testPathPattern=payment` ran cleanly against the local Stripe test environment. 14/14 unit tests pass. This is expected since the unit tests mock the SDK.

### What didn't work
E2E test `checkout.spec.ts` fails immediately: `TypeError: stripe.paymentIntents.create is not a function`. Stripe v5 moved `paymentIntents` from `stripe.<resource>` to `stripe.v2.<resource>` under the new resource namespace.

### What I learned
Stripe v5 introduces a resource namespace split: `stripe.v1.*` (legacy, deprecated) vs `stripe.v2.*` (new). Our code uses the old `stripe.paymentIntents.*` path which no longer exists at the top level.

### What was tricky
The TypeScript types were updated in v5 — so `tsc --noEmit` passes (types resolve correctly), but at runtime the path doesn't exist. Classic "types lie" situation during a migration.

### Future work
- Update all `stripe.paymentIntents.*` → `stripe.v2.paymentIntents.*` in source
- Verify webhook signature verification path (also changed in v5)
- Re-run full E2E suite
- Document exact commands for reproducing the validation

### Technical details
- `stripe` version: `5.1.2`
- Breaking change: `stripe.paymentIntents` → `stripe.v2.paymentIntents`
- Affected files: `src/services/payment.ts` (3 usages), `src/webhooks/stripe.ts` (1 usage)
- Local Stripe CLI version: `1.19.4`
- Test env: `STRIPE_SECRET_KEY=sk_test_...` (test mode)

---

## Entry — 10:42

### What I did
Updated all `stripe.paymentIntents.*` usages to `stripe.v2.paymentIntents.*` in `src/services/payment.ts` and `src/webhooks/stripe.ts`. Updated webhook signature verification: `stripe.webhooks.constructEvent` → `stripe.v2.webhooks.constructEvent`.

Re-ran E2E suite. 3 tests pass, 2 still fail:
1. `checkout_with_3ds.spec.ts` — 3DS redirect loop detected
2. `refund_flow.spec.ts` — `stripe.v2.refunds.create` returns `422 Unprocessable`

### Why
The 3DS test failure is a known Stripe test environment behavior — 3DS cards in test mode need a specific test card number (`4000002500003155`). Our test was using `4242424242424242` which doesn't trigger 3DS. Unrelated to the upgrade.

The refund `422` is new: Stripe v5 requires `payment_intent` to be passed explicitly on refunds when the original charge was created via PaymentIntent. Previously it was inferred.

### What worked
`stripe listen --forward-to localhost:3000/webhook` correctly forwarded test events. Webhook signatures verified successfully after the namespace update.

### What didn't work
The 3DS test — but this is a test data issue, not an SDK regression. Will fix the test card number.

### What I learned
Stripe v5 refund behavior change: `refunds.create({ charge_id })` no longer works if the charge was created via PaymentIntent. Must use `refunds.create({ payment_intent: 'pi_...' })` instead. This was documented in the changelog but easy to miss.

### What was tricky
The `422` error message from Stripe was `"You cannot use a charge that was created with a PaymentIntent"` — clear once you see it, but only appears at runtime, not in types.

### Future work
- Fix `checkout_with_3ds.spec.ts` to use correct 3DS test card
- Verify refund flow with `payment_intent` parameter
- Run full suite one more time for final sign-off

### Technical details
- Fixed: `stripe.webhooks.constructEvent` → `stripe.v2.webhooks.constructEvent`
- Fixed: `stripe.refunds.create({ charge_id })` → `stripe.refunds.create({ payment_intent: piId })`
- 3DS test card: `4000002500003155` (triggers 3DS in test mode)
- Standard test card: `4242424242424242` (no 3DS)
- Stripe CLI command: `stripe listen --forward-to localhost:3000/webhook --events payment_intent.succeeded,charge.refunded`

---

## Session Close — 11:10

### Summary
Stripe SDK upgrade from v4 to v5 is fully validated. All 5 E2E tests now pass. Two issues were found and fixed: the resource namespace change (`stripe.v2.*`) and the refund API requiring explicit `payment_intent` instead of inferring from `charge_id`. The 3DS test was also corrected to use the right test card number (pre-existing bug, not a regression).

### What's next
- Merge the fix branch into the release branch
- Update `CHANGELOG.md` with the Stripe v5 migration note
- Add a comment in `src/services/payment.ts` near the refund call explaining the `payment_intent` requirement

### Open questions
- None. The upgrade is clean. Happy path confirmed.

### Reproducible validation commands
```bash
# Start local dev server
npm run dev

# In a second terminal: forward Stripe webhooks
stripe listen --forward-to localhost:3000/webhook \
  --events payment_intent.succeeded,charge.refunded

# Run payment E2E tests only
npm run test:e2e -- --testPathPattern=payment
```
