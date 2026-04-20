import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from domain.models.user import User
from infrastructure.database import async_session_maker
from uuid import UUID
class SessionHandler:


     def __init__(self ):
         pass


     async def get_session(self, session_id: str):

        if session_id  ==  "":

               uid = uuid.uuid4()
               await self._create_user_guest(uid)
               return uid

        return session_id

     async def _create_user_guest(self, uid: UUID):
         try:
             async with async_session_maker() as session:
                 user = User(
                     id=uid,
                     email=f"guest_{uid}@travelhub.com",
                     password_hash="",
                     first_name="Guest",
                     last_name="User",
                     user_type="guest"
                 )
                 session.add(user)
                 await session.commit()
         except Exception:
             raise

