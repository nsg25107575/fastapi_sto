"""
`config` package.

Re-exports `Config` from `config/config.py` so existing imports across the
codebase (`from config import Config`) keep working unchanged after the
`config.py` -> `config/` module refactor.
"""
from config.config import Config

__all__ = ["Config"]
