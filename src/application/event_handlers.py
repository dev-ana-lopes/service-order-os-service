from __future__ import annotations

from datetime import datetime
from typing import Any

from src.application.ports import (
    EventPublisherPort,
    ProcessedEventRepositoryPort,
    ServiceOrderRepositoryPort,
)
from src.application.use_cases import HandleSagaEventUseCase
from src.domain.events import DomainEvent


class ServiceOrderSagaEventHandler:
    def __init__(
        self,
        service_order_repository: ServiceOrderRepositoryPort,
        publisher: EventPublisherPort,
        processed_events: ProcessedEventRepositoryPort,
    ) -> None:
        self._service_order_repository = service_order_repository
        self._publisher = publisher
        self._processed_events = processed_events

    def handle(self, message: dict[str, Any]) -> str:
        event_id = str(message["event_id"])
        event_type = str(message["event_type"])
        correlation_id = str(message["correlation_id"])
        if self._processed_events.is_processed(event_id):
            return "skipped"

        event = DomainEvent(
            event_id=event_id,
            event_type=event_type,
            correlation_id=correlation_id,
            occurred_at=datetime.fromisoformat(str(message["occurred_at"])),
            payload=dict(message["payload"]),
        )
        HandleSagaEventUseCase(
            self._service_order_repository,
            self._publisher,
        ).execute(event)
        self._processed_events.mark_processed(event_id, event_type, correlation_id)
        return "processed"
