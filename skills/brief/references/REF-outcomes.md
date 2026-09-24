---
name: ref-outcomes
description: >
  Step 1 — Outcomes: what a lagging metric and a damage control indicator must state, the shape
  /prd imports line by line, what is derived and what only the PM decides, and the legitimate
  "not established" states.
type: reference
---

# Outcomes — Step 1

## Definition

An **outcome** is a measurable change on the business or user dashboard — baseline, threshold,
timeframe: what must be different in the world 3 to 12 months after delivery. A list of things to
ship is an output and belongs to nobody's brief.

| Family | Role | Must state |
|---|---|---|
| **Lagging metrics** | What the initiative aims to achieve | A numeric threshold or a direction of change **with its timeframe**; a baseline (T0); the pillar or OKR it serves |
| **Damage control** | What must not degrade meanwhile | The current baseline and the **maximum acceptable degradation** |

## Shape

`/prd` imports both tables **line by line** (as `LGM-XXX` and `DC-XXX`). Sub-headings and column
headers are tokens; cells follow the PM's language.

```
### Lagging Metrics
| Metric | Baseline (T0) | Threshold | Pillar / OKR |
|---|---|---|---|
| Share of guests who book an activity before arrival | 12 % (app analytics, 2026-Q1) | ≥ 20 % at 12 months | OKR 3 — pre-stay engagement |

### Damage Control
| Indicator | Baseline (T0) | Threshold |
|---|---|---|
| Activity no-show rate | 9 % | must not exceed 11 % |
```

## Derive / Ask

**Derive** — the metric candidates, from what the inputs hold (OKR documents, kick-off decks,
dashboards) and from the initiative itself; and the damage-control candidates, by second-order
thinking: *what could optimising this metric degrade, or let rise with no value delivered?* Present
what you read with its source instead of asking from scratch.

**The PM decides** — ask, in one grouped question when several are missing:
- the **threshold**: one metric, one number — what must this achieve at 3 months, at 12 months?
- the **floor**: the indicator, its current value, the level below which it is a regression.
  Having no floor is a conscious decision — ask once, then record theirs;
- the **pillar or OKR**.

A guard-rail *you* propose is a secondary call: name it with the gate, the PM removes it if unwanted.

## Not established — legitimate states

| Situation | Write | And |
|---|---|---|
| Baseline unknown | `TBD` + who can supply it | A tension |
| Floor cannot be set before T0 is known | `to be set once T0 is known` | A tension — this is not "no floor" |
| Floor not decided although T0 is known | `to be set — see T-XX` | A tension |
| The PM chooses no floor | `None identified.` | Name it as their arbitration |
| No pillar or OKR named | `Not established` | A tension — do not block the step |
| No quantitative input at all | Directions of change, `TBD` baselines with an owner | A tension: success criteria nobody can read yet |
| Outcomes fixed by contract | Import them as they are | Still run the Challenge Pass on measurability |

## Check

`REF-challenge-pass.md` — *Outcomes*. The headline outcome is a load-bearing claim: *Challenge the
framing* applies when the evidence does not settle that it is the right thing to move.
