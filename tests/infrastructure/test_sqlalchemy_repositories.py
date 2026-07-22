from src.domain.admin_user import AdminUser
from src.domain.customer import Customer
from src.domain.service_order import ServiceOrder, ServiceOrderStatus
from src.domain.vehicle import Vehicle
from src.infrastructure.repositories.processed_event_repositories import (
    SqlAlchemyProcessedEventRepository,
)
from src.infrastructure.repositories.sqlalchemy_customer_repository import (
    SqlAlchemyCustomerRepository,
)
from src.infrastructure.repositories.sqlalchemy_admin_user_repository import (
    SqlAlchemyAdminUserRepository,
)
from src.infrastructure.repositories.sqlalchemy_service_order_repository import (
    SqlAlchemyServiceOrderRepository,
)
from src.infrastructure.repositories.sqlalchemy_vehicle_repository import (
    SqlAlchemyVehicleRepository,
)


def test_sqlalchemy_service_order_repository_saves_and_restores_order() -> None:
    repository = SqlAlchemyServiceOrderRepository("sqlite+pysqlite:///:memory:")
    service_order = ServiceOrder.open("customer-1", "vehicle-1", "Brake inspection")
    service_order.request_quote()

    repository.save(service_order)
    restored = repository.get(service_order.service_order_id)

    assert restored.service_order_id == service_order.service_order_id
    assert restored.status == ServiceOrderStatus.QUOTE_REQUESTED
    assert restored.history[0].reason == "Service order opened"


def test_sqlalchemy_processed_event_repository_tracks_processed_events() -> None:
    repository = SqlAlchemyProcessedEventRepository("sqlite+pysqlite:///:memory:")

    assert repository.is_processed("event-1") is False

    repository.mark_processed("event-1", "QUOTE_APPROVED", "os-1")
    repository.mark_processed("event-1", "QUOTE_APPROVED", "os-1")

    assert repository.is_processed("event-1") is True


def test_sqlalchemy_customer_and_vehicle_repositories_support_lookup() -> None:
    customer_repository = SqlAlchemyCustomerRepository("sqlite+pysqlite:///:memory:")
    vehicle_repository = SqlAlchemyVehicleRepository("sqlite+pysqlite:///:memory:")
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

    assert customer_repository.find_by_email("cliente@example.com") is not None
    assert vehicle_repository.find_by_plate("BRA2A34") is not None


def test_sqlalchemy_admin_user_repository_supports_lookup() -> None:
    repository = SqlAlchemyAdminUserRepository("sqlite+pysqlite:///:memory:")
    user = AdminUser(
        user_id="admin-1",
        email="admin@example.com",
        password_hash="hash",
    )

    repository.save(user)

    restored = repository.find_by_email("admin@example.com")
    assert restored is not None
    assert restored.user_id == "admin-1"
