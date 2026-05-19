"""Claude Code provider.

Reads JSONL transcripts from ~/.claude/projects/<cwd-slug>/*.jsonl and resolves
nested sub-agent threads from .../subagents/agent-<id>.jsonl + .meta.json.
"""
import glob
import json
import os
from datetime import datetime, timezone

from .base import Provider


def _fmt_ts(ts_raw: str) -> str:
    if not ts_raw:
        return ''
    try:
        dt = datetime.fromisoformat(ts_raw.replace('Z', '+00:00'))
        return dt.strftime('%H:%M:%S')
    except Exception:
        return ts_raw[:8] if len(ts_raw) >= 8 else ts_raw


def _load_jsonl(path: str) -> list:
    records = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        pass
    return records


def _extract_usage(record: dict):
    u = record.get('message', {}).get('usage') or record.get('usage') or {}
    return (
        u.get('input_tokens', 0),
        u.get('output_tokens', 0),
        u.get('cache_creation_input_tokens', 0),
        u.get('cache_read_input_tokens', 0),
    )


def _sum_usage(records: list) -> dict:
    inp = out = cc = cr = 0
    for r in records:
        if r.get('type') == 'assistant':
            a, b, c, d = _extract_usage(r)
            inp += a
            out += b
            cc += c
            cr += d
    return {
        'input': inp, 'output': out,
        'cache_create': cc, 'cache_read': cr,
        'total': inp + out,
    }


def _project_dir(cwd: str) -> str:
    slug = cwd.replace('/', '-')
    return os.path.expanduser(f'~/.claude/projects/{slug}')


class ClaudeCodeProvider(Provider):
    name = 'claude-code'

    @classmethod
    def detect(cls, cwd: str) -> bool:
        return bool(glob.glob(os.path.join(_project_dir(cwd), '*.jsonl')))

    def find_session(self, cwd: str):
        project_dir = _project_dir(cwd)
        files = glob.glob(os.path.join(project_dir, '*.jsonl'))
        if not files:
            return None
        latest = max(files, key=os.path.getmtime)
        uuid = os.path.splitext(os.path.basename(latest))[0]
        subagents_dir = os.path.join(project_dir, uuid, 'subagents')
        return {
            'cwd':            cwd,
            'jsonl_path':     latest,
            'session_uuid':   uuid,
            'subagents_dir':  subagents_dir if os.path.isdir(subagents_dir) else None,
            'project_dir':    project_dir,
            'records':        _load_jsonl(latest),
        }

    def build_turns(self, session, *, include_thinking, no_tools, no_agents):
        return self._build_turns(
            session['records'],
            session.get('subagents_dir'),
            include_thinking=include_thinking,
            no_tools=no_tools,
            no_agents=no_agents,
        )

    def _build_turns(self, records, subagents_dir, *, include_thinking,
                     no_tools, no_agents):
        # Two-pass: first collect agentId lookups from tool_result blocks.
        agent_id_map = {}
        for rec in records:
            if rec.get('type') != 'user':
                continue
            content = rec.get('message', {}).get('content', '')
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get('type') != 'tool_result':
                    continue
                tid = block.get('tool_use_id', '')
                tur = rec.get('toolUseResult')
                aid = tur.get('agentId') if isinstance(tur, dict) else None
                if tid and aid:
                    agent_id_map[tid] = aid

        turns = []
        for rec in records:
            rtype = rec.get('type', '')
            if rtype in ('file-history-snapshot', 'progress', 'system'):
                continue

            ts = _fmt_ts(rec.get('timestamp', ''))

            if rtype == 'user':
                if rec.get('isMeta'):
                    continue
                content = rec.get('message', {}).get('content', '')
                if isinstance(content, list):
                    non_tr = [
                        b for b in content
                        if isinstance(b, dict) and b.get('type') != 'tool_result'
                    ]
                    if not non_tr:
                        continue
                    texts = [
                        b.get('text', '') for b in non_tr
                        if isinstance(b, dict) and b.get('type') == 'text'
                    ]
                    text = '\n'.join(t for t in texts if t).strip()
                else:
                    text = (content or '').strip()

                if text:
                    turns.append({
                        'role': 'human', 'text': text, 'ts': ts,
                        'tools': [], 'thinking': None, 'agents': [],
                        'usage': {'input': 0, 'output': 0,
                                  'cache_create': 0, 'cache_read': 0, 'total': 0},
                    })

            elif rtype == 'assistant':
                content = rec.get('message', {}).get('content', [])
                if not isinstance(content, list):
                    content = [{'type': 'text', 'text': str(content)}] if content else []

                text_parts = []
                tools = []
                thinking = None
                agent_refs = []

                for block in content:
                    if not isinstance(block, dict):
                        continue
                    btype = block.get('type', '')
                    if btype == 'text':
                        text_parts.append(block.get('text', ''))
                    elif btype == 'thinking' and include_thinking:
                        thinking = block.get('thinking', '')
                    elif btype == 'tool_use':
                        name = block.get('name', '')
                        tool_id = block.get('id', '')
                        inp_ = block.get('input', {})
                        if name in ('Agent', 'Task') and not no_agents:
                            agent_refs.append({
                                'tool_id':     tool_id,
                                'agent_type':  inp_.get('subagent_type', inp_.get('name', 'agent')),
                                'prompt':      inp_.get('prompt', ''),
                                'description': inp_.get('description', ''),
                            })
                        elif not no_tools:
                            tools.append(name)

                text = '\n'.join(p for p in text_parts if p).strip()
                tools = list(dict.fromkeys(tools))

                inp_tok, out_tok, cc_tok, cr_tok = _extract_usage(rec)
                usage = {
                    'input': inp_tok, 'output': out_tok,
                    'cache_create': cc_tok, 'cache_read': cr_tok,
                    'total': inp_tok + out_tok,
                }

                resolved_agents = []
                if subagents_dir and os.path.isdir(subagents_dir):
                    for aref in agent_refs:
                        tid = aref['tool_id']
                        aid = agent_id_map.get(tid)
                        if not aid:
                            continue

                        agent_type = aref['agent_type']
                        agent_desc = aref['description'] or aref['prompt'][:100]
                        meta_path = os.path.join(subagents_dir, f'agent-{aid}.meta.json')
                        if os.path.exists(meta_path):
                            try:
                                meta = json.load(open(meta_path))
                                agent_type = meta.get('agentType', agent_type)
                                agent_desc = meta.get('description', agent_desc)
                            except Exception:
                                pass

                        sub_path = os.path.join(subagents_dir, f'agent-{aid}.jsonl')
                        sub_records = _load_jsonl(sub_path)
                        sub_turns = self._build_turns(
                            sub_records,
                            subagents_dir=None,
                            include_thinking=include_thinking,
                            no_tools=no_tools,
                            no_agents=no_agents,
                        )
                        sub_usage = _sum_usage(sub_records)

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

    def get_metadata(self, session, turns):
        records = session['records']
        cwd = session['cwd']
        git_branch = next(
            (r.get('gitBranch', '') for r in records if r.get('gitBranch')), ''
        )
        human_turns = [t for t in turns if t['role'] == 'human']
        return {
            'project_name':  os.path.basename(cwd),
            'project_path':  cwd,
            'git_branch':    git_branch,
            'session_id':    session['session_uuid'],
            'export_date':   datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
            'message_count': len(human_turns),
            'total_usage':   _sum_usage(records),
        }
