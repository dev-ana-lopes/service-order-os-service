from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from src.domain.auth import AuthenticatedPrincipal
from src.infrastructure.config.settings import Settings

bearer_scheme = HTTPBearer(auto_error=False)


def _resolve_principal(token: str, settings: Settings) -> AuthenticatedPrincipal | None:
    customer_principal = _verify_customer_token(token, settings)
    if customer_principal is not None:
        return customer_principal
    return _verify_admin_token(token, settings)


def _verify_customer_token(
    token: str, settings: Settings
) -> AuthenticatedPrincipal | None:
    if not settings.CUSTOMER_JWT_SECRET:
        return None
    try:
        payload = jwt.decode(
            token,
            settings.CUSTOMER_JWT_SECRET,
            algorithms=[settings.CUSTOMER_JWT_ALGORITHM],
            issuer=settings.CUSTOMER_JWT_ISSUER,
            options={"verify_aud": False},
        )
    except JWTError:
        return None
    if payload.get("role") != "customer":
        return None
    customer_id = payload.get("customer_id")
    subject = payload.get("sub")
    if not customer_id or not subject:
        return None
    return AuthenticatedPrincipal(
        subject=str(subject),
        role="customer",
        customer_id=str(customer_id),
        issuer=payload.get("iss"),
        claims=payload,
    )


def _verify_admin_token(token: str, settings: Settings) -> AuthenticatedPrincipal | None:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            options={"verify_aud": False},
        )
    except JWTError:
        return None
    if payload.get("role") != "admin":
        return None
    subject = payload.get("user_id") or payload.get("sub")
    if not subject:
        return None
    return AuthenticatedPrincipal(
        subject=str(subject),
        role="admin",
        customer_id=None,
        issuer=payload.get("iss"),
        claims=payload,
    )


async def get_current_principal(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedPrincipal:
    settings: Settings = request.app.state.settings
    if credentials is None or credentials.scheme.casefold() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    principal = _resolve_principal(credentials.credentials, settings)
    if principal is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired token",
        )
    request.state.principal = principal
    return principal


async def require_admin_principal(
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
) -> AuthenticatedPrincipal:
    if not principal.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return principal


async def require_customer_or_admin_principal(
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
) -> AuthenticatedPrincipal:
    if principal.role not in {"admin", "customer"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unsupported principal role",
        )
    return principal
