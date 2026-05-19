"""Entry point for the export-session skill.

Reads EXP_* env vars (set by SKILL.md from $ARGUMENTS), picks a provider,
builds the IR, renders, writes the file, prints summary lines stdout-side.

Env vars:
  EXP_OUTPUT    output path (optional; default: ~/<project>-<stamp>.<ext>)
  EXP_FORMAT    markdown | json | html | pdf      (default: markdown)
  EXP_TITLE     document title                    (default: Conversation Export)
  EXP_THINKING  '1' to include thinking blocks    (default: 0)
  EXP_NO_TOOLS  '1' to omit tool call details     (default: 0)
  EXP_NO_AGENTS '1' to omit agent thread sections (default: 0)
  EXP_CWD       working directory                  (default: $PWD)
  EXP_PROVIDER  provider override (claude-code)    (default: auto-detect)
"""
import os
import sys
from datetime import datetime

import renderers
from providers import detect_provider


SKILL_DIR     = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(SKILL_DIR, 'conversation-template.html')

EXT_MAP = {'markdown': 'md', 'json': 'json', 'html': 'html', 'pdf': 'pdf'}


def main():
    output_path   = os.environ.get('EXP_OUTPUT', '')
    fmt           = os.environ.get('EXP_FORMAT', 'markdown')
    title         = os.environ.get('EXP_TITLE', 'Conversation Export')
    inc_thinking  = os.environ.get('EXP_THINKING', '0') == '1'
    no_tools      = os.environ.get('EXP_NO_TOOLS', '0') == '1'
    no_agents     = os.environ.get('EXP_NO_AGENTS', '0') == '1'
    cwd           = os.environ.get('EXP_CWD', os.getcwd())
    provider_name = os.environ.get('EXP_PROVIDER') or None

    if fmt not in EXT_MAP:
        print(f"ERROR: Unknown format '{fmt}'", file=sys.stderr)
        sys.exit(1)

    try:
        provider = detect_provider(cwd, provider_name)
    except (ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    session = provider.find_session(cwd)
    if session is None:
        print(f"ERROR: No {provider.name} session found for: {cwd}", file=sys.stderr)
        sys.exit(1)

    turns = provider.build_turns(
        session,
        include_thinking=inc_thinking,
        no_tools=no_tools,
        no_agents=no_agents,
    )
    meta = provider.get_metadata(session, turns)

    if output_path:
        out_path = os.path.expanduser(output_path)
    else:
        stamp = datetime.now().strftime('%Y-%m-%d-%H-%M')
        ext   = EXT_MAP[fmt]
        out_path = os.path.expanduser(f"~/{meta['project_name']}-{stamp}.{ext}")

    warning = None
    if fmt == 'markdown':
        content = renderers.render_markdown(turns, meta, title)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(content)
    elif fmt == 'json':
        content = renderers.render_json(turns, meta, title)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(content)
    elif fmt == 'html':
        content = renderers.render_html(turns, meta, title, TEMPLATE_PATH)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(content)
    elif fmt == 'pdf':
        out_path, warning = renderers.render_pdf(
            turns, meta, title, TEMPLATE_PATH, out_path,
        )

    u = meta['total_usage']
    cache = f" · {u['cache_read']:,} cache-hit" if u['cache_read'] else ''
    print(f"EXPORT_PATH={out_path}")
    print(f"PROVIDER={provider.name}")
    print(f"TOKENS_TOTAL={u['total']:,}")
    print(f"TOKENS_DETAIL={u['input']:,} in · {u['output']:,} out{cache}")
    if warning:
        print(f"WARNING={warning}")


if __name__ == '__main__':
    main()
