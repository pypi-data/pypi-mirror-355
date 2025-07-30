from sqlalchemy.ext.asyncio import AsyncSession
from leodb.models.general.user import User
from leodb.schemas.user import UserCreate, UserUpdate
from .base_repository import BaseRepository

class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    pass