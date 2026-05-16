import pytest

@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_health_db(client):
    # This assumes DB is reachable in the test environment
    response = await client.get("/api/v1/health/db")
    assert response.status_code == 200
    assert "status" in response.json()
