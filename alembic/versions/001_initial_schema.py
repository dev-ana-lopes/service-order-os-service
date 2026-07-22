from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c54fccf2-3962-48ea-beae-b66f847c0642"
down_revision = None
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return inspector.has_table(table_name)


def upgrade() -> None:
    if not _has_table("service_orders"):
        op.create_table(
            "service_orders",
            sa.Column("service_order_id", sa.String(length=64), primary_key=True),
            sa.Column("customer_id", sa.String(length=128), nullable=False),
            sa.Column("vehicle_id", sa.String(length=128), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("status", sa.String(length=64), nullable=False),
            sa.Column("history", sa.JSON(), nullable=False),
        )

    if not _has_table("processed_events"):
        op.create_table(
            "processed_events",
            sa.Column("event_id", sa.String(length=64), primary_key=True),
            sa.Column("event_type", sa.String(length=128), nullable=False),
            sa.Column("correlation_id", sa.String(length=128), nullable=False),
            sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
        )

    if not _has_table("admin_users"):
        op.create_table(
            "admin_users",
            sa.Column("user_id", sa.String(length=64), primary_key=True),
            sa.Column("email", sa.String(length=255), nullable=False, unique=True),
            sa.Column("password_hash", sa.String(length=512), nullable=False),
            sa.Column("created_at", sa.String(length=64), nullable=False),
        )

    if not _has_table("customers"):
        op.create_table(
            "customers",
            sa.Column("customer_id", sa.String(length=64), primary_key=True),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("cpf_cnpj", sa.String(length=32), nullable=True, unique=True),
            sa.Column("email", sa.String(length=255), nullable=False, unique=True),
            sa.Column("phone", sa.String(length=32), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.String(length=64), nullable=False),
            sa.Column("updated_at", sa.String(length=64), nullable=False),
        )

    if not _has_table("vehicles"):
        op.create_table(
            "vehicles",
            sa.Column("vehicle_id", sa.String(length=64), primary_key=True),
            sa.Column("customer_id", sa.String(length=64), nullable=False),
            sa.Column("brand", sa.String(length=100), nullable=False),
            sa.Column("model", sa.String(length=100), nullable=False),
            sa.Column("year", sa.String(length=8), nullable=False),
            sa.Column("plate", sa.String(length=32), nullable=False, unique=True),
            sa.Column("created_at", sa.String(length=64), nullable=False),
            sa.Column("updated_at", sa.String(length=64), nullable=False),
        )


def downgrade() -> None:
    for table_name in (
        "vehicles",
        "customers",
        "admin_users",
        "processed_events",
        "service_orders",
    ):
        if _has_table(table_name):
            op.drop_table(table_name)
