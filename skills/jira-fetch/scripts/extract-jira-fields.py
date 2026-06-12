#!/usr/bin/env python3
"""
extract-jira-fields.py — Extract all fields from a raw Jira issue JSON.

Usage:
    python3 extract-jira-fields.py <path-to-json> [--output-dir <dir>]

Output:
    Writes <output-dir>/ticket.md (default: prints to stdout)
    Copies raw JSON to <output-dir>/raw.json
    Lists attachments under <output-dir>/attachments/ (download requires --download flag)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Club Med custom field labels — used when the field schema name isn't available.
# The script will still process ANY custom field; this is only for display labels.
KNOWN_CUSTOM_FIELDS = {
    "customfield_11553": "User Story",
    "customfield_11554": "Business Rules",
    "customfield_11556": "QA Scenarios",
    "customfield_12207": "API Resources",
    "customfield_12208": "Design Notes",
    "customfield_11563": "Figma URL",
    "customfield_11547": "DOR",
}

FIGMA_URL_RE = re.compile(r"https://www\.figma\.com/[^\s\)\]\"'<]+")

# Standard fields to always include at the top of the output.
STANDARD_FIELDS = [
    ("summary", "Summary"),
    ("status", "Status"),
    ("assignee", "Assignee"),
    ("reporter", "Reporter"),
    ("priority", "Priority"),
    ("issuetype", "Issue Type"),
    ("labels", "Labels"),
    ("components", "Components"),
    ("fixVersions", "Fix Versions"),
    ("story_points", "Story Points"),  # handled specially
    ("created", "Created"),
    ("updated", "Updated"),
    ("duedate", "Due Date"),
    ("description", "Description"),
]


# ---------------------------------------------------------------------------
# ADF renderer
# ---------------------------------------------------------------------------

def render_adf(node, depth: int = 0) -> str:
    if not node:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return "".join(render_adf(n, depth) for n in node)

    t = node.get("type", "")
    content = node.get("content", [])
    indent = "  " * depth

    if t == "doc":
        return render_adf(content, depth)

    if t == "text":
        s = node.get("text", "")
        for mark in node.get("marks", []):
            mt = mark.get("type", "")
            if mt == "strong":
                s = f"**{s}**"
            elif mt == "em":
                s = f"*{s}*"
            elif mt == "code":
                s = f"`{s}`"
            elif mt == "strike":
                s = f"~~{s}~~"
            elif mt == "link":
                href = mark.get("attrs", {}).get("href", "")
                s = f"[{s}]({href})"
            elif mt == "underline":
                s = f"<u>{s}</u>"
        return s

    if t == "hardBreak":
        return "\n"

    if t == "paragraph":
        inner = render_adf(content, depth)
        return (inner + "\n") if inner.strip() else "\n"

    if t == "heading":
        level = node.get("attrs", {}).get("level", 2)
        return "#" * level + " " + render_adf(content, depth) + "\n"

    if t == "bulletList":
        return "".join(render_adf(i, depth) for i in content)

    if t == "orderedList":
        result = []
        for idx, item in enumerate(content, 1):
            item_text = render_adf(item.get("content", []), depth + 1).strip()
            result.append(f"{indent}{idx}. {item_text}\n")
        return "".join(result)

    if t == "listItem":
        inner = render_adf(content, depth + 1).strip()
        return f"{indent}- {inner}\n"

    if t == "taskList":
        return "".join(render_adf(i, depth) for i in content)

    if t == "taskItem":
        state = node.get("attrs", {}).get("state", "TODO")
        check = "[x]" if state == "DONE" else "[ ]"
        inner = render_adf(content, depth + 1).strip()
        return f"{indent}- {check} {inner}\n"

    if t == "blockquote":
        inner = render_adf(content, depth)
        return "\n".join("> " + line for line in inner.splitlines()) + "\n"

    if t == "codeBlock":
        lang = node.get("attrs", {}).get("language", "")
        inner = render_adf(content, depth)
        return f"```{lang}\n{inner}\n```\n"

    if t == "rule":
        return "\n---\n"

    if t == "table":
        return render_table(node, depth)

    if t in ("tableRow", "tableHeader", "tableCell"):
        return render_adf(content, depth)

    if t == "mediaSingle":
        media = content[0] if content else {}
        url = media.get("attrs", {}).get("url", "")
        alt = media.get("attrs", {}).get("alt", "image")
        if url:
            return f"![{alt}]({url})\n"
        return "[image]\n"

    if t == "media":
        url = node.get("attrs", {}).get("url", "")
        alt = node.get("attrs", {}).get("alt", "attachment")
        if url:
            return f"![{alt}]({url})\n"
        return "[attachment]\n"

    if t == "inlineCard":
        url = node.get("attrs", {}).get("url", "")
        return f"[{url}]({url})"

    if t == "blockCard":
        url = node.get("attrs", {}).get("url", "")
        return f"[{url}]({url})\n"

    if t == "expand":
        title = node.get("attrs", {}).get("title", "Details")
        inner = render_adf(content, depth)
        return f"<details><summary>{title}</summary>\n\n{inner}\n</details>\n"

    if t == "mention":
        display = node.get("attrs", {}).get("text", "@mention")
        return display

    if t == "emoji":
        return node.get("attrs", {}).get("text", ":emoji:")

    if t == "status":
        label = node.get("attrs", {}).get("text", "status")
        return f"`{label}`"

    # Generic fallback — recurse into content
    return render_adf(content, depth)


def render_table(node: dict, depth: int) -> str:
    rows = node.get("content", [])
    output_rows = []
    is_header = True
    for row in rows:
        cells = row.get("content", [])
        cell_texts = []
        for cell in cells:
            text = render_adf(cell.get("content", []), depth).strip().replace("\n", " ")
            cell_texts.append(text)
        output_rows.append("| " + " | ".join(cell_texts) + " |")
        if is_header:
            output_rows.append("| " + " | ".join("---" for _ in cell_texts) + " |")
            is_header = False
    return "\n".join(output_rows) + "\n"


# ---------------------------------------------------------------------------
# Field value renderer (handles ADF, plain string, objects)
# ---------------------------------------------------------------------------

def render_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        # ADF document
        if value.get("type") == "doc":
            return render_adf(value)
        # Named object (status, priority, assignee, etc.)
        for key in ("displayName", "name", "value", "key"):
            if key in value:
                return str(value[key])
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        parts = [render_value(v) for v in value if v is not None]
        return ", ".join(p for p in parts if p)
    return str(value)


# ---------------------------------------------------------------------------
# Figma URL extraction
# ---------------------------------------------------------------------------

def collect_figma_urls(text: str) -> list[str]:
    return FIGMA_URL_RE.findall(text)


# ---------------------------------------------------------------------------
# Attachment listing
# ---------------------------------------------------------------------------

def list_attachments(fields: dict) -> list[dict]:
    attachments = fields.get("attachment", [])
    result = []
    for a in attachments:
        result.append({
            "filename": a.get("filename", "unknown"),
            "content_type": a.get("mimeType", ""),
            "size": a.get("size", 0),
            "url": a.get("content", ""),
            "created": a.get("created", ""),
        })
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_ticket_md(data: dict) -> tuple[str, list[str], list[dict]]:
    """Returns (markdown_text, figma_urls, attachments)."""

    # Support both direct API response and MCP wrapper
    if "fields" in data:
        fields = data["fields"]
        key = data.get("key", "UNKNOWN")
    elif "key" in data:
        fields = data
        key = data.get("key", "UNKNOWN")
    else:
        fields = data
        key = "UNKNOWN"

    all_figma_urls: list[str] = []
    sections: list[str] = []

    # Header
    summary = fields.get("summary", "(no summary)")
    status_raw = fields.get("status", {})
    status = render_value(status_raw)
    assignee_raw = fields.get("assignee") or {}
    assignee = render_value(assignee_raw) or "Unassigned"
    reporter_raw = fields.get("reporter") or {}
    reporter = render_value(reporter_raw) or "Unknown"
    priority_raw = fields.get("priority") or {}
    priority = render_value(priority_raw) or "—"
    story_points = (
        fields.get("story_points")
        or fields.get("customfield_10016")  # common SP field
        or fields.get("customfield_10028")
        or "—"
    )

    header = f"# {key}: {summary}\n\n"
    header += f"| Field | Value |\n|---|---|\n"
    header += f"| Status | {status} |\n"
    header += f"| Assignee | {assignee} |\n"
    header += f"| Reporter | {reporter} |\n"
    header += f"| Priority | {priority} |\n"
    header += f"| Story Points | {story_points} |\n"

    for field_id in ("labels", "components", "fixVersions"):
        val = render_value(fields.get(field_id))
        if val:
            label = field_id.replace("V", " V").replace("f", " f").title().strip()
            header += f"| {label} | {val} |\n"

    for date_field in ("created", "updated", "duedate"):
        val = fields.get(date_field)
        if val:
            header += f"| {date_field.title()} | {val} |\n"

    sections.append(header)

    # Description (always first body section)
    desc = fields.get("description")
    if desc:
        rendered = render_value(desc)
        if rendered.strip():
            sections.append(f"\n## Description\n\n{rendered}")
            all_figma_urls.extend(collect_figma_urls(rendered))

    # Custom fields — known ones first, then unknown ones
    rendered_field_ids: set[str] = {"description"}

    # Known Club Med fields in canonical order
    for field_id, label in KNOWN_CUSTOM_FIELDS.items():
        rendered_field_ids.add(field_id)
        value = fields.get(field_id)
        if not value:
            continue
        rendered = render_value(value)
        if rendered.strip():
            sections.append(f"\n## {label}\n\n{rendered}")
            if "figma" not in label.lower():
                all_figma_urls.extend(collect_figma_urls(rendered))
            else:
                # The Figma URL field itself — treat as URLs
                for line in rendered.splitlines():
                    line = line.strip()
                    if line.startswith("http"):
                        all_figma_urls.append(line)

    # All other custom fields not already handled
    for field_id, value in fields.items():
        if field_id in rendered_field_ids:
            continue
        if not field_id.startswith("customfield_"):
            continue
        if value is None or value == "" or value == [] or value == {}:
            continue
        rendered_field_ids.add(field_id)
        rendered = render_value(value)
        if not rendered.strip():
            continue
        label = f"Custom: {field_id}"
        sections.append(f"\n## {label}\n\n{rendered}")
        all_figma_urls.extend(collect_figma_urls(rendered))

    # Attachments
    attachments = list_attachments(fields)
    if attachments:
        att_lines = ["\n## Attachments\n"]
        for a in attachments:
            size_kb = a["size"] // 1024 if a["size"] else 0
            att_lines.append(f"- [{a['filename']}]({a['url']}) — {a['content_type']} ({size_kb} KB)")
            all_figma_urls.extend(collect_figma_urls(a["url"]))
        sections.append("\n".join(att_lines))

    # Deduplicated Figma URLs section
    seen: set[str] = set()
    unique_figma: list[str] = []
    for url in all_figma_urls:
        url = url.rstrip(".,;)")
        if url not in seen:
            seen.add(url)
            unique_figma.append(url)

    if unique_figma:
        figma_section = "\n## Figma URLs\n\n"
        figma_section += "\n".join(f"- {u}" for u in unique_figma)
        sections.insert(1, figma_section)  # place right after header

    return "\n".join(sections), unique_figma, attachments


def main():
    parser = argparse.ArgumentParser(description="Extract all fields from a Jira issue JSON")
    parser.add_argument("json_path", help="Path to raw Jira issue JSON")
    parser.add_argument("--output-dir", "-o", default=None, help="Directory to write ticket.md and raw.json")
    parser.add_argument("--download", action="store_true", help="Download attachments (requires curl)")
    args = parser.parse_args()

    json_path = Path(args.json_path)
    if not json_path.exists():
        print(f"ERROR: file not found: {json_path}", file=sys.stderr)
        sys.exit(1)

    with open(json_path) as f:
        data = json.load(f)

    ticket_md, figma_urls, attachments = build_ticket_md(data)

    if args.output_dir:
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        ticket_path = out_dir / "ticket.md"
        ticket_path.write_text(ticket_md, encoding="utf-8")
        print(f"Written: {ticket_path}", file=sys.stderr)

        raw_dest = out_dir / "raw.json"
        import shutil
        shutil.copy2(json_path, raw_dest)
        print(f"Written: {raw_dest}", file=sys.stderr)

        if attachments:
            att_dir = out_dir / "attachments"
            att_dir.mkdir(exist_ok=True)
            if args.download:
                for a in attachments:
                    dest = att_dir / a["filename"]
                    os.system(f'curl -sSL "{a["url"]}" -o "{dest}"')
                    print(f"Downloaded: {dest}", file=sys.stderr)
            else:
                links_file = att_dir / "attachments.md"
                lines = [f"# Attachments\n"]
                for a in attachments:
                    size_kb = a["size"] // 1024 if a["size"] else 0
                    lines.append(f"- [{a['filename']}]({a['url']}) ({size_kb} KB)")
                links_file.write_text("\n".join(lines), encoding="utf-8")
                print(f"Written: {links_file}", file=sys.stderr)

        print(f"\nFigma URLs ({len(figma_urls)}):", file=sys.stderr)
        for url in figma_urls:
            print(f"  {url}", file=sys.stderr)
    else:
        print(ticket_md)


if __name__ == "__main__":
    main()
