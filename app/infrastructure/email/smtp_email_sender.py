from typing import Optional
import logging
import aiosmtplib
from email.message import EmailMessage
from aiosmtplib import SMTPException
from app.config import settings


logger = logging.getLogger(__name__)

class SmtpEmailSender:
    """
    Async SMTP sender.
    """
    async def send_html(
        self, 
        to: str, 
        subject: str, 
        html: str, 
        sender: Optional[str] = None
    ) -> None:
        msg = EmailMessage()
        msg["From"] = sender or settings.smtp_from
        msg["To"] = to
        msg["Subject"] = subject
        msg["X-Mailer"] = "Nexa Auth API"
        msg.set_content("Veuillez utiliser un client email supportant le HTML.", subtype="plain")
        msg.add_alternative(html, subtype="html")

        use_tls = bool(int(settings.smtp_use_tls or 0))
        
        try:
            response = await aiosmtplib.send(
                msg,
                hostname=settings.smtp_host,
                port=int(settings.smtp_port),
                username=settings.smtp_username or None,
                password=settings.smtp_password or None,
                start_tls=True,
                timeout=30,
            )
            logger.info(f"Email envoyé: {response}")
        except SMTPException as e:
            raise RuntimeError(f"Échec d'envoi d'email: {str(e)}")