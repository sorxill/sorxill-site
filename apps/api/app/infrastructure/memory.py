"""Реализации портов в памяти. В M1 рядом встанут SQLAlchemy-версии,
код use cases при этом не изменится — это и есть смысл DIP."""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.entities import Project
from app.domain.value_objects import PublishStatus, Slug


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class FrozenClock:
    """Для тестов: время не течёт."""

    def __init__(self, at: datetime) -> None:
        self._at = at

    def now(self) -> datetime:
        return self._at


class InMemoryProjectRepository:
    def __init__(self, projects: list[Project] | None = None) -> None:
        self._items: dict[str, Project] = {str(p.slug): p for p in projects or []}

    async def get_by_slug(self, slug: Slug) -> Project | None:
        return self._items.get(str(slug))

    async def list_published(self, limit: int, offset: int) -> list[Project]:
        published = [p for p in self._items.values() if p.status is PublishStatus.PUBLISHED]
        published.sort(key=lambda p: (-p.sort_order, str(p.slug)))
        return published[offset : offset + limit]

    async def save(self, project: Project) -> None:
        self._items[str(project.slug)] = project


class RecordingTaskQueue:
    """Пока нет Redis — задачи копятся в списке. Наблюдаемо в тестах."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def enqueue(self, task: str, /, **payload: object) -> None:
        self.calls.append((task, payload))
