import logging
from typing import List

from sqlalchemy import event, text
from sqlalchemy.orm import object_session

from .service import encryption_service

logger = logging.getLogger(__name__)

class EncryptedModelMixin:
    """
    A mixin for SQLAlchemy models to transparently encrypt and decrypt fields.

    This mixin uses SQLAlchemy event listeners to automatically handle
    encryption before an object is saved and decryption after it is loaded.

    Usage:
        class MyModel(Base, EncryptedModelMixin):
            __tablename__ = 'my_model'
            _encrypted_fields = ['sensitive_data']

            id = Column(Integer, primary_key=True)
            sensitive_data = Column(String) # Will be encrypted in the DB
    """
    _encrypted_fields: List[str] = []

    @staticmethod
    def _encrypt(session, value: str, key: str) -> bytes:
        """Encrypts a single value using pgcrypto if not on sqlite."""
        if value is None:
            return None
        # Bypass encryption for sqlite dialect used in tests
        if session.bind.dialect.name == 'sqlite':
            return value.encode('utf-8')
        
        result = session.execute(
            text("SELECT pgp_sym_encrypt(:value, :key) as encrypted"),
            {"value": str(value), "key": key}
        ).scalar_one()
        return result

    @staticmethod
    def _decrypt(session, encrypted_value: bytes, key: str) -> str:
        """Decrypts a single value using pgcrypto if not on sqlite."""
        if encrypted_value is None:
            return None
        # Bypass decryption for sqlite dialect used in tests
        if session.bind.dialect.name == 'sqlite':
            if isinstance(encrypted_value, bytes):
                return encrypted_value.decode('utf-8')
            return encrypted_value
        
        try:
            result = session.execute(
                text("SELECT pgp_sym_decrypt(:encrypted::bytea, :key) as decrypted"),
                {"encrypted": encrypted_value, "key": key}
            ).scalar_one()
            return result
        except Exception as e:
            logger.error(f"Failed to decrypt value: {e}. Returning raw value.")
            return encrypted_value

    @classmethod
    def __declare_last__(cls):
        """SQLAlchemy hook to set up event listeners."""
        event.listen(cls, 'before_insert', cls._before_save_listener)
        event.listen(cls, 'before_update', cls._before_save_listener)
        event.listen(cls, 'load', cls._load_listener)

    @classmethod
    def _before_save_listener(cls, mapper, connection, target):
        """Encrypts fields before insert or update."""
        session = object_session(target)
        if not session or session.bind.dialect.name == 'sqlite':
            return

        key = encryption_service.get_sync_encryption_key()
        for field in target._encrypted_fields:
            value = getattr(target, field)
            if value and isinstance(value, str): # Only encrypt if it's a non-empty string
                encrypted_value = cls._encrypt(session, value, key)
                setattr(target, field, encrypted_value)

    @classmethod
    def _load_listener(cls, target, context):
        """Decrypts fields after an object is loaded."""
        session = object_session(target)
        if not session or session.bind.dialect.name == 'sqlite':
            return

        key = encryption_service.get_sync_encryption_key()
        for field in target._encrypted_fields:
            encrypted_value = getattr(target, field)
            if encrypted_value:
                decrypted_value = cls._decrypt(session, encrypted_value, key)
                setattr(target, field, decrypted_value)