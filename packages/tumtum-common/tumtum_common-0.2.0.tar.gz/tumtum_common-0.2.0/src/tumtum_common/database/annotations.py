"""Database annotations."""

from fastapi import FastAPI, Depends
from .core import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

DatabaseSession = Annotated[
    AsyncSession,
    Depends(get_db_session)
]


