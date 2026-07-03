import pytest

from src.domain.service_order import ServiceOrder, ServiceOrderStatus


def test_open_service_order_records_initial_status() -> None:
    service_order = ServiceOrder.open("customer-1", "vehicle-1", "Brake inspection")

    assert service_order.status == ServiceOrderStatus.OPENED
    assert service_order.history[0].status == ServiceOrderStatus.OPENED


def test_request_quote_moves_order_and_emits_event() -> None:
    service_order = ServiceOrder.open("customer-1", "vehicle-1", "Brake inspection")

    event = service_order.request_quote()

    assert service_order.status == ServiceOrderStatus.QUOTE_REQUESTED
    assert event.event_type == "OS_OPENED"
    assert event.correlation_id == service_order.service_order_id
    assert (
        event.to_message()["payload"]["service_order_id"]
        == service_order.service_order_id
    )


def test_quote_approval_requires_quote_requested_status() -> None:
    service_order = ServiceOrder.open("customer-1", "vehicle-1", "Brake inspection")

    with pytest.raises(ValueError, match="Quote can only be approved"):
        service_order.mark_quote_approved("quote-1")


def test_happy_path_reaches_completed_status() -> None:
    service_order = ServiceOrder.open("customer-1", "vehicle-1", "Brake inspection")

    service_order.request_quote()
    service_order.mark_quote_approved("quote-1")
    service_order.mark_payment_pending("payment-1")
    service_order.mark_payment_confirmed("payment-1")
    service_order.request_execution()
    service_order.mark_execution_started()
    event = service_order.complete()

    assert service_order.status == ServiceOrderStatus.COMPLETED
    assert event.event_type == "OS_COMPLETED"


def test_failure_status_emits_compensation_event_and_blocks_changes() -> None:
    service_order = ServiceOrder.open("customer-1", "vehicle-1", "Brake inspection")

    event = service_order.fail(ServiceOrderStatus.PAYMENT_FAILED, "Payment rejected")

    assert service_order.status == ServiceOrderStatus.PAYMENT_FAILED
    assert event.event_type == "OS_COMPENSATION_REQUIRED"
    with pytest.raises(ValueError, match="Terminal service orders cannot change status"):
        service_order.request_quote()
