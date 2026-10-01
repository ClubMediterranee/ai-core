#!/usr/bin/env python3
"""
qa_check.py — Contrôle qualité statique d'une variation d'A/B test (CSS + JS).

Usage :
    python qa_check.py --css variation.css --js variation.js
    python qa_check.py --css variation.css           # CSS seul
    echo "<code>" | python qa_check.py --js -         # depuis stdin

Codes de sortie : 0 = aucune alerte bloquante, 1 = au moins une alerte [ERREUR].
Les alertes [WARN] n'échouent pas mais doivent être revues.

Ce lint ne remplace pas la checklist manuelle (cf. references/qa-checklist.md) :
contraste, charte, rendu multi-device se vérifient à l'œil sur les captures.
"""
import argparse
import re
import sys
from pathlib import Path

ERRORS = []
WARNS = []
OKS = []


def err(msg): ERRORS.append(msg)
def warn(msg): WARNS.append(msg)
def ok(msg): OKS.append(msg)


def read(arg):
    if arg is None:
        return None
    if arg == "-":
        return sys.stdin.read()
    p = Path(arg)
    if not p.exists():
        err(f"Fichier introuvable : {arg}")
        return None
    return p.read_text(encoding="utf-8", errors="replace")


def strip_comments_css(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def strip_comments_js(js):
    js = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
    js = re.sub(r"(?m)//.*$", "", js)
    return js


def check_css(css):
    body = strip_comments_css(css)

    # Sélecteurs fragiles : classes hashées
    hashed = re.findall(r"\.(?:css-[0-9a-z]+|sc-[0-9a-z]+|[a-z0-9]*[0-9a-f]{6,}[a-z0-9]*)", body, re.I)
    if hashed:
        warn(f"Sélecteurs fragiles (classes hashées) : {sorted(set(hashed))[:5]} — "
             "préférer data-*/aria/classe sémantique, ou fallback par texte en JS.")
    else:
        ok("Aucune classe hashée fragile dans le CSS.")

    # !important
    bangs = body.count("!important")
    if bangs > 0:
        warn(f"{bangs} occurrence(s) de !important — à réserver aux overrides de styles inline, "
             "à documenter.")
    else:
        ok("Pas de !important.")

    # Scoping : règles non préfixées par une classe racine de variation
    # Neutraliser les placeholders de template {{...}} pour ne pas fausser le parsing
    parse = re.sub(r"\{\{[^}]*\}\}", "PLACEHOLDER", body)
    rules = re.findall(r"([^{}]+)\{", parse)
    root = re.search(r"\.(abt-v\d+|ab-?v\d+|variation-?\d+|v\d+-[a-z]+)", parse)
    root_token = root.group(1) if root else None
    unscoped = []
    for sel in rules:
        sel = sel.strip()
        if not sel or sel.startswith("@") or sel.startswith(":root"):
            continue
        # ignorer ce qui n'est pas un sélecteur (déclarations, variables CSS)
        if ";" in sel or sel.lstrip().startswith("--"):
            continue
        # accepte le scoping par n'importe quelle classe racine .abt-*
        if not re.search(r"\.(abt-|ab-v|variation|v\d)", sel):
            unscoped.append(sel[:50])
    if unscoped:
        warn(f"{len(unscoped)} règle(s) CSS non scopée(s) par une classe racine "
             f"(ex. {unscoped[:3]}) — risque de collision + cleanup difficile. "
             "Préfixer par .abt-vN.")
    else:
        ok("CSS scopé par une classe racine de variation.")

    # Heuristique flicker : display:none sans réaffichage
    if re.search(r"display\s*:\s*none", body) and "visibility" not in body:
        warn("display:none détecté — préférer visibility/opacity pour limiter les reflows "
             "et éviter le saut de layout (flicker).")

    return root_token


def check_js(js, css_root):
    body = strip_comments_js(js)

    # Idempotence : présence d'un flag/garde
    has_guard = bool(re.search(r"classList\.(contains|add)\(['\"]abt", body)) or \
        bool(re.search(r"(if\s*\(.*(already|applied|VARIATION|__abt).*\))", body, re.I)) or \
        bool(re.search(r"dataset\.abt", body))
    if has_guard:
        ok("Garde d'idempotence détectée (flag/classe racine).")
    else:
        err("Pas de garde d'idempotence : le JS peut s'appliquer en double sur navigation SPA. "
            "Ajouter un flag (classe racine ou dataset).")

    # Attente DOM dynamique
    if re.search(r"MutationObserver|waitForElement|querySelector.*setInterval", body):
        ok("Attente des éléments dynamiques gérée (MutationObserver/waitForElement).")
    else:
        if re.search(r"querySelector", body):
            warn("querySelector sans attente d'apparition : si le DOM est rendu en JS, "
                 "l'élément peut être absent. Utiliser waitForElement (cf. assets/variation.js).")

    # Traçabilité pour rollback
    if re.search(r"data-abt|dataset\.abt", body):
        ok("Éléments ajoutés/modifiés marqués (data-abt) → rollback facilité.")
    else:
        warn("Aucun marquage data-abt sur les ajouts : le cleanup sera moins fiable. "
             "Marquer les nœuds créés avec data-abt=\"vN\".")

    # Sauvegarde avant écrasement de contenu
    if re.search(r"(innerHTML|textContent|innerText)\s*=", body) and "abtOriginal" not in body:
        warn("Contenu écrasé sans sauvegarde de l'original : rollback du texte impossible. "
             "Sauvegarder dans el.dataset.abtOriginal avant d'écraser.")

    # Erreurs de syntaxe basiques : déséquilibre d'accolades/parenthèses
    for ch_open, ch_close, name in [("{", "}", "accolades"), ("(", ")", "parenthèses")]:
        if body.count(ch_open) != body.count(ch_close):
            err(f"Déséquilibre de {name} dans le JS ({body.count(ch_open)} ouvrantes "
                f"vs {body.count(ch_close)} fermantes).")


def check_antiflicker(css, js):
    blob = (css or "") + (js or "")
    masks = bool(re.search(r"(visibility\s*:\s*hidden|opacity\s*:\s*0|display\s*:\s*none)", blob))
    has_timeout = bool(re.search(r"setTimeout", js or ""))
    if masks and not has_timeout:
        warn("Masquage détecté (anti-flicker probable) sans setTimeout de sécurité : "
             "risque de page masquée si le JS échoue. Ajouter un timeout de réaffichage (≈3s). "
             "Voir assets/variation.js (bloc AFL_ID) pour le pattern intégré.")
    elif masks and has_timeout:
        ok("Masquage avec timeout de sécurité présent.")


def main():
    ap = argparse.ArgumentParser(description="QA statique d'une variation A/B test")
    ap.add_argument("--css")
    ap.add_argument("--js")
    args = ap.parse_args()

    if not args.css and not args.js:
        ap.error("Fournir au moins --css ou --js")

    css = read(args.css)
    js = read(args.js)

    css_root = None
    if css is not None:
        css_root = check_css(css)
    if js is not None:
        check_js(js, css_root)
    check_antiflicker(css, js)

    print("=" * 60)
    print("QA AUTOMATIQUE — variation A/B test")
    print("=" * 60)
    for m in OKS:
        print(f"  [OK]    {m}")
    for m in WARNS:
        print(f"  [WARN]  {m}")
    for m in ERRORS:
        print(f"  [ERREUR] {m}")
    print("-" * 60)
    print(f"  {len(OKS)} OK · {len(WARNS)} warning(s) · {len(ERRORS)} erreur(s)")
    print("  Rappel : vérifier à la main contraste, charte et rendu multi-device "
          "(references/qa-checklist.md).")
    sys.exit(1 if ERRORS else 0)


if __name__ == "__main__":
    main()
