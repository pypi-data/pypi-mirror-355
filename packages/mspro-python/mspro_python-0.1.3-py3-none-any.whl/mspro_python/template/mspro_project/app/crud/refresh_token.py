# app/crud/refresh_token.py
"""
    CRUD helpers for RefreshToken (generated).
    Author: Jena
    Date: 2025-05-10 02:53:15
"""
from typing import List, Optional, Sequence

from fastapi_pagination import Page
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import RefreshToken
from app.schemas import RefreshTokenCreate, RefreshTokenUpdate, RefreshTokenRead, RefreshTokenFilter
from app.utils.crud import (
    read_one, list_all, paginate_all,
    create_one, update_one, delete_one
)


async def read_refresh_token(db: AsyncSession, id: int = None, params: Optional[RefreshTokenFilter] = None,
                             logic: str = "and") -> Optional[RefreshToken]:
    """Return one record or *None*."""
    return await read_one(db, RefreshToken, "id", id, params, logic)


async def option_refresh_token(db: AsyncSession, params: RefreshTokenFilter = None, logic: str = "and") -> List[
    RefreshToken]:
    """Return all record without pagination or *None*."""
    return await list_all(db, RefreshToken, params, logic)


async def page_refresh_token(db: AsyncSession, params: RefreshTokenFilter = None, logic: str = "and") -> Page[
    RefreshToken]:
    """Return all record with pagination or *None*."""
    return await paginate_all(db, RefreshToken, params, logic)


async def create_refresh_token(db: AsyncSession, obj_in: RefreshTokenCreate) -> RefreshToken:
    return await create_one(db, RefreshToken, obj_in)


async def update_refresh_token(db: AsyncSession, id: int, obj_in: RefreshTokenUpdate) -> Optional[RefreshToken]:
    return await update_one(db, RefreshToken, id, obj_in, "id")


async def remove_refresh_token(db: AsyncSession, id: int) -> RefreshToken | None:
    return await delete_one(db, RefreshToken, id, "id")


async def revoke_refresh_token(db: AsyncSession, token: str) -> Optional[RefreshToken]:
    db_token = await read_refresh_token(db, params=RefreshTokenFilter(token=token))
    if db_token:
        db_token.revoked = True
        await db.commit()
        await db.refresh(db_token)
    return db_token


async def revoke_all_refresh_tokens(db: AsyncSession, user_id: int) -> Sequence[RefreshToken]:
    tokens = await option_refresh_token(db, params=RefreshTokenFilter(user_id=user_id, revoked=False))
    for token in tokens:
        token.revoked = True
    await db.commit()
    return tokens
