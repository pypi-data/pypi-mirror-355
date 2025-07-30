from dataclasses import dataclass
from uuid import UUID

from ed_domain.core.aggregate_roots.base_aggregate_root import \
    BaseAggregateRoot
from ed_domain.core.value_objects.roles import (ROLE_PERMISSIONS_MAP,
                                                AdminRole, Permissions)


@dataclass
class Admin(BaseAggregateRoot):
    user_id: UUID
    first_name: str
    last_name: str
    phone_number: str
    email: str
    role: AdminRole

    def has_permission(self, permission: Permissions) -> bool:
        """
        Checks if the admin's role has the given permission.
        """
        return permission in ROLE_PERMISSIONS_MAP.get(self.role, set())

    @property
    def can_add_driver(self) -> bool:
        """Checks if the admin can add new drivers."""
        return self.has_permission(Permissions.ADD_DRIVER)

    @property
    def can_manage_users(self) -> bool:
        """Checks if the admin can manage (create, delete, update) users."""
        return self.has_permission(Permissions.MANAGE_USERS)

    @property
    def can_view_inventory(self) -> bool:
        """Checks if the admin can read inventory information."""
        return self.has_permission(Permissions.READ_INVENTORY)

    @property
    def can_write_inventory(self) -> bool:
        """Checks if the admin can modify inventory information."""
        return self.has_permission(Permissions.WRITE_INVENTORY)

    @property
    def can_pay_out_drivers(self) -> bool:
        """Checks if the admin can pay out drivers."""
        return self.has_permission(Permissions.PAY_OUT_DRIVERS)

    @property
    def can_receive_money_from_drivers(self) -> bool:
        """Checks if the admin can receive_money_from_drivers."""
        return self.has_permission(Permissions.RECEIVE_MONEY_FROM_DRIVERS)

    @property
    def can_view_financial_reports(self) -> bool:
        """Checks if the admin can view financial reports."""
        return self.has_permission(Permissions.VIEW_FINANCIAL_REPORTS)

    @property
    def can_manage_orders(self) -> bool:
        """Checks if the admin can manage (create, view, update, cancel) orders."""
        return self.has_permission(Permissions.MANAGE_ORDERS)

    @property
    def is_super_admin(self) -> bool:
        """Checks if the admin has the Super Admin role."""
        return self.role == AdminRole.SUPER_ADMIN
