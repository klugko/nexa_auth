import asyncio
from typing import Optional
import aiosmtplib
from email.message import EmailMessage
from app.config import settings

class SmtpEmailSender:
    """
    Async SMTP sender. In dev, you can run MailHog (docker) and point SMTP_HOST/PORT to it.
    """
    async def send_html(self, to: str, subject: str, html: str, sender: Optional[str] = None) -> None:
        msg = EmailMessage()
        msg["From"] = sender or settings.smtp_from
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content("HTML email", subtype="plain")
        msg.add_alternative(html, subtype="html")

        use_tls = bool(int(settings.smtp_use_tls or 0))
        use_ssl = bool(int(settings.smtp_use_ssl or 0))

        if use_ssl:
            await aiosmtplib.send(
                msg,
                hostname=settings.smtp_host,
                port=int(settings.smtp_port),
                username=settings.smtp_username or None,
                password=settings.smtp_password or None,
                use_tls=True,
            )
        else:
            client = aiosmtplib.SMTP(hostname=settings.smtp_host, port=int(settings.smtp_port), use_tls=use_tls)
            await client.connect()
            if settings.smtp_username and settings.smtp_password:
                await client.login(settings.smtp_username, settings.smtp_password)
            await client.send_message(msg)
            await client.quit()
