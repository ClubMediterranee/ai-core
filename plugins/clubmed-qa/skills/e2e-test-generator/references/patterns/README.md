# Advanced patterns (opt-in)

One pattern per file. Unlike `references/rules/` (hard constraints enforced every run), these
are **optional** techniques the `write` phase reaches for **only when the qualified intent calls
for them**. They do not change the five phases — `write` simply has them available, and
`harden`/`review` judge the result by the same rules. All examples follow Club Med conventions:
import `{ test, expect }` from `./fixtures`, multi-locale regex selectors, no hardcoded dates.

| Pattern | Use when |
|---------|----------|
| [network-mocking](network-mocking.md) | Force an error/edge state, or avoid a forbidden real transaction (mock instead of trigger) |
| [visual-regression](visual-regression.md) | Layout correctness of a page/component is the point of the test |
| [accessibility-checks](accessibility-checks.md) | The intent asks for an a11y gate on the flow |
| [debugging-failing-tests](debugging-failing-tests.md) | A spec fails or flakes and you need to find the real cause (harden phase) |
| [parallel-sharding](parallel-sharding.md) | The whole CI suite is slow enough to split across machines |

The default pipeline targets live user journeys with grounded selectors. Reach for these only
when the intent explicitly needs them.
