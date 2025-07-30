"""Models for caching."""

from pydantic import BaseModel
from enums import UserRoleEnum


class UserSession(BaseModel):
    """User session model."""

    id: int
    role: UserRoleEnum

