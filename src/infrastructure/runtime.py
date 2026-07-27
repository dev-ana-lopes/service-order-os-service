from __future__ import annotations

from src.infrastructure.config.settings import Settings
from src.infrastructure.database.readiness import DatabaseReadinessProbe
from src.infrastructure.database.url_utils import validate_runtime_database_url
from src.infrastructure.messaging.in_memory_event_publisher import InMemoryEventPublisher
from src.infrastructure.messaging.rabbitmq_blocking_publisher import (
    RabbitMqBlockingEventPublisher,
)
from src.infrastructure.messaging.rabbitmq_blocking_worker import (
    RabbitMqBlockingEventWorker,
)
from src.infrastructure.repositories.in_memory_admin_user_repository import (
    InMemoryAdminUserRepository,
)
from src.infrastructure.repositories.in_memory_customer_repository import (
    InMemoryCustomerRepository,
)
from src.infrastructure.repositories.in_memory_service_order_repository import (
    InMemoryServiceOrderRepository,
)
from src.infrastructure.repositories.in_memory_vehicle_repository import (
    InMemoryVehicleRepository,
)
from src.infrastructure.repositories.processed_event_repositories import (
    InMemoryProcessedEventRepository,
    SqlAlchemyProcessedEventRepository,
)
from src.infrastructure.repositories.sqlalchemy_admin_user_repository import (
    SqlAlchemyAdminUserRepository,
)
from src.infrastructure.repositories.sqlalchemy_customer_repository import (
    SqlAlchemyCustomerRepository,
)
from src.infrastructure.repositories.sqlalchemy_service_order_repository import (
    SqlAlchemyServiceOrderRepository,
)
from src.infrastructure.repositories.sqlalchemy_vehicle_repository import (
    SqlAlchemyVehicleRepository,
)
from src.infrastructure.security import AdminJwtService, PasswordHasher


def build_service_order_repository(settings: Settings):
    if settings.APP_RUNTIME_MODE == "real":
        return SqlAlchemyServiceOrderRepository(settings.DATABASE_URL)
    return InMemoryServiceOrderRepository()


def build_database_readiness_probe(settings: Settings):
    if settings.APP_RUNTIME_MODE != "real":
        return None

    validate_runtime_database_url(
        settings.DATABASE_URL,
        expected_database=settings.EXPECTED_DATABASE_NAME,
        expected_username=settings.EXPECTED_DATABASE_USERNAME,
    )
    return DatabaseReadinessProbe(
        settings.DATABASE_URL,
        expected_database=settings.EXPECTED_DATABASE_NAME,
        expected_username=settings.EXPECTED_DATABASE_USERNAME,
        timeout_seconds=settings.HEALTHCHECK_TIMEOUT_SECONDS,
    )


def build_customer_repository(settings: Settings):
    if settings.APP_RUNTIME_MODE == "real":
        return SqlAlchemyCustomerRepository(settings.DATABASE_URL)
    return InMemoryCustomerRepository()


def build_admin_user_repository(settings: Settings):
    if settings.APP_RUNTIME_MODE == "real":
        return SqlAlchemyAdminUserRepository(settings.DATABASE_URL)
    return InMemoryAdminUserRepository()


def build_vehicle_repository(settings: Settings):
    if settings.APP_RUNTIME_MODE == "real":
        return SqlAlchemyVehicleRepository(settings.DATABASE_URL)
    return InMemoryVehicleRepository()


def build_password_hasher() -> PasswordHasher:
    return PasswordHasher()


def build_admin_jwt_service(settings: Settings) -> AdminJwtService:
    return AdminJwtService(settings)


def build_event_publisher(settings: Settings):
    if settings.APP_RUNTIME_MODE == "real":
        return RabbitMqBlockingEventPublisher(
            settings.RABBITMQ_URL,
            settings.RABBITMQ_EXCHANGE,
            settings.RABBITMQ_ROUTING_KEY,
            settings.RABBITMQ_QUEUE,
        )
    return InMemoryEventPublisher()


def build_processed_event_repository(settings: Settings):
    if settings.APP_RUNTIME_MODE == "real":
        return SqlAlchemyProcessedEventRepository(settings.DATABASE_URL)
    return InMemoryProcessedEventRepository()


def build_event_worker(settings: Settings, handler):
    return RabbitMqBlockingEventWorker(
        settings.RABBITMQ_URL,
        settings.RABBITMQ_EXCHANGE,
        settings.RABBITMQ_QUEUE,
        settings.RABBITMQ_CONSUME_ROUTING_KEYS,
        handler,
    )
