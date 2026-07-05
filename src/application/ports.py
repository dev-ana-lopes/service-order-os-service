"""Application ports for persistence and messaging."""

from __future__ import annotations

from typing import Protocol

from src.domain.events import DomainEvent
from src.domain.service_order import ServiceOrder


class ServiceOrderRepositoryPort(Protocol):
    def save(self, service_order: ServiceOrder) -> None:
        """Persist the current service order state."""

    def get(self, service_order_id: str) -> ServiceOrder:
        """Return a service order by id."""


class EventPublisherPort(Protocol):
    def publish(self, event: DomainEvent) -> None:
        """Publish an event to the asynchronous integration channel."""
