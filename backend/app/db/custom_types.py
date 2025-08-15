import os
import uuid

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import LargeBinary
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import CHAR, TypeDecorator

from app.core.key_manager import key_manager


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32) for other databases.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value

    def copy(self, **kwargs):
        return GUID(self.impl.length)


NONCE_SIZE = 12


class EncryptedString(TypeDecorator):
    """
    A SQLAlchemy TypeDecorator to store strings as encrypted binary data.
    It uses AES-GCM for authenticated encryption.
    The master key is retrieved from the global key_manager instance.
    """

    impl = LargeBinary
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """
        Encrypt the value on its way to the database.
        """
        if value is None:
            return None

        if not key_manager.is_key_loaded:
            raise RuntimeError(
                "Cannot encrypt data: master key is not loaded in KeyManager."
            )

        # Ensure the value is a string before encoding
        if not isinstance(value, str):
            value = str(value)

        plaintext = value.encode("utf-8")
        aes_gcm = AESGCM(key_manager.master_key)

        # Generate a unique nonce for each encryption
        nonce = os.urandom(NONCE_SIZE)

        # Encrypt the data
        ciphertext = aes_gcm.encrypt(nonce, plaintext, None)

        # Prepend the nonce to the ciphertext for storage
        return nonce + ciphertext

    def process_result_value(self, value, dialect):
        """
        Decrypt the value on its way out of the database.
        """
        if value is None:
            return None

        if not key_manager.is_key_loaded:
            raise RuntimeError(
                "Cannot decrypt data: master key is not loaded in KeyManager."
            )

        # Split the nonce and the ciphertext
        nonce = value[:NONCE_SIZE]
        ciphertext = value[NONCE_SIZE:]

        aes_gcm = AESGCM(key_manager.master_key)

        try:
            # Decrypt and decode back to a string
            decrypted_bytes = aes_gcm.decrypt(nonce, ciphertext, None)
            return decrypted_bytes.decode("utf-8")
        except Exception as e:
            # If decryption fails, it could be due to a wrong key or corrupted data.
            # For now, we raise the exception to be aware of the issue.
            raise e
