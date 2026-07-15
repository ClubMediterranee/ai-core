---
applies-to: [ground, write, review]
enforcement: judgment
---

# Rule: Grounded selectors only

Every selector used in a spec or util **must trace back to a locator that was actually
observed on the live page** and recorded in the flow-map artifact
(`.e2e-artifacts/flow-map.json`). Never invent a selector from assumption about how the DOM
"probably" looks — ungrounded selectors are the number-one source of fragile, hallucinated
tests.

The grounding phase drives the real site (`agent-browser open` → `snapshot -i`) and captures,
per step, a best-first ranked list of observed locators. The author phase consumes only that
contract. If a needed selector is missing from the flow-map, go back and ground it — do not
guess.

**Review action:** a selector with no counterpart in the flow-map is a blocking finding.
