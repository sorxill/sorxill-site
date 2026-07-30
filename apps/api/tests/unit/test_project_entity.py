from datetime import UTC, datetime

import pytest

from app.core.errors import InvariantError
from app.domain.entities import Project
from app.domain.value_objects import Locale, PublishStatus, Slug

AT = datetime(2026, 7, 30, tzinfo=UTC)


def _project(**over: object) -> Project:
    data: dict[str, object] = {
        "slug": Slug("demo"),
        "title": {Locale.RU: "Демо", Locale.EN: "Demo"},
        "summary": {Locale.RU: "Описание", Locale.EN: "Summary"},
        "cover_url": "/covers/demo.avif",
    }
    data.update(over)
    return Project(**data)  # type: ignore[arg-type]


def test_publish_sets_status_and_date() -> None:
    project = _project()
    project.publish(at=AT)
    assert project.status is PublishStatus.PUBLISHED
    assert project.published_at == AT
    assert project.is_public


def test_cannot_publish_without_cover() -> None:
    project = _project(cover_url=None)
    with pytest.raises(InvariantError, match="обложки"):
        project.publish(at=AT)
    assert project.status is PublishStatus.DRAFT


def test_cannot_publish_without_all_locales() -> None:
    project = _project(title={Locale.RU: "Только русский"})
    with pytest.raises(InvariantError, match="en"):
        project.publish(at=AT)


def test_archived_project_is_not_public() -> None:
    project = _project()
    project.publish(at=AT)
    project.archive()
    assert not project.is_public
