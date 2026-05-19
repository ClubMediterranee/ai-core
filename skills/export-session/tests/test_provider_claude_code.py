"""Tests for providers.claude_code — Claude Code session parser."""
import json
import os
import shutil
import tempfile
import unittest
from unittest import mock

from . import _path  # noqa: F401 — sys.path bootstrap
from providers import claude_code as cc
from providers.claude_code import ClaudeCodeProvider


# ── Fixtures ──────────────────────────────────────────────────────────────

def _user_record(text, ts='2026-05-19T10:00:00Z', is_meta=False):
    return {
        'type': 'user',
        'timestamp': ts,
        'isMeta': is_meta,
        'message': {'content': [{'type': 'text', 'text': text}]},
    }


def _assistant_record(text=None, tools=None, thinking=None,
                      ts='2026-05-19T10:00:01Z',
                      input_tokens=10, output_tokens=20,
                      cache_create=0, cache_read=5,
                      git_branch=None):
    content = []
    if thinking:
        content.append({'type': 'thinking', 'thinking': thinking})
    if text:
        content.append({'type': 'text', 'text': text})
    for tool in (tools or []):
        content.append({
            'type': 'tool_use',
            'id': f'tool_{tool}_{len(content)}',
            'name': tool,
            'input': {},
        })
    rec = {
        'type': 'assistant',
        'timestamp': ts,
        'message': {
            'content': content,
            'usage': {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'cache_creation_input_tokens': cache_create,
                'cache_read_input_tokens': cache_read,
            },
        },
    }
    if git_branch:
        rec['gitBranch'] = git_branch
    return rec


def _tool_result_record(tool_use_id, agent_id=None,
                        tool_use_result_is_string=False):
    rec = {
        'type': 'user',
        'message': {
            'content': [{
                'type': 'tool_result',
                'tool_use_id': tool_use_id,
                'content': 'result body',
            }],
        },
    }
    if tool_use_result_is_string:
        rec['toolUseResult'] = 'a-plain-string-not-a-dict'
    elif agent_id is not None:
        rec['toolUseResult'] = {'agentId': agent_id}
    return rec


# ── Pure-function tests ───────────────────────────────────────────────────

class TestFmtTs(unittest.TestCase):
    def test_iso_zulu(self):
        self.assertEqual(cc._fmt_ts('2026-05-19T10:30:45Z'), '10:30:45')

    def test_empty(self):
        self.assertEqual(cc._fmt_ts(''), '')

    def test_garbage_falls_back_to_prefix(self):
        self.assertEqual(cc._fmt_ts('garbage!'), 'garbage!')


class TestExtractUsage(unittest.TestCase):
    def test_reads_message_usage(self):
        rec = {'message': {'usage': {
            'input_tokens': 1, 'output_tokens': 2,
            'cache_creation_input_tokens': 3, 'cache_read_input_tokens': 4,
        }}}
        self.assertEqual(cc._extract_usage(rec), (1, 2, 3, 4))

    def test_falls_back_to_top_level_usage(self):
        rec = {'usage': {'input_tokens': 5, 'output_tokens': 6}}
        self.assertEqual(cc._extract_usage(rec), (5, 6, 0, 0))

    def test_missing_returns_zeros(self):
        self.assertEqual(cc._extract_usage({}), (0, 0, 0, 0))


class TestSumUsage(unittest.TestCase):
    def test_sums_only_assistant_records(self):
        recs = [
            _assistant_record(input_tokens=10, output_tokens=20, cache_read=3),
            _user_record('hi'),
            _assistant_record(input_tokens=5, output_tokens=15, cache_read=7),
        ]
        u = cc._sum_usage(recs)
        self.assertEqual(u, {'input': 15, 'output': 35,
                             'cache_create': 0, 'cache_read': 10,
                             'total': 50})


# ── build_turns ───────────────────────────────────────────────────────────

class TestBuildTurns(unittest.TestCase):
    def setUp(self):
        self.provider = ClaudeCodeProvider()

    def _build(self, records, subagents_dir=None, **flags):
        defaults = {'include_thinking': False,
                    'no_tools': False, 'no_agents': False}
        defaults.update(flags)
        return self.provider._build_turns(records, subagents_dir, **defaults)

    def test_basic_human_then_assistant(self):
        turns = self._build([
            _user_record('hello'),
            _assistant_record(text='hi back'),
        ])
        self.assertEqual([t['role'] for t in turns], ['human', 'assistant'])
        self.assertEqual(turns[0]['text'], 'hello')
        self.assertEqual(turns[1]['text'], 'hi back')

    def test_skips_meta_user_records(self):
        turns = self._build([
            _user_record('shown'),
            _user_record('hidden', is_meta=True),
        ])
        self.assertEqual(len(turns), 1)
        self.assertEqual(turns[0]['text'], 'shown')

    def test_skips_progress_and_snapshot_records(self):
        turns = self._build([
            {'type': 'file-history-snapshot'},
            {'type': 'progress'},
            {'type': 'system'},
            _user_record('only-real'),
        ])
        self.assertEqual(len(turns), 1)
        self.assertEqual(turns[0]['text'], 'only-real')

    def test_skips_pure_tool_result_messages(self):
        turns = self._build([_tool_result_record('tool_x')])
        self.assertEqual(turns, [])

    def test_extracts_tool_names_deduped(self):
        turns = self._build([
            _assistant_record(text='t', tools=['Read', 'Bash', 'Read']),
        ])
        self.assertEqual(turns[0]['tools'], ['Read', 'Bash'])

    def test_no_tools_flag_omits_tools(self):
        turns = self._build([
            _assistant_record(text='t', tools=['Read', 'Bash']),
        ], no_tools=True)
        self.assertEqual(turns[0]['tools'], [])

    def test_thinking_omitted_by_default(self):
        turns = self._build([_assistant_record(text='t', thinking='secret')])
        self.assertIsNone(turns[0]['thinking'])

    def test_thinking_included_when_flag_set(self):
        turns = self._build(
            [_assistant_record(text='t', thinking='secret')],
            include_thinking=True,
        )
        self.assertEqual(turns[0]['thinking'], 'secret')

    def test_usage_propagated(self):
        turns = self._build([_assistant_record(text='t',
                                               input_tokens=11,
                                               output_tokens=22,
                                               cache_read=3)])
        self.assertEqual(turns[0]['usage'], {
            'input': 11, 'output': 22,
            'cache_create': 0, 'cache_read': 3,
            'total': 33,
        })

    def test_empty_assistant_with_no_text_no_tools_no_agents_is_skipped(self):
        rec = {'type': 'assistant', 'message': {'content': [], 'usage': {}}}
        self.assertEqual(self._build([rec]), [])

    def test_string_content_for_user_record(self):
        rec = {'type': 'user',
               'message': {'content': 'plain string content'}}
        turns = self._build([rec])
        self.assertEqual(len(turns), 1)
        self.assertEqual(turns[0]['text'], 'plain string content')


class TestToolUseResultRegression(unittest.TestCase):
    """Regression: toolUseResult can be a string, not a dict — must not crash."""

    def test_string_tool_use_result_does_not_crash(self):
        provider = ClaudeCodeProvider()
        records = [
            _assistant_record(text='t', tools=['Bash']),
            _tool_result_record('tool_x', tool_use_result_is_string=True),
        ]
        turns = provider._build_turns(
            records, None,
            include_thinking=False, no_tools=False, no_agents=False,
        )
        self.assertEqual(len(turns), 1)  # assistant turn only

    def test_missing_tool_use_result_is_fine(self):
        provider = ClaudeCodeProvider()
        records = [
            _tool_result_record('tool_x', agent_id=None),  # no toolUseResult key
        ]
        # Should not raise
        turns = provider._build_turns(
            records, None,
            include_thinking=False, no_tools=False, no_agents=False,
        )
        self.assertEqual(turns, [])


# ── Agent thread resolution ───────────────────────────────────────────────

class TestAgentResolution(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.subagents_dir = os.path.join(self.tmpdir, 'subagents')
        os.makedirs(self.subagents_dir)
        # Sub-agent JSONL with 1 human + 1 assistant turn
        sub_recs = [
            _user_record('sub-question'),
            _assistant_record(text='sub-answer',
                              input_tokens=7, output_tokens=8),
        ]
        with open(os.path.join(self.subagents_dir, 'agent-aaa.jsonl'), 'w') as f:
            for r in sub_recs:
                f.write(json.dumps(r) + '\n')
        with open(os.path.join(self.subagents_dir, 'agent-aaa.meta.json'),
                  'w') as f:
            json.dump({'agentType': 'Explore',
                       'description': 'find things'}, f)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_agent_thread_resolved_and_inlined(self):
        provider = ClaudeCodeProvider()
        # Assistant calls an Agent tool, tool_result carries agentId 'aaa'
        records = [
            {
                'type': 'assistant',
                'timestamp': '2026-05-19T10:00:00Z',
                'message': {
                    'content': [
                        {'type': 'tool_use',
                         'id': 'tool_agent_1',
                         'name': 'Agent',
                         'input': {'subagent_type': 'Explore',
                                   'prompt': 'find stuff',
                                   'description': 'short desc'}},
                    ],
                    'usage': {},
                },
            },
            _tool_result_record('tool_agent_1', agent_id='aaa'),
        ]
        turns = provider._build_turns(
            records, self.subagents_dir,
            include_thinking=False, no_tools=False, no_agents=False,
        )
        self.assertEqual(len(turns), 1)
        agents = turns[0]['agents']
        self.assertEqual(len(agents), 1)
        self.assertEqual(agents[0]['agent_id'], 'aaa')
        # Metadata file overrides agent_type and description
        self.assertEqual(agents[0]['agent_type'], 'Explore')
        self.assertEqual(agents[0]['description'], 'find things')
        # Nested turns
        self.assertEqual(len(agents[0]['turns']), 2)
        self.assertEqual(agents[0]['turns'][0]['role'], 'human')
        self.assertEqual(agents[0]['turns'][1]['role'], 'assistant')
        # Usage summed from sub-records
        self.assertEqual(agents[0]['usage']['total'], 15)

    def test_no_agents_flag_omits_agent_threads(self):
        provider = ClaudeCodeProvider()
        records = [
            {'type': 'assistant',
             'message': {
                 'content': [
                     {'type': 'tool_use', 'id': 't1', 'name': 'Agent',
                      'input': {'subagent_type': 'Explore'}},
                 ],
                 'usage': {},
             }},
            _tool_result_record('t1', agent_id='aaa'),
        ]
        turns = provider._build_turns(
            records, self.subagents_dir,
            include_thinking=False, no_tools=False, no_agents=True,
        )
        # When no_agents is set, the Agent tool call is *not* resolved into a
        # nested thread; it falls back to being listed as a regular tool name.
        self.assertEqual(len(turns), 1)
        self.assertEqual(turns[0]['agents'], [])
        self.assertEqual(turns[0]['tools'], ['Agent'])

    def test_no_agents_and_no_tools_drops_agent_turn_entirely(self):
        provider = ClaudeCodeProvider()
        records = [
            {'type': 'assistant',
             'message': {
                 'content': [
                     {'type': 'tool_use', 'id': 't1', 'name': 'Agent',
                      'input': {'subagent_type': 'Explore'}},
                 ],
                 'usage': {},
             }},
            _tool_result_record('t1', agent_id='aaa'),
        ]
        turns = provider._build_turns(
            records, self.subagents_dir,
            include_thinking=False, no_tools=True, no_agents=True,
        )
        # No text, no tools, no agents → turn is fully dropped.
        self.assertEqual(turns, [])


# ── detect / find_session / get_metadata ───────────────────────────────────

class TestDetectAndFind(unittest.TestCase):
    def setUp(self):
        self.tmphome = tempfile.mkdtemp()
        # Patch _project_dir to map cwd → <tmphome>/projects/<slug>
        self.patch = mock.patch.object(
            cc, '_project_dir',
            lambda cwd: os.path.join(self.tmphome, 'projects',
                                     cwd.replace('/', '-')),
        )
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        shutil.rmtree(self.tmphome)

    def _seed_session(self, cwd, records, uuid='sess-uuid'):
        proj = os.path.join(self.tmphome, 'projects',
                            cwd.replace('/', '-'))
        os.makedirs(proj)
        path = os.path.join(proj, f'{uuid}.jsonl')
        with open(path, 'w') as f:
            for r in records:
                f.write(json.dumps(r) + '\n')
        return path

    def test_detect_false_when_no_session(self):
        self.assertFalse(ClaudeCodeProvider.detect('/no/such/cwd'))

    def test_detect_true_when_jsonl_present(self):
        cwd = '/work/proj-a'
        self._seed_session(cwd, [_user_record('hi')])
        self.assertTrue(ClaudeCodeProvider.detect(cwd))

    def test_find_session_returns_handle(self):
        cwd = '/work/proj-b'
        path = self._seed_session(cwd, [_user_record('hi')],
                                  uuid='abcd1234')
        handle = ClaudeCodeProvider().find_session(cwd)
        self.assertIsNotNone(handle)
        self.assertEqual(handle['cwd'], cwd)
        self.assertEqual(handle['jsonl_path'], path)
        self.assertEqual(handle['session_uuid'], 'abcd1234')
        self.assertIsNone(handle['subagents_dir'])  # no dir created
        self.assertEqual(len(handle['records']), 1)

    def test_find_session_returns_none_when_missing(self):
        self.assertIsNone(ClaudeCodeProvider().find_session('/no/such/cwd'))

    def test_get_metadata_schema(self):
        cwd = '/work/proj-c'
        self._seed_session(cwd, [
            _user_record('q1'),
            _assistant_record(text='a1', input_tokens=10, output_tokens=20,
                              git_branch='main'),
            _user_record('q2'),
        ])
        provider = ClaudeCodeProvider()
        handle = provider.find_session(cwd)
        turns = provider.build_turns(
            handle,
            include_thinking=False, no_tools=False, no_agents=False,
        )
        meta = provider.get_metadata(handle, turns)
        self.assertEqual(set(meta.keys()), {
            'project_name', 'project_path', 'git_branch',
            'session_id', 'export_date', 'message_count', 'total_usage',
        })
        self.assertEqual(meta['project_name'], 'proj-c')
        self.assertEqual(meta['project_path'], cwd)
        self.assertEqual(meta['git_branch'], 'main')
        self.assertEqual(meta['message_count'], 2)  # 2 humans
        self.assertEqual(meta['total_usage']['total'], 30)


if __name__ == '__main__':
    unittest.main()
