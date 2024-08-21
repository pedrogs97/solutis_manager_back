"""Term enums"""

from enum import Enum


class SizesEnum(str, Enum):
    """Sizes enum"""

    PP = "PP"
    P = "P"
    M = "M"
    G = "G"
    GG = "GG"
    XG = "XG"
    XGG = "XGG"
