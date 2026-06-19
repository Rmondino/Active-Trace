"""CipherService — centralized encryption service wrapping AES-256-GCM.

Provides encrypt, decrypt, and masked display for PII at rest.
"""

from app.core.security import (
    decrypt as _decrypt,
    encrypt as _encrypt,
    get_encryption_key,
    mask_pii,
)
from app.core.config import Settings


class CipherService:
    """High-level encryption service for PII fields.

    Wraps the low-level AES-256-GCM functions from core.security
    with automatic key management via Settings.
    """

    def __init__(self, settings: Settings) -> None:
        self._key = get_encryption_key(settings)

    def encrypt(self, plaintext: str) -> str:
        return _encrypt(plaintext, self._key)

    def decrypt(self, ciphertext: str) -> str:
        return _decrypt(ciphertext, self._key)

    def mask(self, value: str | None, visible_chars: int = 3) -> str | None:
        return mask_pii(value, visible_chars)
