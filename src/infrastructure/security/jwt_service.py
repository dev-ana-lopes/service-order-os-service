from __future__ import annotations

from datetime import timedelta
from typing import Any

from jose import JWTError, jwt

from src.infrastructure.config.settings import Settings
from src.infrastructure.time import utcnow


class AdminJwtService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def create_token(self, user_id: str, email: str) -> str:
        expire = utcnow() + timedelta(minutes=self._settings.JWT_EXPIRATION_MINUTES)
        payload = {
            "user_id": user_id,
            "email": email,
            "role": "admin",
            "iss": self._settings.JWT_ISSUER,
            "exp": expire,
        }
        return jwt.encode(
            payload,
            self._settings.JWT_SECRET,
            algorithm=self._settings.JWT_ALGORITHM,
        )

    def verify_token(self, token: str) -> dict[str, Any] | None:
        try:
            return jwt.decode(
                token,
                self._settings.JWT_SECRET,
                algorithms=[self._settings.JWT_ALGORITHM],
                issuer=self._settings.JWT_ISSUER,
                options={"verify_aud": False},
            )
        except JWTError:
            return None
