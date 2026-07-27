from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from src.application.use_cases import (
    HandleSagaEventUseCase,
    OpenServiceOrderCommand,
    OpenServiceOrderUseCase,
)
from src.domain.auth import AuthenticatedPrincipal
from src.domain.events import DomainEvent
from src.domain.service_order import ServiceOrder, ServiceOrderHistoryEntry
from src.presentation.dependencies.auth import (
    require_admin_principal,
    require_customer_or_admin_principal,
)

router = APIRouter(prefix="/service-orders", tags=["service-orders"])


class OpenServiceOrderRequest(BaseModel):
    customer_id: str
    vehicle_id: str
    description: str


class SagaEventRequest(BaseModel):
    event_type: str
    correlation_id: str
    payload: dict[str, Any]


def history_to_response(entry: ServiceOrderHistoryEntry) -> dict[str, str]:
    return {
        "status": entry.status.value,
        "reason": entry.reason,
        "created_at": entry.created_at.isoformat(),
    }


def service_order_to_response(service_order: ServiceOrder) -> dict[str, Any]:
    return {
        "service_order_id": service_order.service_order_id,
        "customer_id": service_order.customer_id,
        "vehicle_id": service_order.vehicle_id,
        "description": service_order.description,
        "status": service_order.status.value,
        "history": [history_to_response(entry) for entry in service_order.history],
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def open_service_order(
    payload: OpenServiceOrderRequest,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_customer_or_admin_principal),
) -> dict[str, Any]:
    use_case = OpenServiceOrderUseCase(
        request.app.state.service_order_repository,
        request.app.state.event_publisher,
        request.app.state.customer_repository,
        request.app.state.vehicle_repository,
    )
    customer_id = payload.customer_id
    if principal.is_customer:
        if payload.customer_id != principal.customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Customer token cannot create service orders for another customer"
                ),
            )
        customer_id = str(principal.customer_id)
    try:
        service_order = use_case.execute(
            OpenServiceOrderCommand(
                customer_id=customer_id,
                vehicle_id=payload.vehicle_id,
                description=payload.description,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return service_order_to_response(service_order)


@router.get("/{service_order_id}")
def get_service_order(
    service_order_id: str,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_customer_or_admin_principal),
) -> dict[str, Any]:
    try:
        service_order = request.app.state.service_order_repository.get(service_order_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    if principal.is_customer and service_order.customer_id != principal.customer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer token cannot access another customer's service order",
        )
    return service_order_to_response(service_order)


@router.post("/{service_order_id}/events")
def handle_saga_event(
    service_order_id: str,
    payload: SagaEventRequest,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_admin_principal),
) -> dict[str, Any]:
    del principal
    event_payload = {"service_order_id": service_order_id}
    event_payload.update(payload.payload)
    event = DomainEvent(
        event_type=payload.event_type,
        correlation_id=payload.correlation_id,
        payload=event_payload,
    )
    use_case = HandleSagaEventUseCase(
        request.app.state.service_order_repository,
        request.app.state.event_publisher,
    )
    try:
        service_order = use_case.execute(event)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return service_order_to_response(service_order)
