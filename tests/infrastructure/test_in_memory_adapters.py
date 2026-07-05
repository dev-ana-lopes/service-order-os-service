import pytest

from src.application.use_cases import OpenServiceOrderCommand, OpenServiceOrderUseCase
from src.domain.events import DomainEvent
from src.infrastructure.messaging.in_memory_event_publisher import InMemoryEventPublisher
from src.infrastructure.repositories.in_memory_service_order_repository import (
    InMemoryServiceOrderRepository,
)


def test_in_memory_repository_and_publisher_support_use_case() -> None:
    repository = InMemoryServiceOrderRepository()
    publisher = InMemoryEventPublisher()

    service_order = OpenServiceOrderUseCase(repository, publisher).execute(
        OpenServiceOrderCommand("customer-1", "vehicle-1", "Brake inspection")
    )

    assert repository.get(service_order.service_order_id) is service_order
    assert publisher.events[0].event_type == "OS_OPENED"


def test_in_memory_repository_raises_when_service_order_is_missing() -> None:
    repository = InMemoryServiceOrderRepository()

    with pytest.raises(KeyError, match="Service order not found"):
        repository.get("missing")


def test_in_memory_publisher_keeps_event_order() -> None:
    publisher = InMemoryEventPublisher()
    first = DomainEvent(event_type="FIRST", correlation_id="os-1", payload={})
    second = DomainEvent(event_type="SECOND", correlation_id="os-1", payload={})

    publisher.publish(first)
    publisher.publish(second)

    assert publisher.events == [first, second]
