#!/usr/bin/env python3
"""Detect synchronisation points between specs produced by the `spec` skill.

Deterministic, dependency-free (stdlib only), **offline**. It answers one question: **which specs
of different PRDs share a key?** — never whether that sharing implies a shared rule, which is a
judgement only a reader can make.

This exists because the alternative is comparing 27 PRDs pairwise on prose. A PRD carries no
machine-comparable key; a spec does — its §8 names endpoints and CMS keys under stable anchors.
Joining on those keys is an index lookup, not an analysis, and it cannot forget a pair.

What it reads, per spec:
  frontmatter   `prd_source` (the join dimension), `related_specs`, `status`
  §8 endpoints  first table cell shaped as an HTTP path — the `dc:index` table and the detail blocks
  §8 CMS keys   first table cell shaped as a dotted editorial key
  §9 scenarios  trace tags, used to tell a bound rule from a *tested* rule
  citations     `<!-- feature:<slug> VAR-01=<value> … -->`

What it emits:
  synchro       a key carried by specs of exactly 2 distinct PRDs
  factorisation a *behaviour* key carried by specs of ≥3 distinct PRDs — a transversal feature candidate
  attention     an elided endpoint that resolves to several full paths, or to none

Two deliberate limits, both about not faking precision:

  * **A key shared inside a single PRD is ignored.** The `spec` skill already handles it with its
    `related_specs` + owner-spec rule; re-reporting it would be noise.
  * **CMS keys never become a factorisation candidate.** Two specs showing the same label raise an
    editorial-consistency or duplication question, not a shared behaviour. They stay in the register.

State-machine ids (`ST-xxx`) are **not** join keys: they are numbered per spec, so `ST-001` in two
specs denotes two different machines. Shared behaviour is detected through endpoints; a shared state
machine is evidence a human adds when confirming a transversal feature.

Exit codes: 0 = clean · 1 = at least one ERROR · 2 = nothing to analyse (bad or empty path — not a
success). WARN never fails the run.

Usage:
    python3 sync_specs.py <DOCS_ROOT>/specs                    # every PRD folder
    python3 sync_specs.py <DOCS_ROOT>/specs --features <DOCS_ROOT>/transversal-features
    python3 sync_specs.py <DOCS_ROOT>/specs --repo-root <path/to/knowledge-base>
    python3 sync_specs.py <DOCS_ROOT>/specs --json            # machine-readable
"""

import argparse
import json
import re
import sys

# Never leave a `__pycache__` behind: this script is often run against a read-only checkout, and a
# skill that writes into its own directory while auditing someone else's is a bad neighbour.
sys.dont_write_bytecode = True

from pathlib import Path  # noqa: E402

# --------------------------------------------------------------------------- shared with validate_specs.py
# Copied, not imported: each script must stay runnable on its own from the skill directory.

ID_RE = re.compile(r"\b(?:FUNC|BR|ERR|ACC|PERM|ST)-(?:G\d+|\d+[a-z]?)", re.I)
TRACE_RE = re.compile(r"@(?:FUNC|BR|ERR|ACC|PERM|ST)-(?:G\d+|\d+[a-z]?)", re.I)
# Transversal feature rule ids live in a namespace of their own (`RULE-RSV-01`) so a spec naming one is telling
# us it carries that rule — the equivalent, at spec level, of a §9 trace tag.
RULE_ID_RE = re.compile(r"\bRULE-[A-Z0-9]+-\d+\b", re.I)

SCENARIO_WORDS = [
    "scenario outline", "scenario template", "abstract scenario", "scenario",
    "example", "scénario", "plan du scénario", "plan du scenario", "exemple",
    "szenario", "szenariogrundriss", "beispiel",
    "escenario", "esquema del escenario", "ejemplo",
    "cenário", "cenario", "esquema do cenário", "exemplo",
    "voorbeeld",
]
_SCENARIO = re.compile(
    r"^\s*(?:" + "|".join(sorted((re.escape(w) for w in SCENARIO_WORDS), key=len, reverse=True)) + r")\s*:\s*(.*)$",
    re.I,
)
_TAG_LINE = re.compile(r"^\s*@\S")
_HEADING = re.compile(r"(?m)^####[ \t]*(\d+)\.[ \t]*(.*?)[ \t]*$")
_FENCE = re.compile(r"(?m)^\s*(`{3,}|~{3,})")


def mask_fences(text: str) -> str:
    """Blank out fenced-code content, preserving length and newlines."""
    out = list(text)
    in_fence, marker = False, ""
    for m in re.finditer(r"(?m)^.*$", text):
        line = m.group(0)
        f = _FENCE.match(line)
        if not in_fence and f:
            in_fence, marker = True, f.group(1)[0]
            continue
        if in_fence:
            if f and f.group(1)[0] == marker:
                in_fence = False
                continue
            for i in range(m.start(), m.end()):
                if out[i] != "\n":
                    out[i] = " "
    return "".join(out)


def parse_frontmatter(text: str):
    """Minimal YAML frontmatter parser: `key: value`, `[a, b]` inline lists, `-` block lists."""
    text = text.lstrip("﻿ \t\r\n")
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end == -1:
        return None, text
    fm_raw, body = text[3:end].strip("\n"), text[end + 4:]
    fm, cur = {}, None
    for line in fm_raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if cur is not None and re.match(r"\s*-\s+", line) and not re.match(r"\s*[A-Za-z0-9_]+:", line):
            fm[cur].append(line.strip()[1:].strip().strip("'\""))
            continue
        m = re.match(r"([A-Za-z0-9_]+):\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val and not val.startswith(("'", '"')):
            val = re.sub(r"\s{2,}#.*$", "", val).strip()
        if val == "":
            fm[key], cur = [], key
        elif val.startswith("[") and val.endswith("]"):
            fm[key] = [x.strip().strip("'\"") for x in val[1:-1].split(",") if x.strip()]
            cur = None
        else:
            fm[key], cur = val.strip("'\""), None
    return fm, body


def sections(body: str):
    """Return {section_number: (title, text)} — headings located on a fence-masked copy."""
    masked = mask_fences(body)
    heads = list(_HEADING.finditer(masked))
    out = {}
    for i, h in enumerate(heads):
        num = int(h.group(1))
        start, end = h.end(), heads[i + 1].start() if i + 1 < len(heads) else len(body)
        if num in out:
            out[num] = (out[num][0], out[num][1] + "\n" + body[start:end])
        else:
            out[num] = (h.group(2).strip(), body[start:end])
    return out


def gherkin_scenarios(section_text: str):
    """Parse the ```gherkin fences into [{'label', 'tags'}] — fence content only."""
    scenarios = []
    for block in re.findall(
        r"(?ms)^\s*(?:`{3,}|~{3,})gherkin[ \t]*\n(.*?)^\s*(?:`{3,}|~{3,})", section_text
    ):
        pending = []
        for raw in block.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if _TAG_LINE.match(line):
                pending.extend(t for t in line.split() if t.startswith("@"))
                continue
            m = _SCENARIO.match(line)
            if m:
                scenarios.append({"label": m.group(1).strip(), "tags": pending})
                pending = []
                continue
            pending = []
    return scenarios


# --------------------------------------------------------------------------- key extraction

METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS")
ELISION = ("…", "...")
# An editorial key is dotted, lowercase, no slash — `childcare.card.tag.addons`.
CMS_KEY_RE = re.compile(r"^[a-z0-9_]+(?:\.[a-z0-9_-]+){1,}$")
CITATION_RE = re.compile(r"<!--\s*feature:([A-Za-z0-9._-]+)((?:\s+VAR-\d+=[^\s>]+)*)\s*-->")
VAR_BINDING_RE = re.compile(r"(VAR-\d+)=([^\s>]+)")
TABLE_ROW_RE = re.compile(r"(?m)^\s*\|(.+)$")
SUBHEAD_BACKTICK_RE = re.compile(r"(?m)^#{5,6}[ \t]+`([^`]+)`")


def _first_cell(row: str):
    """First cell of a markdown table row, or None for a separator/header-less row."""
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    if not cells:
        return None
    head = cells[0]
    if not head or set(head) <= set("-: "):
        return None
    return head


def _backticked(cell: str):
    m = re.search(r"`([^`]+)`", cell)
    return m.group(1).strip() if m else None


def normalise_endpoint(raw: str):
    """(method, path, is_elided) — or None when `raw` is not an endpoint.

    The §8 template allows both the full path and an elided one (`POST …/cart/services`), and specs
    use both. Normalising to a comparable shape is what makes the two forms joinable at all.
    """
    s = raw.strip()
    method = ""
    parts = s.split(None, 1)
    if parts and parts[0].upper().rstrip(":") in METHODS:
        method = parts[0].upper().rstrip(":")
        s = parts[1].strip() if len(parts) > 1 else ""
    s = re.sub(r"^https?://[^/]+", "", s).strip()
    elided = False
    for e in ELISION:
        if s.startswith(e):
            elided, s = True, s[len(e):]
            break
    if not s.startswith("/"):
        if method and s:
            s = "/" + s.lstrip("/")
        else:
            return None
    s = re.sub(r"\{[^}]*\}", "{}", s)          # {customer_id} and {id} are the same slot
    s = re.sub(r"/{2,}", "/", s).rstrip("/")
    if not s or " " in s:
        return None
    return method, s, elided


def normalise_label(raw: str) -> str:
    """Comparable form of an editorial label — for *detection*, never for rewriting.

    Case and surrounding punctuation are dropped so `"Add-ons"` and `Add-Ons` meet; a human then
    decides whether the collision is a duplication or two surfaces that happen to share a word.
    """
    s = raw.replace("\\", "").strip().strip("`").strip()
    s = s.strip('"').strip("'").strip()
    s = re.sub(r"\s+", " ", s)
    return s.casefold().strip(" .:")


def extract_keys(spec_text: str):
    """(endpoints, cms) of §8 — endpoints as (parsed, raw), CMS as (key, label, source) triples.

    Deliberately not keyed on the sub-section labels: those are translated into the spec's language
    (`📝 CMS Keys` / `📝 Clés CMS`), while the values keep their shape in every language.

    The CMS table carries the label in column 2 and its attestation in column 3. Reading all three
    is what lets the detector see the *other* editorial defect — two keys for one label — which a
    key-only join is blind to by construction.
    """
    secs = sections(spec_text)
    if 8 not in secs:
        return [], []
    body = mask_fences(secs[8][1])
    endpoints, cms = [], []

    for row in TABLE_ROW_RE.findall(body):
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if not cells:
            continue
        tok = _backticked(cells[0])
        if not tok:
            continue
        ep = normalise_endpoint(tok)
        if ep:
            endpoints.append((ep, tok))
        elif CMS_KEY_RE.match(tok):
            label = (cells[1].replace("\\", "").strip().strip("`").strip('"').strip()
                     if len(cells) > 1 else "")
            source = cells[2].strip() if len(cells) > 2 else ""
            cms.append((tok, label, source))

    for tok in SUBHEAD_BACKTICK_RE.findall(body):
        ep = normalise_endpoint(tok)
        if ep:
            endpoints.append((ep, tok))

    return endpoints, cms


def extract_citations(spec_text: str):
    """[{'contract', 'bindings': {VAR-nn: [values]}}] from the `<!-- feature:… -->` comments."""
    out = []
    for slug, binds in CITATION_RE.findall(spec_text):
        bindings = {}
        for var, val in VAR_BINDING_RE.findall(binds):
            bindings[var] = [v for v in val.split(",") if v]
        out.append({"contract": slug, "bindings": bindings})
    return out


def traced_ids(spec_text: str):
    """Rule ids that at least one §9 scenario is tagged with — a *tested* rule, not merely cited.

    `TRACE_RE` is copied from `validate_specs.py`, whose alternation predates transversal features
    and therefore does not know `RULE-`. Matching on it alone would make QG-S8 unsatisfiable: the
    gate looks for a rule tag that nothing ever collects, so every carried branch reads as untested
    however many scenarios exercise it.
    """
    secs = sections(spec_text)
    if 9 not in secs:
        return set()
    ids = set()
    for sc in gherkin_scenarios(secs[9][1]):
        for t in sc["tags"]:
            bare = t.lstrip("@")
            if TRACE_RE.fullmatch(t) or RULE_ID_RE.fullmatch(bare):
                ids.add(bare.upper())
    return ids


# --------------------------------------------------------------------------- model

class Spec:
    __slots__ = ("path", "rel", "prd", "status", "endpoints", "cms", "citations", "traced", "ids",
                 "declared")

    def __init__(self, path, rel, prd, status, endpoints, cms, citations, traced, ids, declared):
        self.path, self.rel, self.prd, self.status = path, rel, prd, status
        self.endpoints, self.cms = endpoints, cms
        self.citations, self.traced, self.ids = citations, traced, ids
        # `transversal_features:` in the frontmatter — what the spec *declares* it carries, as
        # opposed to the inline comments, which bind the variation points. Two different jobs:
        # the declaration is greppable and visible without reading the body; the binding says which
        # branch. Keeping both lets `validate_sync.py` catch one drifting from the other.
        self.declared = declared


def repo_relative(path: Path, repo_root: Path | None) -> str:
    """Link target relative to the knowledge-base repo root — these documents are read on GitHub."""
    if repo_root:
        try:
            return str(path.resolve().relative_to(repo_root.resolve()))
        except ValueError:
            pass
    return path.name


def load_specs(specs_root: Path, repo_root: Path | None, findings: list):
    specs = []
    for path in sorted(specs_root.rglob("*.md")):
        if path.name == "index.md":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as e:
            findings.append(("ERROR", path.name, f"illisible : {e}"))
            continue
        fm, body = parse_frontmatter(text)
        if not fm:
            continue
        prd_source = fm.get("prd_source") or ""
        # The PRD is the join dimension: without it a spec cannot be attributed, so it is excluded
        # rather than silently counted under an empty key.
        prd = Path(str(prd_source)).stem if prd_source else ""
        if not prd:
            findings.append(("ERROR", path.name, "`prd_source` absent — spec exclue de la jointure"))
            continue
        endpoints, cms = extract_keys(text)
        specs.append(Spec(
            path=path,
            rel=repo_relative(path, repo_root),
            prd=prd,
            status=str(fm.get("status") or ""),
            endpoints=endpoints,
            cms=cms,
            citations=extract_citations(text),
            traced=traced_ids(text),
            ids={i.upper() for i in ID_RE.findall(text)} | {i.upper() for i in RULE_ID_RE.findall(text)},
            declared=[Path(str(x)).stem for x in (fm.get("transversal_features") or [])],
        ))
    return specs


def resolve_endpoints(specs, findings):
    """Canonical key per endpoint occurrence, plus the attention points resolution could not settle.

    An elided path is resolved against the full paths seen elsewhere. When it matches several, the
    script refuses to pick — guessing here would silently join two unrelated specs, which is worse
    than reporting the ambiguity and letting the MCP step settle it.
    """
    full = {}
    for s in specs:
        for (method, path, elided), _raw in s.endpoints:
            if not elided:
                full.setdefault((method, path), set()).add(s.prd)

    attention, resolved = [], {}
    for s in specs:
        for (method, path, elided), raw in s.endpoints:
            if not elided:
                resolved[(s.rel, raw)] = f"{method} {path}".strip()
                continue
            cands = [
                (m, p) for (m, p) in full
                if p.endswith(path) and (not method or not m or m == method)
            ]
            if len(cands) == 1:
                m, p = cands[0]
                resolved[(s.rel, raw)] = f"{m} {p}".strip()
            elif len(cands) > 1:
                attention.append({
                    "severity": "Blocking",
                    "spec": s.rel,
                    "key": raw,
                    "point": f"le suffixe élidé `{raw}` correspond à {len(cands)} chemins complets",
                    "impact": "jointure impossible sans arbitrer — la clé est exclue du rapport",
                    "resolution": "résoudre via le MCP `clubmed_api` (`search_openapi` / "
                                  "`validate_route`) puis écrire la forme canonique dans la spec",
                })
                # Left unresolved on purpose: excluded from the join rather than joined at random.
            else:
                # No full form anywhere — the suffix becomes its own key so two specs that both
                # write the elided form still meet. This is the childcare ↔ activities case.
                resolved[(s.rel, raw)] = f"{method} …{path}".strip()
                attention.append({
                    "severity": "Medium",
                    "spec": s.rel,
                    "key": raw,
                    "point": f"le suffixe élidé `{raw}` ne correspond à aucun chemin complet connu",
                    "impact": "jointure faite sur le suffixe seul — la forme canonique reste inconnue",
                    "resolution": "résoudre via le MCP `clubmed_api` et écrire la forme complète "
                                  "dans la spec propriétaire",
                })
    return resolved, attention


def build_index(specs, resolved):
    """key -> {'type', 'carriers': [(prd, rel)]} — the inverted index the whole report hangs off."""
    index = {}
    for s in specs:
        seen = set()
        for _ep, raw in s.endpoints:
            key = resolved.get((s.rel, raw))
            if key and (key, "endpoint") not in seen:
                seen.add((key, "endpoint"))
                index.setdefault((key, "endpoint"), []).append((s.prd, s.rel))
        for key, _label, _src in s.cms:
            if (key, "cms") not in seen:
                seen.add((key, "cms"))
                index.setdefault((key, "cms"), []).append((s.prd, s.rel))
    return index


# --------------------------------------------------------------------------- editorial axis

GENERIC_THRESHOLD = 3          # a label spread over this many keys is interface vocabulary
# A label that was never written. Not a duplication finding — a hole, and it must not be counted
# as evidence that two keys say the same thing: they say nothing yet.
PLACEHOLDER_LABEL_RE = re.compile(
    r"^(?:tbd\b|to ?be ?defined|à définir|a definir|todo\b|xxx+$|\[.*\]$|…$|\.\.\.$)", re.I
)


def classify_source(raw: str) -> str:
    """Attestation class of a label: grounded in a DRD, still to create in Directus, or other.

    The §8 template writes `drd:<Component>` or `directus (to add)`, but the cell is prose and the
    wording drifts. Only the class is comparable — and only the class carries a decision: a
    DRD-attested label wins over a proposal, whatever the phrasing around it.
    """
    s = raw.casefold()
    if "drd" in s:
        return "drd"
    if "directus" in s:
        return "directus"
    return "autre"


def unification_signal(keys):
    """How strong a same-label collision is, from the *shape* of the differing keys.

    Two keys of the same arity differing in exactly one segment usually name the same element in two
    places — the Save CTA on two pages, the same remote item keyed per page. Keys of different arity,
    or differing in several places, usually name two surfaces that merely share a word: unifying
    those would forbid ever wording them differently, which is a real loss disguised as a cleanup.
    """
    segs = [k.split(".") for k in keys]
    if len({len(x) for x in segs}) > 1:
        return "surfaces différentes — probablement légitime"
    positions = {i for i in range(len(segs[0])) if len({x[i] for x in segs}) > 1}
    if len(positions) == 1:
        return "même élément à deux emplacements — candidat sérieux"
    return "surfaces différentes — probablement légitime"


def editorial_findings(specs):
    """The two defects a key-only join cannot see.

    * **Same key, different labels** — a contradiction: one render, two texts, so one spec is wrong.
      Reported as a divergence, and gated as an ERROR by `validate_sync.py`.
    * **Same label, different keys** — a possible missing factorisation. *Possible* only: two
      surfaces legitimately share a word, and interface vocabulary (`Add-ons`, `Learn more`) is
      duplicated on purpose. The detector counts and describes; it never concludes.
    """
    by_key, by_label, placeholders = {}, {}, []
    for s in specs:
        for key, label, source in s.cms:
            by_key.setdefault(key, []).append((s, label, source))
            if not label:
                continue
            if PLACEHOLDER_LABEL_RE.match(label.strip()):
                placeholders.append({"key": key, "label": label, "prd": s.prd, "spec": s.rel})
                continue
            by_label.setdefault(normalise_label(label), []).append((s, key, label, source))

    divergence = []
    for key, entries in sorted(by_key.items()):
        variants = {normalise_label(lab) for _s, lab, _src in entries if lab}
        if len(variants) > 1:
            divergence.append({
                "key": key,
                "variants": sorted({lab for _s, lab, _src in entries if lab}),
                "carriers": sorted({(s.prd, s.rel) for s, _l, _src in entries}),
            })
        # The Source cell is free text: two specs citing the same DRD word it differently, and
        # comparing the raw strings only produces noise. What is worth comparing is the *class* of
        # attestation — a label grounded in a DRD versus one still to create in Directus.
        classes = {classify_source(src) for _s, _l, src in entries if src}
        if len(classes) > 1:
            divergence.append({
                "key": key, "variants": [], "sources": sorted(classes),
                "carriers": sorted({(s.prd, s.rel) for s, _l, _src in entries}),
            })

    revision = []
    for norm, entries in sorted(by_label.items()):
        keys = sorted({k for _s, k, _l, _src in entries})
        if len(keys) < 2:
            continue
        prds = sorted({s.prd for s, _k, _l, _src in entries})
        # The common prefix says a lot: keys differing only in a page segment usually denote the
        # same element rendered twice, while a different structure usually means a different surface.
        segs = [k.split(".") for k in keys]
        common = []
        for i in range(min(len(x) for x in segs)):
            col = {x[i] for x in segs}
            if len(col) == 1:
                common.append(segs[0][i])
            else:
                break
        generic = len(keys) >= GENERIC_THRESHOLD
        revision.append({
            "label": entries[0][2],
            "keys": keys,
            "prds": prds,
            "scope": "inter-PRD" if len(prds) > 1 else "intra-PRD",
            "generic": generic,
            "signal": "vocabulaire d'interface probable" if generic else unification_signal(keys),
            "common_prefix": ".".join(common),
            "carriers": sorted({(s.prd, s.rel) for s, _k, _l, _src in entries}),
            "attested": sorted({src for _s, _k, _l, src in entries if src}),
        })
    return divergence, revision, placeholders


def classify(index, covered):
    """Three buckets. One PRD is never a finding — the `spec` skill already owns that case.

    A key already covered goes to `rattachement`: the answer to a new carrier on a known mechanism
    is to attach it, not to open a second transversal feature on the same thing.
    """
    synchro, factorisation, rattachement = [], [], []
    for (key, ktype), carriers in sorted(index.items()):
        prds = sorted({p for p, _ in carriers})
        if len(prds) < 2:
            continue
        entry = {"key": key, "type": ktype, "prds": prds, "carriers": sorted(set(carriers))}
        if key in covered:
            entry["covered_by"] = covered[key]
            rattachement.append(entry)
        elif len(prds) >= 3 and ktype == "endpoint":
            factorisation.append(entry)
        else:
            synchro.append(entry)
    return synchro, factorisation, rattachement


# --------------------------------------------------------------------------- existing coverage

SYNC_KEYS_BLOCK_RE = re.compile(r"(?s)<!--\s*sync:keys\s*-->(.*?)<!--\s*/sync:keys\s*-->")
BACKTICKED_RE = re.compile(r"`([^`]+)`")


def load_covered_keys(features_root: Path, register: Path):
    """Keys already covered, read from the transversal features and the register.

    Read *before* proposing anything, and matched **by key, never by title**: a title drifts as the
    wording is polished, a key does not. This is what stops the second run from proposing again what
    the first one already extracted.
    """
    covered, consulted = {}, []
    if features_root:
        if features_root.is_dir():
            consulted.append(f"`{features_root.name}/`")
        else:
            consulted.append(f"`{features_root.name}/` (absent — premier passage)")
    if features_root and features_root.is_dir():
        for path in sorted(features_root.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            for block in SYNC_KEYS_BLOCK_RE.findall(text):
                for tok in BACKTICKED_RE.findall(block):
                    ep = normalise_endpoint(tok)
                    key = f"{ep[0]} {ep[1]}".strip() if ep else tok.strip()
                    covered.setdefault(key, []).append(("fonctionnalité transverse", path.stem))
    if register:
        consulted.append(
            f"`{register.name}`" if register.is_file()
            else f"`{register.name}` (absent — premier passage)")
    if register and register.is_file():
        text = register.read_text(encoding="utf-8")
        for block in re.findall(r"(?s)<!--\s*sync:auto[^>]*-->(.*?)<!--\s*/sync:auto\s*-->", text):
            for row in TABLE_ROW_RE.findall(block):
                cell = _first_cell(row)
                tok = _backticked(cell) if cell else None
                if not tok:
                    continue
                ep = normalise_endpoint(tok)
                key = f"{ep[0]} {ep[1]}".strip() if ep else tok.strip()
                covered.setdefault(key, []).append(("registre", "SYNCHRO.md"))
    return covered, consulted


def regroupement_hints(factorisation) -> list:
    """One transversal feature per mechanism — but is a pair of keys one mechanism or two?

    The report cannot decide it; it can order the reading. Two keys carried by the *same* specs move
    together, which is what a shared state machine looks like from the outside. Two keys carried by
    different specs are either two mechanisms, or one mechanism with a carrier missing — and that
    difference is exactly what the reader must go and settle.
    """
    if len(factorisation) < 2:
        return []
    out = ["#### Regroupement — un mécanisme ou plusieurs ?\n"]
    same, differ = [], []
    for i, a in enumerate(factorisation):
        for b in factorisation[i + 1:]:
            sa = {rel for _prd, rel in a["carriers"]}
            sb = {rel for _prd, rel in b["carriers"]}
            (same if sa == sb else differ).append((a["key"], b["key"], sa, sb))
    for ka, kb, _sa, _sb in same:
        out.append(f"- `{ka}` et `{kb}` — **mêmes specs porteuses**. Indice fort d'un mécanisme "
                   "unique : un seul document, sauf raison contraire.")
    for ka, kb, sa, sb in differ:
        common = len(sa & sb)
        out.append(f"- `{ka}` et `{kb}` — porteuses **différentes** ({len(sa)} vs {len(sb)} specs, "
                   f"{common} en commun). Soit deux mécanismes, soit un porteur manquant.")
    out.append("\nCe classement n'est qu'un ordre de lecture. Le test qui tranche est dans "
               "`refs/REF-extraction-criteria.md` : peut-on énoncer chaque règle en ne nommant "
               "qu'une seule de ces clés ?\n")
    return out


# --------------------------------------------------------------------------- report

def render(specs, synchro, factorisation, rattachement, revision, attention, findings,
           focus=None, consulted=None) -> str:
    consulted = consulted or []
    L = []
    add = L.append
    add("# Rapport de synchronisation inter-specs\n")
    prds = sorted({s.prd for s in specs})
    add(f"{len(specs)} specs analysées, réparties sur {len(prds)} PRD : {', '.join(prds)}.\n")
    if focus:
        add(f"**Rapport restreint à `{focus}`.** Le corpus entier a été lu — une collision se voit "
            "des deux côtés — mais seuls les constats qui impliquent ce PRD sont listés.\n")

    if attention:
        add("## Points d'attention\n")
        add("| Sévérité | Spec | Point | Impact | Résolution |")
        add("|---|---|---|---|---|")
        order = {"Blocking": 0, "Medium": 1, "Minor": 2}
        for a in sorted(attention, key=lambda x: order.get(x["severity"], 9)):
            add(f"| **{a['severity']}** | `{a['spec']}` | {a['point']} | {a['impact']} | {a['resolution']} |")
        add("")

    add("## Candidats à factorisation — fonctionnalité transverse\n")
    if not factorisation:
        add("_Aucun : aucune clé de comportement n'est portée par 3 PRD distincts ou plus._\n")
    else:
        add("Une clé de comportement portée par ≥3 PRD. À confirmer par un jugement d'observabilité "
            "avant toute extraction — une clé partagée n'est pas toujours une règle partagée.\n")
        for e in factorisation:
            add(f"### `{e['key']}`\n")
            add(f"PRD porteurs ({len(e['prds'])}) : {', '.join(e['prds'])}\n")
            for prd, rel in e["carriers"]:
                add(f"- {prd} — [{Path(rel).stem}]({rel})")
            add("")
        for line in regroupement_hints(factorisation):
            add(line)

    add("## Déjà couvert — rattacher un porteur\n")
    if not rattachement and not consulted:
        # Silence and "nothing found" are not the same answer. Printing the reassuring line when no
        # source was consulted is how a second run re-proposes what the first one already extracted.
        add("⚠ **Couverture non vérifiée** — ni `--features` ni `--register` n'ont été fournis. "
            "Le rapport ne peut pas dire si ces clés sont déjà portées par un document existant : "
            "relancer avec les deux chemins avant de proposer quoi que ce soit.\n")
    elif not rattachement:
        add(f"_Aucune clé déjà couverte._ Sources consultées : {', '.join(consulted)}.\n")
    else:
        add("Ces clés sont déjà portées par un document existant. Rattacher le porteur, "
            "ne rien créer.\n")
        add("| Clé | Couverte par | PRD porteurs |")
        add("|---|---|---|")
        for e in rattachement:
            by = ", ".join(f"{kind} `{name}`" for kind, name in e["covered_by"])
            add(f"| `{e['key']}` | {by} | {', '.join(e['prds'])} |")
        add("")

    add("## Synchros à documenter — registre\n")
    if not synchro:
        add("_Aucune._\n")
    else:
        add("Une clé portée par 2 PRD, ou une clé CMS quel que soit le nombre de porteurs. "
            "Ces entrées vont au registre, jamais en fonctionnalité transverse.\n")
        add("| Clé | Type | PRD porteurs | Specs |")
        add("|---|---|---|---|")
        for e in synchro:
            links = ", ".join(f"[{Path(rel).stem}]({rel})" for _p, rel in e["carriers"])
            add(f"| `{e['key']}` | {e['type']} | {', '.join(e['prds'])} | {links} |")
        add("")

    add("## Révisions éditoriales — même libellé, clés différentes\n")
    if not revision:
        add("_Aucune._\n")
    else:
        add("Un même libellé porté par plusieurs clés. **Ce n'est pas une conclusion** : deux "
            "surfaces partagent légitimement un mot, et le vocabulaire d'interface se duplique "
            "à dessein. Trancher au cas par cas — voir l'anti-pattern « libellé générique pris "
            "pour un doublon ».\n")
        add("| Libellé | Portée | Clés | Signal |")
        add("|---|---|---|---|")
        rank = {"même élément à deux emplacements — candidat sérieux": 0,
                "surfaces différentes — probablement légitime": 1,
                "vocabulaire d'interface probable": 2}
        for r in sorted(revision, key=lambda x: (rank.get(x["signal"], 9), x["scope"] != "inter-PRD")):
            keys = " · ".join(f"`{k}`" for k in r["keys"])
            add(f"| «&nbsp;{r['label']}&nbsp;» | {r['scope']} | {keys} | {r['signal']} |")
        add("")

    errors = [f for f in findings if f[0] == "ERROR"]
    warns = [f for f in findings if f[0] == "WARN"]
    if errors or warns:
        add("## Intégrité du graphe de citations\n")
        for level, where, msg in errors + warns:
            mark = "✗ ERROR" if level == "ERROR" else "⚠ WARN"
            add(f"- {mark} · `{where}` — {msg}")
        add("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description="Detect synchronisation points between specs.")
    ap.add_argument("specs_root", help="{DOCS_ROOT}/specs")
    ap.add_argument("--features", help="{DOCS_ROOT}/transversal-features", default=None)
    ap.add_argument("--register", help="{DOCS_ROOT}/SYNCHRO.md", default=None)
    ap.add_argument("--repo-root", help="knowledge-base root, for repo-relative links", default=None)
    ap.add_argument("--focus", default=None,
                    help="report only what involves this PRD (slug or substring). The whole corpus "
                         "is still read — a collision cannot be seen from one side alone.")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    specs_root = Path(args.specs_root)
    if not specs_root.is_dir():
        print(f"✗ {specs_root} n'est pas un dossier", file=sys.stderr)
        return 2

    repo_root = Path(args.repo_root) if args.repo_root else None
    findings = []
    specs = load_specs(specs_root, repo_root, findings)
    if not specs:
        print(f"✗ aucune spec exploitable sous {specs_root}", file=sys.stderr)
        return 2

    resolved, attention = resolve_endpoints(specs, findings)
    index = build_index(specs, resolved)
    covered, consulted = load_covered_keys(
        Path(args.features) if args.features else None,
        Path(args.register) if args.register else None,
    )
    synchro, factorisation, rattachement = classify(index, covered)
    divergence, revision, placeholders = editorial_findings(specs)

    # Focus filters the *report*, never the corpus: a collision involves two sides, and dropping
    # the other side before joining would make it invisible instead of shorter.
    if args.focus:
        f = args.focus
        keep = lambda prds: any(f in p for p in prds)  # noqa: E731
        synchro = [e for e in synchro if keep(e["prds"])]
        factorisation = [e for e in factorisation if keep(e["prds"])]
        rattachement = [e for e in rattachement if keep(e["prds"])]
        revision = [e for e in revision if keep(e["prds"])]
        divergence = [d for d in divergence if keep([p for p, _r in d["carriers"]])]
        placeholders = [p for p in placeholders if f in p["prd"]]
        attention = [a for a in attention if any(f in s.rel and s.rel == a["spec"] for s in specs)]
    for p in placeholders:
        findings.append((
            "WARN", p["spec"],
            f"`{p['key']}` porte un libellé non rédigé (« {p['label']} ») — la clé ne peut être "
            "ni comparée ni dédoublonnée tant que son texte n'existe pas",
        ))

    # A same-key/different-label collision is not a candidate awaiting judgement: one key renders
    # one text, so two texts mean one spec is wrong. It is reported as a defect, and it fails the run.
    for d in divergence:
        if d["variants"]:
            findings.append((
                "ERROR", d["key"],
                "même clé, libellés différents : " + " vs ".join(f'« {v} »' for v in d["variants"])
                + " — une clé rend un seul texte, l'une des specs se trompe",
            ))
        else:
            findings.append((
                "WARN", d["key"],
                "même clé, attestations divergentes : " + " vs ".join(d.get("sources", []))
                + " — une seule des deux fait foi",
            ))

    if args.json:
        print(json.dumps({
            "specs": [{"rel": s.rel, "prd": s.prd, "status": s.status} for s in specs],
            "synchro": synchro,
            "factorisation": factorisation,
            "rattachement": rattachement,
            "coverage_sources": consulted,
            "revision": revision,
            "divergence": divergence,
            "placeholders": placeholders,
            "attention": attention,
            "findings": [{"level": l, "where": w, "message": m} for l, w, m in findings],
        }, ensure_ascii=False, indent=2))
    else:
        print(render(specs, synchro, factorisation, rattachement, revision, attention, findings,
                     focus=args.focus, consulted=consulted))

    return 1 if any(f[0] == "ERROR" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
