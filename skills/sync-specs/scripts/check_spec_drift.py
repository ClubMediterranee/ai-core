#!/usr/bin/env python3
"""Check that what `sync-specs` borrowed from the `spec` skill still matches its source.

`sync_specs.py` **copies** six things from `validate_specs.py` rather than importing them — two
regexes and four parsers — because a skill must run without assuming its sibling is installed. The
copies are free to drift, and drift here is **silent**: nothing raises, the detector simply sees a
different document than the one `spec` validated, and a quality gate becomes quietly wrong.

That is not hypothetical. It has happened twice, both times the same way — an alternation of id
prefixes copied from `spec`, written before transversal features existed:

  - `ID_RE` did not know `RULE-`    → QG-S5 reported every rule as dead;
  - `TRACE_RE` did not know `RULE-` → QG-S8 reported every branch as untested, forever.

Two lists are also duplicated between prose and code — the five gherkin category tags and the six
trace prefixes, written in clear in `refs/REF-citation-feature.md`. Checking them here turns a
documentation drift into a detectable condition.

Run it at **Step 1, before the detector**. Later is useless: a `sections()` that has drifted has
already falsified the whole detection.

Exit codes: 0 = aligned · 1 = at least one divergence · 2 = `spec` not found / nothing to compare.
"""

import argparse
import importlib.util
import re
import sys

sys.dont_write_bytecode = True     # same reason as the sibling scripts: never write into the tree

from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
REF_CITATION = HERE.parent / "refs" / "REF-citation-feature.md"

# The two lists this skill restates in prose. Kept here so the check has something to compare the
# documentation against — the code is the reference, the prose must follow.
CATEGORY_TAGS_DOC_RE = re.compile(r"`(@[a-z]+(?:-[a-z]+)*)`")   # `@edge` carries no hyphen
TRACE_PREFIX_DOC_RE = re.compile(r"`@([A-Z]+)-…`")


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _sections(mod, text):
    """`spec` returns (mapping, order, duplicates); this skill returns the mapping alone."""
    out = mod.sections(text)
    return out[0] if isinstance(out, tuple) else out


def _frontmatter(mod, text):
    out = mod.parse_frontmatter(text)
    return out[0] if isinstance(out, tuple) else out


def check_regexes(vs, ss, out: list) -> None:
    for name in ("ID_RE", "TRACE_RE"):
        a, b = getattr(vs, name, None), getattr(ss, name, None)
        if a is None or b is None:
            out.append(f"✗ {name} — introuvable dans {'validate_specs.py' if a is None else 'sync_specs.py'}")
        elif a.pattern != b.pattern:
            out.append(f"✗ {name} a divergé\n    spec       : {a.pattern}\n    sync-specs : {b.pattern}")


def check_parsers(vs, ss, specs: list, out: list) -> None:
    """Behavioural equality on the real corpus — the only comparison that means anything.

    The bodies may legitimately differ (docstrings, annotations, the `sections` return shape). What
    must not differ is what they *see*: a heading boundary, a masked fence, a frontmatter value, a
    scenario tag. Each of those feeds a gate.
    """
    checks = {
        "mask_fences": lambda m, t: m.mask_fences(t),
        "parse_frontmatter": lambda m, t: _frontmatter(m, t),
        "sections": lambda m, t: {k: v[1] for k, v in _sections(m, t).items()},
        "gherkin_scenarios": lambda m, t: (
            m.gherkin_scenarios(_sections(m, t)[9][1]) if 9 in _sections(m, t) else []),
    }
    for name, fn in checks.items():
        bad = []
        for path in specs:
            text = path.read_text(encoding="utf-8")
            try:
                if fn(vs, text) != fn(ss, text):
                    bad.append(path.name)
            except Exception as exc:                      # noqa: BLE001 — a raise is a divergence too
                bad.append(f"{path.name} ({type(exc).__name__})")
        if bad:
            shown = ", ".join(bad[:3]) + (f" … +{len(bad) - 3}" if len(bad) > 3 else "")
            out.append(f"✗ {name} ne donne pas le même résultat que `spec` sur {len(bad)} spec(s) : {shown}")


def check_documented_lists(vs, ss, out: list) -> None:
    """The prose of REF-citation-feature.md must still name exactly what the code accepts."""
    if not REF_CITATION.is_file():
        out.append(f"✗ {REF_CITATION.name} introuvable — les listes documentées ne peuvent pas être vérifiées")
        return
    text = REF_CITATION.read_text(encoding="utf-8")

    coded = set(getattr(vs, "CATEGORY_TAGS", set()))
    documented = {t for t in CATEGORY_TAGS_DOC_RE.findall(text) if t in coded or t.startswith("@")}
    documented = {t for t in documented if not t.startswith(("@FUNC", "@BR", "@ERR", "@ACC", "@PERM", "@ST", "@RULE"))}
    if coded and documented != coded:
        out.append("✗ tags de catégorie : la ref ne dit pas ce que le code accepte"
                   f"\n    code : {sorted(coded)}\n    ref  : {sorted(documented)}")

    m = re.search(r"@\(\?:([A-Z|]+)\)-", getattr(ss, "TRACE_RE").pattern)
    coded_prefixes = set(m.group(1).split("|")) if m else set()
    doc_prefixes = set(TRACE_PREFIX_DOC_RE.findall(text))
    if coded_prefixes and doc_prefixes != coded_prefixes:
        out.append("✗ préfixes de trace : la ref ne dit pas ce que le code accepte"
                   f"\n    code : {sorted(coded_prefixes)}\n    ref  : {sorted(doc_prefixes)}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Check sync-specs against the spec skill it borrows from.")
    ap.add_argument("specs", help="the specs/ directory — the corpus the parsers are compared on")
    ap.add_argument("--spec-skill-dir", default=str(HERE.parent.parent / "spec"),
                    help="the spec skill's directory (default: ../spec, sibling of this skill)")
    args = ap.parse_args()

    validator = Path(args.spec_skill_dir) / "scripts" / "validate_specs.py"
    if not validator.is_file():
        print(f"⊘ `spec` introuvable en {validator}.\n"
              "  Sans lui, ni ce contrôle ni le diff de non-régression des étapes 3 et 7 ne sont "
              "possibles. Donner --spec-skill-dir.", file=sys.stderr)
        return 2

    root = Path(args.specs)
    specs = [p for p in sorted(root.rglob("*.md")) if p.name != "index.md"]
    if not specs:
        print(f"⊘ aucune spec sous {root}.", file=sys.stderr)
        return 2

    vs = load("_vs", validator)
    ss = load("_ss", HERE / "sync_specs.py")

    findings: list = []
    check_regexes(vs, ss, findings)
    check_parsers(vs, ss, specs, findings)
    check_documented_lists(vs, ss, findings)

    if not findings:
        print(f"✓ aligné sur `spec` — 2 regex, 4 parseurs sur {len(specs)} specs, 2 listes documentées.")
        return 0

    print(f"Dérive avec le skill `spec` — {len(findings)} constat(s) :\n")
    for f in findings:
        print(f"  {f}")
    print("\nLa détection de ce run repose sur ces éléments : un écart ici fausse silencieusement une "
          "quality gate.\nAligner avant de continuer — voir `ADHERENCES-spec.md`.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
