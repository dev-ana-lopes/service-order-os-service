import pytest
from httpx import ASGITransport, AsyncClient

from src.infrastructure.config.settings import Settings
from src.main import create_app


def test_app_has_service_order_dependencies():
    app = create_app(_settings())

    assert hasattr(app.state, "service_order_repository")
    assert hasattr(app.state, "event_publisher")


@pytest.mark.asyncio
async def test_service_order_api_happy_path():
    app = create_app(_settings())
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        create_response = await client.post(
            "/service-orders",
            json={
                "customer_id": "customer-1",
                "vehicle_id": "vehicle-1",
                "description": "Brake inspection",
            },
        )
        service_order_id = create_response.json()["service_order_id"]
        get_response = await client.get(f"/service-orders/{service_order_id}")
        event_response = await client.post(
            f"/service-orders/{service_order_id}/events",
            json={
                "event_type": "QUOTE_APPROVED",
                "correlation_id": service_order_id,
                "payload": {"quote_id": "quote-1"},
            },
        )

    assert create_response.status_code == 201
    assert create_response.json()["status"] == "QUOTE_REQUESTED"
    assert get_response.status_code == 200
    assert get_response.json()["service_order_id"] == service_order_id
    assert event_response.status_code == 200
    assert event_response.json()["status"] == "QUOTE_APPROVED"


@pytest.mark.asyncio
async def test_service_order_api_returns_not_found():
    app = create_app(_settings())
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/service-orders/missing")

    assert response.status_code == 404


def _settings() -> Settings:
    return Settings(
        APP_NAME="service-order-os-service",
        APP_VERSION="0.1.0",
        ENVIRONMENT="test",
        DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/db",
        JWT_SECRET="test-secret-value-with-32-characters",
        APPROVAL_TOKEN_SECRET="approval-secret-value-with-32-chars",
    )
