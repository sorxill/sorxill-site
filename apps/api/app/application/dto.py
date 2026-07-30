"""DTO слоя приложения. Не Pydantic — чтобы домен не зависел от схем API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.entities import Project
from app.domain.value_objects import Locale


@dataclass(frozen=True, slots=True)
class ProjectDTO:
    slug: str
    title: str
    summary: str
    status: str
    cover_url: str | None
    stack: tuple[str, ...]
    published_at: datetime | None

    @classmethod
    def from_entity(cls, project: Project, locale: Locale) -> ProjectDTO:
        return cls(
            slug=str(project.slug),
            title=project.title.get(locale, ""),
            summary=project.summary.get(locale, ""),
            status=project.status.value,
            cover_url=project.cover_url,
            stack=tuple(project.stack),
            published_at=project.published_at,
        )
