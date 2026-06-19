"""AES-256-GCM encryption for PII at rest, plus Argon2id password hashing.

Provides:
    - encrypt/decrypt: AES-256-GCM for PII at rest
    - hash_password/verify_password: Argon2id for authentication
    - hash_email: SHA-256(LOWER(email)) for login lookup
    - mask_pii: mask sensitive fields for list responses
    - get_encryption_key: retrieve the AES-256 key from Settings
"""

import base64
import hashlib
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


def hash_email(email: str) -> str:
    """Compute SHA-256 hash of a lowercased email for lookup.

    Args:
        email: The plaintext email address.

    Returns:
        Hex-encoded SHA-256 digest.
    """
    return hashlib.sha256(email.lower().encode("utf-8")).hexdigest()


def mask_pii(value: str | None, visible_chars: int = 3) -> str | None:
    """Mask a PII field showing only the last N characters.

    Args:
        value: The plaintext value to mask.
        visible_chars: Number of trailing characters to show.

    Returns:
        Masked string (e.g. "*********123") or None if input is None.
    """
    if value is None:
        return None
    if len(value) <= visible_chars:
        return value
    return "*" * (len(value) - visible_chars) + value[-visible_chars:]


def mask_email(email: str) -> str:
    """Mask an email address for safe display.

    Shows first character of local part + domain.

    Args:
        email: Plaintext email address.

    Returns:
        Masked email (e.g. "j***@example.com").
    """
    if "@" not in email:
        return mask_pii(email, 3) or email
    local, domain = email.split("@", 1)
    if len(local) <= 1:
        masked_local = local
    else:
        masked_local = local[0] + "*" * (len(local) - 1)
    return f"{masked_local}@***" if not domain else f"{masked_local}@***"
