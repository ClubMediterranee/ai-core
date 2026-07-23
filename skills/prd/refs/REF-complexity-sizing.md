---
name: ref-complexity-sizing
description: >
  PRD complexity sizing grid (S/M/L/XL) based on number of FUNCs
  and personas. Calculation rule and evaluation process.
type: reference
---

# PRD Complexity Sizing — Reference

Complexity is evaluated automatically **at the end of the analysis, before drafting** and proposed to the PM for confirmation. It is based on two measurable criteria derived from the analysis.

---

## Sizing Grid

| Complexity | FUNCs | Personas |
|------------|-------|----------|
| **S** | 1–3 | 1–2 |
| **M** | 4–7 | 2–3 |
| **L** | 8–14 | 3–5 |
| **XL** | 15+ | 5+ |

---

## Calculation Rule

Take the **highest band** between FUNCs and Personas.

> Example: 6 FUNCs (band M) + 4 personas (band L) → complexity **L**

---

## Evaluation Process

1. Count the validated FUNCs (final list after FUNC derivation)
2. Count the active personas (PER-XXX defined or imported from the brief)
3. Apply the grid → identify the band for each criterion → retain the highest
4. Propose the result to the PM with justification
5. If the PM disputes: present the criteria → then defer to the PM's final decision

---

## Usage in the PRD

Complexity is recorded in the frontmatter:
```yaml
complexity: M   # S / M / L / XL
```

It sets expectations for downstream work (Tech estimation effort, DRD/QA review depth) but is not a firm commitment.

