import json
from pathlib import Path

from config import Config


class Translator:
    """
    Loads and resolves translations for user-facing API messages.

    Each locale is read from a JSON file in `locales_dir` on first access
    and cached in memory. `en` is the 'source of truth': if a key is missing
    in the requested locale, resolution falls back to `default_locale`.
    If the key is missing there too, the key itself is returned so a
    missing translation never breaks the response, while still being
    easy to spot in logs/QA.
    """

    def __init__(self, locales_dir: Path, default_locale: str = Config.app_default_locale):
        self._locales_dir = locales_dir
        self._default_locale = default_locale
        self._cache: dict[str, dict] = {}

    def _load(self, locale: str) -> dict:
        """
        Load the translation data for a given locale from the JSON file, caching it in memory.
        """
        if locale not in self._cache:
            path = self._locales_dir / f"{locale}.json"
            if not path.exists():
                path = self._locales_dir / f"{self._default_locale}.json"
            self._cache[locale] = json.loads(path.read_text(encoding="utf-8"))
        return self._cache[locale]

    @staticmethod
    def _resolve_key(data: dict, dotted_key: str) -> str | None:
        """
        Resolve a dotted key (e.g., "service.not_found") in a nested dictionary.
        Returns the corresponding string value if found, or None if not found.
        """
        node = data
        for part in dotted_key.split("."):
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]
        return node if isinstance(node, str) else None

    def reload(self) -> None:
        """
        Drop the in-memory cache (dev hot-reload / tests).
        """
        self._cache.clear()

    def t(self, key: str, locale: str, **kwargs) -> str:
        """
        Translate a message key into the appropriate localized string.
        If the key is missing in the requested locale, it falls back to the default locale.
        If the key is missing in both, it returns the key itself.
        """
        message = self._resolve_key(self._load(locale), key)

        if message is None and locale != self._default_locale:
            message = self._resolve_key(self._load(self._default_locale), key)

        if message is None:
            return key

        return message.format(**kwargs) if kwargs else message
