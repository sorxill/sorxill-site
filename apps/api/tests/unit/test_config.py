"""Регрессионный тест на разбор ENV.

Ошибка, ради которой он написан: pydantic-settings пытался разобрать
CORS_ORIGINS как JSON до валидатора и падал на строке через запятую.
Деплой ломался на миграциях, хотя все остальные тесты были зелёными.
"""

import pytest

from app.core.config import Settings


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://sorxill.ru", ["https://sorxill.ru"]),
        (
            "https://sorxill.ru,https://www.sorxill.ru",
            ["https://sorxill.ru", "https://www.sorxill.ru"],
        ),
        ("https://a.ru, https://b.ru ", ["https://a.ru", "https://b.ru"]),
        ('["https://a.ru","https://b.ru"]', ["https://a.ru", "https://b.ru"]),
        ("", []),
    ],
)
def test_cors_origins_parsing(
    monkeypatch: pytest.MonkeyPatch, raw: str, expected: list[str]
) -> None:
    monkeypatch.setenv("CORS_ORIGINS", raw)
    assert Settings(_env_file=None).cors_origins == expected


def test_unknown_env_vars_are_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    """На сервере в .env лежат переменные для compose и других сервисов —
    приложение не должно падать из-за них."""
    monkeypatch.setenv("UMAMI_SECRET", "не для нас")
    monkeypatch.setenv("GH_OWNER", "sorxill")
    assert Settings(_env_file=None).app_env in {"local", "ci", "production"}


def test_production_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    assert Settings(_env_file=None).is_production is True
