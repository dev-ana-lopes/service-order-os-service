from __future__ import annotations

from src.domain.customer import Customer


class InMemoryCustomerRepository:
    def __init__(self) -> None:
        self._items: dict[str, Customer] = {}

    def save(self, customer: Customer) -> None:
        self._items[customer.customer_id] = customer

    def update(self, customer: Customer) -> None:
        self._items[customer.customer_id] = customer

    def delete(self, customer_id: str) -> bool:
        return self._items.pop(customer_id, None) is not None

    def get(self, customer_id: str) -> Customer:
        try:
            return self._items[customer_id]
        except KeyError as exc:
            raise KeyError(f"Customer not found: {customer_id}") from exc

    def list(self) -> list[Customer]:
        return list(self._items.values())

    def find_by_cpf_cnpj(self, cpf_cnpj: str) -> Customer | None:
        return next(
            (item for item in self._items.values() if item.cpf_cnpj == cpf_cnpj),
            None,
        )

    def find_by_email(self, email: str) -> Customer | None:
        return next(
            (
                item
                for item in self._items.values()
                if item.email.casefold() == email.casefold()
            ),
            None,
        )
