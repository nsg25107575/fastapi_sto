from pathlib import Path

from config import Config
from i18n.context import get_current_locale
from i18n.translator import Translator

LOCALES_DIR = Path(__file__).parent / "locales"

_translator = Translator(locales_dir=LOCALES_DIR, default_locale=Config.app_default_locale)


def get_translator() -> Translator:
    return _translator


def t(key: str, locale: str | None = None, **kwargs) -> str:
    resolved_locale = locale if locale is not None else get_current_locale()
    return _translator.t(key, locale=resolved_locale, **kwargs)
