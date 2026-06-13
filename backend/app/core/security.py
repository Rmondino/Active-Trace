"""AES-256-GCM encryption for PII at rest, plus Argon2id password hashing.

Provides:
    - encrypt/decrypt: AES-256-GCM for PII at rest
    - hash_password/verify_password: Argon2id for authentication
    - get_encryption_key: retrieve the AES-256 key from Settings
"""

import base64
import os

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import Settings


_ph = PasswordHasher(
    time_cost=2,
    memory_cost=19456,  # ~19 MB
    parallelism=1,
    hash_len=32,
    salt_len=16,
)


def hash_password(plain: str) -> str:
    """Hash a password using Argon2id.

    Args:
        plain: The plaintext password.

    Returns:
        Argon2id hash string.
    """
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against an Argon2id hash.

    Args:
        plain: The plaintext password to verify.
        hashed: The Argon2id hash string.

    Returns:
        True if the password matches, False otherwise.
    """
    try:
        return _ph.verify(hashed, plain)
    except VerifyMismatchError:
        return False


def _validate_key(key: bytes) -> None:
    """Validate that the key is exactly 32 bytes (AES-256)."""
    if len(key) != 32:
        raise ValueError(
            f"Encryption key must be exactly 32 bytes (got {len(key)})"
        )


def encrypt(plaintext: str, key: bytes) -> str:
    """Encrypt a plaintext string using AES-256-GCM.

    Args:
        plaintext: The string to encrypt.
        key: AES-256 key, must be exactly 32 bytes.

    Returns:
        Base64-encoded string containing nonce + ciphertext + tag.
    """
    _validate_key(key)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce recommended for GCM
    plaintext_bytes = plaintext.encode("utf-8")
    ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, None)
    # Combine nonce + ciphertext (which includes the tag)
    return base64.b64encode(nonce + ciphertext).decode("ascii")


def decrypt(ciphertext_b64: str, key: bytes) -> str:
    """Decrypt a base64-encoded AES-256-GCM ciphertext.

    Args:
        ciphertext_b64: Base64 string from a previous encrypt() call.
        key: AES-256 key, must be exactly 32 bytes.

    Returns:
        Original plaintext string.
    """
    _validate_key(key)
    aesgcm = AESGCM(key)
    data = base64.b64decode(ciphertext_b64)
    nonce = data[:12]
    ciphertext = data[12:]
    plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext_bytes.decode("utf-8")


def get_encryption_key(settings: Settings) -> bytes:
    """Retrieve the AES-256 key from application Settings.

    Args:
        settings: Application Settings with ENCRYPTION_KEY.

    Returns:
        Key as bytes (exactly 32 bytes).
    """
    key = settings.ENCRYPTION_KEY.encode("utf-8")
    _validate_key(key)
    return key
