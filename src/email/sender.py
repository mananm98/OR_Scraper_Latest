"""Email sending functionality."""
import smtplib
import time
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailSender:
    """Sends emails via SMTP."""

    def __init__(self, smtp_config, dry_run=False, rate_limit_delay=1.5):
        """
        Initialize the email sender.

        Args:
            smtp_config: Dictionary with SMTP configuration (host, port, use_tls, username, password)
            dry_run: If True, simulate sending without actually transmitting (default: False)
            rate_limit_delay: Seconds to wait between emails (default: 1.5)
        """
        self.smtp_config = smtp_config
        self.dry_run = dry_run
        self.rate_limit_delay = rate_limit_delay
        self.last_send_time = 0

    def send_email(self, to_email, subject, body, from_email):
        """
        Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body
            from_email: Sender email address

        Returns:
            bool: True if sent successfully, False otherwise
        """
        # Input validation
        if not self._validate_inputs(to_email, subject, body, from_email):
            return False

        # Rate limiting
        self._apply_rate_limit()

        # Dry-run mode
        if self.dry_run:
            return self._dry_run_send(to_email, subject, body)

        # Build MIME message
        msg = self._build_message(to_email, subject, body, from_email)

        # Send via SMTP
        return self._send_via_smtp(msg, to_email, subject)

    def _validate_inputs(self, to_email, subject, body, from_email):
        """
        Validate email inputs.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body
            from_email: Sender email address

        Returns:
            bool: True if valid, False otherwise
        """
        # Check for empty values
        if not to_email or not subject or not body or not from_email:
            print("✗ Validation error: Missing required fields")
            return False

        # Basic email format validation
        if '@' not in to_email or '.' not in to_email.split('@')[-1]:
            print(f"✗ Validation error: Invalid recipient email format: {to_email}")
            return False

        if '@' not in from_email or '.' not in from_email.split('@')[-1]:
            print(f"✗ Validation error: Invalid sender email format: {from_email}")
            return False

        return True

    def _apply_rate_limit(self):
        """Apply rate limiting by sleeping if necessary."""
        if self.last_send_time > 0:
            elapsed = time.time() - self.last_send_time
            if elapsed < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - elapsed
                time.sleep(sleep_time)

        self.last_send_time = time.time()

    def _dry_run_send(self, to_email, subject, body):
        """
        Simulate sending email in dry-run mode.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body

        Returns:
            bool: Always returns True (simulated success)
        """
        print(f"[DRY RUN] Would send email to {to_email}")
        print(f"  Subject: {subject}")
        body_preview = body[:100] + "..." if len(body) > 100 else body
        print(f"  Body preview: {body_preview}")
        return True

    def _build_message(self, to_email, subject, body, from_email):
        """
        Build MIME message for plain text email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body
            from_email: Sender email address

        Returns:
            MIMEText: Constructed email message
        """
        msg = MIMEText(body, 'plain')
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        return msg

    def _send_via_smtp(self, msg, to_email, subject):
        """
        Send email via SMTP with error handling.

        Args:
            msg: MIME message object
            to_email: Recipient email address (for logging)
            subject: Email subject (for logging)

        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # Connect to SMTP server
            server = smtplib.SMTP(
                self.smtp_config['host'],
                self.smtp_config['port'],
                timeout=30
            )

            # Start TLS if enabled
            if self.smtp_config.get('use_tls', True):
                server.starttls()

            # Login with credentials
            server.login(
                self.smtp_config['username'],
                self.smtp_config['password']
            )

            # Send email
            server.send_message(msg)

            # Close connection
            server.quit()

            # Log success
            print(f"✓ Sent email to {to_email}")
            print(f"  Subject: {subject}")

            return True

        except smtplib.SMTPAuthenticationError as e:
            print(f"✗ Failed to send email to {to_email}")
            print(f"  Error: SMTPAuthenticationError - Invalid credentials")
            print(f"  Details: {str(e)}")
            return False

        except smtplib.SMTPServerDisconnected as e:
            print(f"✗ Failed to send email to {to_email}")
            print(f"  Error: SMTPServerDisconnected - Connection lost")
            print(f"  Details: {str(e)}")
            return False

        except smtplib.SMTPException as e:
            print(f"✗ Failed to send email to {to_email}")
            print(f"  Error: SMTPException - SMTP protocol error")
            print(f"  Details: {str(e)}")
            return False

        except socket.gaierror as e:
            print(f"✗ Failed to send email to {to_email}")
            print(f"  Error: gaierror - DNS/Network error")
            print(f"  Details: {str(e)}")
            return False

        except Exception as e:
            print(f"✗ Failed to send email to {to_email}")
            print(f"  Error: {type(e).__name__}: {str(e)}")
            return False
