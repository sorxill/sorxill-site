"""Сущности домена. Инварианты живут здесь, а не в роутере."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.core.errors import InvariantError
from app.domain.value_objects import Locale, PublishStatus, Slug


@dataclass(slots=True)
class Project:
    slug: Slug
    title: dict[Locale, str]
    summary: dict[Locale, str]
    status: PublishStatus = PublishStatus.DRAFT
    cover_url: str | None = None
    stack: list[str] = field(default_factory=list)
    published_at: datetime | None = None
    sort_order: int = 0

    def publish(self, at: datetime) -> None:
        """Опубликовать проект. Обойти эти проверки из API невозможно."""
        if self.cover_url is None:
            raise InvariantError("Нельзя опубликовать проект без обложки")
        missing = [loc.value for loc in Locale if not self.title.get(loc)]
        if missing:
            raise InvariantError(f"Нет заголовка для локалей: {', '.join(missing)}")
        self.status = PublishStatus.PUBLISHED
        self.published_at = at

    def archive(self) -> None:
        self.status = PublishStatus.ARCHIVED

    @property
    def is_public(self) -> bool:
        return self.status is PublishStatus.PUBLISHED
