import pytest

from src.application.use_cases import (
    HandleSagaEventUseCase,
    LoginAdminUserCommand,
    LoginAdminUserUseCase,
    OpenServiceOrderCommand,
    OpenServiceOrderUseCase,
    RegisterAdminUserCommand,
    RegisterAdminUserUseCase,
)
from src.infrastructure.repositories.in_memory_admin_user_repository import (
    InMemoryAdminUserRepository,
)
from src.infrastructure.security import AdminJwtService, PasswordHasher
from src.infrastructure.config.settings import Settings
from src.domain.events import DomainEvent
from src.domain.service_order import ServiceOrder, ServiceOrderStatus


class InMemoryServiceOrderRepository:
    def __init__(self) -> None:
        self.items: dict[str, ServiceOrder] = {}

    def save(self, service_order: ServiceOrder) -> None:
        self.items[service_order.service_order_id] = service_order

    def get(self, service_order_id: str) -> ServiceOrder:
        return self.items[service_order_id]


class EventCollector:
    def __init__(self) -> None:
        self.events: list[DomainEvent] = []

    def publish(self, event: DomainEvent) -> None:
        self.events.append(event)


def test_open_service_order_persists_and_publishes_quote_request() -> None:
    repository = InMemoryServiceOrderRepository()
    publisher = EventCollector()
    use_case = OpenServiceOrderUseCase(repository, publisher)

    service_order = use_case.execute(
        OpenServiceOrderCommand("customer-1", "vehicle-1", "Brake inspection")
    )

    assert (
        repository.get(service_order.service_order_id).status
        == ServiceOrderStatus.QUOTE_REQUESTED
    )
    assert publisher.events[0].event_type == "OS_OPENED"


def test_handle_saga_happy_path_reaches_completed_status() -> None:
    repository = InMemoryServiceOrderRepository()
    publisher = EventCollector()
    service_order = OpenServiceOrderUseCase(repository, publisher).execute(
        OpenServiceOrderCommand("customer-1", "vehicle-1", "Brake inspection")
    )
    handler = HandleSagaEventUseCase(repository, publisher)

    handler.execute(
        _event("QUOTE_APPROVED", service_order.service_order_id, quote_id="quote-1")
    )
    handler.execute(
        _event(
            "PAYMENT_PREFERENCE_CREATED",
            service_order.service_order_id,
            payment_id="payment-1",
        )
    )
    handler.execute(
        _event(
            "PAYMENT_CONFIRMED", service_order.service_order_id, payment_id="payment-1"
        )
    )
    handler.execute(_event("EXECUTION_STARTED", service_order.service_order_id))
    completed = handler.execute(
        _event("EXECUTION_COMPLETED", service_order.service_order_id)
    )

    assert completed.status == ServiceOrderStatus.COMPLETED
    assert [event.event_type for event in publisher.events] == [
        "OS_OPENED",
        "QUOTE_APPROVED",
        "PAYMENT_PENDING",
        "EXECUTION_REQUESTED",
        "EXECUTION_STARTED",
        "OS_COMPLETED",
    ]


def test_handle_payment_failure_marks_order_as_failed() -> None:
    repository = InMemoryServiceOrderRepository()
    publisher = EventCollector()
    service_order = OpenServiceOrderUseCase(repository, publisher).execute(
        OpenServiceOrderCommand("customer-1", "vehicle-1", "Brake inspection")
    )
    handler = HandleSagaEventUseCase(repository, publisher)
    handler.execute(
        _event("QUOTE_APPROVED", service_order.service_order_id, quote_id="quote-1")
    )
    handler.execute(
        _event(
            "PAYMENT_PREFERENCE_CREATED",
            service_order.service_order_id,
            payment_id="payment-1",
        )
    )

    failed = handler.execute(
        _event("PAYMENT_FAILED", service_order.service_order_id, payment_id="payment-1")
    )

    assert failed.status == ServiceOrderStatus.PAYMENT_FAILED
    assert publisher.events[-1].event_type == "OS_COMPENSATION_REQUIRED"


def test_unsupported_saga_event_raises_error() -> None:
    repository = InMemoryServiceOrderRepository()
    publisher = EventCollector()
    service_order = OpenServiceOrderUseCase(repository, publisher).execute(
        OpenServiceOrderCommand("customer-1", "vehicle-1", "Brake inspection")
    )

    with pytest.raises(ValueError, match="Unsupported saga event"):
        HandleSagaEventUseCase(repository, publisher).execute(
            _event("UNKNOWN", service_order.service_order_id)
        )


def test_register_and_login_admin_user_use_cases() -> None:
    repository = InMemoryAdminUserRepository()
    password_hasher = PasswordHasher()
    jwt_service = AdminJwtService(
        Settings(
            ENVIRONMENT="test",
            JWT_SECRET="test-secret-value-with-32-characters",
        )
    )

    user = RegisterAdminUserUseCase(repository, password_hasher).execute(
        RegisterAdminUserCommand(
            email="admin@example.com",
            password="123456",
        )
    )
    token = LoginAdminUserUseCase(repository, password_hasher, jwt_service).execute(
        LoginAdminUserCommand(
            email="admin@example.com",
            password="123456",
        )
    )

    assert user.email == "admin@example.com"
    assert token is not None


def _event(event_type: str, service_order_id: str, **payload: str) -> DomainEvent:
    data = {"service_order_id": service_order_id}
    data.update(payload)
    return DomainEvent(
        event_type=event_type, correlation_id=service_order_id, payload=data
    )
