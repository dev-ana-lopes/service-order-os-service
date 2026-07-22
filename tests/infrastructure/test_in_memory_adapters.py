import pytest

from src.application.use_cases import OpenServiceOrderCommand, OpenServiceOrderUseCase
from src.domain.customer import Customer
from src.domain.events import DomainEvent
from src.domain.vehicle import Vehicle
from src.infrastructure.messaging.in_memory_event_publisher import InMemoryEventPublisher
from src.infrastructure.repositories.in_memory_customer_repository import (
    InMemoryCustomerRepository,
)
from src.infrastructure.repositories.in_memory_service_order_repository import (
    InMemoryServiceOrderRepository,
)
from src.infrastructure.repositories.in_memory_vehicle_repository import (
    InMemoryVehicleRepository,
)


def test_in_memory_repository_and_publisher_support_use_case() -> None:
    repository = InMemoryServiceOrderRepository()
    customer_repository = InMemoryCustomerRepository()
    vehicle_repository = InMemoryVehicleRepository()
    customer_repository.save(
        Customer(
            customer_id="customer-1",
            name="Cliente",
            cpf_cnpj="11144477735",
            email="cliente@example.com",
            phone="11999999999",
        )
    )
    vehicle_repository.save(
        Vehicle(
            vehicle_id="vehicle-1",
            customer_id="customer-1",
            brand="Toyota",
            model="Corolla",
            year=2023,
            plate="BRA2A34",
        )
    )
    publisher = InMemoryEventPublisher()

    service_order = OpenServiceOrderUseCase(
        repository,
        publisher,
        customer_repository,
        vehicle_repository,
    ).execute(OpenServiceOrderCommand("customer-1", "vehicle-1", "Brake inspection"))

    assert repository.get(service_order.service_order_id) is service_order
    assert publisher.events[0].event_type == "OS_OPENED"


def test_in_memory_repository_raises_when_service_order_is_missing() -> None:
    repository = InMemoryServiceOrderRepository()

    with pytest.raises(KeyError, match="Service order not found"):
        repository.get("missing")


def test_in_memory_publisher_keeps_event_order() -> None:
    publisher = InMemoryEventPublisher()
    first = DomainEvent(event_type="OS_OPENED", correlation_id="os-1", payload={})
    second = DomainEvent(event_type="PAYMENT_PENDING", correlation_id="os-1", payload={})

    publisher.publish(first)
    publisher.publish(second)

    assert publisher.events == [first, second]


def test_in_memory_customer_and_vehicle_repositories_support_crud() -> None:
    customer_repository = InMemoryCustomerRepository()
    vehicle_repository = InMemoryVehicleRepository()
    customer = Customer(
        customer_id="customer-1",
        name="Cliente",
        cpf_cnpj="11144477735",
        email="cliente@example.com",
        phone="11999999999",
    )
    vehicle = Vehicle(
        vehicle_id="vehicle-1",
        customer_id="customer-1",
        brand="Toyota",
        model="Corolla",
        year=2023,
        plate="BRA2A34",
    )

    customer_repository.save(customer)
    vehicle_repository.save(vehicle)

    assert customer_repository.find_by_email("cliente@example.com") == customer
    assert vehicle_repository.find_by_plate("BRA2A34") == vehicle
    assert vehicle_repository.list("customer-1") == [vehicle]
