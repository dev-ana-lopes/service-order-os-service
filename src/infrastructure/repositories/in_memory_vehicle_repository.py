from __future__ import annotations

from src.domain.vehicle import Vehicle


class InMemoryVehicleRepository:
    def __init__(self) -> None:
        self._items: dict[str, Vehicle] = {}

    def save(self, vehicle: Vehicle) -> None:
        self._items[vehicle.vehicle_id] = vehicle

    def update(self, vehicle: Vehicle) -> None:
        self._items[vehicle.vehicle_id] = vehicle

    def delete(self, vehicle_id: str) -> bool:
        return self._items.pop(vehicle_id, None) is not None

    def get(self, vehicle_id: str) -> Vehicle:
        try:
            return self._items[vehicle_id]
        except KeyError as exc:
            raise KeyError(f"Vehicle not found: {vehicle_id}") from exc

    def list(self, customer_id: str | None = None) -> list[Vehicle]:
        vehicles = list(self._items.values())
        if customer_id is None:
            return vehicles
        return [vehicle for vehicle in vehicles if vehicle.customer_id == customer_id]

    def find_by_plate(self, plate: str) -> Vehicle | None:
        return next((item for item in self._items.values() if item.plate == plate), None)
