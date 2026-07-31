from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_project_repo
from app.domain.entities import Project
from app.domain.value_objects import Locale, Slug
from app.infrastructure.memory import InMemoryProjectRepository
from app.main import create_app


def _seed() -> list[Project]:
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


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Тесты API идут на in-memory репозитории: они проверяют HTTP-слой,
    а работу с базой покрывают контрактные тесты."""
    app = create_app()
    app.dependency_overrides[get_project_repo] = lambda: InMemoryProjectRepository(_seed())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
