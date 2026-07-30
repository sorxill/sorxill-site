from __future__ import annotations

from dataclasses import dataclass

from app.application.dto import ProjectDTO
from app.domain.ports import ProjectRepository
from app.domain.value_objects import Locale


@dataclass(frozen=True, slots=True)
class ListPublishedProjectsQuery:
    locale: Locale
    limit: int = 20
    offset: int = 0


class ListPublishedProjects:
    """Один use case — один класс с одним публичным методом."""

    def __init__(self, repo: ProjectRepository) -> None:
        self._repo = repo

    async def execute(self, query: ListPublishedProjectsQuery) -> list[ProjectDTO]:
        projects = await self._repo.list_published(query.limit, query.offset)
        return [ProjectDTO.from_entity(p, query.locale) for p in projects]
