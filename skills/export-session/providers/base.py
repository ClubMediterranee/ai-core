"""Provider interface for session-export skill.

Each provider knows how to discover and parse one AI coding tool's session
transcripts (Claude Code, Codex, OpenCode, ...) and normalize them into the
intermediate representation (IR) the renderers consume.

IR — `Turn` dict
----------------
    {
      'role':      'human' | 'assistant',
      'text':      str,
      'ts':        str,        # 'HH:MM:SS'
      'tools':     [str],      # tool names invoked in this turn (assistant only)
      'thinking':  str | None, # internal reasoning, when include_thinking=True
      'agents':    [Agent],    # nested sub-agent threads
      'usage':     {'input', 'output', 'cache_create', 'cache_read', 'total'},
    }

IR — `Agent` dict
-----------------
    {
      'agent_id':    str,
      'agent_type':  str,
      'description': str,
      'turns':       [Turn],
      'usage':       {...},
    }

IR — `Metadata` dict (returned by `get_metadata`)
-------------------------------------------------
    {
      'project_name':  str,
      'project_path':  str,
      'git_branch':    str,
      'session_id':    str,
      'export_date':   str,         # 'YYYY-MM-DD HH:MM UTC'
      'message_count': int,         # human turns only
      'total_usage':   {...},
    }
"""
from abc import ABC, abstractmethod


class Provider(ABC):
    name: str = ''

    @classmethod
    @abstractmethod
    def detect(cls, cwd: str) -> bool:
        """Cheap existence check — does any session for cwd live on disk?"""

    @abstractmethod
    def find_session(self, cwd: str):
        """Locate the session. Returns a provider-specific handle, or None."""

    @abstractmethod
    def build_turns(self, session, *, include_thinking: bool,
                    no_tools: bool, no_agents: bool) -> list:
        """Parse the session into a list of Turn dicts (see module docstring)."""

    @abstractmethod
    def get_metadata(self, session, turns: list) -> dict:
        """Return the Metadata dict for this session."""
