from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column, MetaData, String, Table, Text, create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from src.domain.service_order import (
    ServiceOrder,
    ServiceOrderHistoryEntry,
    ServiceOrderStatus,
)

metadata = MetaData()

service_orders = Table(
    "service_orders",
    metadata,
    Column("service_order_id", String(64), primary_key=True),
    Column("customer_id", String(128), nullable=False),
    Column("vehicle_id", String(128), nullable=False),
    Column("description", Text, nullable=False),
    Column("status", String(64), nullable=False),
    Column("history", JSON, nullable=False),
)


def normalize_sync_database_url(database_url: str) -> str:
    return (
        database_url.replace("postgresql+asyncpg://", "postgresql+psycopg://")
        .replace("sqlite+aiosqlite://", "sqlite+pysqlite://")
        .replace("?ssl=require", "?sslmode=require")
    )


class SqlAlchemyServiceOrderRepository:
    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(normalize_sync_database_url(database_url))
        metadata.create_all(self._engine)
        self._session_factory = sessionmaker(bind=self._engine)

    @classmethod
    def from_engine(cls, engine: Engine) -> "SqlAlchemyServiceOrderRepository":
        repository = cls.__new__(cls)
        repository._engine = engine
        metadata.create_all(engine)
        repository._session_factory = sessionmaker(bind=engine)
        return repository

    def save(self, service_order: ServiceOrder) -> None:
        values = {
            "service_order_id": service_order.service_order_id,
            "customer_id": service_order.customer_id,
            "vehicle_id": service_order.vehicle_id,
            "description": service_order.description,
            "status": service_order.status.value,
            "history": [
                {
                    "status": entry.status.value,
                    "reason": entry.reason,
                    "created_at": entry.created_at.isoformat(),
                }
                for entry in service_order.history
            ],
        }
        with self._session_factory() as session:
            existing = session.execute(
                select(service_orders.c.service_order_id).where(
                    service_orders.c.service_order_id == service_order.service_order_id
                )
            ).scalar_one_or_none()
            if existing is None:
                session.execute(service_orders.insert().values(**values))
            else:
                session.execute(
                    service_orders.update()
                    .where(
                        service_orders.c.service_order_id
                        == service_order.service_order_id
                    )
                    .values(**values)
                )
            session.commit()

    def get(self, service_order_id: str) -> ServiceOrder:
        with self._session_factory() as session:
            row = (
                session.execute(
                    select(service_orders).where(
                        service_orders.c.service_order_id == service_order_id
                    )
                )
                .mappings()
                .first()
            )
        if row is None:
            raise KeyError(f"Service order not found: {service_order_id}")
        return self._from_row(dict(row))

    def _from_row(self, row: dict[str, Any]) -> ServiceOrder:
        raw_history = row["history"]
        if isinstance(raw_history, str):
            raw_history = json.loads(raw_history)
        return ServiceOrder(
            service_order_id=str(row["service_order_id"]),
            customer_id=str(row["customer_id"]),
            vehicle_id=str(row["vehicle_id"]),
            description=str(row["description"]),
            status=ServiceOrderStatus(str(row["status"])),
            history=[
                ServiceOrderHistoryEntry(
                    status=ServiceOrderStatus(str(entry["status"])),
                    reason=str(entry["reason"]),
                    created_at=datetime.fromisoformat(str(entry["created_at"])),
                )
                for entry in raw_history
            ],
        )
