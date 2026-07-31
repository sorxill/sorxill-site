"""Сборка зависимостей — единственное место, где склеиваются слои.

Выбор реализации репозитория живёт здесь и только здесь: use cases
о нём не знают, поэтому переход с in-memory на Postgres не потребовал
ни одной правки в application-слое.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.list_published_projects import ListPublishedProjects
from app.application.use_cases.publish_project import PublishProject
from app.core.config import get_settings
from app.domain.ports import ProjectRepository
from app.infrastructure.db.engine import make_engine, make_session_factory
from app.infrastructure.memory import (
    InMemoryProjectRepository,
    RecordingTaskQueue,
    SystemClock,
)


@lru_cache
def _engine():  # type: ignore[no-untyped-def]
    settings = get_settings()
    return make_engine(settings.database_url, echo=settings.app_env == "local")


@lru_cache
def _session_factory():  # type: ignore[no-untyped-def]
    return make_session_factory(_engine())


async def get_session() -> AsyncIterator[AsyncSession]:
    async with _session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@lru_cache
def _queue() -> RecordingTaskQueue:
    return RecordingTaskQueue()


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_project_repo(session: SessionDep) -> ProjectRepository:
    # Импорт внутри функции: без базы приложение всё равно должно стартовать,
    # чтобы отдавать /health и статику (деградация из HLD §3).
    from app.infrastructure.db.repositories import SqlAlchemyProjectRepository

    return SqlAlchemyProjectRepository(session)


RepoDep = Annotated[ProjectRepository, Depends(get_project_repo)]


def list_projects_uc(repo: RepoDep) -> ListPublishedProjects:
    return ListPublishedProjects(repo)


def publish_project_uc(repo: RepoDep) -> PublishProject:
    return PublishProject(repo, SystemClock(), _queue())


def in_memory_repo_override() -> ProjectRepository:
    """Для тестов API: подменяет базу без поднятия Postgres."""
    return InMemoryProjectRepository([])
