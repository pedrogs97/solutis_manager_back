from typing import TypedDict


class PermissionDict(TypedDict):
    module: str
    model: str
    action: str
