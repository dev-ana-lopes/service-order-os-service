import pytest
from httpx import ASGITransport, AsyncClient

from src.infrastructure.config.settings import Settings
from src.main import create_app


@pytest.mark.asyncio
async def test_register_login_token_and_validate_flow():
    settings = _settings()
    app = create_app(settings)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        register_response = await client.post(
            "/auth/register",
            json={"email": "admin@example.com", "password": "123456"},
        )
        login_response = await client.post(
            "/auth/login",
            json={"email": "admin@example.com", "password": "123456"},
        )
        form_token_response = await client.post(
            "/auth/token",
            data={"username": "admin@example.com", "password": "123456"},
        )
        access_token = login_response.json()["access_token"]
        validate_response = await client.get(
            "/auth/validate",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    assert register_response.status_code == 201
    assert register_response.json()["user_id"]
    assert login_response.status_code == 200
    assert form_token_response.status_code == 200
    assert validate_response.status_code == 200
    assert validate_response.json()["role"] == "admin"
    assert validate_response.json()["email"] == "admin@example.com"
    assert validate_response.json()["issuer"] == settings.JWT_ISSUER


@pytest.mark.asyncio
async def test_register_rejects_duplicate_email_and_login_rejects_invalid_password():
    app = create_app(_settings())
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        first_register = await client.post(
            "/auth/register",
            json={"email": "admin@example.com", "password": "123456"},
        )
        second_register = await client.post(
            "/auth/register",
            json={"email": "admin@example.com", "password": "123456"},
        )
        invalid_login = await client.post(
            "/auth/login",
            json={"email": "admin@example.com", "password": "wrong-password"},
        )

    assert first_register.status_code == 201
    assert second_register.status_code == 409
    assert invalid_login.status_code == 401


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
