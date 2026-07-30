"""Контрактные тесты порта. Любая новая реализация ProjectRepository
обязана пройти этот же набор — в M1 сюда добавится SQLAlchemy-версия."""

from collections.abc import Callable
from datetime import UTC, datetime

import pytest

from app.domain.entities import Project
from app.domain.ports import ProjectRepository
from app.domain.value_objects import Locale, Slug
from app.infrastructure.memory import InMemoryProjectRepository

AT = datetime(2026, 1, 1, tzinfo=UTC)

IMPLEMENTATIONS: list[Callable[[], ProjectRepository]] = [
    lambda: InMemoryProjectRepository([]),
]


@pytest.fixture(params=IMPLEMENTATIONS, ids=["memory"])
def repo(request: pytest.FixtureRequest) -> ProjectRepository:
    factory: Callable[[], ProjectRepository] = request.param
    return factory()


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
    assert found is not None and str(found.slug) == "alpha"


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
