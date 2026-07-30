from __future__ import annotations

from dataclasses import dataclass

from app.application.dto import ProjectDTO
from app.core.errors import NotFoundError
from app.domain.ports import Clock, ProjectRepository, TaskQueue
from app.domain.value_objects import Locale, Slug


@dataclass(frozen=True, slots=True)
class PublishProjectCommand:
    slug: str
    locale: Locale = Locale.RU


class PublishProject:
    def __init__(self, repo: ProjectRepository, clock: Clock, tasks: TaskQueue) -> None:
        self._repo = repo
        self._clock = clock
        self._tasks = tasks

    async def execute(self, cmd: PublishProjectCommand) -> ProjectDTO:
        slug = Slug(cmd.slug)
        project = await self._repo.get_by_slug(slug)
        if project is None:
            raise NotFoundError(f"Проект {cmd.slug!r} не найден")
        project.publish(at=self._clock.now())
        await self._repo.save(project)
        await self._tasks.enqueue(
            "revalidate", tags=["projects", f"project:{slug}"]
        )
        return ProjectDTO.from_entity(project, cmd.locale)
