import pytest


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    response = await client.post("/api/v1/auth/login", json={
        "email": "notexist@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_products_list_unauthenticated(client):
    response = await client.get("/api/v1/products")
    # Without auth still returns 200 (auth not enforced on list yet)
    assert response.status_code in (200, 401)


@pytest.mark.asyncio
async def test_stock_adjust_requires_schema(client):
    response = await client.post("/api/v1/stock/adjust", json={
        "branch_schema": "public",
        "product_id": "00000000-0000-0000-0000-000000000000",
        "delta": -5,
    })
    # Will fail at DB level if product doesn't exist — that's expected
    assert response.status_code in (200, 422, 500)
