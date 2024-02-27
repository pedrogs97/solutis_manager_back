"""Lending Filters"""

from typing import Optional

from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter

from src.lending.models import DocumentModel, DocumentTypeModel


class DocumentTypeFilter(Filter):
    """Document type filters"""

    name: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = DocumentTypeModel


class DocumentFilter(Filter):
    """Document filters"""

    doc_type: Optional[DocumentTypeFilter] = FilterDepends(
        with_prefix("doc_type", DocumentTypeFilter)
    )

    class Constants(Filter.Constants):
        """Filter constants"""

        model = DocumentModel
