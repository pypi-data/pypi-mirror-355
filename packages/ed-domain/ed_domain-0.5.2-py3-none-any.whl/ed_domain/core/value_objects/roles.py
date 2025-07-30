from enum import StrEnum


class Permissions(StrEnum):
    # Inventory Permissions
    READ_INVENTORY = "read_inventory"
    WRITE_INVENTORY = "write_inventory"
    MANAGE_INVENTORY = "manage_inventory"

    # User Management Permissions
    MANAGE_USERS = "manage_users"
    CREATE_USERS = "create_users"
    DELETE_USERS = "delete_users"

    # Driver Management Permissions
    ADD_DRIVER = "add_driver"
    VIEW_DRIVERS = "view_drivers"
    MANAGE_DRIVERS = "manage_drivers"  # Broader permission

    # Order Management Permissions
    CREATE_ORDER = "create_order"
    VIEW_ORDERS = "view_orders"
    UPDATE_ORDER_STATUS = "update_order_status"
    CANCEL_ORDER = "cancel_order"
    MANAGE_ORDERS = "manage_orders"  # Broader permission

    # Financial Permissions
    VIEW_FINANCIAL_REPORTS = "view_financial_reports"
    MANAGE_FINANCIAL_TRANSACTIONS = "manage_financial_transactions"
    PAY_OUT_DRIVERS = "pay_out_drivers"
    RECEIVE_MONEY_FROM_DRIVERS = "receive_money_from_drivers"

    # System Configuration Permissions
    CONFIGURE_SETTINGS = "configure_settings"
    VIEW_AUDIT_LOGS = "view_audit_logs"


class AdminRole(StrEnum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    WAREHOUSE_WORKER = "warehouse_worker"
    ACCOUNTANT = "accountant"


ROLE_PERMISSIONS_MAP = {
    AdminRole.SUPER_ADMIN: {
        Permissions.READ_INVENTORY,
        Permissions.WRITE_INVENTORY,
        Permissions.MANAGE_INVENTORY,
        Permissions.MANAGE_USERS,
        Permissions.CREATE_USERS,
        Permissions.DELETE_USERS,
        Permissions.ADD_DRIVER,
        Permissions.VIEW_DRIVERS,
        Permissions.MANAGE_DRIVERS,
        Permissions.CREATE_ORDER,
        Permissions.VIEW_ORDERS,
        Permissions.UPDATE_ORDER_STATUS,
        Permissions.CANCEL_ORDER,
        Permissions.MANAGE_ORDERS,
        Permissions.VIEW_FINANCIAL_REPORTS,
        Permissions.MANAGE_FINANCIAL_TRANSACTIONS,
        Permissions.CONFIGURE_SETTINGS,
        Permissions.VIEW_AUDIT_LOGS,
    },
    AdminRole.ADMIN: {
        Permissions.READ_INVENTORY,
        Permissions.WRITE_INVENTORY,
        Permissions.MANAGE_USERS,
        Permissions.CREATE_USERS,
        Permissions.ADD_DRIVER,
        Permissions.VIEW_DRIVERS,
        Permissions.CREATE_ORDER,
        Permissions.VIEW_ORDERS,
        Permissions.UPDATE_ORDER_STATUS,
        Permissions.CANCEL_ORDER,
        Permissions.VIEW_AUDIT_LOGS,
    },
    AdminRole.WAREHOUSE_WORKER: {
        Permissions.READ_INVENTORY,
        Permissions.WRITE_INVENTORY,
        Permissions.VIEW_ORDERS,
        Permissions.UPDATE_ORDER_STATUS,
    },
    AdminRole.ACCOUNTANT: {
        Permissions.VIEW_FINANCIAL_REPORTS,
        Permissions.MANAGE_FINANCIAL_TRANSACTIONS,
        Permissions.VIEW_ORDERS,
        Permissions.PAY_OUT_DRIVERS,
        Permissions.RECEIVE_MONEY_FROM_DRIVERS,
    },
}
