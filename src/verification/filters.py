"""Verification filters"""
from typing import Optional

from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter

from src.asset.filters import AssetTypeFilter
from src.lending.filters import LendingFilter
from src.verification.models import (
    VerificationAnswerModel,
    VerificationModel,
    VerificationTypeModel,
)


class VerificationTypeFilter(Filter):
    """VerificationType filters"""

    name: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = VerificationTypeModel


class VerificationFilter(Filter):
    """Verification filters"""

    question_ilike: Optional[str] = None
    question_like: Optional[str] = None
    step: Optional[str] = None
    asset_type: Optional[AssetTypeFilter] = FilterDepends(
        with_prefix("asset_type", AssetTypeFilter)
    )

    class Constants(Filter.Constants):
        """Filter constants"""

        model = VerificationModel


class VerificationAnswerFilter(Filter):
    """VerificationAnswer filters"""

    answer_ilike: Optional[str] = None
    answer_like: Optional[str] = None
    type: Optional[VerificationTypeFilter] = FilterDepends(
        with_prefix("type", VerificationTypeFilter)
    )
    verification: Optional[VerificationFilter] = FilterDepends(
        with_prefix("verification", VerificationFilter)
    )
    lending: Optional[LendingFilter] = FilterDepends(
        with_prefix("lending", LendingFilter)
    )

    class Constants(Filter.Constants):
        """Filter constants"""

        model = VerificationAnswerModel
