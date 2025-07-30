from sqlalchemy.ext.asyncio import AsyncSession
from leodb.models.general.account import Account
from leodb.schemas.account import AccountCreate, AccountUpdate
from .base_repository import BaseRepository

class AccountRepository(BaseRepository[Account, AccountCreate, AccountUpdate]):
    pass