from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field

from src.application.use_cases import (
    LoginAdminUserCommand,
    LoginAdminUserUseCase,
    RegisterAdminUserCommand,
    RegisterAdminUserUseCase,
)
from src.domain.auth import AuthenticatedPrincipal
from src.presentation.dependencies.auth import get_current_principal

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class RegisterResponse(BaseModel):
    user_id: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class LoginResponse(BaseModel):
    access_token: str


def _login(
    request: Request,
    email: str,
    password: str,
) -> LoginResponse:
    token = LoginAdminUserUseCase(
        request.app.state.admin_user_repository,
        request.app.state.password_hasher,
        request.app.state.admin_jwt_service,
    ).execute(LoginAdminUserCommand(email=email, password=password))
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return LoginResponse(access_token=token)


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(request_body: RegisterRequest, request: Request) -> RegisterResponse:
    try:
        user = RegisterAdminUserUseCase(
            request.app.state.admin_user_repository,
            request.app.state.password_hasher,
        ).execute(
            RegisterAdminUserCommand(
                email=str(request_body.email),
                password=request_body.password,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    return RegisterResponse(user_id=user.user_id)


@router.post("/login")
def login(request_body: LoginRequest, request: Request) -> LoginResponse:
    return _login(
        request,
        email=str(request_body.email),
        password=request_body.password,
    )


@router.post("/token")
async def token(request: Request) -> LoginResponse:
    form = await request.form()
    return _login(
        request,
        email=str(form.get("username", "")),
        password=str(form.get("password", "")),
    )


@router.get("/validate")
def validate_token(
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
) -> dict[str, str | None]:
    return {
        "subject": principal.subject,
        "role": principal.role,
        "customer_id": principal.customer_id,
        "issuer": principal.issuer,
        "email": None
        if "email" not in principal.claims
        else str(principal.claims["email"]),
    }
