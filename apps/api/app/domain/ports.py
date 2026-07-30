"""Порты. Узкие Protocol-интерфейсы, которые реализует infrastructure."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.domain.entities import Project
from app.domain.value_objects import Slug


class Clock(Protocol):
    def now(self) -> datetime: ...


class ProjectRepository(Protocol):
    async def get_by_slug(self, slug: Slug) -> Project | None: ...

    async def list_published(self, limit: int, offset: int) -> list[Project]: ...

    async def save(self, project: Project) -> None: ...


class TaskQueue(Protocol):
    async def enqueue(self, task: str, /, **payload: object) -> None: ...
