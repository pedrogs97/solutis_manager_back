"""Functional tests for the report module."""

from src.report.service import ReportService
from src.tests.base import TestBase


class TestReport(TestBase):
    """TestReport class."""

    def test_report_by_employee(self, setup):
        """Test report by employee."""
        report_service = ReportService()
        test_db_session = self.testing_session_local()
        report_service.report_by_employee(
            "2021-01-01",
            "2024-04-31",
            [],
            test_db_session,
        )
        test_db_session.close()
