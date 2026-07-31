"""Реализация портов на SQLAlchemy. Обязана проходить те же контрактные
тесты, что и in-memory версия — см. tests/contract/."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Project
from app.domain.value_objects import Locale, PublishStatus, Slug
from app.infrastructure.db.models import ProjectModel, ProjectTranslationModel


def _to_entity(row: ProjectModel) -> Project:
    return Project(
        slug=Slug(row.slug),
        title={Locale(t.locale): t.title for t in row.translations},
        summary={Locale(t.locale): t.summary for t in row.translations},
        status=PublishStatus(row.status),
        cover_url=row.cover_url,
        stack=list(row.stack),
        published_at=row.published_at,
        sort_order=row.sort_order,
    )


class SqlAlchemyProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_slug(self, slug: Slug) -> Project | None:
        row = await self._session.scalar(select(ProjectModel).where(ProjectModel.slug == str(slug)))
        return _to_entity(row) if row is not None else None

    async def list_published(self, limit: int, offset: int) -> list[Project]:
        stmt = (
            select(ProjectModel)
            .where(ProjectModel.status == PublishStatus.PUBLISHED.value)
            .order_by(ProjectModel.sort_order.desc(), ProjectModel.slug)
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.scalars(stmt)).all()
        return [_to_entity(r) for r in rows]

    async def save(self, project: Project) -> None:
        row = await self._session.scalar(
            select(ProjectModel).where(ProjectModel.slug == str(project.slug))
        )
        if row is None:
            row = ProjectModel(slug=str(project.slug))
            self._session.add(row)

        row.status = project.status.value
        row.cover_url = project.cover_url
        row.stack = list(project.stack)
        row.published_at = project.published_at
        row.sort_order = project.sort_order

        existing = {t.locale: t for t in row.translations}
        for locale, title in project.title.items():
            summary = project.summary.get(locale, "")
            tr = existing.get(locale.value)
            if tr is None:
                row.translations.append(
                    ProjectTranslationModel(locale=locale.value, title=title, summary=summary)
                )
            else:
                tr.title, tr.summary = title, summary

        await self._session.flush()
