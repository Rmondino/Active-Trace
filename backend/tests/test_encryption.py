"""Tests for AES-256-GCM encryption (core/security.py).

These tests do NOT require a database — pure crypto.
"""

import pytest

from app.core.security import decrypt, encrypt, get_encryption_key


class TestEncryption:
    """AES-256-GCM round-trip and edge cases."""

    VALID_KEY = b"a" * 32  # Exactly 32 bytes

    def test_encrypt_decrypt_round_trip(self):
        """Encrypting then decrypting returns the original plaintext."""
        plaintext = "sensitive-data-123"
        ciphertext = encrypt(plaintext, self.VALID_KEY)
        decrypted = decrypt(ciphertext, self.VALID_KEY)
        assert decrypted == plaintext

    def test_different_nonce_per_encryption(self):
        """Two encryptions of the same data produce different ciphertexts."""
        plaintext = "same-data"
        c1 = encrypt(plaintext, self.VALID_KEY)
        c2 = encrypt(plaintext, self.VALID_KEY)
        assert c1 != c2

    def test_wrong_key_fails_to_decrypt(self):
        """Decrypting with a different key raises an error."""
        plaintext = "secret"
        ciphertext = encrypt(plaintext, self.VALID_KEY)
        wrong_key = b"b" * 32
        with pytest.raises(Exception):
            decrypt(ciphertext, wrong_key)

    def test_invalid_key_length_raises_error(self):
        """Using a key that is not 32 bytes raises ValueError."""
        with pytest.raises(ValueError, match="exactly 32 bytes"):
            encrypt("test", b"short-key")

    def test_get_encryption_key_from_settings(self):
        """get_encryption_key extracts and validates the key from Settings."""
        from app.core.config import Settings

        settings = Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://u:p@localhost:5432/db",
            SECRET_KEY="x" * 32,
            ENCRYPTION_KEY="y" * 32,
        )
        key = get_encryption_key(settings)
        assert len(key) == 32
        assert key == b"y" * 32

    def test_encrypt_unicode(self):
        """Unicode characters are handled correctly."""
        plaintext = "ñoño áéíóú 😊"
        ciphertext = encrypt(plaintext, self.VALID_KEY)
        decrypted = decrypt(ciphertext, self.VALID_KEY)
        assert decrypted == plaintext
