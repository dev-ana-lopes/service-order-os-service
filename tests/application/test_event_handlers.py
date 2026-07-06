from src.application.event_handlers import ServiceOrderSagaEventHandler
from src.application.use_cases import OpenServiceOrderCommand, OpenServiceOrderUseCase
from src.domain.events import DomainEvent
from src.domain.service_order import ServiceOrderStatus
from src.infrastructure.messaging.in_memory_event_publisher import InMemoryEventPublisher
from src.infrastructure.repositories.in_memory_service_order_repository import (
    InMemoryServiceOrderRepository,
)
from src.infrastructure.repositories.processed_event_repositories import (
    InMemoryProcessedEventRepository,
)


def test_saga_worker_handler_processes_event_once() -> None:
    repository = InMemoryServiceOrderRepository()
    publisher = InMemoryEventPublisher()
    processed_events = InMemoryProcessedEventRepository()
    service_order = OpenServiceOrderUseCase(repository, publisher).execute(
        OpenServiceOrderCommand("customer-1", "vehicle-1", "Brake inspection")
    )
    message = DomainEvent(
        event_id="event-1",
        event_type="QUOTE_APPROVED",
        correlation_id=service_order.service_order_id,
        payload={"service_order_id": service_order.service_order_id, "quote_id": "q-1"},
    ).to_message()
    handler = ServiceOrderSagaEventHandler(repository, publisher, processed_events)

    first_result = handler.handle(message)
    second_result = handler.handle(message)

    assert first_result == "processed"
    assert second_result == "skipped"
    assert repository.get(service_order.service_order_id).status == (
        ServiceOrderStatus.QUOTE_APPROVED
    )
