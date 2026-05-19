"""Provider registry.

To add a new provider:
  1. Drop a module next to claude_code.py (e.g. codex.py) that subclasses
     `Provider` from .base and sets a unique `name`.
  2. Import it here and append the class to `ALL_PROVIDERS`.

`detect_provider` returns the first provider whose `.detect(cwd)` is truthy,
unless an explicit override name is given.
"""
from typing import Optional

from .base import Provider
from .claude_code import ClaudeCodeProvider

ALL_PROVIDERS = [ClaudeCodeProvider]


def detect_provider(cwd: str, override: Optional[str] = None) -> Provider:
    if override:
        for cls in ALL_PROVIDERS:
            if cls.name == override:
                return cls()
        known = ', '.join(c.name for c in ALL_PROVIDERS)
        raise ValueError(f"Unknown provider '{override}'. Known: {known}")

    for cls in ALL_PROVIDERS:
        if cls.detect(cwd):
            return cls()

    known = ', '.join(c.name for c in ALL_PROVIDERS)
    raise RuntimeError(
        f"No session found for {cwd} in any provider ({known})."
    )


__all__ = ['Provider', 'ALL_PROVIDERS', 'detect_provider']
