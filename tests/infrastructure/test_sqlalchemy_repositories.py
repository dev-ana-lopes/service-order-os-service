from src.domain.service_order import ServiceOrder, ServiceOrderStatus
from src.infrastructure.repositories.processed_event_repositories import (
    SqlAlchemyProcessedEventRepository,
)
from src.infrastructure.repositories.sqlalchemy_service_order_repository import (
    SqlAlchemyServiceOrderRepository,
)


def test_sqlalchemy_service_order_repository_saves_and_restores_order() -> None:
    repository = SqlAlchemyServiceOrderRepository("sqlite+pysqlite:///:memory:")
    service_order = ServiceOrder.open("customer-1", "vehicle-1", "Brake inspection")
    service_order.request_quote()

    repository.save(service_order)
    restored = repository.get(service_order.service_order_id)

    assert restored.service_order_id == service_order.service_order_id
    assert restored.status == ServiceOrderStatus.QUOTE_REQUESTED
    assert restored.history[0].reason == "Service order opened"


def test_sqlalchemy_processed_event_repository_tracks_processed_events() -> None:
    repository = SqlAlchemyProcessedEventRepository("sqlite+pysqlite:///:memory:")

    assert repository.is_processed("event-1") is False

    repository.mark_processed("event-1", "QUOTE_APPROVED", "os-1")
    repository.mark_processed("event-1", "QUOTE_APPROVED", "os-1")

    assert repository.is_processed("event-1") is True
