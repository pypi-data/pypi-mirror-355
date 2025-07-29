from typing import Any


class Company:
    def __init__(self, data: dict[str, Any]):
        self.data = data

    @property
    def uuid(self) -> str:
        return self.data.get("uuid")

    @property
    def name(self) -> str:
        return self.data.get("name")

    @property
    def area(self) -> dict[str, Any]:
        return self.data.get("area")

    @property
    def role(self) -> dict[str, Any]:
        return self.data.get("role")

    @property
    def apps(self) -> list[str]:
        return self.data.get("apps", [])

    @property
    def permissions(self) -> list[str]:
        return self.data.get("permissions", [])

    def has_permission(self, permission: str) -> bool:
        """Check if the company has a specific permission."""
        return permission in self.permissions

    def has_any_permission(self, permissions: list[str]) -> bool:
        """Check if the company has any of the specified permissions."""
        return any(perm in self.permissions for perm in permissions)
