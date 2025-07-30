from sqlalchemy import TypeDecorator, String
from cryptography.fernet import Fernet

from leodb.encryption.service import encryption_service

class EncryptedString(TypeDecorator):
    """
    A SQLAlchemy TypeDecorator to store encrypted strings in the database.
    """
    impl = String
    cache_ok = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get the key from the service.
        # In a real application, consider how to handle key rotation.
        key = encryption_service.get_sync_encryption_key()
        self.fernet = Fernet(key.encode())

    def process_bind_param(self, value, dialect):
        """
        Encrypt the value before sending it to the database.
        """
        if value is not None:
            return self.fernet.encrypt(value.encode()).decode()
        return value

    def process_result_value(self, value, dialect):
        """
        Decrypt the value after fetching it from the database.
        """
        if value is not None:
            return self.fernet.decrypt(value.encode()).decode()
        return value