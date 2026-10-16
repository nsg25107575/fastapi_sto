from contextvars import ContextVar, Token

from config import Config

_current_locale: ContextVar[str] = ContextVar("current_locale", default=Config.app_default_locale)


def set_current_locale(locale: str) -> Token[str]:
    return _current_locale.set(locale)


def reset_current_locale(token: Token[str]) -> None:
    _current_locale.reset(token)


def get_current_locale() -> str:
    return _current_locale.get()
