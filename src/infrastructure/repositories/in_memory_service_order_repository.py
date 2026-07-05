from __future__ import annotations

from src.domain.service_order import ServiceOrder


class InMemoryServiceOrderRepository:
    def __init__(self) -> None:
        self._items: dict[str, ServiceOrder] = {}

    def save(self, service_order: ServiceOrder) -> None:
        self._items[service_order.service_order_id] = service_order

    def get(self, service_order_id: str) -> ServiceOrder:
        try:
            return self._items[service_order_id]
        except KeyError as exc:
            raise KeyError(f"Service order not found: {service_order_id}") from exc

    def clear(self) -> None:
        self._items.clear()
