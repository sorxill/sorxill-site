from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["ops"])


@router.get("/health", summary="Живость процесса")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": get_settings().app_version}


@router.get("/readyz", summary="Готовность принимать трафик")
async def readyz() -> dict[str, str]:
    # В M1 здесь появятся проверки Postgres и Redis.
    return {"status": "ready"}
