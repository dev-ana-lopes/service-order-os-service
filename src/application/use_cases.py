from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from src.application.ports import (
    AdminJwtServicePort,
    AdminUserRepositoryPort,
    CustomerRepositoryPort,
    EventPublisherPort,
    PasswordHasherPort,
    ServiceOrderRepositoryPort,
    VehicleRepositoryPort,
)
from src.domain.admin_user import AdminUser
from src.domain.customer import Customer
from src.domain.events import DomainEvent
from src.domain.service_order import ServiceOrder, ServiceOrderStatus
from src.domain.vehicle import Vehicle


@dataclass(frozen=True, slots=True)
class OpenServiceOrderCommand:
    customer_id: str
    vehicle_id: str
    description: str


class OpenServiceOrderUseCase:
    def __init__(
        self,
        repository: ServiceOrderRepositoryPort,
        publisher: EventPublisherPort,
        customer_repository: CustomerRepositoryPort | None = None,
        vehicle_repository: VehicleRepositoryPort | None = None,
    ) -> None:
        self._repository = repository
        self._publisher = publisher
        self._customer_repository = customer_repository
        self._vehicle_repository = vehicle_repository

    def execute(self, command: OpenServiceOrderCommand) -> ServiceOrder:
        self._ensure_customer_vehicle_are_valid(
            command.customer_id,
            command.vehicle_id,
        )
        service_order = ServiceOrder.open(
            customer_id=command.customer_id,
            vehicle_id=command.vehicle_id,
            description=command.description,
        )
        event = service_order.request_quote()
        self._repository.save(service_order)
        self._publisher.publish(event)
        return service_order

    def _ensure_customer_vehicle_are_valid(
        self, customer_id: str, vehicle_id: str
    ) -> None:
        if self._customer_repository is None or self._vehicle_repository is None:
            return

        customer = self._customer_repository.get(customer_id)
        if not customer.is_active:
            raise ValueError("Customer is inactive")

        vehicle = self._vehicle_repository.get(vehicle_id)
        if vehicle.customer_id != customer.customer_id:
            raise ValueError("Vehicle does not belong to the informed customer")


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


@dataclass(frozen=True, slots=True)
class CreateCustomerCommand:
    name: str
    cpf_cnpj: str | None
    email: str
    phone: str
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class UpdateCustomerCommand:
    customer_id: str
    name: str
    cpf_cnpj: str | None
    email: str
    phone: str
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class CreateVehicleCommand:
    customer_id: str
    brand: str
    model: str
    year: int
    plate: str


@dataclass(frozen=True, slots=True)
class UpdateVehicleCommand:
    vehicle_id: str
    customer_id: str
    brand: str
    model: str
    year: int
    plate: str


class CreateCustomerUseCase:
    def __init__(self, repository: CustomerRepositoryPort) -> None:
        self._repository = repository

    def execute(self, command: CreateCustomerCommand) -> Customer:
        if command.cpf_cnpj and self._repository.find_by_cpf_cnpj(command.cpf_cnpj):
            raise ValueError("CPF/CNPJ already registered")
        if self._repository.find_by_email(command.email):
            raise ValueError("Email already registered")

        customer = Customer(
            name=command.name,
            cpf_cnpj=command.cpf_cnpj,
            email=command.email,
            phone=command.phone,
            is_active=command.is_active,
        )
        self._repository.save(customer)
        return customer


class UpdateCustomerUseCase:
    def __init__(self, repository: CustomerRepositoryPort) -> None:
        self._repository = repository

    def execute(self, command: UpdateCustomerCommand) -> Customer:
        customer = self._repository.get(command.customer_id)

        if command.cpf_cnpj and command.cpf_cnpj != customer.cpf_cnpj:
            other = self._repository.find_by_cpf_cnpj(command.cpf_cnpj)
            if other is not None and other.customer_id != command.customer_id:
                raise ValueError("CPF/CNPJ already registered")

        if command.email != customer.email:
            other_email = self._repository.find_by_email(command.email)
            if other_email is not None and other_email.customer_id != command.customer_id:
                raise ValueError("Email already registered")

        customer.name = command.name
        customer.cpf_cnpj = command.cpf_cnpj
        customer.email = command.email
        customer.phone = command.phone
        customer.is_active = command.is_active
        customer.updated_at = datetime.now(UTC)
        self._repository.update(customer)
        return customer


class ListCustomersUseCase:
    def __init__(self, repository: CustomerRepositoryPort) -> None:
        self._repository = repository

    def execute(self) -> list[Customer]:
        return self._repository.list()


class GetCustomerUseCase:
    def __init__(self, repository: CustomerRepositoryPort) -> None:
        self._repository = repository

    def execute(self, customer_id: str) -> Customer:
        return self._repository.get(customer_id)


class DeleteCustomerUseCase:
    def __init__(self, repository: CustomerRepositoryPort) -> None:
        self._repository = repository

    def execute(self, customer_id: str) -> bool:
        return self._repository.delete(customer_id)


class CreateVehicleUseCase:
    def __init__(
        self,
        repository: VehicleRepositoryPort,
        customer_repository: CustomerRepositoryPort,
    ) -> None:
        self._repository = repository
        self._customer_repository = customer_repository

    def execute(self, command: CreateVehicleCommand) -> Vehicle:
        self._customer_repository.get(command.customer_id)
        if self._repository.find_by_plate(command.plate):
            raise ValueError("Vehicle plate already registered")

        vehicle = Vehicle(
            customer_id=command.customer_id,
            brand=command.brand,
            model=command.model,
            year=command.year,
            plate=command.plate,
        )
        self._repository.save(vehicle)
        return vehicle


class UpdateVehicleUseCase:
    def __init__(
        self,
        repository: VehicleRepositoryPort,
        customer_repository: CustomerRepositoryPort,
    ) -> None:
        self._repository = repository
        self._customer_repository = customer_repository

    def execute(self, command: UpdateVehicleCommand) -> Vehicle:
        vehicle = self._repository.get(command.vehicle_id)
        self._customer_repository.get(command.customer_id)

        if command.plate != vehicle.plate:
            other = self._repository.find_by_plate(command.plate)
            if other is not None and other.vehicle_id != command.vehicle_id:
                raise ValueError("Vehicle plate already registered")

        vehicle.customer_id = command.customer_id
        vehicle.brand = command.brand
        vehicle.model = command.model
        vehicle.year = command.year
        vehicle.plate = command.plate
        vehicle.updated_at = datetime.now(UTC)
        self._repository.update(vehicle)
        return vehicle


class ListVehiclesUseCase:
    def __init__(self, repository: VehicleRepositoryPort) -> None:
        self._repository = repository

    def execute(self, customer_id: str | None = None) -> list[Vehicle]:
        return self._repository.list(customer_id)


class GetVehicleUseCase:
    def __init__(self, repository: VehicleRepositoryPort) -> None:
        self._repository = repository

    def execute(self, vehicle_id: str) -> Vehicle:
        return self._repository.get(vehicle_id)


class DeleteVehicleUseCase:
    def __init__(self, repository: VehicleRepositoryPort) -> None:
        self._repository = repository

    def execute(self, vehicle_id: str) -> bool:
        return self._repository.delete(vehicle_id)


@dataclass(frozen=True, slots=True)
class RegisterAdminUserCommand:
    email: str
    password: str


@dataclass(frozen=True, slots=True)
class LoginAdminUserCommand:
    email: str
    password: str


class RegisterAdminUserUseCase:
    def __init__(
        self,
        repository: AdminUserRepositoryPort,
        password_hasher: PasswordHasherPort,
    ) -> None:
        self._repository = repository
        self._password_hasher = password_hasher

    def execute(self, command: RegisterAdminUserCommand) -> AdminUser:
        existing = self._repository.find_by_email(command.email)
        if existing is not None:
            raise ValueError("Email already registered")

        user = AdminUser(
            email=command.email,
            password_hash=self._password_hasher.hash_password(command.password),
        )
        self._repository.save(user)
        return user


class LoginAdminUserUseCase:
    def __init__(
        self,
        repository: AdminUserRepositoryPort,
        password_hasher: PasswordHasherPort,
        jwt_service: AdminJwtServicePort,
    ) -> None:
        self._repository = repository
        self._password_hasher = password_hasher
        self._jwt_service = jwt_service

    def execute(self, command: LoginAdminUserCommand) -> str | None:
        user = self._repository.find_by_email(command.email)
        if user is None:
            return None
        if not self._password_hasher.verify_password(
            command.password, user.password_hash
        ):
            return None
        return self._jwt_service.create_token(user.user_id, user.email)
