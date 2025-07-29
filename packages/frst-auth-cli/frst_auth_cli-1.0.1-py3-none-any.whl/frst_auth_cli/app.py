from typing import Any


class App:
    def __init__(self, data: dict[str, Any]):
        self.data = data

    @property
    def uuid(self) -> str:
        return self.data.get("uuid")

    @property
    def name(self) -> str:
        return self.data.get("name")

    @property
    def permissions(self) -> list[str]:
        return self.data.get("permissions", [])

    def has_permission(self, permission: str) -> bool:
        """Check if the app has a specific permission."""
        return permission in self.permissions

    def has_any_permission(self, permissions: list[str]) -> bool:
        """Check if the app has any of the specified permissions."""
        return any(perm in self.permissions for perm in permissions)
