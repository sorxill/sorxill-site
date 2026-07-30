from httpx import AsyncClient


async def test_list_projects_ru(client: AsyncClient) -> None:
    r = await client.get("/api/v1/projects")
    assert r.status_code == 200
    items = r.json()["items"]
    assert items and items[0]["slug"] == "fastapi-gateway"
    assert "Шлюз" in items[0]["title"]


async def test_list_projects_en(client: AsyncClient) -> None:
    r = await client.get("/api/v1/projects", params={"locale": "en"})
    assert r.json()["items"][0]["title"] == "FastAPI gateway"


async def test_invalid_locale_is_rejected(client: AsyncClient) -> None:
    r = await client.get("/api/v1/projects", params={"locale": "de"})
    assert r.status_code == 422


async def test_limit_is_bounded(client: AsyncClient) -> None:
    r = await client.get("/api/v1/projects", params={"limit": 500})
    assert r.status_code == 422
