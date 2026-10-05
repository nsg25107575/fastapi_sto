"""
Unit tests for the Translator class in the i18n module.
"""

import json
from pathlib import Path

import pytest

from i18n.translator import Translator


@pytest.fixture
def locales_dir(tmp_path: Path) -> Path:
    """
    Create a temporary directory with locale JSON files for testing.
    """
    en = {"service": {"not_found": "Service not found"},
          "auth": {"rate_limited": "Please wait {seconds} seconds"}}
    uk = {"service": {"not_found": "Послугу не знайдено"}}
    # auth.rate_limited is missing in uk — for fallback testing
    (tmp_path / "en.json").write_text(json.dumps(en), encoding="utf-8")
    (tmp_path / "uk.json").write_text(json.dumps(uk), encoding="utf-8")
    return tmp_path


@pytest.fixture
def translator(locales_dir: Path) -> Translator:
    """
    Fixture that provides a Translator instance for testing.
    """
    return Translator(locales_dir=locales_dir, default_locale="en")


def test_t_returns_translation_for_known_key_and_locale(translator):
    """
    Test that the translator returns the correct translation for a known key and locale.
    """
    assert translator.t("service.not_found", locale="uk") == "Послугу не знайдено"


def test_t_falls_back_to_default_locale_when_key_missing_in_locale(translator):
    """
    Test that the translator falls back to the default locale when a key is missing in the requested locale.
    """
    # auth.rate_limited is not in uk.json -> should be pulled from en
    result = translator.t("auth.rate_limited", locale="uk", seconds=30)
    assert result == "Please wait 30 seconds"


def test_t_returns_key_itself_when_missing_everywhere(translator):
    """
    Test that the translator returns the key itself when it is missing in all locales.
    """
    assert translator.t("nonexistent.key", locale="uk") == "nonexistent.key"


def test_t_interpolates_kwargs(translator):
    """
    Test that the translator correctly interpolates keyword arguments into translations.
    """
    result = translator.t("auth.rate_limited", locale="en", seconds=5)
    assert result == "Please wait 5 seconds"


def test_t_falls_back_to_default_locale_when_requested_locale_file_missing(translator):
    """
    Test that the translator falls back to the default locale when the requested locale file is missing.
    """
    # pl.json does not exist in the fixture at all -> fallback to en, without an error.
    result = translator.t("service.not_found", locale="pl")
    assert result == "Service not found"


def test_reload_picks_up_changed_translation_file(translator, locales_dir):
    """
    Test that the translator reloads translations from files when reload() is called.
    """
    assert translator.t("service.not_found", locale="uk") == "Послугу не знайдено"

    updated = {"service": {"not_found": "Таку послугу не знайдено"}}
    (locales_dir / "uk.json").write_text(json.dumps(updated), encoding="utf-8")

    # without reload(), the cache remains stale
    assert translator.t("service.not_found", locale="uk") == "Послугу не знайдено"

    translator.reload()
    assert translator.t("service.not_found", locale="uk") == "Таку послугу не знайдено"


def test_each_translator_instance_has_isolated_cache(locales_dir):
    """
    Test that each Translator instance maintains its own isolated cache and does not affect other instances.
    """
    # two separate instances should not share cache state.
    t1 = Translator(locales_dir=locales_dir, default_locale="en")
    t2 = Translator(locales_dir=locales_dir, default_locale="en")
    t1.t("service.not_found", locale="uk")  # warms up the T1 cache
    t2.reload()  # should not affect t1
    assert t1.t("service.not_found", locale="uk") == "Послугу не знайдено"
