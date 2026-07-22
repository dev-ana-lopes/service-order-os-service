from __future__ import annotations

from sqlalchemy import MetaData

from src.infrastructure.repositories.processed_event_repositories import (
    metadata as processed_event_metadata,
)
from src.infrastructure.repositories.sqlalchemy_admin_user_repository import (
    metadata as admin_user_metadata,
)
from src.infrastructure.repositories.sqlalchemy_customer_repository import (
    metadata as customer_metadata,
)
from src.infrastructure.repositories.sqlalchemy_service_order_repository import (
    metadata as service_order_metadata,
)
from src.infrastructure.repositories.sqlalchemy_vehicle_repository import (
    metadata as vehicle_metadata,
)

ALL_METADATA = (
    service_order_metadata,
    processed_event_metadata,
    admin_user_metadata,
    customer_metadata,
    vehicle_metadata,
)


def build_combined_metadata() -> MetaData:
    metadata = MetaData()
    for source_metadata in ALL_METADATA:
        for table in source_metadata.tables.values():
            table.to_metadata(metadata)
    return metadata
