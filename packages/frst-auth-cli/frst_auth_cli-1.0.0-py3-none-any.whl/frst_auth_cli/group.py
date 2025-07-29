from typing import Any
from frst_auth_cli.company import Company


class Group:

    def __init__(self, data: dict[str, Any], company: Company | None = None):  # noqa E501
        self.data = data
        self.company = company or Company({})
        self.__modules_cache = None
        self.__children_cache = None

    @property
    def uuid(self) -> str:
        return self.data.get("uuid")

    @property
    def name(self) -> str:
        return self.data.get("name")

    @property
    def group_type(self) -> str:
        return self.data.get("group_type")

    @property
    def type_uuid(self) -> str:
        return self.data.get("type_uuid")

    @property
    def origin_type(self) -> str:
        return self.data.get("origin_type")

    @property
    def origin_uuid(self) -> str:
        return self.data.get("origin_uuid")

    @property
    def permissions(self) -> list[str]:
        return self.data.get("permissions", [])

    @property
    def modules(self) -> list[dict]:
        return self.__modules.get('modules', [])

    @property
    def module_codes(self) -> list[str]:
        return self.__modules.get('codes', [])

    @property
    def module_default(self) -> str:
        return self.__modules.get('default', '')

    @property
    def __modules(self) -> dict:
        if self.__modules_cache is None:
            self.__modules_cache = {
                'modules': [],
                'codes': [],
                'default': ''
            }
            for module in self.data.get("modules", []):
                self.__modules_cache['modules'].append(module)
                self.__modules_cache['codes'].append(module.get('code', ''))
                if module.get('default', False):
                    self.__modules_cache['default'] = module.get('code', '')
        return self.__modules_cache

    @property
    def children(self) -> list["Group"]:
        if self.__children_cache is None:
            self.__children_cache = [
                Group(child, company=self.company)
                for child in self.data.get("children", [])
            ]
        return self.__children_cache

    def has_permission(self, permission: str) -> bool:
        """Check if the group has a specific permission."""
        return permission in self.permissions

    def has_any_permission(self, permissions: list[str]) -> bool:
        """Check if the group has any of the specified permissions."""
        return any(perm in self.permissions for perm in permissions)

    def has_module(self, code: str) -> bool:
        """Check if the group has a specific module."""
        return code in self.module_codes

    def has_any_module(self, codes: list[str]) -> bool:
        """Check if the group has any of the specified modules."""
        return any(code in self.module_codes for code in codes)
