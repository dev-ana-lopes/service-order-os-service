from typing import Any

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from src.application.use_cases import (
    HandleSagaEventUseCase,
    OpenServiceOrderCommand,
    OpenServiceOrderUseCase,
)
from src.domain.events import DomainEvent
from src.domain.service_order import ServiceOrder, ServiceOrderStatus
from tests.application.test_use_cases import (
    EventCollector,
    InMemoryServiceOrderRepository,
)


@scenario(
    "features/saga_happy_path.feature",
    "Complete a service order after quote, payment, and execution events",
)
def test_service_order_saga_happy_path() -> None:
    """BDD coverage for the application-level saga happy path."""


@pytest.fixture
def context() -> dict[str, Any]:
    repository = InMemoryServiceOrderRepository()
    publisher = EventCollector()
    return {
        "repository": repository,
        "publisher": publisher,
        "handler": HandleSagaEventUseCase(repository, publisher),
    }


@given("a service order was opened")
def open_service_order(context: dict[str, Any]) -> None:
    service_order = OpenServiceOrderUseCase(
        context["repository"], context["publisher"]
    ).execute(OpenServiceOrderCommand("customer-1", "vehicle-1", "Brake inspection"))
    context["service_order"] = service_order


@when(parsers.parse("the {event_name}"))
def apply_named_event(context: dict[str, Any], event_name: str) -> None:
    service_order: ServiceOrder = context["service_order"]
    events = {
        "quote is approved": _event(
            "QUOTE_APPROVED", service_order.service_order_id, quote_id="quote-1"
        ),
        "payment preference is created": _event(
            "PAYMENT_PREFERENCE_CREATED",
            service_order.service_order_id,
            payment_id="payment-1",
        ),
        "payment is confirmed": _event(
            "PAYMENT_CONFIRMED", service_order.service_order_id, payment_id="payment-1"
        ),
        "execution starts": _event("EXECUTION_STARTED", service_order.service_order_id),
        "execution completes": _event(
            "EXECUTION_COMPLETED", service_order.service_order_id
        ),
    }
    context["service_order"] = context["handler"].execute(events[event_name])


@then("the service order status is completed")
def assert_completed(context: dict[str, Any]) -> None:
    assert context["service_order"].status == ServiceOrderStatus.COMPLETED


@then("the saga publishes the expected events")
def assert_published_events(context: dict[str, Any]) -> None:
    assert [event.event_type for event in context["publisher"].events] == [
        "OS_OPENED",
        "QUOTE_APPROVED",
        "PAYMENT_PENDING",
        "EXECUTION_REQUESTED",
        "EXECUTION_STARTED",
        "OS_COMPLETED",
    ]


def _event(event_type: str, service_order_id: str, **payload: str) -> DomainEvent:
    data = {"service_order_id": service_order_id}
    data.update(payload)
    return DomainEvent(
        event_type=event_type, correlation_id=service_order_id, payload=data
    )
