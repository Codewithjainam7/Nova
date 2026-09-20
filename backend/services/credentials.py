import os
from cryptography.fernet import Fernet
from typing import Optional
from backend.core.logger import app_logger

class CredentialsManager:
    """
    Manages secure symmetric encryption and decryption of API keys and OAuth tokens.
    """
    def __init__(self, key: Optional[bytes] = None):
        # In production, this key should be loaded securely from environment variables.
        # If not provided, we look for ENCRYPTION_KEY in env, or generate a temporary one (not persistent).
        env_key = os.environ.get("NOVA_ENCRYPTION_KEY")
        if key:
            self._key = key
        elif env_key:
            self._key = env_key.encode()
        else:
            # Fallback for dev: Generate a static key based on a known seed so it survives restarts,
            # but ideally the user should set NOVA_ENCRYPTION_KEY in .env.
            app_logger.warning("NOVA_ENCRYPTION_KEY not found. Using development key. DO NOT USE IN PRODUCTION.")
            # This is a valid 32-byte url-safe base64-encoded Fernet key.
            self._key = b"tY2w9v3kG3wK7i8m8j9V7m2P0x1L4n6F8o9V2b3N5m8="

        self.cipher_suite = Fernet(self._key)

    def encrypt(self, data: str) -> str:
        """Encrypts a plaintext string."""
        if not data:
            return data
        return self.cipher_suite.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypts a previously encrypted string."""
        if not encrypted_data:
            return encrypted_data
        try:
            return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            app_logger.error(f"Failed to decrypt credentials: {e}")
            raise ValueError("Decryption failed. The encryption key may have changed.")
