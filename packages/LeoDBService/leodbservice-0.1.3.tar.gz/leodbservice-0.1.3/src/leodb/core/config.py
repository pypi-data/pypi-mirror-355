import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Charger les variables d'environnement depuis un fichier .env
load_dotenv()

class Settings(BaseSettings):
    """
    Configuration de la bibliothèque leodb.
    Lit les variables d'environnement.
    """
    # Configuration de la base de données
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", 5432))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "app")
    POSTGRES_SCHEMA: str = os.getenv("POSTGRES_SCHEMA", "account-schema")

    # Configuration Azure Key Vault pour le chiffrement
    AZURE_KEY_VAULT_URL: str | None = os.getenv("AZURE_KEY_VAULT_URL")
    ENCRYPTION_KEY_NAME: str | None = os.getenv("ENCRYPTION_KEY_NAME")
    
    # Clé de secours si Key Vault n'est pas disponible
    SECRET_KEY: str = os.getenv("SECRET_KEY", "a_very_secret_key_that_should_be_changed")

    @property
    def DATABASE_URL(self) -> str:
        """Retourne l'URL de connexion à la base de données."""
        return f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def is_azure_key_vault_enabled(self) -> bool:
        """Vérifie si la configuration pour Azure Key Vault est présente."""
        return bool(self.AZURE_KEY_VAULT_URL and self.ENCRYPTION_KEY_NAME)

# Instance globale des configurations
settings = Settings()