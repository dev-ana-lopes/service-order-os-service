"""Use cases for service order orchestration."""

from __future__ import annotations

from dataclasses import dataclass

from src.application.ports import EventPublisherPort, ServiceOrderRepositoryPort
from src.domain.events import DomainEvent
from src.domain.service_order import ServiceOrder, ServiceOrderStatus


@dataclass(frozen=True, slots=True)
class OpenServiceOrderCommand:
    customer_id: str
    vehicle_id: str
    description: str


class OpenServiceOrderUseCase:
    def __init__(
        self, repository: ServiceOrderRepositoryPort, publisher: EventPublisherPort
    ) -> None:
        self._repository = repository
        self._publisher = publisher

    def execute(self, command: OpenServiceOrderCommand) -> ServiceOrder:
        service_order = ServiceOrder.open(
            customer_id=command.customer_id,
            vehicle_id=command.vehicle_id,
            description=command.description,
        )
        event = service_order.request_quote()
        self._repository.save(service_order)
        self._publisher.publish(event)
        return service_order


class HandleSagaEventUseCase:
    def __init__(
        self, repository: ServiceOrderRepositoryPort, publisher: EventPublisherPort
    ) -> None:
        self._repository = repository
        self._publisher = publisher

    def execute(self, event: DomainEvent) -> ServiceOrder:
        service_order_id = str(
            event.payload.get("service_order_id") or event.correlation_id
        )
        service_order = self._repository.get(service_order_id)
        next_event = self._apply(event, service_order)
        self._repository.save(service_order)
        if next_event is not None:
            self._publisher.publish(next_event)
        return service_order

    def _apply(
        self, event: DomainEvent, service_order: ServiceOrder
    ) -> DomainEvent | None:
        if event.event_type == "QUOTE_APPROVED":
            return service_order.mark_quote_approved(str(event.payload["quote_id"]))
        if event.event_type == "PAYMENT_PREFERENCE_CREATED":
            return service_order.mark_payment_pending(str(event.payload["payment_id"]))
        if event.event_type == "PAYMENT_CONFIRMED":
            service_order.mark_payment_confirmed(str(event.payload["payment_id"]))
            return service_order.request_execution()
        if event.event_type == "EXECUTION_STARTED":
            return service_order.mark_execution_started()
        if event.event_type == "EXECUTION_COMPLETED":
            return service_order.complete()
        if event.event_type == "QUOTE_FAILED":
            return service_order.fail(
                ServiceOrderStatus.QUOTE_FAILED, "Quote creation failed"
            )
        if event.event_type == "PAYMENT_FAILED":
            return service_order.fail(
                ServiceOrderStatus.PAYMENT_FAILED, "Payment failed"
            )
        if event.event_type == "EXECUTION_ENQUEUE_FAILED":
            return service_order.fail(
                ServiceOrderStatus.EXECUTION_ENQUEUE_FAILED,
                "Execution enqueue failed",
            )
        if event.event_type == "EXECUTION_FAILED":
            return service_order.fail(
                ServiceOrderStatus.EXECUTION_FAILED, "Execution failed"
            )
        raise ValueError(f"Unsupported saga event: {event.event_type}")
