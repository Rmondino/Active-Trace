"""Background worker for processing Comunicacion email dispatch.

Replaces C-01's no-op placeholder with a real async loop that:
    - Polls for Pendiente messages ready to send (approved or no approval needed)
    - Transitions to Enviando → sends email → Enviado or Error
    - Recovers from individual message failures without blocking the queue

Usage:
    python -m app.workers.main
"""

import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy import select

from app.core.config import Settings
from app.core.crypto import CipherService
from app.core.database import async_sessionmaker, create_async_engine
from app.integrations.email_sender import SmtpEmailSender
from app.models.comunicacion import Comunicacion
from app.services.comunicacion_service import validar_transicion

logger = logging.getLogger(__name__)


class ComunicacionWorker:

    def __init__(
        self,
        session_factory,
        email_sender,
        cipher_service,
    ) -> None:
        self.session_factory = session_factory
        self.email_sender = email_sender
        self.cipher_service = cipher_service

    async def run(self) -> None:
        logger.info("ComunicacionWorker started")
        while True:
            try:
                async with self.session_factory() as session:
                    stmt = (
                        select(Comunicacion)
                        .where(
                            Comunicacion.estado == "Pendiente",
                            Comunicacion.deleted_at.is_(None),
                        )
                        .limit(20)
                    )
                    result = await session.execute(stmt)
                    pendientes = list(result.scalars().all())

                    for msg in pendientes:
                        await self._procesar(msg, session)

            except Exception as e:
                logger.error("Worker loop error: %s", e)

            await asyncio.sleep(5)

    async def _procesar(self, msg: Comunicacion, session) -> None:
        try:
            validar_transicion(msg.estado, "Enviando")
            msg.estado = "Enviando"
            await session.flush()

            email = self.cipher_service.decrypt(msg.destinatario)
            success = await self.email_sender.send(
                to=email, subject=msg.asunto, body=msg.cuerpo
            )

            if success:
                validar_transicion(msg.estado, "Enviado")
                msg.estado = "Enviado"
                msg.enviado_at = datetime.now(UTC)
            else:
                validar_transicion(msg.estado, "Error")
                msg.estado = "Error"
                msg.error_msg = "SMTP delivery failed"

            await session.commit()
            logger.info(
                "Message %s: %s -> %s",
                msg.id,
                "Enviado" if success else "Error",
                msg.destinatario[:20] if msg.destinatario else "?",
            )

        except Exception as e:
            logger.error("Error processing message %s: %s", msg.id, e)
            await session.rollback()

            try:
                async with self.session_factory() as s:
                    m = await s.get(Comunicacion, msg.id)
                    if m and m.estado not in ("Enviado",):
                        try:
                            validar_transicion(m.estado, "Error")
                        except ValueError:
                            pass
                        else:
                            m.estado = "Error"
                            m.error_msg = str(e)[:200]
                            await s.commit()
            except Exception as recovery_error:
                logger.error(
                    "Recovery failed for message %s: %s",
                    msg.id,
                    recovery_error,
                )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    settings = Settings()  # type: ignore[call-arg]
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    email_sender = SmtpEmailSender(
        host=settings.EMAIL_SMTP_HOST,
        port=settings.EMAIL_SMTP_PORT,
        username=settings.EMAIL_SMTP_USERNAME,
        password=settings.EMAIL_SMTP_PASSWORD,
        from_addr=settings.EMAIL_FROM_ADDR,
        use_tls=settings.EMAIL_USE_TLS,
    )
    cipher_service = CipherService(settings)

    worker = ComunicacionWorker(
        session_factory=session_factory,
        email_sender=email_sender,
        cipher_service=cipher_service,
    )

    try:
        asyncio.run(worker.run())
    except (asyncio.CancelledError, KeyboardInterrupt):
        logger.info("Worker stopped")


if __name__ == "__main__":
    main()
