import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt

from src.domain.customer import Customer
from src.domain.vehicle import Vehicle
from src.infrastructure.config.settings import Settings
from src.main import create_app


def test_app_has_service_order_dependencies():
    app = create_app(_settings())

    assert hasattr(app.state, "service_order_repository")
    assert hasattr(app.state, "admin_user_repository")
    assert hasattr(app.state, "customer_repository")
    assert hasattr(app.state, "vehicle_repository")
    assert hasattr(app.state, "password_hasher")
    assert hasattr(app.state, "admin_jwt_service")
    assert hasattr(app.state, "event_publisher")


@pytest.mark.asyncio
async def test_service_order_api_happy_path():
    app = create_app(_settings())
    _seed_customer_and_vehicle(app, "customer-1", "vehicle-1")
    transport = ASGITransport(app=app)
    admin_headers = _auth_headers(_settings())

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        create_response = await client.post(
            "/service-orders",
            json={
                "customer_id": "customer-1",
                "vehicle_id": "vehicle-1",
                "description": "Brake inspection",
            },
            headers=admin_headers,
        )
        service_order_id = create_response.json()["service_order_id"]
        get_response = await client.get(
            f"/service-orders/{service_order_id}",
            headers=admin_headers,
        )
        event_response = await client.post(
            f"/service-orders/{service_order_id}/events",
            json={
                "event_type": "QUOTE_APPROVED",
                "correlation_id": service_order_id,
                "payload": {"quote_id": "quote-1"},
            },
            headers=admin_headers,
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
        response = await client.get(
            "/service-orders/missing",
            headers=_auth_headers(_settings()),
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_customer_token_cannot_open_service_order_for_another_customer():
    settings = _settings()
    app = create_app(settings)
    _seed_customer_and_vehicle(app, "customer-1", "vehicle-1")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/service-orders",
            json={
                "customer_id": "customer-1",
                "vehicle_id": "vehicle-1",
                "description": "Brake inspection",
            },
            headers=_customer_auth_headers(settings, "other-customer"),
        )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_invalid_token_returns_403():
    settings = _settings()
    app = create_app(settings)
    transport = ASGITransport(app=app)

    token = jwt.encode({"role": "admin", "user_id": "admin-1"}, "wrong-secret", "HS256")
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            "/service-orders/missing",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 403


def _settings() -> Settings:
    return Settings(
        APP_NAME="service-order-os-service",
        APP_VERSION="0.1.0",
        ENVIRONMENT="test",
        DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/db",
        JWT_SECRET="test-secret-value-with-32-characters",
        CUSTOMER_JWT_SECRET="customer-secret-value-with-32-characters",
        CUSTOMER_JWT_ISSUER="service-order-auth-lambda/test",
    )


def _auth_headers(settings: Settings) -> dict[str, str]:
    token = jwt.encode(
        {"role": "admin", "user_id": "admin-1", "iss": settings.JWT_ISSUER},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    return {"Authorization": f"Bearer {token}"}


def _customer_auth_headers(settings: Settings, customer_id: str) -> dict[str, str]:
    token = jwt.encode(
        {
            "sub": "11144477735",
            "role": "customer",
            "customer_id": customer_id,
            "iss": settings.CUSTOMER_JWT_ISSUER,
        },
        settings.CUSTOMER_JWT_SECRET,
        algorithm=settings.CUSTOMER_JWT_ALGORITHM,
    )
    return {"Authorization": f"Bearer {token}"}


def _seed_customer_and_vehicle(app, customer_id: str, vehicle_id: str) -> None:
    app.state.customer_repository.save(
        Customer(
            customer_id=customer_id,
            name="Cliente",
            cpf_cnpj="11144477735",
            email="cliente@example.com",
            phone="11999999999",
        )
    )
    app.state.vehicle_repository.save(
        Vehicle(
            vehicle_id=vehicle_id,
            customer_id=customer_id,
            brand="Toyota",
            model="Corolla",
            year=2023,
            plate="BRA2A34",
        )
    )
