from fastapi import Request

from config import Config


def get_locale(request: Request) -> str:
    supported = {loc["abbr"] for loc in Config.app_sup_locales}

    # 1. explicit query param `?lang=uk` — handy for debugging/frontend overrides
    lang = request.query_params.get("lang")
    if lang in supported:
        return lang

    # 2. authenticated user's profile locale, if present
    user = getattr(request.state, "user", None)
    user_locale = getattr(user, "locale", None) if user else None
    if isinstance(user_locale, str) and user_locale in supported:
        return user_locale

    # 3. Accept-Language header
    header = request.headers.get("accept-language", "")
    for part in header.split(","):
        code = part.split(";")[0].strip().split("-")[0]
        if code in supported:
            return code

    return Config.app_default_locale
