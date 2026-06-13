"""Background worker entrypoint (placeholder).

C-01 provides a minimal no-op loop as a placeholder.
The actual queue technology (asyncio, ARQ, Celery, etc.) will be
determined by ADR-003 when the communications module is built.

Usage:
    python -m app.workers.main
"""

import asyncio
import logging

logger = logging.getLogger(__name__)


async def main() -> None:
    """Worker main loop: placeholder that logs and sleeps."""
    logger.info("Worker started (placeholder — no-op mode)")
    try:
        while True:
            await asyncio.sleep(60)
            logger.debug("Worker heartbeat (placeholder)")
    except asyncio.CancelledError:
        logger.info("Worker received shutdown signal")
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")


if __name__ == "__main__":
    asyncio.run(main())
