from __future__ import annotations

from typing import Protocol

from src.domain.events import DomainEvent
from src.domain.service_order import ServiceOrder


class ServiceOrderRepositoryPort(Protocol):
    def save(self, service_order: ServiceOrder) -> None:
        pass

    def get(self, service_order_id: str) -> ServiceOrder:
        pass


class EventPublisherPort(Protocol):
    def publish(self, event: DomainEvent) -> None:
        pass
