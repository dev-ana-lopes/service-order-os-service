from __future__ import annotations

from typing import Protocol

from src.domain.admin_user import AdminUser
from src.domain.events import DomainEvent
from src.domain.customer import Customer
from src.domain.service_order import ServiceOrder
from src.domain.vehicle import Vehicle


class ServiceOrderRepositoryPort(Protocol):
    def save(self, service_order: ServiceOrder) -> None:
        ...

    def get(self, service_order_id: str) -> ServiceOrder:
        ...


class EventPublisherPort(Protocol):
    def publish(self, event: DomainEvent) -> None:
        ...


class CustomerRepositoryPort(Protocol):
    def save(self, customer: Customer) -> None:
        ...

    def update(self, customer: Customer) -> None:
        ...

    def delete(self, customer_id: str) -> bool:
        ...

    def get(self, customer_id: str) -> Customer:
        ...

    def list(self) -> list[Customer]:
        ...

    def find_by_cpf_cnpj(self, cpf_cnpj: str) -> Customer | None:
        ...

    def find_by_email(self, email: str) -> Customer | None:
        ...


class VehicleRepositoryPort(Protocol):
    def save(self, vehicle: Vehicle) -> None:
        ...

    def update(self, vehicle: Vehicle) -> None:
        ...

    def delete(self, vehicle_id: str) -> bool:
        ...

    def get(self, vehicle_id: str) -> Vehicle:
        ...

    def list(self, customer_id: str | None = None) -> list[Vehicle]:
        ...

    def find_by_plate(self, plate: str) -> Vehicle | None:
        ...


class AdminUserRepositoryPort(Protocol):
    def save(self, user: AdminUser) -> None:
        ...

    def find_by_email(self, email: str) -> AdminUser | None:
        ...


class PasswordHasherPort(Protocol):
    def hash_password(self, password: str) -> str:
        ...

    def verify_password(self, password: str, password_hash: str) -> bool:
        ...


class AdminJwtServicePort(Protocol):
    def create_token(self, user_id: str, email: str) -> str:
        ...

    def verify_token(self, token: str) -> dict[str, object] | None:
        ...


class ProcessedEventRepositoryPort(Protocol):
    def is_processed(self, event_id: str) -> bool:
        ...

    def mark_processed(
        self, event_id: str, event_type: str, correlation_id: str
    ) -> None:
        ...
