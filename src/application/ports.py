from __future__ import annotations

from typing import Protocol

from src.domain.events import DomainEvent
from src.domain.service_order import ServiceOrder


class ServiceOrderRepositoryPort(Protocol):
    def save(self, service_order: ServiceOrder) -> None:
        ...

    def get(self, service_order_id: str) -> ServiceOrder:
        ...


class EventPublisherPort(Protocol):
    def publish(self, event: DomainEvent) -> None:
        ...


class ProcessedEventRepositoryPort(Protocol):
    def is_processed(self, event_id: str) -> bool:
        ...

    def mark_processed(
        self, event_id: str, event_type: str, correlation_id: str
    ) -> None:
        ...
