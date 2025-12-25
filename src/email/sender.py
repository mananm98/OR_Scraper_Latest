"""Email sending functionality."""


class EmailSender:
    """Sends emails via SMTP."""

    def __init__(self, smtp_config):
        """
        Initialize the email sender.

        Args:
            smtp_config: Dictionary with SMTP configuration
        """
        self.smtp_config = smtp_config

    def send_email(self, to_email, subject, body, from_email):
        """
        Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body
            from_email: Sender email address

        Returns:
            bool: True if sent successfully
        """
        pass
