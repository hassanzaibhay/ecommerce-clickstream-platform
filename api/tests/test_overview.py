from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_data_range(client: AsyncClient) -> None:
    response = await client.get("/api/data-range")
    assert response.status_code == 200
    data = response.json()
    assert data["min_date"] == "2019-10-01"
    assert data["max_date"] == "2019-11-30"


@pytest.mark.asyncio
async def test_overview_empty(client: AsyncClient, mock_db: AsyncMock) -> None:
    mock_db.fetchrow.return_value = {
        "total_events": 0,
        "unique_users": 0,
        "total_views": 0,
        "total_carts": 0,
        "total_purchases": 0,
        "total_revenue": 0,
        "conversion_rate": 0,
        "avg_order_value": 0,
    }
    mock_db.fetch.return_value = []
    response = await client.get(
        "/api/overview?start_date=2019-10-01&end_date=2019-10-31"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_events"] == 0
    assert data["daily_trend"] == []


@pytest.mark.asyncio
async def test_overview_missing_params(client: AsyncClient) -> None:
    response = await client.get("/api/overview")
    assert response.status_code == 422
