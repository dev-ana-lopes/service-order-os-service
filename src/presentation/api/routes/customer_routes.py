from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field, field_validator

from src.application.use_cases import (
    CreateCustomerCommand,
    CreateCustomerUseCase,
    DeleteCustomerUseCase,
    GetCustomerUseCase,
    ListCustomersUseCase,
    UpdateCustomerCommand,
    UpdateCustomerUseCase,
)
from src.domain.auth import AuthenticatedPrincipal
from src.domain.customer import Customer
from src.domain.validation import is_valid_cpf_cnpj, normalize_digits
from src.presentation.dependencies.auth import require_admin_principal

router = APIRouter(prefix="/customers", tags=["customers"])


class CustomerRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    cpf_cnpj: str | None = None
    email: EmailStr
    phone: str = Field(min_length=1, max_length=32)
    is_active: bool = True

    @field_validator("cpf_cnpj")
    @classmethod
    def validate_cpf_cnpj(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not is_valid_cpf_cnpj(value):
            raise ValueError("Invalid CPF/CNPJ")
        return normalize_digits(value)


def customer_to_response(customer: Customer) -> dict[str, Any]:
    return {
        "customer_id": customer.customer_id,
        "name": customer.name,
        "cpf_cnpj": customer.cpf_cnpj,
        "email": customer.email,
        "phone": customer.phone,
        "is_active": customer.is_active,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_customer(
    payload: CustomerRequest,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_admin_principal),
) -> dict[str, Any]:
    del principal
    try:
        customer = CreateCustomerUseCase(request.app.state.customer_repository).execute(
            CreateCustomerCommand(
                name=payload.name,
                cpf_cnpj=payload.cpf_cnpj,
                email=str(payload.email),
                phone=payload.phone,
                is_active=payload.is_active,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    return customer_to_response(customer)


@router.get("")
def list_customers(
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_admin_principal),
) -> list[dict[str, Any]]:
    del principal
    customers = ListCustomersUseCase(request.app.state.customer_repository).execute()
    return [customer_to_response(customer) for customer in customers]


@router.get("/{customer_id}")
def get_customer(
    customer_id: str,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_admin_principal),
) -> dict[str, Any]:
    del principal
    try:
        customer = GetCustomerUseCase(request.app.state.customer_repository).execute(
            customer_id
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return customer_to_response(customer)


@router.put("/{customer_id}")
def update_customer(
    customer_id: str,
    payload: CustomerRequest,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_admin_principal),
) -> dict[str, bool]:
    del principal
    try:
        UpdateCustomerUseCase(request.app.state.customer_repository).execute(
            UpdateCustomerCommand(
                customer_id=customer_id,
                name=payload.name,
                cpf_cnpj=payload.cpf_cnpj,
                email=str(payload.email),
                phone=payload.phone,
                is_active=payload.is_active,
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


@router.delete("/{customer_id}")
def delete_customer(
    customer_id: str,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_admin_principal),
) -> dict[str, bool]:
    del principal
    deleted = DeleteCustomerUseCase(request.app.state.customer_repository).execute(
        customer_id
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return {"success": True}
