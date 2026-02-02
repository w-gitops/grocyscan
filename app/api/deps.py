"""API dependencies for dependency injection."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db

# Type alias for database session dependency
DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user_id() -> AsyncGenerator[str, None]:
    """Get the current authenticated user ID.

    This is a placeholder that will be replaced with actual auth logic.

    Yields:
        str: The current user's ID
    """
    # TODO: Implement actual authentication
    yield "default-user-id"


CurrentUserId = Annotated[str, Depends(get_current_user_id)]
