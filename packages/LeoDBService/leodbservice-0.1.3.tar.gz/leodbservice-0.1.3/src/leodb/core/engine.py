from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from leodb.models.base import Base
from .connection_manager import connection_manager


async def create_database_and_tables():
    """
    Creates the database schema and all tables defined in the models
    on the default database connection.
    """
    engine = await connection_manager.get_engine()
    async with engine.begin() as conn:
        # This will create tables in the 'general' schema as defined in models
        await conn.run_sync(Base.metadata.create_all)


async def get_db_session(
    account_uuid: Optional[str] = None,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get a database session.
    
    If account_uuid is provided, it returns a session for that account's
    dedicated database. Otherwise, it returns a session for the shared database.
    """
    session = await connection_manager.get_session(account_uuid)
    try:
        yield session
    finally:
        await session.close()