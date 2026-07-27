from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, MetaData, String, Table, create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from src.domain.vehicle import Vehicle
from src.infrastructure.repositories.sqlalchemy_service_order_repository import (
    normalize_sync_database_url,
)

metadata = MetaData()

vehicles = Table(
    "vehicles",
    metadata,
    Column("vehicle_id", String(64), primary_key=True),
    Column("customer_id", String(64), nullable=False),
    Column("brand", String(100), nullable=False),
    Column("model", String(100), nullable=False),
    Column("year", String(8), nullable=False),
    Column("plate", String(32), nullable=False, unique=True),
    Column("created_at", String(64), nullable=False),
    Column("updated_at", String(64), nullable=False),
)


class SqlAlchemyVehicleRepository:
    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(normalize_sync_database_url(database_url))
        metadata.create_all(self._engine)
        self._session_factory = sessionmaker(bind=self._engine)

    @classmethod
    def from_engine(cls, engine: Engine) -> "SqlAlchemyVehicleRepository":
        repository = cls.__new__(cls)
        repository._engine = engine
        metadata.create_all(engine)
        repository._session_factory = sessionmaker(bind=engine)
        return repository

    def save(self, vehicle: Vehicle) -> None:
        with self._session_factory() as session:
            session.execute(
                vehicles.insert().values(
                    vehicle_id=vehicle.vehicle_id,
                    customer_id=vehicle.customer_id,
                    brand=vehicle.brand,
                    model=vehicle.model,
                    year=str(vehicle.year),
                    plate=vehicle.plate,
                    created_at=vehicle.created_at.isoformat(),
                    updated_at=vehicle.updated_at.isoformat(),
                )
            )
            session.commit()

    def update(self, vehicle: Vehicle) -> None:
        with self._session_factory() as session:
            session.execute(
                vehicles.update()
                .where(vehicles.c.vehicle_id == vehicle.vehicle_id)
                .values(
                    customer_id=vehicle.customer_id,
                    brand=vehicle.brand,
                    model=vehicle.model,
                    year=str(vehicle.year),
                    plate=vehicle.plate,
                    updated_at=vehicle.updated_at.isoformat(),
                )
            )
            session.commit()

    def delete(self, vehicle_id: str) -> bool:
        with self._session_factory() as session:
            deleted = session.execute(
                vehicles.delete().where(vehicles.c.vehicle_id == vehicle_id)
            ).rowcount
            session.commit()
        return bool(deleted)

    def get(self, vehicle_id: str) -> Vehicle:
        with self._session_factory() as session:
            row = (
                session.execute(
                    select(vehicles).where(vehicles.c.vehicle_id == vehicle_id)
                )
                .mappings()
                .first()
            )
        if row is None:
            raise KeyError(f"Vehicle not found: {vehicle_id}")
        return self._from_row(dict(row))

    def list(self, customer_id: str | None = None) -> list[Vehicle]:
        query = select(vehicles)
        if customer_id is not None:
            query = query.where(vehicles.c.customer_id == customer_id)
        with self._session_factory() as session:
            rows = session.execute(query).mappings().all()
        return [self._from_row(dict(row)) for row in rows]

    def find_by_plate(self, plate: str) -> Vehicle | None:
        with self._session_factory() as session:
            row = (
                session.execute(select(vehicles).where(vehicles.c.plate == plate))
                .mappings()
                .first()
            )
        return None if row is None else self._from_row(dict(row))

    def _from_row(self, row: dict[str, object]) -> Vehicle:
        return Vehicle(
            vehicle_id=str(row["vehicle_id"]),
            customer_id=str(row["customer_id"]),
            brand=str(row["brand"]),
            model=str(row["model"]),
            year=int(row["year"]),
            plate=str(row["plate"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
        )
