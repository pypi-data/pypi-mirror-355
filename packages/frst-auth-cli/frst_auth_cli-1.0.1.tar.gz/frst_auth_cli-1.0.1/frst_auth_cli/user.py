from typing import Any
from frst_auth_cli.group import Group
from frst_auth_cli.company import Company
from frst_auth_cli.exceptions import CompanyNotFoundError
from frst_auth_cli.exceptions import GroupNotFoundError


class User:
    def __init__(self, data: dict[str, Any]):
        self.data = data
        self._groups_cache = None
        self._companies_cache = None

    @property
    def uuid(self) -> str:
        return self.data.get("uuid")

    @property
    def name(self) -> str:
        return self.data.get("name")

    @property
    def email(self) -> str:
        return self.data.get("email")

    @property
    def avatar(self) -> str:
        return self.data.get("avatar")

    @property
    def language(self) -> str:
        return self.data.get("language")

    @property
    def permissions(self) -> list[str]:
        return self.data.get("permissions", [])

    @property
    def companies(self) -> list[Company]:
        """Return a cached list of Company objects the user is linked to."""
        if self._companies_cache is None:
            companies_data = self.data.get("companies", [])
            self._companies_cache = [Company(c) for c in companies_data]
        return self._companies_cache

    @property
    def groups(self) -> list[Group]:
        if self._groups_cache is None:
            groups_data = self.data.get("groups", [])
            companies_by_uuid = {c.uuid: c for c in self.companies}
            group_objs = []
            for g in groups_data:
                company_uuid = g.get("origin_uuid")
                company = companies_by_uuid.get(company_uuid)
                group_objs.append(Group(g, company=company))
            self._groups_cache = group_objs
        return self._groups_cache

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def has_any_permission(self, permissions: list[str]) -> bool:
        return any(perm in self.permissions for perm in permissions)

    def get_group(self, uuid: str) -> Group:
        """
        Return the Group object for the given uuid.

        Raises:
            GroupNotFoundError: If no group with the given uuid exists.
        """
        for group in self.groups:
            if group.uuid == uuid:
                return group
        raise GroupNotFoundError(f"Group with uuid {uuid} not found")

    def get_group_default(self) -> Group:
        """
        Return the default group for this user.

        Raises:
            GroupNotFoundError: If the default group cannot be found.
        """
        return self.get_group(self.data.get('default_group', ''))

    def get_company(self, uuid: str) -> Company:
        """
        Return the Company object for the given uuid.

        Raises:
            CompanyNotFoundError: If no company with the given uuid exists.
        """
        for company in self.companies:
            if company.uuid == uuid:
                return company
        raise CompanyNotFoundError(f"Company with uuid {uuid} not found")
