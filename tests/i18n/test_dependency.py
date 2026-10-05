import pytest
from fastapi import Request

from config import Config
from i18n.dependency import get_locale


@pytest.fixture(autouse=True)
def supported_locales(monkeypatch):
    monkeypatch.setattr(
        Config,
        "app_sup_locales",
        [
            {"abbr": "en", "name": "English"},
            {"abbr": "uk", "name": "Українська"},
            {"abbr": "pl", "name": "Polski"},
        ],
    )
    monkeypatch.setattr(Config, "app_default_locale", "en")


def make_request(query_string: str = "", headers: list[tuple[bytes, bytes]] | None = None,
                 state_locale: str | None = None) -> Request:
    scope = {
        "type": "http",
        "query_string": query_string.encode(),
        "headers": headers or [],
    }
    request = Request(scope)
    if state_locale is not None:
        class FakeUser:
            locale = state_locale

        request.state.user = FakeUser()
    return request


def test_get_locale_prefers_query_param_over_everything():
    request = make_request(
        query_string="lang=uk",
        headers=[(b"accept-language", b"pl")],
        state_locale="pl",
    )
    assert get_locale(request) == "uk"


def test_get_locale_ignores_unsupported_query_param():
    request = make_request(query_string="lang=fr", headers=[(b"accept-language", b"uk")])
    assert get_locale(request) == "uk"


def test_get_locale_falls_back_to_user_profile_locale():
    request = make_request(state_locale="pl")
    assert get_locale(request) == "pl"


def test_get_locale_falls_back_to_accept_language_header():
    request = make_request(headers=[(b"accept-language", b"uk-UA,en;q=0.8")])
    assert get_locale(request) == "uk"


def test_get_locale_defaults_to_configured_default_locale_when_nothing_matches():
    request = make_request()
    assert get_locale(request) == Config.app_default_locale


def test_get_locale_ignores_unsupported_accept_language():
    request = make_request(headers=[(b"accept-language", b"fr-FR,de;q=0.8")])
    assert get_locale(request) == Config.app_default_locale


def test_get_locale_respects_non_en_default_locale(monkeypatch):
    # proves the fallback truly reads Config.app_default_locale,
    # not a hardcoded "en" literal in get_locale()
    monkeypatch.setattr(Config, "app_default_locale", "pl")
    request = make_request()
    assert get_locale(request) == "pl"
