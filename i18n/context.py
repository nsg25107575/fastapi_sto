from contextvars import ContextVar

from config import Config

_current_locale: ContextVar[str] = ContextVar("current_locale", default=Config.app_default_locale)


def set_current_locale(locale: str) -> None:
    _current_locale.set(locale)


def get_current_locale() -> str:
    return _current_locale.get()
