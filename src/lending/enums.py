"""Lending enums"""

from enum import Enum


class LendingBUEnum(str, Enum):
    """BU choices"""

    ADS = "ADS"
    CSA = "CSA"
    BPS = "BPS"
    CORP = "CORP"
