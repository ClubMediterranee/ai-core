---
name: export-claude-session
description: Export the current Claude Code session to Markdown, JSON, or a beautiful self-contained HTML file — with agent threads, token counts, and tool call badges. Claude Code only.
argument-hint: "[output-path] [--format markdown|json|html|pdf] [--title '...'] [--include-thinking] [--no-tools] [--no-agents]"
user-invocable: true
allowed-tools: Bash, Write, Read
---

# Export Conversation

Export the current Claude Code session from its JSONL source files to a readable format.
Agent / skill threads are inlined. Total tokens and per-thread token costs are shown.

## Arguments

```
ARGUMENTS: $ARGUMENTS
```

Parse from `$ARGUMENTS`:
- **Positional** `[output-path]` — where to write the file (optional; default: `~/conversation-YYYY-MM-DD-HH-MM.<ext>`)
- `--format markdown|json|html|pdf` — output format (default: `markdown`)
- `--title "..."` — document title (default: `"Conversation Export"`)
- `--include-thinking` — include internal thinking blocks (hidden by default)
- `--no-tools` — omit tool call details
- `--no-agents` — omit agent / skill thread sections

---

## Steps

### Step 1 — Write the export script to /tmp

Use the **Bash** tool to write and immediately run the following Python 3 script.
Inject the parsed argument values using environment variables (shown at the top of the script).

```bash
python3 - << 'PYEOF'
import sys, os, glob, json, html as H, subprocess
from datetime import datetime, timezone

# ── Config (injected as env vars by Claude before running) ─────────────
OUTPUT_PATH     = os.environ.get('CC_OUTPUT', '')
FORMAT          = os.environ.get('CC_FORMAT', 'markdown')       # markdown|json|html|pdf
TITLE           = os.environ.get('CC_TITLE', 'Conversation Export')
INC_THINKING    = os.environ.get('CC_THINKING', '0') == '1'
NO_TOOLS        = os.environ.get('CC_NO_TOOLS', '0') == '1'
NO_AGENTS       = os.environ.get('CC_NO_AGENTS', '0') == '1'
CWD             = os.environ.get('CC_CWD', os.getcwd())
SKILL_DIR       = os.path.expanduser('~/.claude/skills/export-claude-session')
TEMPLATE_PATH   = os.path.join(SKILL_DIR, 'conversation-template.html')

# ── Helpers ──────────────────────────────────────────────────────────────

def fmt_ts(ts_raw):
    if not ts_raw: return ''
    try:
        dt = datetime.fromisoformat(ts_raw.replace('Z', '+00:00'))
        return dt.strftime('%H:%M:%S')
    except:
        return ts_raw[:8] if len(ts_raw) >= 8 else ts_raw

def fmt_datetime(ts_raw):
    if not ts_raw: return ''
    try:
        dt = datetime.fromisoformat(ts_raw.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M UTC')
    except:
        return ts_raw

def load_jsonl(path):
    records = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try: records.append(json.loads(line))
                    except: pass
    except: pass
    return records

def find_session(cwd):
    slug = cwd.replace('/', '-')
    project_dir = os.path.expanduser(f'~/.claude/projects/{slug}')
    files = glob.glob(os.path.join(project_dir, '*.jsonl'))
    if not files:
        return None, None, None, None
    latest = max(files, key=os.path.getmtime)
    uuid   = os.path.splitext(os.path.basename(latest))[0]
    subagents_dir = os.path.join(project_dir, uuid, 'subagents')
    return latest, uuid, subagents_dir, project_dir

def extract_usage(record):
    """Return (input, output, cache_create, cache_read) tokens from a record."""
    u = record.get('message', {}).get('usage') or record.get('usage') or {}
    return (
        u.get('input_tokens', 0),
        u.get('output_tokens', 0),
        u.get('cache_creation_input_tokens', 0),
        u.get('cache_read_input_tokens', 0),
    )

def sum_usage(records):
    inp = out = cc = cr = 0
    for r in records:
        if r.get('type') == 'assistant':
            a, b, c, d = extract_usage(r)
            inp += a; out += b; cc += c; cr += d
    return {'input': inp, 'output': out, 'cache_create': cc, 'cache_read': cr,
            'total': inp + out}

# ── Build turns ──────────────────────────────────────────────────────────

def build_turns(records, subagents_dir=None):
    """
    Parse JSONL records into a list of turn dicts.
    Resolves Agent tool calls to their subagent JSONL files.

    Turn dict:
      role        : 'human' | 'assistant'
      text        : str
      ts          : 'HH:MM:SS'
      tools       : [str]        -- tool names used (assistant only)
      thinking    : str | None   -- thinking content if INC_THINKING
      agents      : [agent_dict] -- resolved agent threads
      usage       : {input, output, cache_create, cache_read, total}
    """
    # Two-pass: first collect all agentId lookups from tool_results
    agent_id_map = {}  # tool_use_id -> agentId
    for rec in records:
        if rec.get('type') == 'user':
            content = rec.get('message', {}).get('content', '')
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get('type') == 'tool_result':
                        tid  = block.get('tool_use_id', '')
                        aid  = (rec.get('toolUseResult') or {}).get('agentId')
                        if tid and aid:
                            agent_id_map[tid] = aid

    turns = []
    for rec in records:
        rtype = rec.get('type', '')

        if rtype in ('file-history-snapshot', 'progress', 'system'):
            continue

        ts = fmt_ts(rec.get('timestamp', ''))

        # ── Human turn ──────────────────────────────────────────────────
        if rtype == 'user':
            if rec.get('isMeta'): continue
            content = rec.get('message', {}).get('content', '')

            if isinstance(content, list):
                # Skip pure tool-result messages
                non_tr = [b for b in content
                          if isinstance(b, dict) and b.get('type') != 'tool_result']
                if not non_tr: continue
                texts = [b.get('text', '') for b in non_tr
                         if isinstance(b, dict) and b.get('type') == 'text']
                text = '\n'.join(t for t in texts if t).strip()
            else:
                text = (content or '').strip()

            if text:
                turns.append({
                    'role': 'human', 'text': text, 'ts': ts,
                    'tools': [], 'thinking': None, 'agents': [],
                    'usage': {'input': 0, 'output': 0, 'cache_create': 0, 'cache_read': 0, 'total': 0},
                })

        # ── Assistant turn ───────────────────────────────────────────────
        elif rtype == 'assistant':
            content = rec.get('message', {}).get('content', [])
            if not isinstance(content, list):
                content = [{'type': 'text', 'text': str(content)}] if content else []

            text_parts = []
            tools      = []
            thinking   = None
            agent_refs = []  # (tool_use_id, agent_type, prompt)

            for block in content:
                if not isinstance(block, dict): continue
                btype = block.get('type', '')

                if btype == 'text':
                    text_parts.append(block.get('text', ''))

                elif btype == 'thinking' and INC_THINKING:
                    thinking = block.get('thinking', '')

                elif btype == 'tool_use':
                    name    = block.get('name', '')
                    tool_id = block.get('id', '')
                    inp_    = block.get('input', {})

                    if name in ('Agent', 'Task') and not NO_AGENTS:
                        agent_refs.append({
                            'tool_id':    tool_id,
                            'agent_type': inp_.get('subagent_type', inp_.get('name', 'agent')),
                            'prompt':     inp_.get('prompt', ''),
                            'description': inp_.get('description', ''),
                        })
                    elif not NO_TOOLS:
                        tools.append(name)

            text  = '\n'.join(p for p in text_parts if p).strip()
            tools = list(dict.fromkeys(tools))  # dedupe, preserve order

            inp_tok, out_tok, cc_tok, cr_tok = extract_usage(rec)
            usage = {'input': inp_tok, 'output': out_tok,
                     'cache_create': cc_tok, 'cache_read': cr_tok,
                     'total': inp_tok + out_tok}

            # Resolve agent threads
            resolved_agents = []
            if subagents_dir and os.path.isdir(subagents_dir):
                for aref in agent_refs:
                    tid = aref['tool_id']
                    aid = agent_id_map.get(tid)
                    if not aid: continue

                    agent_type = aref['agent_type']
                    agent_desc = aref['description'] or aref['prompt'][:100]
                    meta_path  = os.path.join(subagents_dir, f'agent-{aid}.meta.json')
                    if os.path.exists(meta_path):
                        try:
                            meta = json.load(open(meta_path))
                            agent_type = meta.get('agentType', agent_type)
                            agent_desc = meta.get('description', agent_desc)
                        except: pass

                    # Load and build sub-turns (no nested agent resolution)
                    sub_path = os.path.join(subagents_dir, f'agent-{aid}.jsonl')
                    sub_records = load_jsonl(sub_path)
                    sub_turns   = build_turns(sub_records, subagents_dir=None)
                    sub_usage   = sum_usage(sub_records)

                    resolved_agents.append({
                        'agent_id':    aid,
                        'agent_type':  agent_type,
                        'description': agent_desc,
                        'turns':       sub_turns,
                        'usage':       sub_usage,
                    })

            if text or tools or resolved_agents:
                turns.append({
                    'role': 'assistant', 'text': text, 'ts': ts,
                    'tools': tools, 'thinking': thinking,
                    'agents': resolved_agents, 'usage': usage,
                })

    return turns

# ── Markdown formatter ───────────────────────────────────────────────────

def md_turns(turns, depth=0):
    lines = []
    h = '#' * (max(2, depth + 2))
    for t in turns:
        role_label = 'Human' if t['role'] == 'human' else 'Assistant'
        lines.append(f"{h} {role_label} *({t['ts']})*\n")

        if t['role'] == 'assistant':
            if t['tools']:
                lines.append('> Tools: ' + ', '.join(f'`{x}`' for x in t['tools']) + '\n')
            if t['usage']['total']:
                u = t['usage']
                lines.append(f"> Tokens: {u['input']:,} in · {u['output']:,} out"
                              + (f" · {u['cache_read']:,} cache-hit" if u['cache_read'] else '') + '\n')

        lines.append(t['text'] + '\n')

        if t['thinking']:
            lines.append('<details><summary>Thinking</summary>\n\n')
            lines.append('*' + t['thinking'].replace('\n', '  \n') + '*\n')
            lines.append('</details>\n')

        for agent in t.get('agents', []):
            u = agent['usage']
            tok_summary = f"{u['total']:,} tokens" if u['total'] else ''
            lines.append(f"<details><summary>Agent: <code>{agent['agent_type']}</code>"
                         f" — {agent['description'][:80]}"
                         + (f" · {tok_summary}" if tok_summary else '') + "</summary>\n\n")
            lines.extend(md_turns(agent['turns'], depth=depth+1))
            lines.append('</details>\n')

        lines.append('\n---\n\n')

    return lines

def render_markdown(turns, meta):
    u = meta['total_usage']
    lines = [
        f"# {TITLE}\n\n",
        f"> **Project:** {meta['project_name']}  ",
        f"**Branch:** `{meta['git_branch']}`  ",
        f"**Session:** `{meta['session_id'][:8]}…`  ",
        f"**Exported:** {meta['export_date']}\n\n",
        f"> **Tokens (session):** {u['input']:,} in · {u['output']:,} out"
        + (f" · {u['cache_read']:,} cache-hit" if u['cache_read'] else '')
        + f" · **{u['total']:,} total**\n\n",
        "---\n\n",
    ]
    lines.extend(md_turns(turns))
    return ''.join(lines)

# ── JSON formatter ────────────────────────────────────────────────────────

def render_json(turns, meta):
    return json.dumps({
        'metadata': meta,
        'messages': turns,
    }, indent=2, default=str, ensure_ascii=False)

# ── HTML formatter ────────────────────────────────────────────────────────

def e(s):
    """HTML-escape a string."""
    return H.escape(str(s), quote=True)

def render_tool_chips(tools):
    if not tools: return ''
    chips = ''.join(f'<span class="tool-chip">{e(t)}</span>' for t in tools)
    return f'<div class="tool-chips">{chips}</div>'

def render_usage_line(usage):
    if not usage or usage.get('total', 0) == 0: return ''
    u = usage
    parts = [f"{u['input']:,} in", f"{u['output']:,} out"]
    if u.get('cache_read'):
        parts.append(f"{u['cache_read']:,} cache-hit")
    return (
        f'<div class="token-line">'
        f'<span class="token-icon">◈</span>'
        + ' · '.join(parts) +
        f' <strong>= {u["total"]:,}</strong>'
        f'</div>'
    )

def render_thinking(text):
    return (
        f'<details class="thinking-block">'
        f'<summary>Internal reasoning</summary>'
        f'<div class="thinking-content">{e(text)}</div>'
        f'</details>'
    )

def render_agent_thread(agent):
    u = agent['usage']
    tok = f"{u['total']:,} tok" if u.get('total') else ''
    inner = render_turns_html(agent['turns'], nested=True)
    return (
        f'<details class="agent-thread">'
        f'<summary>'
        f'<svg class="agent-chevron" viewBox="0 0 16 16" fill="currentColor">'
        f'<path d="M6.22 3.22a.75.75 0 0 1 1.06 0l4.25 4.25a.75.75 0 0 1 0 1.06l-4.25 4.25a.75.75 0 0 1-1.06-1.06L9.94 8 6.22 4.28a.75.75 0 0 1 0-1.06z"/>'
        f'</svg>'
        f'<div class="agent-icon-badge">'
        f'<svg viewBox="0 0 16 16" fill="currentColor">'
        f'<path d="M8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0zM1.5 8a6.5 6.5 0 1 0 13 0 6.5 6.5 0 0 0-13 0zm4.879-2.773 4.264 2.559a.25.25 0 0 1 0 .428l-4.264 2.559A.25.25 0 0 1 6 10.559V5.442a.25.25 0 0 1 .379-.215z"/>'
        f'</svg>'
        f'</div>'
        f'<span class="agent-type-label">{e(agent["agent_type"])}</span>'
        f'<span class="agent-desc">{e(agent["description"][:90])}</span>'
        f'<span class="agent-thread-count">{e(tok)}</span>'
        f'</summary>'
        f'<div class="agent-messages">{inner}</div>'
        f'</details>'
    )

def text_to_html(text):
    """Convert plain text to HTML, preserving code fences as <pre><code>."""
    parts = re.split(r'(```(?:[a-z]*\n)?.*?```)', text, flags=re.DOTALL)
    out = []
    for part in parts:
        if part.startswith('```'):
            lang_match = re.match(r'```([a-z]*)\n?', part)
            lang = lang_match.group(1) if lang_match else ''
            code = re.sub(r'^```[a-z]*\n?', '', part)
            code = re.sub(r'```$', '', code)
            lang_badge = f'<span class="code-lang">{e(lang)}</span>' if lang else ''
            out.append(f'<pre>{lang_badge}<code>{e(code.rstrip())}</code></pre>')
        else:
            # Inline code
            inlined = re.sub(r'`([^`]+)`',
                             lambda m: f'<code>{e(m.group(1))}</code>', part)
            # Paragraphs
            paras = [p.strip() for p in inlined.split('\n\n') if p.strip()]
            out.append(''.join(f'<p>{p}</p>' for p in paras) if paras else '')
    return ''.join(out)

def render_turns_html(turns, nested=False):
    parts = []
    for t in turns:
        role = t['role']
        cls  = f'msg msg--{role}'
        avatar_label = 'H' if role == 'human' else 'C'
        role_label   = 'Human' if role == 'human' else 'Claude'

        header = (
            f'<div class="msg-header">'
            f'<div class="avatar avatar--{role}">{avatar_label}</div>'
            f'<span class="msg-role">{role_label}</span>'
            f'<span class="msg-ts">{e(t["ts"])}</span>'
            f'</div>'
        )

        inner = ''
        if role == 'assistant':
            inner += render_tool_chips(t.get('tools', []))
            inner += render_usage_line(t.get('usage'))
        inner += text_to_html(t['text'])
        if t.get('thinking'):
            inner += render_thinking(t['thinking'])

        bubble = f'<div class="msg-bubble">{inner}</div>'

        agent_html = ''.join(render_agent_thread(a) for a in t.get('agents', []))

        parts.append(f'<div class="{cls}">{header}{bubble}</div>{agent_html}')

    return '\n'.join(parts)

def render_html(turns, meta):
    # Load template
    try:
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            template = f.read()
        # Extract CSS
        css_match = re.search(r'<style>(.*?)</style>', template, re.DOTALL)
        css = css_match.group(1) if css_match else ''
    except:
        css = ''

    u  = meta['total_usage']
    messages_html = render_turns_html(turns)

    # Build stat cards
    agent_count = sum(len(t.get('agents', [])) for t in turns)

    tok_total  = f"{u['total']:,}"
    tok_detail = f"{u['input']:,} in · {u['output']:,} out"
    if u.get('cache_read'):
        tok_detail += f" · {u['cache_read']:,} cached"

    project_name = e(meta['project_name'])
    project_path = e(meta['project_path'])
    git_branch   = e(meta['git_branch'])
    session_id   = e(meta['session_id'])
    export_date  = e(meta['export_date'])

    # Extra CSS for token display
    extra_css = """
      .token-line {
        display: flex; align-items: center; gap: 5px;
        font-size: 11px; font-family: var(--font-mono);
        color: var(--accent-tool); opacity: 0.85;
        margin-bottom: 6px;
      }
      .token-icon { font-size: 9px; opacity: 0.6; }
      .stat-card .stat-number { font-size: 18px; }
      .stat-card.wide { grid-column: span 2; }
      .stat-card.tok-card { flex-direction: row; align-items: center; gap: 8px; }
      .tok-total { font-size: 20px; font-weight: 800; font-family: var(--font-mono); color: var(--accent-tool); }
      .tok-detail { font-size: 10px; color: var(--text-muted); font-family: var(--font-mono); line-height: 1.5; }
    """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{e(TITLE)}</title>
  <style>
  {css}
  {extra_css}
  </style>
</head>
<body>
<input type="checkbox" id="theme-toggle">
<div class="shell">

  <aside class="sidebar">
    <div class="sidebar-brand">
      <div class="brand-icon">
        <svg viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
          <polygon points="14,2 26,8 26,20 14,26 2,20 2,8" fill="none" stroke="var(--accent-assistant)" stroke-width="1.5"/>
          <polygon points="14,7 21,11 21,17 14,21 7,17 7,11" fill="var(--accent-assistant)" opacity="0.15"/>
          <circle cx="14" cy="14" r="3" fill="var(--accent-assistant)" opacity="0.8"/>
        </svg>
      </div>
      <div class="brand-text">
        <span class="brand-name">Session Export</span>
        <span class="brand-sub" title="{project_path}">{project_name}</span>
      </div>
      <label for="theme-toggle" class="theme-toggle-label" title="Toggle light/dark mode"></label>
    </div>

    <div class="sidebar-section">
      <div class="sidebar-section-label">Metadata</div>
      <div class="meta-row">
        <div class="meta-item">
          <span class="meta-label">Branch</span>
          <span class="meta-value highlight">{git_branch}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Session</span>
          <span class="meta-value" style="font-size:10px;opacity:.6">{session_id[:36]}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Exported</span>
          <span class="meta-value">{export_date}</span>
        </div>
      </div>
    </div>

    <div class="sidebar-section">
      <div class="sidebar-section-label">Stats</div>
      <div class="stat-row">
        <div class="stat-card">
          <span class="stat-number">{meta['message_count']}</span>
          <span class="stat-label">Messages</span>
        </div>
        <div class="stat-card">
          <span class="stat-number">{agent_count}</span>
          <span class="stat-label">Agents</span>
        </div>
        <div class="stat-card wide tok-card">
          <div>
            <div class="tok-total">{tok_total}</div>
            <div class="stat-label">Total Tokens</div>
          </div>
          <div class="tok-detail">{tok_detail}</div>
        </div>
      </div>
    </div>

    <div class="sidebar-legend">
      <div class="sidebar-section-label">Legend</div>
      <div class="legend-item"><span class="legend-dot" style="background:var(--accent-human)"></span>Human messages</div>
      <div class="legend-item"><span class="legend-dot" style="background:var(--accent-assistant)"></span>Claude responses</div>
      <div class="legend-item"><span class="legend-dot" style="background:var(--accent-agent)"></span>Agent / skill threads</div>
      <div class="legend-item"><span class="legend-dot" style="background:var(--accent-tool)"></span>Tool calls + tokens</div>
    </div>
  </aside>

  <div class="chat-main">
    <header class="chat-header">
      <span class="chat-title">{e(TITLE)}</span>
      <span class="branch-badge">
        <svg viewBox="0 0 16 16" fill="currentColor"><path d="M11.75 2.5a.75.75 0 1 0 1.5 0 .75.75 0 0 0-1.5 0zm.75 2.75a2.25 2.25 0 1 1-1.5-2.122V5c0 .414-.336.75-.75.75H5a.75.75 0 0 0-.75.75v3.372a2.25 2.25 0 1 1-1.5.003V6.5A2.25 2.25 0 0 1 5 4.25h4.75V4.628A2.251 2.251 0 0 1 12.5 5.25z"/></svg>
        {git_branch}
      </span>
    </header>
    <div class="messages">
      {messages_html}
    </div>
  </div>

</div>
</body>
</html>"""

# ── PDF formatter (via weasyprint or browser-print fallback) ─────────────

def render_pdf(turns, meta, output_path):
    # Generate HTML first
    html_content = render_html(turns, meta)
    html_path    = output_path.replace('.pdf', '.html')

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # Try weasyprint
    try:
        import weasyprint
        weasyprint.HTML(filename=html_path).write_pdf(output_path)
        os.remove(html_path)
        return output_path, None
    except ImportError:
        pass

    # Try wkhtmltopdf
    try:
        result = subprocess.run(
            ['wkhtmltopdf', '--quiet', html_path, output_path],
            capture_output=True, timeout=60
        )
        if result.returncode == 0:
            os.remove(html_path)
            return output_path, None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback: keep HTML, instruct user
    return html_path, (
        "PDF converter not found. Install weasyprint (pip install weasyprint) "
        "or wkhtmltopdf to generate PDF. Saved as HTML instead."
    )

# ── Main ─────────────────────────────────────────────────────────────────

def main():
    # Locate session
    jsonl_path, session_uuid, subagents_dir, project_dir = find_session(CWD)
    if not jsonl_path:
        print(f"ERROR: No session found for project: {CWD}", file=sys.stderr)
        sys.exit(1)

    # Parse
    records       = load_jsonl(jsonl_path)
    total_usage   = sum_usage(records)
    turns         = build_turns(records, subagents_dir if os.path.isdir(subagents_dir or '') else None)
    human_turns   = [t for t in turns if t['role'] == 'human']

    # Git branch from first record that has it
    git_branch = next(
        (r.get('gitBranch', '') for r in records if r.get('gitBranch')), ''
    )
    project_name = os.path.basename(CWD)
    export_date  = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    meta = {
        'project_name':  project_name,
        'project_path':  CWD,
        'git_branch':    git_branch,
        'session_id':    session_uuid,
        'export_date':   export_date,
        'message_count': len(human_turns),
        'total_usage':   total_usage,
    }

    # Determine output path
    ext_map = {'markdown': 'md', 'json': 'json', 'html': 'html', 'pdf': 'pdf'}
    ext = ext_map.get(FORMAT, 'md')
    if OUTPUT_PATH:
        out_path = os.path.expanduser(OUTPUT_PATH)
    else:
        stamp    = datetime.now().strftime('%Y-%m-%d-%H-%M')
        out_path = os.path.expanduser(f'~/{project_name}-{stamp}.{ext}')

    # Render
    warning = None
    if FORMAT == 'markdown':
        content = render_markdown(turns, meta)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(content)

    elif FORMAT == 'json':
        content = render_json(turns, meta)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(content)

    elif FORMAT == 'html':
        content = render_html(turns, meta)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(content)

    elif FORMAT == 'pdf':
        out_path, warning = render_pdf(turns, meta, out_path)

    else:
        print(f"ERROR: Unknown format '{FORMAT}'", file=sys.stderr)
        sys.exit(1)

    u = total_usage
    print(f"EXPORT_PATH={out_path}")
    print(f"TOKENS_TOTAL={u['total']:,}")
    print(f"TOKENS_DETAIL={u['input']:,} in · {u['output']:,} out" +
          (f" · {u['cache_read']:,} cache-hit" if u['cache_read'] else ''))
    if warning:
        print(f"WARNING={warning}")

main()
PYEOF
```

---

### Step 2 — Run the script with the correct env vars

Before running, set the environment variables based on the parsed arguments:

```bash
CC_OUTPUT="<resolved-output-path-or-empty>"  \
CC_FORMAT="<markdown|json|html|pdf>"         \
CC_TITLE="<title>"                           \
CC_THINKING="<1-or-0>"                       \
CC_NO_TOOLS="<1-or-0>"                       \
CC_NO_AGENTS="<1-or-0>"                      \
CC_CWD="$(pwd)"                              \
python3 - << 'PYEOF'
... (paste the script above) ...
PYEOF
```

Capture stdout. Parse `EXPORT_PATH=`, `TOKENS_TOTAL=`, `TOKENS_DETAIL=`, and `WARNING=` lines from output.

---

### Step 3 — Report result

After the script completes, tell the user:

```
Exported to: <EXPORT_PATH>
Tokens: <TOKENS_DETAIL> — <TOKENS_TOTAL> total
```

If there is a `WARNING=` line, display it.

If format is `html`, suggest opening the file:
```
open <EXPORT_PATH>
```

---

## Examples

```
/export-conversation
/export-conversation ~/Desktop/my-session.md
/export-conversation --format html ~/Desktop/session.html
/export-conversation --format json --no-agents
/export-conversation --format pdf --title "PRD-014 review"
/export-conversation --include-thinking --no-tools
```

---

## Notes

- **PDF**: Requires `weasyprint` (`pip install weasyprint`) or `wkhtmltopdf` on PATH.
  Without either, the HTML file is saved and a fallback message shown.
  For `@react-pdf/renderer`-based PDF, run `/skill-creator` to create a dedicated `pdf-export` skill.
- **Token counts**: Summed from `usage.output_tokens` + `usage.input_tokens` in assistant records.
  Cache-read tokens (`cache_read_input_tokens`) are shown separately as they incur reduced cost.
- **Agent threads**: Resolved from `~/.claude/projects/<slug>/<uuid>/subagents/agent-*.jsonl`.
  Each thread shows its own token footprint.
- **Template**: The HTML output reads CSS from `~/.claude/skills/export-conversation/conversation-template.html`.
  Edit that file to customise the visual design.

---

**BEGIN EXPORT**

Parse `$ARGUMENTS`, set environment variables, run the Python script via Bash, then report the result.
