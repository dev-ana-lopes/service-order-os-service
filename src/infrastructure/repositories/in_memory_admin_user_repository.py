from __future__ import annotations

from src.domain.admin_user import AdminUser


class InMemoryAdminUserRepository:
    def __init__(self) -> None:
        self._items: dict[str, AdminUser] = {}

    def save(self, user: AdminUser) -> None:
        self._items[user.user_id] = user

    def find_by_email(self, email: str) -> AdminUser | None:
        normalized = email.casefold()
        return next(
            (
                item
                for item in self._items.values()
                if item.email.casefold() == normalized
            ),
            None,
        )
