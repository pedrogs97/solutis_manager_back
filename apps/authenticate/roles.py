"""Roles for authenticate module"""
from rolepermissions.roles import AbstractUserRole


class Assistant(AbstractUserRole):
    """Assistant permissions"""

    available_permissions = {
        # user
        "add_auth_user": False,
        "view_auth_user": True,
        "change_auth_user": True,
        "delete_auth_user": False,
        # lending
        "add_auth_lending": False,
        "view_auth_lending": True,
        "change_auth_lending": False,
        "delete_auth_lending": False,
    }


class Manager(AbstractUserRole):
    """Manager permissions"""

    available_permissions = {
        # user
        "add_auth_user": True,
        "view_auth_user": True,
        "change_auth_user": True,
        "delete_auth_user": True,
        # lending
        "add_auth_lending": True,
        "view_auth_lending": True,
        "change_auth_lending": True,
        "delete_auth_lending": True,
    }
