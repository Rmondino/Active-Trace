"""Email sender abstraction and SMTP implementation."""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class EmailSender(ABC):

    @abstractmethod
    async def send(self, to: str, subject: str, body: str) -> bool:
        ...


class SmtpEmailSender(EmailSender):

    def __init__(
        self,
        host: str,
        port: int,
        username: str | None = None,
        password: str | None = None,
        from_addr: str = "noreply@activia-trace.com",
        use_tls: bool = True,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_addr = from_addr
        self.use_tls = use_tls

    async def send(self, to: str, subject: str, body: str) -> bool:
        try:
            import aiosmtplib

            message = (
                f"From: {self.from_addr}\r\n"
                f"To: {to}\r\n"
                f"Subject: {subject}\r\n"
                f"MIME-Version: 1.0\r\n"
                f"Content-Type: text/plain; charset=UTF-8\r\n"
                f"\r\n"
                f"{body}"
            )
            if self.use_tls:
                await aiosmtplib.send(
                    message,
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    use_tls=True,
                )
            else:
                async with aiosmtplib.SMTP(
                    hostname=self.host, port=self.port
                ) as smtp:
                    if self.username and self.password:
                        await smtp.login(self.username, self.password)
                    await smtp.sendmail(self.from_addr, [to], message)
            return True
        except Exception as e:
            logger.error("SMTP error sending to %s: %s", to, e)
            return False


class FakeEmailSender(EmailSender):

    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []

    async def send(self, to: str, subject: str, body: str) -> bool:
        self.sent.append((to, subject, body))
        return True
