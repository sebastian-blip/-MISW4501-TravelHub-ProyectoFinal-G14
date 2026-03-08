import uuid
from ..db_client import get_user as _get_user, anonymize_user as _anonymize_user


class UserRepository:
    """Uses DB API (DuckDB service)."""

    async def get(self, user_id: uuid.UUID) -> dict | None:
        return await _get_user(str(user_id))

    async def anonymize(self, user_id: uuid.UUID) -> bool:
        return await _anonymize_user(str(user_id))
