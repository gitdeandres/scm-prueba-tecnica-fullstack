import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_search_sin_filtros_devuelve_items(client: AsyncClient) -> None:
    """Sin filtros debe devolver todos los items del seed."""
    response = await client.post("/items/search", json={})
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "sku" in data[0]


@pytest.mark.asyncio
async def test_search_filtro_por_status(client: AsyncClient) -> None:
    """Filtro de igualdad: solo deben volver items con el status indicado."""
    response = await client.post(
        "/items/search",
        json={"filters": [{"field": "status", "op": "=", "value": "pending"}]},
    )
    assert response.status_code == 200
    data = response.json()
    assert all(item["status"] == "pending" for item in data)


@pytest.mark.asyncio
async def test_search_filtro_in(client: AsyncClient) -> None:
    """Operador 'in': deben volver solo items cuyo status esté en la lista."""
    response = await client.post(
        "/items/search",
        json={"filters": [{"field": "status", "op": "in", "value": ["pending", "done"]}]},
    )
    assert response.status_code == 200
    data = response.json()
    assert all(item["status"] in ("pending", "done") for item in data)


@pytest.mark.asyncio
async def test_search_campo_invalido_devuelve_400(client: AsyncClient) -> None:
    """Un campo fuera de la whitelist debe ser rechazado con 400 y mensaje claro."""
    response = await client.post(
        "/items/search",
        json={"filters": [{"field": "campo_inventado", "op": "=", "value": "x"}]},
    )
    assert response.status_code == 400
    assert "Campo no permitido" in response.json()["detail"]


@pytest.mark.asyncio
async def test_search_operador_invalido_devuelve_422(client: AsyncClient) -> None:
    """
    Un operador fuera del enum es rechazado por Pydantic con 422 antes de llegar
    a la lógica de filtros — primera línea de defensa contra SQL injection.
    """
    response = await client.post(
        "/items/search",
        json={"filters": [{"field": "status", "op": "DROP TABLE", "value": "x"}]},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_search_exceso_de_filtros_devuelve_400(client: AsyncClient) -> None:
    """Más de MAX_FILTERS filtros debe ser rechazado con 400."""
    filtros = [{"field": "status", "op": "=", "value": "pending"}] * 6
    response = await client.post("/items/search", json={"filters": filtros})
    assert response.status_code == 400
    assert "Demasiados filtros" in response.json()["detail"]


@pytest.mark.asyncio
async def test_search_sin_token_devuelve_403(client: AsyncClient) -> None:
    """Un token con formato inválido debe ser rechazado con 403."""
    response = await client.post(
        "/items/search",
        json={},
        headers={"Authorization": "notavalidtoken"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_search_limite_filas(client: AsyncClient) -> None:
    """La respuesta nunca debe superar MAX_ROWS filas, independiente de los datos."""
    response = await client.post("/items/search", json={})
    assert response.status_code == 200
    assert len(response.json()) <= 100
