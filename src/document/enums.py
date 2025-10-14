"""Document enums"""

from enum import IntEnum


class DocumentTypeEnum(IntEnum):
    """Document type enum"""

    LENDING = 1
    TERM = 2
    REVOKE_LENDING = 3
    REVOKE_TERM = 4
