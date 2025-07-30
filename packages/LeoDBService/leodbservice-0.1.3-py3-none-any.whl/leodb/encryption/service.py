import asyncio
import logging
from typing import Optional

from azure.identity.aio import DefaultAzureCredential
from azure.keyvault.secrets.aio import SecretClient

from leodb.core.config import settings

logger = logging.getLogger(__name__)

class EncryptionService:
    """
    Service to fetch the database encryption key from Azure Key Vault.
    """

    def __init__(self):
        self._encryption_key: Optional[str] = None
        self._key_client: Optional[SecretClient] = None

        if settings.is_azure_key_vault_enabled:
            try:
                credential = DefaultAzureCredential()
                self._key_client = SecretClient(
                    vault_url=settings.AZURE_KEY_VAULT_URL, credential=credential
                )
                logger.info("Azure Key Vault client initialized for encryption.")
            except Exception as e:
                logger.error(f"Failed to initialize Azure Key Vault client: {e}")
                self._key_client = None

    async def initialize(self):
        """Pre-loads the encryption key. Should be called at application startup."""
        if not self._encryption_key:
            await self.get_encryption_key()

    def get_sync_encryption_key(self) -> str:
        """
        Returns the cached encryption key.
        Raises an exception if the key is not pre-loaded.
        """
        if not self._encryption_key:
            # In a real app, this indicates a startup logic error.
            # For tests or simple scripts, we can fallback, but it's better to be strict.
            logger.warning("Encryption key was not pre-loaded. Using fallback for now.")
            self._encryption_key = settings.SECRET_KEY
        
        if not self._encryption_key:
             raise RuntimeError(
                "Encryption key not available. "
                "The service must be initialized at startup."
            )
        return self._encryption_key

    async def get_encryption_key(self) -> str:
        """
        Retrieves the encryption key from Azure Key Vault, caching it in memory.
        Falls back to the SECRET_KEY from settings if Key Vault is unavailable.
        """
        if self._encryption_key:
            return self._encryption_key

        if not self._key_client:
            logger.warning("Azure Key Vault not configured. Using fallback secret key.")
            self._encryption_key = settings.SECRET_KEY
            return self._encryption_key

        try:
            secret = await self._key_client.get_secret(settings.ENCRYPTION_KEY_NAME)
            self._encryption_key = secret.value
            logger.info("Successfully retrieved encryption key from Azure Key Vault.")
            return self._encryption_key
        except Exception as e:
            logger.error(f"Failed to retrieve encryption key from Key Vault: {e}")
            logger.warning("Using fallback secret key due to Key Vault error.")
            self._encryption_key = settings.SECRET_KEY
            return self._encryption_key

    async def close(self):
        """Closes the Azure Key Vault client session."""
        if self._key_client:
            await self._key_client.close()
            await self._key_client.__aexit__()


# Global instance of the encryption service
encryption_service = EncryptionService()