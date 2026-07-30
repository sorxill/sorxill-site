"""Сборка зависимостей. Единственное место, где слои склеиваются."""

from __future__ import annotations

from datetime import UTC, datetime
from functools import lru_cache

from app.application.use_cases.list_published_projects import ListPublishedProjects
from app.application.use_cases.publish_project import PublishProject
from app.domain.entities import Project
from app.domain.value_objects import Locale, Slug
from app.infrastructure.memory import (
    InMemoryProjectRepository,
    RecordingTaskQueue,
    SystemClock,
)


def _seed() -> list[Project]:
    """Временные данные M0. В M1 их заменит Postgres."""
    gateway = Project(
        slug=Slug("fastapi-gateway"),
        title={Locale.RU: "Шлюз на FastAPI", Locale.EN: "FastAPI gateway"},
        summary={
            Locale.RU: "Rate limiting, кэш ответов и circuit breaker. 500+ RPS в проде.",
            Locale.EN: "Rate limiting, response cache and circuit breaker. 500+ RPS.",
        },
        cover_url="/covers/gateway.avif",
        stack=["FastAPI", "Redis", "asyncio"],
        sort_order=10,
    )
    gateway.publish(at=datetime(2026, 5, 1, tzinfo=UTC))
    return [gateway]


@lru_cache
def _repo() -> InMemoryProjectRepository:
    return InMemoryProjectRepository(_seed())


@lru_cache
def _queue() -> RecordingTaskQueue:
    return RecordingTaskQueue()


def list_projects_uc() -> ListPublishedProjects:
    return ListPublishedProjects(_repo())


def publish_project_uc() -> PublishProject:
    return PublishProject(_repo(), SystemClock(), _queue())
