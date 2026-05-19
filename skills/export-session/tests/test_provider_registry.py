"""Tests for providers.__init__ — provider registry and dispatch."""
import unittest
from unittest import mock

from . import _path  # noqa: F401
import providers
from providers import detect_provider, ALL_PROVIDERS, Provider
from providers.claude_code import ClaudeCodeProvider


class _StubProvider(Provider):
    name = 'stub'
    _detect_result = False

    @classmethod
    def detect(cls, cwd):
        return cls._detect_result

    def find_session(self, cwd):
        return {'cwd': cwd}

    def build_turns(self, session, *, include_thinking, no_tools, no_agents):
        return []

    def get_metadata(self, session, turns):
        return {}


class TestDetectProvider(unittest.TestCase):
    def test_explicit_override_returns_named_provider(self):
        p = detect_provider('/anywhere', override='claude-code')
        self.assertIsInstance(p, ClaudeCodeProvider)

    def test_unknown_override_raises_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            detect_provider('/anywhere', override='bogus')
        self.assertIn("Unknown provider 'bogus'", str(ctx.exception))
        self.assertIn('claude-code', str(ctx.exception))

    def test_no_match_raises_runtime_error(self):
        with mock.patch.object(ClaudeCodeProvider, 'detect',
                               classmethod(lambda cls, cwd: False)):
            with self.assertRaises(RuntimeError) as ctx:
                detect_provider('/nothing/here')
            self.assertIn('No session found', str(ctx.exception))
            self.assertIn('claude-code', str(ctx.exception))

    def test_auto_detect_picks_first_matching(self):
        with mock.patch.object(ClaudeCodeProvider, 'detect',
                               classmethod(lambda cls, cwd: True)):
            p = detect_provider('/anywhere')
            self.assertIsInstance(p, ClaudeCodeProvider)

    def test_registry_order_respected(self):
        """When multiple providers detect a session, the first wins."""
        _StubProvider._detect_result = True
        original = list(ALL_PROVIDERS)
        try:
            # Insert stub at index 0 — should win over claude-code
            providers.ALL_PROVIDERS.insert(0, _StubProvider)
            with mock.patch.object(ClaudeCodeProvider, 'detect',
                                   classmethod(lambda cls, cwd: True)):
                p = detect_provider('/anywhere')
                self.assertEqual(p.name, 'stub')
        finally:
            providers.ALL_PROVIDERS[:] = original
            _StubProvider._detect_result = False


class TestProviderInterface(unittest.TestCase):
    def test_cannot_instantiate_abstract_base(self):
        with self.assertRaises(TypeError):
            Provider()

    def test_concrete_subclass_must_implement_all_methods(self):
        # Missing get_metadata
        class Incomplete(Provider):
            name = 'incomplete'

            @classmethod
            def detect(cls, cwd):
                return False

            def find_session(self, cwd):
                return None

            def build_turns(self, session, *, include_thinking,
                            no_tools, no_agents):
                return []
            # get_metadata intentionally omitted

        with self.assertRaises(TypeError):
            Incomplete()


if __name__ == '__main__':
    unittest.main()
