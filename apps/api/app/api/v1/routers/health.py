from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.core.config import get_settings

router = APIRouter(tags=["ops"])


@router.get("/health", summary="Живость процесса")
async def health() -> dict[str, str]:
    """Не трогает зависимости: отвечает, пока жив сам процесс."""
    return {"status": "ok", "version": get_settings().app_version}


@router.get("/readyz", summary="Готовность принимать трафик")
async def readyz(
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, str]:
    """Проверяет базу по-настоящему: readyz без запроса к БД — это ложь,
    из-за которой rollout считает контейнер здоровым, пока он не работает."""
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        response.status_code = 503
        return {"status": "degraded", "database": "unreachable"}
    return {"status": "ready", "database": "ok"}
