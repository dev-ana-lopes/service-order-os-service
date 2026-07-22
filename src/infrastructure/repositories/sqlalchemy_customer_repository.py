from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, MetaData, String, Table, create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from src.domain.customer import Customer
from src.infrastructure.repositories.sqlalchemy_service_order_repository import (
    normalize_sync_database_url,
)

metadata = MetaData()

customers = Table(
    "customers",
    metadata,
    Column("customer_id", String(64), primary_key=True),
    Column("name", String(255), nullable=False),
    Column("cpf_cnpj", String(32), nullable=True, unique=True),
    Column("email", String(255), nullable=False, unique=True),
    Column("phone", String(32), nullable=False),
    Column("is_active", Boolean, nullable=False, default=True),
    Column("created_at", String(64), nullable=False),
    Column("updated_at", String(64), nullable=False),
)


class SqlAlchemyCustomerRepository:
    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(normalize_sync_database_url(database_url))
        metadata.create_all(self._engine)
        self._session_factory = sessionmaker(bind=self._engine)

    @classmethod
    def from_engine(cls, engine: Engine) -> "SqlAlchemyCustomerRepository":
        repository = cls.__new__(cls)
        repository._engine = engine
        metadata.create_all(engine)
        repository._session_factory = sessionmaker(bind=engine)
        return repository

    def save(self, customer: Customer) -> None:
        with self._session_factory() as session:
            session.execute(
                customers.insert().values(
                    customer_id=customer.customer_id,
                    name=customer.name,
                    cpf_cnpj=customer.cpf_cnpj,
                    email=customer.email,
                    phone=customer.phone,
                    is_active=customer.is_active,
                    created_at=customer.created_at.isoformat(),
                    updated_at=customer.updated_at.isoformat(),
                )
            )
            session.commit()

    def update(self, customer: Customer) -> None:
        with self._session_factory() as session:
            session.execute(
                customers.update()
                .where(customers.c.customer_id == customer.customer_id)
                .values(
                    name=customer.name,
                    cpf_cnpj=customer.cpf_cnpj,
                    email=customer.email,
                    phone=customer.phone,
                    is_active=customer.is_active,
                    updated_at=customer.updated_at.isoformat(),
                )
            )
            session.commit()

    def delete(self, customer_id: str) -> bool:
        with self._session_factory() as session:
            deleted = session.execute(
                customers.delete().where(customers.c.customer_id == customer_id)
            ).rowcount
            session.commit()
        return bool(deleted)

    def get(self, customer_id: str) -> Customer:
        with self._session_factory() as session:
            row = (
                session.execute(
                    select(customers).where(customers.c.customer_id == customer_id)
                )
                .mappings()
                .first()
            )
        if row is None:
            raise KeyError(f"Customer not found: {customer_id}")
        return self._from_row(dict(row))

    def list(self) -> list[Customer]:
        with self._session_factory() as session:
            rows = session.execute(select(customers)).mappings().all()
        return [self._from_row(dict(row)) for row in rows]

    def find_by_cpf_cnpj(self, cpf_cnpj: str) -> Customer | None:
        with self._session_factory() as session:
            row = (
                session.execute(
                    select(customers).where(customers.c.cpf_cnpj == cpf_cnpj)
                )
                .mappings()
                .first()
            )
        return None if row is None else self._from_row(dict(row))

    def find_by_email(self, email: str) -> Customer | None:
        with self._session_factory() as session:
            row = (
                session.execute(select(customers).where(customers.c.email == email))
                .mappings()
                .first()
            )
        return None if row is None else self._from_row(dict(row))

    def _from_row(self, row: dict[str, object]) -> Customer:
        return Customer(
            customer_id=str(row["customer_id"]),
            name=str(row["name"]),
            cpf_cnpj=None if row["cpf_cnpj"] is None else str(row["cpf_cnpj"]),
            email=str(row["email"]),
            phone=str(row["phone"]),
            is_active=bool(row["is_active"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
        )
