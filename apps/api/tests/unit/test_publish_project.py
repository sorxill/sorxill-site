from datetime import UTC, datetime

import pytest

from app.application.use_cases.publish_project import (
    PublishProject,
    PublishProjectCommand,
)
from app.core.errors import NotFoundError
from app.domain.entities import Project
from app.domain.value_objects import Locale, Slug
from app.infrastructure.memory import (
    FrozenClock,
    InMemoryProjectRepository,
    RecordingTaskQueue,
)

AT = datetime(2026, 7, 30, 12, tzinfo=UTC)


def _uc(repo: InMemoryProjectRepository) -> tuple[PublishProject, RecordingTaskQueue]:
    queue = RecordingTaskQueue()
    return PublishProject(repo, FrozenClock(AT), queue), queue


async def test_publish_saves_and_enqueues_revalidation() -> None:
    project = Project(
        slug=Slug("demo"),
        title={Locale.RU: "Демо", Locale.EN: "Demo"},
        summary={Locale.RU: "Описание", Locale.EN: "Summary"},
        cover_url="/covers/demo.avif",
    )
    repo = InMemoryProjectRepository([project])
    uc, queue = _uc(repo)

    dto = await uc.execute(PublishProjectCommand(slug="demo"))

    assert dto.title == "Демо"
    assert dto.published_at == AT
    assert queue.calls == [("revalidate", {"tags": ["projects", "project:demo"]})]


async def test_publish_missing_project_raises_not_found() -> None:
    uc, queue = _uc(InMemoryProjectRepository([]))
    with pytest.raises(NotFoundError):
        await uc.execute(PublishProjectCommand(slug="nope"))
    assert queue.calls == []
