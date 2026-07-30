"""Value objects: неизменяемые, самовалидирующиеся, без внешних зависимостей."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from app.core.errors import ValidationError

_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


@dataclass(frozen=True, slots=True)
class Slug:
    value: str

    def __post_init__(self) -> None:
        if not _SLUG_RE.match(self.value):
            raise ValidationError(f"Некорректный slug: {self.value!r}")
        if len(self.value) > 80:
            raise ValidationError("Slug длиннее 80 символов")

    def __str__(self) -> str:
        return self.value


class Locale(StrEnum):
    RU = "ru"
    EN = "en"


class PublishStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
