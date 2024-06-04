"""Functional tests for email client"""

from src.backends import Email365Client


class TestEmail365Client:
    """
    Email client tests

    This class provides functional tests for the Email client.
    """

    def test_send_new_password_email_sucess(self):
        """Test send new password email success case"""
        client = Email365Client(
            mail_to="teste@email.com",
            mail_subject="teste de email",
            type_message="new_password",
            extra={
                "username": "teste",
                "new_password": "teste",
                "full_name": "teste nome completo",
            },
        )

        result = client.send_message(fake=True)
        assert result
