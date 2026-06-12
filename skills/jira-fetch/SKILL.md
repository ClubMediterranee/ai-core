---
name: jira-fetch
description: >
  Fetch a Jira ticket and write its full structured content to disk (.jira/<KEY>/). Extracts all standard fields, all custom fields present on the issue, attachments, and linked assets (Figma URLs, images, files). Use this skill whenever the user mentions a Jira ticket key (e.g. SHOP-123, LBE-456, LCA-789), pastes a Jira URL (atlassian.net/browse/...), says "fetch the ticket", "pull the Jira issue", "get the ticket", "show me the ticket", "read the Jira", or needs to start working on a ticket. Also triggers when the user mentions ticket context like "the acceptance criteria", "the business rules from the ticket", "the Figma from the ticket", "what does the ticket say about X", or any phrase that implies reading a Jira issue.
allowed-tools: Bash, Read, Write
version: 1.0.0
changelog:
  - version: 1.0.0
    date: 2026-06-12
    changes:
      - Initial release
created-at: 2026-06-12
created-by: "Raphaël Moisset <raphael.moisset@clubmed.com>"
---

# Jira Fetch

Fetch a Jira ticket and persist its full structured content to `.jira/<KEY>/` in the working directory. Extracts all fields — standard and custom — plus aggregates all linked assets (Figma URLs, image attachments, file attachments).

## When to run

Whenever a ticket key or Jira URL appears in context and the user needs its content to start work, review acceptance criteria, find a Figma link, or understand requirements.

## Step 1 — Resolve the ticket key

Extract the key from whatever the user provided:
- Bare key: `SHOP-2124` → use as-is
- URL: `https://clubmed.atlassian.net/browse/SHOP-2124` → extract `SHOP-2124`

## Step 2 — Fetch the raw issue

Choose the method based on what's available in the environment:

### MCP method (preferred when `mcp__jira__get_issue` is available)

```bash
# Call the MCP tool, save raw response
mcp__jira__get_issue issueKey="<KEY>"
```

Save the full JSON response to `/tmp/jira-<KEY>.json`.

### CLI method (fallback)

```bash
JIRA_KEY="<KEY>"
jira issue view "$JIRA_KEY" --raw > "/tmp/jira-${JIRA_KEY}.json"
```

If neither works, ask the user to paste the ticket content manually and write it verbatim to `.jira/<KEY>/raw.txt`.

## Step 3 — Extract and render all fields

Run the bundled extraction script:

```bash
python3 "$(dirname "$0")/scripts/extract-jira-fields.py" "/tmp/jira-<KEY>.json" --output-dir ".jira/<KEY>"
```

The script:
- Renders every field present in `fields` (not just a hardcoded list)
- Detects and renders ADF (Atlassian Document Format) fields as Markdown
- Scans all rendered text for Figma URLs and deduplicates them
- Downloads or lists all file attachments into `.jira/<KEY>/attachments/`
- Writes `.jira/<KEY>/ticket.md` — the main structured output

## Step 4 — Output location

By default, all output goes to `.jira/<KEY>/`:

```
.jira/
└── SHOP-2124/
    ├── ticket.md          ← structured Markdown of the full ticket
    ├── attachments/       ← downloaded binary files (images, PDFs, etc.)
    └── raw.json           ← copy of the raw API response for debugging
```

If the user requests a specific output location or format in their prompt, honour that instead. Examples:
- "save to /tmp/SHOP-2124.md" → write there
- "just show me the ticket" → print ticket.md to the conversation, skip the file write
- "paste the business rules" → print only the BUSINESS RULES section

## Step 5 — Confirm to the user

After writing files, report:

```
Fetched SHOP-2124: <summary>
Output: .jira/SHOP-2124/ticket.md
Figma URLs found: <N>
Attachments: <N> files
```

If there are Figma URLs, list them explicitly so the user can see them at a glance.

---

## Known Club Med custom fields

These fields are common in Club Med Jira projects. The script will still extract *any* custom field present on the issue — this table is just reference context for how to label them in the output:

| Field ID            | Label            |
| ------------------- | ---------------- |
| `customfield_11553` | User Story       |
| `customfield_11554` | Business Rules   |
| `customfield_11556` | QA Scenarios     |
| `customfield_12207` | API Resources    |
| `customfield_12208` | Design Notes     |
| `customfield_11563` | Figma URL        |
| `customfield_11547` | DOR              |

For fields not in this table, use the `name` from the field schema or fall back to the raw field ID as the section heading.

---

## Error handling

| Situation | Action |
|-----------|--------|
| Auth error or 401 | Print `ERROR: auth failed — run \`jira login\` or check MCP credentials` |
| Ticket not found (404) | Print `ERROR: <KEY> not found — verify the key and project access` |
| ADF rendering fails | Fall back to raw JSON string for that field, note the fallback in output |
| Attachment download fails | Log the attachment name and URL in ticket.md under a "Failed downloads" note |
