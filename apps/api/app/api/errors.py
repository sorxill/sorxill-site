"""Доменные ошибки -> RFC 9457 problem+json с trace_id."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.errors import DomainError


def _problem(request: Request, status: int, code: str, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        content={
            "type": f"https://sorxill.ru/errors/{code.replace('_', '-')}",
            "title": code.replace("_", " ").capitalize(),
            "status": status,
            "detail": detail,
            "instance": request.url.path,
            "trace_id": request.headers.get("x-request-id", "-"),
        },
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain(request: Request, exc: DomainError) -> JSONResponse:
        return _problem(request, exc.status, exc.code, str(exc))
