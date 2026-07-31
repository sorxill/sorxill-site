"""Контрактные тесты порта ProjectRepository.

Один и тот же набор гоняется против всех реализаций. In-memory доступна
всегда, SQLAlchemy — когда задан DATABASE_URL (в CI это сервис postgres).
Именно это делает подмену реализации безопасной: если новая нарушит
контракт, тесты упадут здесь, а не в проде.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.domain.entities import Project
from app.domain.ports import ProjectRepository
from app.domain.value_objects import Locale, Slug
from app.infrastructure.db.repositories import SqlAlchemyProjectRepository
from app.infrastructure.memory import InMemoryProjectRepository

AT = datetime(2026, 1, 1, tzinfo=UTC)
DSN = os.getenv("DATABASE_URL")

IMPLEMENTATIONS = ["memory"] + (["sqlalchemy"] if DSN else [])


@pytest.fixture(params=IMPLEMENTATIONS)
async def repo(request: pytest.FixtureRequest) -> AsyncIterator[ProjectRepository]:
    if request.param == "memory":
        yield InMemoryProjectRepository([])
        return

    engine = create_async_engine(DSN or "", poolclass=None)
    async with engine.connect() as conn:
        # Тест идёт внутри транзакции, которая откатывается: база остаётся
        # чистой между тестами без пересоздания схемы.
        trans = await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)
        try:
            yield SqlAlchemyProjectRepository(session)
        finally:
            await session.close()
            await trans.rollback()
    await engine.dispose()


def _project(slug: str, order: int = 0) -> Project:
    return Project(
        slug=Slug(slug),
        title={Locale.RU: slug, Locale.EN: slug},
        summary={Locale.RU: "s", Locale.EN: "s"},
        cover_url="/c.avif",
        sort_order=order,
    )


async def test_get_by_slug_returns_none_when_absent(repo: ProjectRepository) -> None:
    assert await repo.get_by_slug(Slug("absent")) is None


async def test_save_then_get(repo: ProjectRepository) -> None:
    await repo.save(_project("alpha"))
    found = await repo.get_by_slug(Slug("alpha"))
    assert found is not None
    assert str(found.slug) == "alpha"
    assert found.title[Locale.RU] == "alpha"


async def test_list_published_excludes_drafts(repo: ProjectRepository) -> None:
    draft = _project("draft")
    live = _project("live")
    live.publish(at=AT)
    await repo.save(draft)
    await repo.save(live)

    items = await repo.list_published(limit=10, offset=0)
    assert [str(p.slug) for p in items] == ["live"]


async def test_list_published_respects_sort_order(repo: ProjectRepository) -> None:
    for slug, order in (("low", 1), ("high", 9)):
        project = _project(slug, order)
        project.publish(at=AT)
        await repo.save(project)

    items = await repo.list_published(limit=10, offset=0)
    assert [str(p.slug) for p in items] == ["high", "low"]


async def test_save_is_idempotent_by_slug(repo: ProjectRepository) -> None:
    project = _project("same")
    await repo.save(project)
    project.title[Locale.RU] = "изменено"
    await repo.save(project)

    found = await repo.get_by_slug(Slug("same"))
    assert found is not None
    assert found.title[Locale.RU] == "изменено"
    assert len(await repo.list_published(limit=10, offset=0)) == 0
