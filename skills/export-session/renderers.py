"""Provider-agnostic renderers — operate only on the IR from providers.base."""
import html as H
import os
import re
import subprocess
import json as _json


# ── Helpers ──────────────────────────────────────────────────────────────

def e(s) -> str:
    """HTML-escape a string."""
    return H.escape(str(s), quote=True)


# ── Markdown ─────────────────────────────────────────────────────────────

def _md_turns(turns, depth=0):
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
                cache = f" · {u['cache_read']:,} cache-hit" if u['cache_read'] else ''
                lines.append(f"> Tokens: {u['input']:,} in · {u['output']:,} out{cache}\n")

        lines.append(t['text'] + '\n')

        if t['thinking']:
            lines.append('<details><summary>Thinking</summary>\n\n')
            lines.append('*' + t['thinking'].replace('\n', '  \n') + '*\n')
            lines.append('</details>\n')

        for agent in t.get('agents', []):
            u = agent['usage']
            tok_summary = f"{u['total']:,} tokens" if u['total'] else ''
            tok_part = f" · {tok_summary}" if tok_summary else ''
            lines.append(
                f"<details><summary>Agent: <code>{agent['agent_type']}</code>"
                f" — {agent['description'][:80]}{tok_part}</summary>\n\n"
            )
            lines.extend(_md_turns(agent['turns'], depth=depth + 1))
            lines.append('</details>\n')

        lines.append('\n---\n\n')
    return lines


def render_markdown(turns, meta, title):
    u = meta['total_usage']
    cache = f" · {u['cache_read']:,} cache-hit" if u['cache_read'] else ''
    lines = [
        f"# {title}\n\n",
        f"> **Project:** {meta['project_name']}  ",
        f"**Branch:** `{meta['git_branch']}`  ",
        f"**Session:** `{meta['session_id'][:8]}…`  ",
        f"**Exported:** {meta['export_date']}\n\n",
        f"> **Tokens (session):** {u['input']:,} in · {u['output']:,} out{cache}"
        f" · **{u['total']:,} total**\n\n",
        "---\n\n",
    ]
    lines.extend(_md_turns(turns))
    return ''.join(lines)


# ── JSON ─────────────────────────────────────────────────────────────────

def render_json(turns, meta, title):
    return _json.dumps(
        {'metadata': meta, 'title': title, 'messages': turns},
        indent=2, default=str, ensure_ascii=False,
    )


# ── HTML ─────────────────────────────────────────────────────────────────

def _render_tool_chips(tools):
    if not tools:
        return ''
    chips = ''.join(f'<span class="tool-chip">{e(t)}</span>' for t in tools)
    return f'<div class="tool-chips">{chips}</div>'


def _render_usage_line(usage):
    if not usage or usage.get('total', 0) == 0:
        return ''
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


def _render_thinking(text):
    return (
        f'<details class="thinking-block">'
        f'<summary>Internal reasoning</summary>'
        f'<div class="thinking-content">{e(text)}</div>'
        f'</details>'
    )


def _render_agent_thread(agent):
    u = agent['usage']
    tok = f"{u['total']:,} tok" if u.get('total') else ''
    inner = _render_turns_html(agent['turns'], nested=True)
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


def _text_to_html(text):
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
            # Escape first, then re-introduce <code> for backticked segments.
            # html.escape leaves backticks intact, so the regex still matches.
            escaped = e(part)
            inlined = re.sub(
                r'`([^`]+)`',
                lambda m: f'<code>{m.group(1)}</code>',
                escaped,
            )
            paras = [p.strip() for p in inlined.split('\n\n') if p.strip()]
            out.append(''.join(f'<p>{p}</p>' for p in paras) if paras else '')
    return ''.join(out)


def _render_turns_html(turns, nested=False):
    parts = []
    for t in turns:
        role = t['role']
        cls = f'msg msg--{role}'
        avatar_label = 'H' if role == 'human' else 'C'
        role_label = 'Human' if role == 'human' else 'Claude'

        header = (
            f'<div class="msg-header">'
            f'<div class="avatar avatar--{role}">{avatar_label}</div>'
            f'<span class="msg-role">{role_label}</span>'
            f'<span class="msg-ts">{e(t["ts"])}</span>'
            f'</div>'
        )

        inner = ''
        if role == 'assistant':
            inner += _render_tool_chips(t.get('tools', []))
            inner += _render_usage_line(t.get('usage'))
        inner += _text_to_html(t['text'])
        if t.get('thinking'):
            inner += _render_thinking(t['thinking'])

        bubble = f'<div class="msg-bubble">{inner}</div>'
        agent_html = ''.join(_render_agent_thread(a) for a in t.get('agents', []))
        parts.append(f'<div class="{cls}">{header}{bubble}</div>{agent_html}')

    return '\n'.join(parts)


_EXTRA_CSS = """
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


def render_html(turns, meta, title, template_path):
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        css_match = re.search(r'<style>(.*?)</style>', template, re.DOTALL)
        css = css_match.group(1) if css_match else ''
    except Exception:
        css = ''

    u = meta['total_usage']
    messages_html = _render_turns_html(turns)
    agent_count = sum(len(t.get('agents', [])) for t in turns)

    tok_total = f"{u['total']:,}"
    tok_detail = f"{u['input']:,} in · {u['output']:,} out"
    if u.get('cache_read'):
        tok_detail += f" · {u['cache_read']:,} cached"

    project_name = e(meta['project_name'])
    project_path = e(meta['project_path'])
    git_branch   = e(meta['git_branch'])
    session_id   = e(meta['session_id'])
    export_date  = e(meta['export_date'])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{e(title)}</title>
  <style>
  {css}
  {_EXTRA_CSS}
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
      <span class="chat-title">{e(title)}</span>
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


# ── PDF (weasyprint → wkhtmltopdf fallback) ───────────────────────────────

def render_pdf(turns, meta, title, template_path, output_path):
    html_content = render_html(turns, meta, title, template_path)
    html_path = output_path.replace('.pdf', '.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    try:
        import weasyprint
        weasyprint.HTML(filename=html_path).write_pdf(output_path)
        os.remove(html_path)
        return output_path, None
    except ImportError:
        pass

    try:
        result = subprocess.run(
            ['wkhtmltopdf', '--quiet', html_path, output_path],
            capture_output=True, timeout=60,
        )
        if result.returncode == 0:
            os.remove(html_path)
            return output_path, None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return html_path, (
        "PDF converter not found. Install weasyprint (pip install weasyprint) "
        "or wkhtmltopdf to generate PDF. Saved as HTML instead."
    )
