"""Service order aggregate and saga status rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from src.domain.events import DomainEvent


class ServiceOrderStatus(StrEnum):
    OPENED = "OPENED"
    QUOTE_REQUESTED = "QUOTE_REQUESTED"
    QUOTE_FAILED = "QUOTE_FAILED"
    QUOTE_APPROVED = "QUOTE_APPROVED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAYMENT_CONFIRMED = "PAYMENT_CONFIRMED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    EXECUTION_REQUESTED = "EXECUTION_REQUESTED"
    EXECUTION_ENQUEUE_FAILED = "EXECUTION_ENQUEUE_FAILED"
    EXECUTION_IN_PROGRESS = "EXECUTION_IN_PROGRESS"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    COMPLETED = "COMPLETED"


TERMINAL_STATUSES = {
    ServiceOrderStatus.QUOTE_FAILED,
    ServiceOrderStatus.PAYMENT_FAILED,
    ServiceOrderStatus.EXECUTION_ENQUEUE_FAILED,
    ServiceOrderStatus.EXECUTION_FAILED,
    ServiceOrderStatus.COMPLETED,
}


@dataclass(frozen=True, slots=True)
class ServiceOrderHistoryEntry:
    status: ServiceOrderStatus
    reason: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class ServiceOrder:
    customer_id: str
    vehicle_id: str
    description: str
    service_order_id: str = field(default_factory=lambda: str(uuid4()))
    status: ServiceOrderStatus = ServiceOrderStatus.OPENED
    history: list[ServiceOrderHistoryEntry] = field(default_factory=list)

    @classmethod
    def open(cls, customer_id: str, vehicle_id: str, description: str) -> "ServiceOrder":
        if not customer_id.strip():
            raise ValueError("Customer id is required")
        if not vehicle_id.strip():
            raise ValueError("Vehicle id is required")
        if not description.strip():
            raise ValueError("Description is required")

        service_order = cls(
            customer_id=customer_id, vehicle_id=vehicle_id, description=description
        )
        service_order._record(ServiceOrderStatus.OPENED, "Service order opened")
        return service_order

    def request_quote(self) -> DomainEvent:
        self._transition(ServiceOrderStatus.QUOTE_REQUESTED, "Quote requested")
        return self._event(
            "OS_OPENED",
            {
                "service_order_id": self.service_order_id,
                "customer_id": self.customer_id,
                "vehicle_id": self.vehicle_id,
                "description": self.description,
            },
        )

    def mark_quote_approved(self, quote_id: str) -> DomainEvent:
        if self.status != ServiceOrderStatus.QUOTE_REQUESTED:
            raise ValueError("Quote can only be approved after it is requested")
        self._transition(ServiceOrderStatus.QUOTE_APPROVED, "Quote approved")
        return self._event(
            "QUOTE_APPROVED",
            {"service_order_id": self.service_order_id, "quote_id": quote_id},
        )

    def mark_payment_pending(self, payment_id: str) -> DomainEvent:
        if self.status != ServiceOrderStatus.QUOTE_APPROVED:
            raise ValueError("Payment can only start after quote approval")
        self._transition(
            ServiceOrderStatus.PAYMENT_PENDING, "Payment preference created"
        )
        return self._event(
            "PAYMENT_PENDING",
            {"service_order_id": self.service_order_id, "payment_id": payment_id},
        )

    def request_execution(self) -> DomainEvent:
        if self.status != ServiceOrderStatus.PAYMENT_CONFIRMED:
            raise ValueError(
                "Execution can only be requested after payment confirmation"
            )
        self._transition(ServiceOrderStatus.EXECUTION_REQUESTED, "Execution requested")
        return self._event(
            "EXECUTION_REQUESTED", {"service_order_id": self.service_order_id}
        )

    def mark_payment_confirmed(self, payment_id: str) -> DomainEvent:
        if self.status != ServiceOrderStatus.PAYMENT_PENDING:
            raise ValueError("Payment can only be confirmed after it is pending")
        self._transition(ServiceOrderStatus.PAYMENT_CONFIRMED, "Payment confirmed")
        return self._event(
            "PAYMENT_CONFIRMED",
            {"service_order_id": self.service_order_id, "payment_id": payment_id},
        )

    def mark_execution_started(self) -> DomainEvent:
        if self.status != ServiceOrderStatus.EXECUTION_REQUESTED:
            raise ValueError("Execution can only start after it is requested")
        self._transition(ServiceOrderStatus.EXECUTION_IN_PROGRESS, "Execution started")
        return self._event(
            "EXECUTION_STARTED", {"service_order_id": self.service_order_id}
        )

    def complete(self) -> DomainEvent:
        if self.status != ServiceOrderStatus.EXECUTION_IN_PROGRESS:
            raise ValueError(
                "Service order can only complete while execution is in progress"
            )
        self._transition(ServiceOrderStatus.COMPLETED, "Execution completed")
        return self._event("OS_COMPLETED", {"service_order_id": self.service_order_id})

    def fail(self, status: ServiceOrderStatus, reason: str) -> DomainEvent:
        if status not in TERMINAL_STATUSES - {ServiceOrderStatus.COMPLETED}:
            raise ValueError("Failure status must be a terminal failure")
        self._transition(status, reason)
        return self._event(
            "OS_COMPENSATION_REQUIRED",
            {
                "service_order_id": self.service_order_id,
                "status": status.value,
                "reason": reason,
            },
        )

    def _transition(self, status: ServiceOrderStatus, reason: str) -> None:
        if self.status in TERMINAL_STATUSES:
            raise ValueError("Terminal service orders cannot change status")
        self.status = status
        self._record(status, reason)

    def _record(self, status: ServiceOrderStatus, reason: str) -> None:
        self.history.append(ServiceOrderHistoryEntry(status=status, reason=reason))

    def _event(self, event_type: str, payload: dict[str, str]) -> DomainEvent:
        return DomainEvent(
            event_type=event_type, correlation_id=self.service_order_id, payload=payload
        )
