from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field, field_validator

from src.application.use_cases import (
    CreateVehicleCommand,
    CreateVehicleUseCase,
    DeleteVehicleUseCase,
    GetVehicleUseCase,
    ListVehiclesUseCase,
    UpdateVehicleCommand,
    UpdateVehicleUseCase,
)
from src.domain.auth import AuthenticatedPrincipal
from src.domain.validation import is_valid_br_plate, normalize_plate
from src.domain.vehicle import Vehicle
from src.presentation.dependencies.auth import require_admin_principal

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


class VehicleRequest(BaseModel):
    customer_id: str
    brand: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=1900, le=2100)
    plate: str = Field(min_length=1, max_length=20)

    @field_validator("plate")
    @classmethod
    def validate_plate(cls, value: str) -> str:
        if not is_valid_br_plate(value):
            raise ValueError("Invalid vehicle plate")
        return normalize_plate(value)


def vehicle_to_response(vehicle: Vehicle) -> dict[str, Any]:
    return {
        "vehicle_id": vehicle.vehicle_id,
        "customer_id": vehicle.customer_id,
        "brand": vehicle.brand,
        "model": vehicle.model,
        "year": vehicle.year,
        "plate": vehicle.plate,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_vehicle(
    payload: VehicleRequest,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_admin_principal),
) -> dict[str, Any]:
    del principal
    try:
        vehicle = CreateVehicleUseCase(
            request.app.state.vehicle_repository,
            request.app.state.customer_repository,
        ).execute(
            CreateVehicleCommand(
                customer_id=payload.customer_id,
                brand=payload.brand,
                model=payload.model,
                year=payload.year,
                plate=payload.plate,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    return vehicle_to_response(vehicle)


@router.get("")
def list_vehicles(
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_admin_principal),
    customer_id: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    del principal
    vehicles = ListVehiclesUseCase(request.app.state.vehicle_repository).execute(
        customer_id
    )
    return [vehicle_to_response(vehicle) for vehicle in vehicles]


@router.get("/{vehicle_id}")
def get_vehicle(
    vehicle_id: str,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_admin_principal),
) -> dict[str, Any]:
    del principal
    try:
        vehicle = GetVehicleUseCase(request.app.state.vehicle_repository).execute(
            vehicle_id
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return vehicle_to_response(vehicle)


@router.put("/{vehicle_id}")
def update_vehicle(
    vehicle_id: str,
    payload: VehicleRequest,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_admin_principal),
) -> dict[str, bool]:
    del principal
    try:
        UpdateVehicleUseCase(
            request.app.state.vehicle_repository,
            request.app.state.customer_repository,
        ).execute(
            UpdateVehicleCommand(
                vehicle_id=vehicle_id,
                customer_id=payload.customer_id,
                brand=payload.brand,
                model=payload.model,
                year=payload.year,
                plate=payload.plate,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    return {"success": True}


@router.delete("/{vehicle_id}")
def delete_vehicle(
    vehicle_id: str,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_admin_principal),
) -> dict[str, bool]:
    del principal
    deleted = DeleteVehicleUseCase(request.app.state.vehicle_repository).execute(
        vehicle_id
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return {"success": True}
