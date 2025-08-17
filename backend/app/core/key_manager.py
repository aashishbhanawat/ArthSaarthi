import hashlib
import os
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Define the path for storing the encrypted master key.
# This should be in a user-specific, hidden directory.
CONFIG_DIR = Path.home() / ".config" / "arthsaarthi"
KEY_FILE_PATH = CONFIG_DIR / "key.dat"

# Constants for KDF
SALT_SIZE = 16
PBKDF2_ITERATIONS = 390000

# Constants for AES GCM
NONCE_SIZE = 12
TAG_SIZE = 16


class KeyManager:
    """
    A singleton class to manage the master encryption key using an envelope
    encryption pattern.
    """
    _instance = None
    _master_key: bytes | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KeyManager, cls).__new__(cls)
            cls._master_key = None
        return cls._instance

    @property
    def is_key_loaded(self) -> bool:
        """Check if the master key is loaded into memory."""
        return self._master_key is not None

    @property
    def master_key(self) -> bytes:
        """
        Get the master key. Raises an exception if the key is not loaded.
        """
        if not self.is_key_loaded:
            raise RuntimeError("Master key has not been unlocked.")
        return self._master_key

    def _derive_wrapping_key(self, password: str, salt: bytes) -> bytes:
        """Derive a 32-byte key from a password using PBKDF2."""
        return hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS, dklen=32
        )

    def generate_and_wrap_master_key(self, password: str) -> None:
        """
        Generates a new master key, encrypts it with a key derived from the
        password, and saves it to disk.
        """
        # 1. Generate a new master key
        new_master_key = AESGCM.generate_key(bit_length=256)

        # 2. Generate a new salt for the KDF
        salt = os.urandom(SALT_SIZE)

        # 3. Derive the wrapping key from the password
        wrapping_key = self._derive_wrapping_key(password, salt)

        # 4. Encrypt the master key with AES-GCM
        aes_gcm = AESGCM(wrapping_key)
        nonce = os.urandom(NONCE_SIZE)
        encrypted_master_key = aes_gcm.encrypt(nonce, new_master_key, None)

        # 5. Save salt, nonce, and encrypted key to file
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(KEY_FILE_PATH, "wb") as f:
            f.write(salt)
            f.write(nonce)
            f.write(encrypted_master_key)

        # 6. Load the new key into memory for the current session
        self._master_key = new_master_key

    def unlock_master_key(self, password: str) -> bool:
        """
        Loads the encrypted master key from disk and decrypts it using a key
        derived from the provided password.
        """
        if not KEY_FILE_PATH.exists():
            return False

        try:
            with open(KEY_FILE_PATH, "rb") as f:
                salt = f.read(SALT_SIZE)
                nonce = f.read(NONCE_SIZE)
                encrypted_master_key = f.read()

            # 1. Derive the wrapping key
            wrapping_key = self._derive_wrapping_key(password, salt)

            # 2. Decrypt the master key
            aes_gcm = AESGCM(wrapping_key)
            decrypted_master_key = aes_gcm.decrypt(nonce, encrypted_master_key, None)

            # 3. Store the master key in memory
            self._master_key = decrypted_master_key
            return True
        except Exception:
            # This can fail if the password is wrong (decryption error) or if the
            # file is corrupted.
            self._master_key = None
            return False

    def change_password(self, old_password: str, new_password: str) -> bool:
        """
        Decrypts the master key with the old password and re-encrypts it
        with the new one.
        """
        if not self.unlock_master_key(old_password):
            return False

        # The master key is now in memory, re-wrap it with the new password
        self.generate_and_wrap_master_key(new_password)
        return True

# Create a single, shared instance of the KeyManager
key_manager = KeyManager()