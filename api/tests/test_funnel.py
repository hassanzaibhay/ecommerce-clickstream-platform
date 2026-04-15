from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_funnel_empty(client: AsyncClient, mock_db: AsyncMock) -> None:
    mock_db.fetch.return_value = []
    mock_db.fetchrow.return_value = {"views": 0, "carts": 0, "purchases": 0}
    response = await client.get(
        "/api/funnel?start_date=2019-10-01&end_date=2019-10-31"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["stages"]) == 3
    assert data["stages"][0]["stage"] == "Views"
    assert data["categories"] == []


@pytest.mark.asyncio
async def test_funnel_with_category(client: AsyncClient, mock_db: AsyncMock) -> None:
    mock_db.fetch.side_effect = [
        [],  # categories query
        [],  # abandonment query
    ]
    mock_db.fetchrow.return_value = {"views": 1000, "carts": 100, "purchases": 10}
    response = await client.get(
        "/api/funnel?start_date=2019-10-01&end_date=2019-10-31&category=electronics"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["stages"][1]["count"] == 100
    assert data["view_to_cart_rate"] == 0.1


@pytest.mark.asyncio
async def test_funnel_missing_params(client: AsyncClient) -> None:
    response = await client.get("/api/funnel")
    assert response.status_code == 422
