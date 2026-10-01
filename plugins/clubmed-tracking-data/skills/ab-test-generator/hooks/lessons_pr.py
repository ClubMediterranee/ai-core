#!/usr/bin/env python3
"""
Hook Stop Claude Code — si le skill ab-test-generator a été utilisé dans la session,
extrait une éventuelle leçon généralisable et l'ajoute à la Knowledgebase ClubMed
(dcx/cro/docs/lessons-learned/) via une pull request — jamais de push direct sur main.

Comment ça marche :
  1. Claude Code appelle ce script à la fin de chaque session
  2. Si /tmp/abt_session_active n'existe pas -> skip immédiat (session sans AB test)
  3. Si le flag existe -> lit le transcript JSONL, appelle Claude CLI pour extraire
     une éventuelle nouvelle leçon (seuil de qualité strict : pas de leçon anecdotique)
  4. Si une leçon est identifiée -> écrit dans le clone local de knowledge-base, commit
     sur une branche dédiée, push, ouvre ou met à jour une pull request via l'API GitHub
  5. Si rien de généralisable -> ne fait rien, silencieusement (cas normal et attendu)

Prérequis : GITHUB_TOKEN disponible dans l'environnement (géré par le skill
github-authentication du plugin clubmed-github — voir sa SKILL.md pour le cycle de vie du PAT).
"""

import json
import os
import re
import sys
import glob
import subprocess
import urllib.request
import urllib.error
from datetime import date
from pathlib import Path

KB = Path(os.environ.get("CLUBMED_KB", str(Path.home() / ".clubmed" / "knowledge-base")))
LESSONS_DIR = KB / "dcx" / "cro" / "docs" / "lessons-learned"
FLAG_FILE = Path("/tmp/abt_session_active")
PROJECTS_DIR = Path.home() / ".claude" / "projects"
SKILL_NAMES = ("ab-test-generator",)

LESSON_FILES = [
    "page-intelligence.md",
    "targeting.md",
    "ux.md",
    "build.md",
    "qa.md",
    "review.md",
]

GITHUB_API_REPO = "ClubMediterranee/knowledge-base"


def log(msg: str) -> None:
    print(f"[abt_lessons] {msg}", file=sys.stderr)


def cleanup_flag() -> None:
    try:
        FLAG_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def find_transcript(session_id: str) -> Path | None:
    pattern = str(PROJECTS_DIR / "**" / f"{session_id}.jsonl")
    matches = glob.glob(pattern, recursive=True)
    return Path(matches[0]) if matches else None


def skill_was_used(transcript_path: Path) -> bool:
    try:
        with open(transcript_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if d.get("type") != "assistant":
                    continue
                for item in d.get("message", {}).get("content", []):
                    if not isinstance(item, dict):
                        continue
                    if item.get("type") == "tool_use" and item.get("name") == "Skill":
                        skill_arg = item.get("input", {}).get("skill", "")
                        if any(name in skill_arg for name in SKILL_NAMES):
                            return True
    except Exception:
        pass
    return False


def extract_conversation_text(transcript_path: Path) -> str:
    parts = []
    try:
        with open(transcript_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                role = d.get("type")
                if role not in ("user", "assistant"):
                    continue
                content = d.get("message", {}).get("content", [])
                if isinstance(content, str):
                    parts.append(f"[{role.upper()}]: {content[:600]}")
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            parts.append(f"[{role.upper()}]: {item.get('text','')[:600]}")
                            break
                        elif isinstance(item, str):
                            parts.append(f"[{role.upper()}]: {item[:600]}")
                            break
    except Exception:
        pass
    return "\n\n".join(parts[-40:])


def read_current_lessons() -> str:
    parts = []
    for name in LESSON_FILES:
        f = LESSONS_DIR / name
        if f.exists():
            parts.append(f"### {name}\n{f.read_text(encoding='utf-8')[:1500]}")
    return "\n\n".join(parts) if parts else "(aucune leçon documentée pour l'instant)"


def call_claude_for_lesson(conversation_text: str, current_lessons: str) -> dict | None:
    prompt = f"""Tu es un assistant qui identifie les leçons généralisables à ajouter à la base de
connaissance du skill ab-test-generator (génération d'A/B tests AB Tasty pour clubmed.fr et
sites locaux).

Fichiers de leçons existants, par domaine :
<lessons_actuelles>
{current_lessons[:4000]}
</lessons_actuelles>

Extrait de la session qui vient de se terminer :
<session>
{conversation_text[:4000]}
</session>

Ta tâche :
1. Identifie si cette session contient une erreur, un blocage ou un apprentissage CONCRET et
   GÉNÉRALISABLE (pas spécifique à un seul test ponctuel, pas une anecdote sans valeur réutilisable).
2. Sois strict : la majorité des sessions n'apportent RIEN de nouveau à documenter. Ne force jamais
   une leçon pour avoir quelque chose à écrire.
3. Vérifie qu'elle n'est pas déjà documentée (évite les doublons et les quasi-doublons).
4. Si une leçon mérite d'être ajoutée, réponds UNIQUEMENT avec un JSON de cette forme (rien
   d'autre, pas de bloc markdown autour) :
   {{"file": "page-intelligence.md|targeting.md|ux.md|build.md|qa.md|review.md",
     "heading": "Titre court de la leçon",
     "body": "Règle en markdown (1-3 paragraphes), factuel et actionnable"}}
5. Si rien de nouveau et généralisable -> réponds UNIQUEMENT : NOTHING_TO_ADD

Maximum 1 leçon. Sois concis, factuel, exigeant."""

    try:
        result = subprocess.run(
            ["claude", "--print"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=90,
        )
        if result.returncode != 0:
            return None
        output = result.stdout.strip()
        if not output or "NOTHING_TO_ADD" in output:
            return None
        output = re.sub(r"^```(?:json)?\s*|\s*```$", "", output.strip())
        data = json.loads(output)
        if data.get("file") not in LESSON_FILES or not data.get("heading") or not data.get("body"):
            return None
        return data
    except Exception as e:
        log(f"Erreur appel Claude : {e}")
        return None


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def github_api(method: str, path: str, token: str, body: dict | None = None) -> tuple[int, dict]:
    url = f"https://api.github.com{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except Exception:
            return e.code, {}


def open_or_update_pr(branch: str, token: str) -> str | None:
    status, existing = github_api(
        "GET", f"/repos/{GITHUB_API_REPO}/pulls?head=ClubMediterranee:{branch}&state=open", token
    )
    if status == 200 and isinstance(existing, list) and existing:
        return existing[0].get("html_url")

    body = {
        "title": "chore(cro): nouvelle leçon ab-test-generator",
        "head": branch,
        "base": "main",
        "body": "Leçon extraite automatiquement en fin de session par le skill "
                "`ab-test-generator` (hook Stop). À relire avant merge.",
    }
    status, created = github_api("POST", f"/repos/{GITHUB_API_REPO}/pulls", token, body)
    if status in (200, 201):
        return created.get("html_url")
    log(f"Création PR échouée (HTTP {status}): {created}")
    return None


def append_lesson_and_publish(lesson: dict) -> None:
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        log("GITHUB_TOKEN absent — leçon non publiée. Invoquer github-authentication puis relancer manuellement si besoin.")
        return

    branch = f"cro-lessons/{date.today().isoformat()}"
    target = LESSONS_DIR / lesson["file"]

    r = run(["git", "checkout", "main"], KB)
    if r.returncode != 0:
        log(f"git checkout main a échoué : {r.stderr.strip()}")
        return
    run(["git", "pull", "origin", "main", "--quiet"], KB)

    existing_branch = run(["git", "rev-parse", "--verify", branch], KB)
    if existing_branch.returncode == 0:
        run(["git", "checkout", branch], KB)
        run(["git", "merge", "main", "--quiet"], KB)
    else:
        run(["git", "checkout", "-b", branch], KB)

    existing = target.read_text(encoding="utf-8") if target.exists() else f"# Leçons — {lesson['file'][:-3]}\n"
    addition = f"\n\n## {lesson['heading']}\n\n{lesson['body'].strip()}\n"
    target.write_text(existing.rstrip() + addition, encoding="utf-8")

    run(["git", "add", str(target.relative_to(KB))], KB)
    commit = run(["git", "commit", "-m", f"chore(cro): leçon ab-test-generator — {lesson['heading']}"], KB)
    if commit.returncode != 0:
        log(f"Rien à committer ou échec commit : {commit.stderr.strip()}")
        run(["git", "checkout", "main"], KB)
        return

    push = run(["git", "push", "-u", "origin", branch, "--quiet"], KB)
    if push.returncode != 0:
        log(f"Push échoué : {push.stderr.strip()}")
        run(["git", "checkout", "main"], KB)
        return

    pr_url = open_or_update_pr(branch, token)
    run(["git", "checkout", "main"], KB)

    if pr_url:
        log(f"Leçon publiée — PR : {pr_url}")
    else:
        log("Leçon poussée sur la branche mais la PR n'a pas pu être créée automatiquement — ouvrir une PR manuellement depuis GitHub.")


def main() -> None:
    try:
        stdin_data = json.loads(sys.stdin.read())
    except Exception:
        stdin_data = {}

    session_id = stdin_data.get("session_id", "")

    if not FLAG_FILE.exists():
        cleanup_flag()
        return

    log(f"Flag détecté — analyse de la session {session_id}")

    if not session_id:
        log("Pas de session_id — abandon")
        cleanup_flag()
        return

    transcript = find_transcript(session_id)
    if not transcript:
        log(f"Transcript introuvable pour session {session_id}")
        cleanup_flag()
        return

    if not skill_was_used(transcript):
        log("Skill ab-test-generator non détecté — skip")
        cleanup_flag()
        return

    if not (KB / ".git").is_dir():
        log(f"Knowledgebase introuvable ({KB}) — pas d'extraction de leçon possible")
        cleanup_flag()
        return

    log("Skill confirmé — extraction d'une éventuelle leçon...")

    conversation_text = extract_conversation_text(transcript)
    if not conversation_text:
        log("Transcript vide — abandon")
        cleanup_flag()
        return

    current_lessons = read_current_lessons()
    lesson = call_claude_for_lesson(conversation_text, current_lessons)

    if lesson:
        append_lesson_and_publish(lesson)
    else:
        log("Rien de nouveau et généralisable à documenter — pas de leçon cette session")

    cleanup_flag()


if __name__ == "__main__":
    main()
