import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt

from src.infrastructure.config.settings import Settings
from src.main import create_app


@pytest.mark.asyncio
async def test_customer_and_vehicle_crud_are_protected_and_work():
    settings = _settings()
    app = create_app(settings)
    transport = ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {_admin_token(settings)}"}

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        unauthorized = await client.get("/customers")
        customer_response = await client.post(
            "/customers",
            json={
                "name": "Cliente",
                "cpf_cnpj": "111.444.777-35",
                "email": "cliente@example.com",
                "phone": "11999999999",
                "is_active": True,
            },
            headers=headers,
        )
        customer_id = customer_response.json()["customer_id"]
        customer_list = await client.get("/customers", headers=headers)
        vehicle_response = await client.post(
            "/vehicles",
            json={
                "customer_id": customer_id,
                "brand": "Toyota",
                "model": "Corolla",
                "year": 2023,
                "plate": "BRA2A34",
            },
            headers=headers,
        )
        vehicle_id = vehicle_response.json()["vehicle_id"]
        vehicle_detail = await client.get(f"/vehicles/{vehicle_id}", headers=headers)

    assert unauthorized.status_code == 401
    assert customer_response.status_code == 201
    assert customer_list.json()[0]["cpf_cnpj"] == "11144477735"
    assert vehicle_response.status_code == 201
    assert vehicle_detail.json()["plate"] == "BRA2A34"


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


def _admin_token(settings: Settings) -> str:
    return jwt.encode(
        {"role": "admin", "user_id": "admin-1", "iss": settings.JWT_ISSUER},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
