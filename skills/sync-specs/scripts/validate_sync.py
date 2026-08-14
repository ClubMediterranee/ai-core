#!/usr/bin/env python3
"""Validate the documents produced by the `sync-specs` skill — the register and the transversal features.

Deterministic, dependency-free (stdlib only). It checks **form and graph integrity**, never whether
a rule deserved to be extracted, which only a reader can judge.

This exists for the same reason as `validate_prd.py`: the checks below would otherwise be self-graded
by the model that just wrote the documents, and a gate where the author is the judge drifts quietly.

It matters more here than elsewhere, because a transversal feature carries **no acceptance tests** — by design,
its tests live in the carrier specs. Without the gates below, nothing would ever fail when a transversal feature
goes stale: a rule can be wrong indefinitely without any test run noticing.

Gates — scripted:
  QG-S1  Transversal feature frontmatter : id/title/status/owner/date present, status in enum, date ISO   ERROR
  QG-S2  Anchors `sync:auto` / `sync:keys` present and paired                                 ERROR
  QG-S3  Body links repo-relative (never absolute) and resolving on disk                      ERROR
  QG-S4  Carriers table non-empty and matching the specs that actually cite the transversal feature         ERROR
  QG-S5  Rule cited by no spec — a dead rule                                                   ERROR
  QG-S6  Citation not binding every VAR-nn the transversal feature declares                                 ERROR
  QG-S7  VAR value bound by no spec — an unborne branch                                        WARN
  QG-S8  VAR value bound but no §9 scenario tagged with a rule of the transversal feature — untested branch WARN
  QG-S9  Register entry whose "À aligner" is empty — the human work still to do                WARN
  QG-S10 Register key no longer carried by any spec and not marked obsolete                    ERROR
  QG-S11 Transversal feature whose evidence keys are only CMS keys — a transversal feature is for behaviour             ERROR
  QG-S12 Transversal feature with fewer than two rules — noise, the register carries it better              WARN
  QG-S13 A carrier's `prd_source` does not resolve (the PRD is the join dimension)             ERROR
  QG-S14 Every carrier of a transversal feature is `status: draft` — a fragile foundation                  WARN
  QG-S15 Template leftovers: instantiation comment removed (ERROR), no `[placeholder]` (WARN)
  QG-S16 `transversal_features:` declaration and the binding comments disagree                 ERROR
  QG-S17 VAR-nn naming no §8 field — an axis nothing in the data contract carries               WARN

QG-S1 also covers the `TF-nn` id: its format, and its uniqueness across the features directory —
the latter in `main()`, since one file alone cannot see a collision.

Left to the model, documented in `refs/REF-quality-gates.md`: whether the rule is **observable**,
whether "À aligner" says something useful, whether a CMS revision proposal is right, and whether a
transversal feature covers exactly one mechanism.

Exit codes: 0 = clean · 1 = at least one ERROR · 2 = nothing to validate. WARN never fails the run.

Usage:
    python3 validate_sync.py --specs <DOCS_ROOT>/specs \\
                             --features <DOCS_ROOT>/transversal-features \\
                             --register <DOCS_ROOT>/SYNCHRO.md \\
                             --repo-root <path/to/knowledge-base>
"""

import argparse
import re
import sys

sys.dont_write_bytecode = True     # same reason as sync_specs.py: never write into the audited tree

from pathlib import Path  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_specs import (  # noqa: E402  (bundled sibling, same skill)
    BACKTICKED_RE, SYNC_KEYS_BLOCK_RE, TABLE_ROW_RE, _backticked, _first_cell,
    build_index, load_specs, normalise_endpoint, parse_frontmatter, resolve_endpoints,
)

REQUIRED_FM = ["id", "title", "status", "owner", "date"]
STATUS = {"draft", "review", "approved", "done"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TF_ID_RE = re.compile(r"^TF-\d{2,}$")
RULE_RE = re.compile(r"\b(RULE-[A-Z0-9]+-\d+)\b")
VAR_ROW_RE = re.compile(r"(?m)^\s*\|\s*\**\s*(VAR-\d+)\**\s*\|([^|]*)\|")
VAR_CELL_RE = re.compile(r"^\**\s*(VAR-\d+)")
SECTION8_COL_RE = re.compile(r"(?i)§\s*8|\bchamp\b|\bfield\b")
PLACEHOLDER_CELL_RE = re.compile(r"^\s*[`*]*\s*\[[^\]]*\]\s*[`*]*\s*$")
AUTO_BLOCK_RE = re.compile(r"(?s)<!--\s*sync:auto[^>]*-->(.*?)<!--\s*/sync:auto\s*-->")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
ENTRY_RE = re.compile(r"(?m)^##[ \t]+(?!#)(.+?)[ \t]*$")
ALIGN_RE = re.compile(r"(?mi)^\*\*(?:À aligner|A aligner|To align)\s*:?\*\*[ \t]*(.*)$")
OBSOLETE_RE = re.compile(r"(?i)\bobsol[èe]te\b|\bobsolete\b")
PLACEHOLDER_RE = re.compile(r"\[[^\]\n]{2,}\](?!\()")
INSTANTIATION_RE = re.compile(r"<!--\s*(?:instancier|instantiate|TEMPLATE)\b")


class F:
    __slots__ = ("level", "gate", "where", "msg")

    def __init__(self, level, gate, where, msg):
        self.level, self.gate, self.where, self.msg = level, gate, where, msg


def _links(text: str):
    """Body links, excluding those inside a sync:auto block? No — those count too: a generated
    link that does not resolve is exactly the kind of rot this gate exists to catch."""
    return LINK_RE.findall(text)


def check_links(text: str, where: str, repo_root: Path, out: list, gate="QG-S3"):
    for target in _links(text):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        if target.startswith("/") or re.match(r"^[A-Za-z]:[\\/]", target):
            out.append(F("ERROR", gate, where,
                         f"lien absolu `{target}` — les liens doivent être relatifs au repo "
                         "pour rester cliquables sur GitHub"))
            continue
        if repo_root and not (repo_root / target.split("#")[0]).exists():
            out.append(F("ERROR", gate, where, f"lien `{target}` ne résout pas sous le repo"))


def check_leftovers(text: str, where: str, out: list):
    if INSTANTIATION_RE.search(text):
        out.append(F("ERROR", "QG-S15", where, "commentaire d'instanciation du template non retiré"))
    for ph in set(PLACEHOLDER_RE.findall(text)):
        out.append(F("WARN", "QG-S15", where, f"placeholder `{ph}` laissé en place"))


# --------------------------------------------------------------------------- transversal features

def var_section8_fields(text: str) -> dict:
    """VAR-nn -> the §8 field it names, located by the **table header** and not by column position.

    Position would be a trap: in a three-column table written against the older template, the third
    cell is "Qui décide", which a positional read would happily accept as a data-contract field. Here
    such a table has no matching header, every axis comes back empty, and QG-S17 reports it — which
    is the whole point of the gate.
    """
    fields, col = {}, None
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            col = None                      # a blank line or prose ends the table
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not cells:
            continue
        m = VAR_CELL_RE.match(cells[0])
        if not m:
            for i, c in enumerate(cells):   # header row: find the §8 column once per table
                if SECTION8_COL_RE.search(c):
                    col = i
                    break
            continue
        raw = cells[col] if col is not None and col < len(cells) else ""
        fields.setdefault(m.group(1), "" if PLACEHOLDER_CELL_RE.match(raw) else raw.strip("`* "))
    return fields


def parse_contract(path: Path):
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    keys = []
    for block in SYNC_KEYS_BLOCK_RE.findall(text):
        for tok in BACKTICKED_RE.findall(block):
            ep = normalise_endpoint(tok)
            keys.append((f"{ep[0]} {ep[1]}".strip() if ep else tok.strip(), "endpoint" if ep else "cms"))
    vars_ = {}
    for var, cell in VAR_ROW_RE.findall(text):
        vals = [v.strip().strip("`*") for v in re.split(r"[,/]|\bou\b|\bor\b", cell) if v.strip()]
        if vals:
            vars_.setdefault(var, vals)
    var_fields = var_section8_fields(text)
    carriers = []
    for block in AUTO_BLOCK_RE.findall(text):
        for row in TABLE_ROW_RE.findall(block):
            cell = _first_cell(row)
            if not cell:
                continue
            # Only a link or a backticked path is a carrier — this skips the header row, which is
            # plain text and would otherwise be reported as a spec that does not cite the transversal feature.
            m = LINK_RE.search(cell)
            if m:
                carriers.append(m.group(1))
            elif "`" in cell:
                carriers.append(cell.strip().strip("`"))
    return {
        "slug": path.stem, "path": path, "text": text, "fm": fm or {},
        "keys": keys, "vars": vars_, "var_fields": var_fields, "carriers": carriers,
        "rules": sorted(set(RULE_RE.findall(text))),
        "has_auto": bool(AUTO_BLOCK_RE.search(text)),
        "has_keys": bool(SYNC_KEYS_BLOCK_RE.search(text)),
    }


def check_contract(c, specs, repo_root, out):
    where = c["path"].name
    fm = c["fm"]
    missing = [k for k in REQUIRED_FM if not fm.get(k)]
    if missing:
        out.append(F("ERROR", "QG-S1", where, f"frontmatter incomplet : {', '.join(missing)}"))
    if fm.get("id") and not TF_ID_RE.match(str(fm["id"])):
        out.append(F("ERROR", "QG-S1", where,
                     f"`id: {fm['id']}` — attendu `TF-nn`, deux chiffres au moins. Un id de format "
                     "libre ne peut pas être incrémenté sans risque de collision"))
    if fm.get("status") and fm["status"] not in STATUS:
        out.append(F("ERROR", "QG-S1", where,
                     f"`status: {fm['status']}` hors énumération {sorted(STATUS)}"))
    if fm.get("date") and not DATE_RE.match(str(fm["date"])):
        out.append(F("ERROR", "QG-S1", where, f"`date: {fm['date']}` n'est pas au format AAAA-MM-JJ"))

    if not c["has_keys"]:
        out.append(F("ERROR", "QG-S2", where, "ancre `sync:keys` absente — la preuve d'entrée "
                                              "ne peut pas être relue par la machine"))
    if not c["has_auto"]:
        out.append(F("ERROR", "QG-S2", where, "ancre `sync:auto` absente — la table des porteurs "
                                              "ne peut pas être régénérée"))
    check_links(c["text"], where, repo_root, out)
    check_leftovers(c["text"], where, out)

    if c["keys"] and all(t == "cms" for _k, t in c["keys"]):
        out.append(F("ERROR", "QG-S11", where,
                     "la preuve d'entrée ne contient que des clés CMS — un libellé partagé pose une "
                     "question éditoriale, pas un comportement commun ; cette entrée va au registre"))
    if len(c["rules"]) < 2:
        out.append(F("WARN", "QG-S12", where,
                     f"{len(c['rules'])} règle(s) — une fonctionnalité transverse d'une seule règle est "
                     "du bruit, le registre la porte mieux"))

    # An axis nothing in the data contract carries may still be legitimate — a locale, a resort rule —
    # so this is a WARN. It exists to force the check: the §8 payload is where variation is actually
    # visible, and an axis read off the §5 alone is a guess.
    for var in sorted(c["vars"]):
        if not c["var_fields"].get(var):
            out.append(F("WARN", "QG-S17", where,
                         f"`{var}` ne nomme aucun champ du §8 — vérifier que l'axe se lit bien dans le "
                         "contrat de données des porteurs, ou justifier qu'il est d'origine produit"))

    citing = [s for s in specs if any(x["contract"] == c["slug"] for x in s.citations)]
    if not c["carriers"]:
        out.append(F("ERROR", "QG-S4", where, "table des porteurs vide"))
    declared = {Path(x).name for x in c["carriers"]}
    actual = {Path(s.rel).name for s in citing}
    for miss in sorted(actual - declared):
        out.append(F("ERROR", "QG-S4", where, f"`{miss}` cite la fonctionnalité transverse mais n'est pas dans la table "
                                              "des porteurs — la table doit être régénérée"))
    for extra in sorted(declared - actual):
        out.append(F("ERROR", "QG-S4", where, f"`{extra}` est listé porteur mais ne cite pas la fonctionnalité transverse"))

    if citing and all(s.status == "draft" for s in citing):
        out.append(F("WARN", "QG-S14", where,
                     "tous les porteurs sont en `draft` — la fonctionnalité transverse repose sur une base mouvante"))

    cited_rules, bound = set(), {}
    for s in citing:
        cited_rules |= {r for r in c["rules"] if r in s.ids}
        for cit in s.citations:
            if cit["contract"] != c["slug"]:
                continue
            missing_vars = set(c["vars"]) - set(cit["bindings"])
            if missing_vars:
                out.append(F("ERROR", "QG-S6", s.rel,
                             f"cite `{c['slug']}` sans lier {', '.join(sorted(missing_vars))} — "
                             "une citation incomplète ne dit pas quelle branche la spec porte"))
            for var, vals in cit["bindings"].items():
                for v in vals:
                    bound.setdefault((var, v), []).append(s)

    for rule in c["rules"]:
        if rule not in cited_rules:
            out.append(F("ERROR", "QG-S5", where,
                         f"{rule} n'est nommé par aucune spec porteuse — règle morte. Une spec qui "
                         "porte cette règle doit la nommer dans son §5, comme un scénario nomme "
                         "les ids qu'il trace"))
    for var, vals in c["vars"].items():
        for v in vals:
            carriers = bound.get((var, v), [])
            if not carriers:
                out.append(F("WARN", "QG-S7", where, f"{var}={v} n'est lié par aucune spec — "
                                                     "branche non portée"))
            elif not any(s.traced & set(c["rules"]) for s in carriers):
                out.append(F("WARN", "QG-S8", where,
                             f"{var}={v} est lié mais aucun scénario §9 de ses porteurs n'est tagué "
                             f"avec une règle de `{c['slug']}` — branche non testée"))


# --------------------------------------------------------------------------- register

def check_register(path: Path, live_keys: set, repo_root: Path, out: list):
    text = path.read_text(encoding="utf-8")
    where = path.name
    if AUTO_BLOCK_RE.search(text) is None:
        out.append(F("ERROR", "QG-S2", where, "aucun bloc `sync:auto` — le registre ne peut pas "
                                              "être régénéré sans écraser le travail humain"))
    opens = len(re.findall(r"<!--\s*sync:auto", text))
    closes = len(re.findall(r"<!--\s*/sync:auto\s*-->", text))
    if opens != closes:
        out.append(F("ERROR", "QG-S2", where,
                     f"ancres `sync:auto` non appariées ({opens} ouvrantes, {closes} fermantes)"))
    check_links(text, where, repo_root, out)
    check_leftovers(text, where, out)

    heads = list(ENTRY_RE.finditer(text))
    for i, h in enumerate(heads):
        title = h.group(1).strip()
        start = h.end()
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        entry = text[start:end]
        obsolete = bool(OBSOLETE_RE.search(title) or OBSOLETE_RE.search(entry[:400]))

        keys = []
        for block in AUTO_BLOCK_RE.findall(entry):
            for row in TABLE_ROW_RE.findall(block):
                cell = _first_cell(row)
                tok = _backticked(cell) if cell else None
                if tok:
                    ep = normalise_endpoint(tok)
                    keys.append(f"{ep[0]} {ep[1]}".strip() if ep else tok.strip())

        # Only a section that yields keys is a synchro entry. The register also carries the
        # template's own structural sections — "Points d'attention", "Révisions éditoriales" — which
        # have no "À aligner" by design (their human field is named differently). Discriminating on
        # keys rather than on titles keeps this working whatever language the register is written in.
        align = ALIGN_RE.search(entry)
        if keys and not obsolete and (not align or not align.group(1).strip() or
                                      PLACEHOLDER_RE.fullmatch(align.group(1).strip() or "")):
            out.append(F("WARN", "QG-S9", f"{where} › {title}",
                         "« À aligner » est vide — c'est le travail humain qui reste à faire, "
                         "l'entrée ne vaut rien sans lui"))

        gone = [k for k in keys if k not in live_keys]
        if gone and not obsolete:
            out.append(F("ERROR", "QG-S10", f"{where} › {title}",
                         f"{', '.join('`%s`' % g for g in gone)} n'est plus portée par aucune spec "
                         "et l'entrée n'est pas marquée obsolète — une entrée périmée qui se tait "
                         "est indiscernable d'une entrée juste"))


# --------------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description="Validate sync-specs outputs.")
    ap.add_argument("--specs", required=True)
    ap.add_argument("--features", default=None)
    ap.add_argument("--register", default=None)
    ap.add_argument("--repo-root", default=None)
    args = ap.parse_args()

    specs_root = Path(args.specs)
    if not specs_root.is_dir():
        print(f"✗ {specs_root} n'est pas un dossier", file=sys.stderr)
        return 2
    repo_root = Path(args.repo_root) if args.repo_root else None

    out, load_findings = [], []
    specs = load_specs(specs_root, repo_root, load_findings)
    if not specs:
        print(f"✗ aucune spec exploitable sous {specs_root}", file=sys.stderr)
        return 2
    for level, where, msg in load_findings:
        # A spec without a resolvable `prd_source` cannot be attributed to a PRD, and the PRD is the
        # dimension the whole join hangs off — so it is an error here, not a silent exclusion.
        out.append(F(level, "QG-S13", where, msg))

    resolved, _attention = resolve_endpoints(specs, [])
    live_keys = {k for (k, _t) in build_index(specs, resolved)}

    # QG-S16 — the frontmatter declaration and the inline bindings must agree. They are written at
    # different moments and by different hands, so one drifts from the other silently: a spec that
    # declares a feature but never binds it looks compliant in a frontmatter listing while carrying
    # nothing; one that binds without declaring is invisible to anyone grepping the frontmatter.
    for s in specs:
        bound = {x["contract"] for x in s.citations}
        declared = set(s.declared)
        for miss in sorted(bound - declared):
            out.append(F("ERROR", "QG-S16", s.rel,
                         f"lie `{miss}` en commentaire mais ne le déclare pas dans "
                         "`transversal_features:` — la référence est invisible sans lire le corps"))
        for miss in sorted(declared - bound):
            out.append(F("ERROR", "QG-S16", s.rel,
                         f"déclare `{miss}` dans `transversal_features:` sans lier ses points de "
                         "variation — la déclaration ne dit pas quelle branche la spec porte"))

    features_root = Path(args.features) if args.features else None
    if features_root and features_root.is_dir():
        seen_ids: dict = {}
        for path in sorted(features_root.glob("*.md")):
            c = parse_contract(path)
            check_contract(c, specs, repo_root, out)
            # QG-S1, uniqueness — a single file cannot see a collision, so it is checked here. Two
            # features sharing an id make every reference to it ambiguous, and the next increment
            # inherits the ambiguity.
            tf_id = str(c["fm"].get("id", "")).strip()
            if TF_ID_RE.match(tf_id):
                if tf_id in seen_ids:
                    out.append(F("ERROR", "QG-S1", path.name,
                                 f"`id: {tf_id}` est déjà porté par `{seen_ids[tf_id]}` — "
                                 "l'incrément de l'étape 4 doit repartir du plus haut id existant"))
                else:
                    seen_ids[tf_id] = path.name

    register = Path(args.register) if args.register else None
    if register and register.is_file():
        check_register(register, live_keys, repo_root, out)

    if not out:
        print("✓ aucun constat")
        return 0

    order = {"ERROR": 0, "WARN": 1}
    for f in sorted(out, key=lambda x: (order[x.level], x.gate, x.where)):
        mark = "✗ ERROR" if f.level == "ERROR" else "⚠ WARN "
        print(f"{mark} {f.gate:7} {f.where} — {f.msg}")
    errors = sum(1 for f in out if f.level == "ERROR")
    print(f"\n{errors} erreur(s), {len(out) - errors} avertissement(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
