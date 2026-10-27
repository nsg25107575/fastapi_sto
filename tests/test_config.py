import os
import subprocess
import sys

CONFIG_IMPORT = "from config.config import Config"


def run_config_import(**env_vars: str | None) -> subprocess.CompletedProcess:
    env = os.environ.copy()

    # Ensure each test uses only explicitly supplied security settings.
    for key in ("APP_ENV", "JWT_SECRET_KEY", "COOKIES_SECRET_KEY"):
        env.pop(key, None)

    env.update({
        key: value
        for key, value in env_vars.items()
        if value is not None
    })

    return subprocess.run(
        [
            sys.executable,
            "-c",
            """
import dotenv
dotenv.load_dotenv = lambda *args, **kwargs: False
from config.config import Config
""",
        ],
        env=env,
        capture_output=True,
        text=True,
    )


def test_production_without_secrets_fails():
    result = run_config_import(APP_ENV="production")

    assert result.returncode != 0
    assert "JWT_SECRET_KEY" in result.stderr
    assert "COOKIES_SECRET_KEY" in result.stderr


def test_production_without_jwt_secret_fails():
    result = run_config_import(
        APP_ENV="production",
        COOKIES_SECRET_KEY="secure-cookie-secret",
    )

    assert result.returncode != 0
    assert "JWT_SECRET_KEY" in result.stderr


def test_production_without_cookie_secret_fails():
    result = run_config_import(
        APP_ENV="production",
        JWT_SECRET_KEY="secure-jwt-secret",
    )

    assert result.returncode != 0
    assert "COOKIES_SECRET_KEY" in result.stderr


def test_production_with_default_placeholder_fails():
    result = run_config_import(
        APP_ENV="production",
        JWT_SECRET_KEY="secure-jwt-secret",
        COOKIES_SECRET_KEY="supersecretkey",
    )

    assert result.returncode != 0
    assert "COOKIES_SECRET_KEY" in result.stderr


def test_production_with_secure_secrets_succeeds():
    result = run_config_import(
        APP_ENV="production",
        JWT_SECRET_KEY="secure-jwt-secret",
        COOKIES_SECRET_KEY="secure-cookie-secret",
    )

    assert result.returncode == 0, result.stderr


def test_development_without_secrets_succeeds():
    result = run_config_import(APP_ENV="development")

    assert result.returncode == 0, result.stderr
