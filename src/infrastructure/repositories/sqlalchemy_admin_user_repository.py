from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, MetaData, String, Table, create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from src.domain.admin_user import AdminUser
from src.infrastructure.repositories.sqlalchemy_service_order_repository import (
    normalize_sync_database_url,
)

metadata = MetaData()

admin_users = Table(
    "admin_users",
    metadata,
    Column("user_id", String(64), primary_key=True),
    Column("email", String(255), nullable=False, unique=True),
    Column("password_hash", String(512), nullable=False),
    Column("created_at", String(64), nullable=False),
)


class SqlAlchemyAdminUserRepository:
    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(normalize_sync_database_url(database_url))
        metadata.create_all(self._engine)
        self._session_factory = sessionmaker(bind=self._engine)

    @classmethod
    def from_engine(cls, engine: Engine) -> "SqlAlchemyAdminUserRepository":
        repository = cls.__new__(cls)
        repository._engine = engine
        metadata.create_all(engine)
        repository._session_factory = sessionmaker(bind=engine)
        return repository

    def save(self, user: AdminUser) -> None:
        with self._session_factory() as session:
            session.execute(
                admin_users.insert().values(
                    user_id=user.user_id,
                    email=user.email,
                    password_hash=user.password_hash,
                    created_at=user.created_at.isoformat(),
                )
            )
            session.commit()

    def find_by_email(self, email: str) -> AdminUser | None:
        with self._session_factory() as session:
            row = (
                session.execute(select(admin_users).where(admin_users.c.email == email))
                .mappings()
                .first()
            )
        if row is None:
            return None
        return AdminUser(
            user_id=str(row["user_id"]),
            email=str(row["email"]),
            password_hash=str(row["password_hash"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )
