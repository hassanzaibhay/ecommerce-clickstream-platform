from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_products_empty(client: AsyncClient, mock_db: AsyncMock) -> None:
    mock_db.fetch.return_value = []
    response = await client.get("/api/products")
    assert response.status_code == 200
    data = response.json()
    assert data["products"] == []


@pytest.mark.asyncio
async def test_brands_empty(client: AsyncClient, mock_db: AsyncMock) -> None:
    mock_db.fetch.return_value = []
    response = await client.get("/api/brands")
    assert response.status_code == 200
    data = response.json()
    assert data["brands"] == []


@pytest.mark.asyncio
async def test_categories_empty(client: AsyncClient, mock_db: AsyncMock) -> None:
    mock_db.fetch.return_value = []
    response = await client.get("/api/categories")
    assert response.status_code == 200
    data = response.json()
    assert data["categories"] == []


@pytest.mark.asyncio
async def test_products_with_limit(client: AsyncClient, mock_db: AsyncMock) -> None:
    mock_db.fetch.return_value = []
    response = await client.get("/api/products?limit=5")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_products_invalid_limit(client: AsyncClient) -> None:
    response = await client.get("/api/products?limit=0")
    assert response.status_code == 422
