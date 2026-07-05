from __future__ import annotations

from src.infrastructure.config.settings import Settings
from src.infrastructure.messaging.in_memory_event_publisher import InMemoryEventPublisher
from src.infrastructure.messaging.rabbitmq_blocking_publisher import (
    RabbitMqBlockingEventPublisher,
)
from src.infrastructure.repositories.in_memory_service_order_repository import (
    InMemoryServiceOrderRepository,
)
from src.infrastructure.repositories.sqlalchemy_service_order_repository import (
    SqlAlchemyServiceOrderRepository,
)


def build_service_order_repository(settings: Settings):
    if settings.APP_RUNTIME_MODE == "real":
        return SqlAlchemyServiceOrderRepository(settings.DATABASE_URL)
    return InMemoryServiceOrderRepository()


def build_event_publisher(settings: Settings):
    if settings.APP_RUNTIME_MODE == "real":
        return RabbitMqBlockingEventPublisher(
            settings.RABBITMQ_URL,
            settings.RABBITMQ_EXCHANGE,
            settings.RABBITMQ_ROUTING_KEY,
            settings.RABBITMQ_QUEUE,
        )
    return InMemoryEventPublisher()
