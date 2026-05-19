"""Tests for renderers.py — provider-agnostic output formatting."""
import json
import os
import tempfile
import unittest

from . import _path  # noqa: F401 — sys.path bootstrap
import renderers


def _human_turn(text='hi', ts='10:00:00'):
    return {
        'role': 'human', 'text': text, 'ts': ts,
        'tools': [], 'thinking': None, 'agents': [],
        'usage': {'input': 0, 'output': 0,
                  'cache_create': 0, 'cache_read': 0, 'total': 0},
    }


def _assistant_turn(text='ok', tools=None, agents=None, thinking=None,
                    ts='10:00:01', total=100):
    return {
        'role': 'assistant', 'text': text, 'ts': ts,
        'tools': tools or [], 'thinking': thinking, 'agents': agents or [],
        'usage': {'input': 10, 'output': 90,
                  'cache_create': 0, 'cache_read': 5, 'total': total},
    }


def _meta(branch='main', total=100):
    return {
        'project_name':  'demo',
        'project_path':  '/tmp/demo',
        'git_branch':    branch,
        'session_id':    'abcd1234-0000-0000-0000-000000000000',
        'export_date':   '2026-05-19 15:00 UTC',
        'message_count': 1,
        'total_usage':   {'input': 10, 'output': 90,
                          'cache_create': 0, 'cache_read': 5, 'total': total},
    }


class TestEscape(unittest.TestCase):
    def test_escapes_lt_gt_amp_quote(self):
        self.assertEqual(renderers.e('<a&b">'), '&lt;a&amp;b&quot;&gt;')

    def test_stringifies_non_strings(self):
        self.assertEqual(renderers.e(42), '42')


class TestTextToHtmlXSS(unittest.TestCase):
    """Critical security regression tests for the XSS fix."""

    def test_raw_script_tag_is_escaped(self):
        html = renderers._text_to_html('hello <script>alert(1)</script> world')
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertIn('&lt;/script&gt;', html)

    def test_img_onerror_payload_is_escaped(self):
        payload = '<img src=x onerror=alert(document.cookie)>'
        html = renderers._text_to_html(payload)
        self.assertNotIn('<img src=x onerror=', html)
        self.assertIn('&lt;img src=x onerror=', html)

    def test_double_quote_attributes_are_escaped(self):
        html = renderers._text_to_html('<a href="javascript:alert(1)">x</a>')
        self.assertNotIn('<a href=', html)
        self.assertIn('&lt;a href=&quot;javascript:alert(1)&quot;&gt;', html)

    def test_ampersand_in_text_is_escaped(self):
        html = renderers._text_to_html('a & b')
        self.assertIn('a &amp; b', html)


class TestTextToHtmlFormatting(unittest.TestCase):
    def test_inline_backticks_become_code_tags_with_escaped_content(self):
        html = renderers._text_to_html('use `<b>` here')
        self.assertIn('<code>&lt;b&gt;</code>', html)
        # Non-code text remains escaped, not raw:
        self.assertNotIn('<b>', html)

    def test_code_fence_becomes_pre_code_with_lang_badge(self):
        html = renderers._text_to_html('```python\nprint("<x>")\n```')
        self.assertIn('<pre>', html)
        self.assertIn('<span class="code-lang">python</span>', html)
        self.assertIn('<code>', html)
        # Code content inside the fence is also escaped:
        self.assertIn('&lt;x&gt;', html)
        self.assertNotIn('<x>', html)

    def test_code_fence_without_lang_no_badge(self):
        html = renderers._text_to_html('```\nplain\n```')
        self.assertIn('<pre><code>', html)
        self.assertNotIn('code-lang', html)

    def test_paragraphs_split_on_blank_lines(self):
        html = renderers._text_to_html('first\n\nsecond')
        self.assertEqual(html.count('<p>'), 2)
        self.assertIn('<p>first</p>', html)
        self.assertIn('<p>second</p>', html)

    def test_mixed_fence_and_prose_preserves_order_and_safety(self):
        html = renderers._text_to_html(
            'intro <evil>\n\n```js\n<bad>\n```\n\nouter `<inline>` tail'
        )
        # Prose escaped:
        self.assertIn('&lt;evil&gt;', html)
        # Code fence escaped:
        self.assertIn('<pre>', html)
        self.assertIn('&lt;bad&gt;', html)
        # Inline backtick wrapping escaped:
        self.assertIn('<code>&lt;inline&gt;</code>', html)
        # No raw injection survived anywhere:
        self.assertNotIn('<evil>', html)
        self.assertNotIn('<bad>', html)
        self.assertNotIn('<inline>', html)


class TestRenderMarkdown(unittest.TestCase):
    def test_includes_title_and_metadata(self):
        out = renderers.render_markdown(
            [_human_turn('hello')], _meta(branch='dev'), 'My Title')
        self.assertIn('# My Title', out)
        self.assertIn('**Project:** demo', out)
        self.assertIn('**Branch:** `dev`', out)
        self.assertIn('**Session:** `abcd1234…`', out)

    def test_assistant_turn_renders_tools_and_tokens(self):
        out = renderers.render_markdown(
            [_assistant_turn(text='done', tools=['Read', 'Bash'])],
            _meta(), 't')
        self.assertIn('## Assistant', out)
        self.assertIn('> Tools: `Read`, `Bash`', out)
        self.assertIn('> Tokens:', out)

    def test_agent_thread_renders_as_details(self):
        agent = {
            'agent_id': 'a1', 'agent_type': 'Explore',
            'description': 'find things', 'turns': [_human_turn('q')],
            'usage': {'input': 0, 'output': 0, 'cache_create': 0,
                      'cache_read': 0, 'total': 500},
        }
        out = renderers.render_markdown(
            [_assistant_turn(agents=[agent])], _meta(), 't')
        self.assertIn('<details><summary>Agent: <code>Explore</code>', out)
        self.assertIn('500 tokens', out)


class TestRenderJson(unittest.TestCase):
    def test_top_level_keys(self):
        s = renderers.render_json([_human_turn()], _meta(), 'Title X')
        d = json.loads(s)
        self.assertEqual(set(d.keys()), {'metadata', 'title', 'messages'})
        self.assertEqual(d['title'], 'Title X')
        self.assertEqual(len(d['messages']), 1)

    def test_metadata_passthrough(self):
        s = renderers.render_json([], _meta(branch='feat/x', total=42), 't')
        d = json.loads(s)
        self.assertEqual(d['metadata']['git_branch'], 'feat/x')
        self.assertEqual(d['metadata']['total_usage']['total'], 42)

    def test_handles_non_ascii(self):
        s = renderers.render_json(
            [_human_turn('café — naïve')], _meta(), 't')
        # ensure_ascii=False keeps real chars; JSON still parseable:
        self.assertIn('café — naïve', s)
        json.loads(s)


class TestRenderHtml(unittest.TestCase):
    def setUp(self):
        # Minimal template with extractable <style>
        self.tmpdir = tempfile.mkdtemp()
        self.tpl = os.path.join(self.tmpdir, 'tpl.html')
        with open(self.tpl, 'w') as f:
            f.write('<html><head><style>.msg{color:red}</style></head></html>')

    def tearDown(self):
        os.remove(self.tpl)
        os.rmdir(self.tmpdir)

    def test_includes_title_branch_project(self):
        html = renderers.render_html(
            [_human_turn()], _meta(branch='feat/x'),
            'My HTML', self.tpl)
        self.assertIn('<title>My HTML</title>', html)
        self.assertIn('feat/x', html)
        self.assertIn('demo', html)

    def test_embeds_template_css(self):
        html = renderers.render_html(
            [_human_turn()], _meta(), 't', self.tpl)
        self.assertIn('.msg{color:red}', html)

    def test_handles_missing_template_gracefully(self):
        html = renderers.render_html(
            [_human_turn()], _meta(), 't', '/no/such/template.html')
        # No raise; just no template CSS — extra CSS still present
        self.assertIn('<!DOCTYPE html>', html)
        self.assertIn('.token-line', html)  # _EXTRA_CSS still inlined

    def test_message_text_is_escaped(self):
        """End-to-end XSS regression: a turn whose text contains a payload
        must not produce executable HTML in the final document."""
        evil = _human_turn(text='boom <img src=x onerror=alert(1)>')
        html = renderers.render_html([evil], _meta(), 't', self.tpl)
        self.assertNotIn('<img src=x onerror=alert(1)>', html)
        self.assertIn('&lt;img src=x onerror=alert(1)&gt;', html)

    def test_assistant_tool_chips_rendered(self):
        turn = _assistant_turn(tools=['Read', 'Bash'])
        html = renderers.render_html([turn], _meta(), 't', self.tpl)
        self.assertIn('<span class="tool-chip">Read</span>', html)
        self.assertIn('<span class="tool-chip">Bash</span>', html)


if __name__ == '__main__':
    unittest.main()
