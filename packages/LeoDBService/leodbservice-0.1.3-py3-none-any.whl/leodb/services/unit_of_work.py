from __future__ import annotations
import abc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from leodb.core.engine import get_db_session
from leodb.models.general.account import Account
from leodb.models.general.user import User
from leodb.repositories.user_repository import UserRepository
from leodb.repositories.account_repository import AccountRepository
# Import other repositories here as they are created

class AbstractUnitOfWork(abc.ABC):
    users: UserRepository
    accounts: AccountRepository
    # Define other repositories here

    def __init__(self, account_uuid: Optional[str] = None):
        self.account_uuid = account_uuid
        self._session_context = get_db_session(account_uuid)

    async def __aenter__(self) -> AbstractUnitOfWork:
        self._session = await self._session_context.__aenter__()
        self.users = UserRepository(self._session, User)
        self.accounts = AccountRepository(self._session, Account)
        # Instantiate other repositories here
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # The session is automatically closed by the context manager from get_db_session
        if self._session:
            if exc_type:
                await self.rollback()
            else:
                await self.commit()
        
        await self._session_context.__aexit__(exc_type, exc_val, exc_tb)


    @abc.abstractmethod
    async def commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def rollback(self):
        raise NotImplementedError

class UnitOfWork(AbstractUnitOfWork):

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()