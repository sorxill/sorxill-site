from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.deps import list_projects_uc
from app.application.use_cases.list_published_projects import (
    ListPublishedProjects,
    ListPublishedProjectsQuery,
)
from app.domain.value_objects import Locale

router = APIRouter(prefix="/api/v1", tags=["projects"])


class ProjectOut(BaseModel):
    slug: str
    title: str
    summary: str
    cover_url: str | None
    stack: list[str]


class ProjectListOut(BaseModel):
    items: list[ProjectOut]


@router.get("/projects", response_model=ProjectListOut)
async def list_projects(
    uc: Annotated[ListPublishedProjects, Depends(list_projects_uc)],
    locale: Locale = Locale.RU,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> ProjectListOut:
    dtos = await uc.execute(ListPublishedProjectsQuery(locale=locale, limit=limit))
    return ProjectListOut(
        items=[
            ProjectOut(
                slug=d.slug,
                title=d.title,
                summary=d.summary,
                cover_url=d.cover_url,
                stack=list(d.stack),
            )
            for d in dtos
        ]
    )
