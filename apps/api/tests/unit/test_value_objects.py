import pytest

from app.core.errors import ValidationError
from app.domain.value_objects import Slug


@pytest.mark.parametrize("value", ["fastapi-gateway", "pg-slow-query-lab", "abc123"])
def test_valid_slugs(value: str) -> None:
    assert str(Slug(value)) == value


@pytest.mark.parametrize(
    "value", ["Uppercase", "two words", "-leading", "trailing-", "double--dash", ""]
)
def test_invalid_slugs(value: str) -> None:
    with pytest.raises(ValidationError):
        Slug(value)


def test_slug_is_immutable() -> None:
    slug = Slug("ok")
    with pytest.raises(AttributeError):
        slug.value = "changed"  # type: ignore[misc]
