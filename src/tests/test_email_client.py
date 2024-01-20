"""Functional tests for email client"""
import pytest

from src.backends import Email365Client

pytest_plugins = ("pytest_asyncio",)


class TestEmail365Client:
    """
    Email client tests

    This class provides functional tests for the Email client.
    """

    @pytest.mark.asyncio
    async def test_send_message_sucess(self):
        """Test send message success case"""
        client = Email365Client(
            mail_to="pedrogustavosantana97@gmail.com",
            mail_subject="teste de email",
            mail_body="testando envio de email",
        )

        result = await client.send_message()
        assert result
