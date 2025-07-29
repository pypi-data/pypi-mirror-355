# app/crud/user.py
"""
    CRUD helpers for User (generated).
    Author: Jena
    Date: 2025-05-10 02:53:15
"""
from typing import List, Optional

from fastapi_pagination import Page
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import User
from app.schemas import UserCreate, UserUpdate, UserRead, UserFilter
from app.utils.crud import (
    read_one, list_all, paginate_all,
    create_one, update_one, delete_one
)


async def read_user(db: AsyncSession, user_id: int = None, params: Optional[UserFilter] = None, logic: str = "and") -> Optional[User]:
    """Return one record or *None*."""
    return await read_one(db, User, "user_id", user_id, params, logic)


async def option_user(db: AsyncSession, params: UserFilter = None, logic: str = "and") -> List[User]:
    """Return all record without pagination or *None*."""
    return await list_all(db, User, params, logic)


async def page_user(db: AsyncSession, params: UserFilter = None, logic: str = "and") -> Page[User]:
    """Return all record with pagination or *None*."""
    return await paginate_all(db, User, params, logic)


async def create_user(db: AsyncSession, obj_in: UserCreate) -> User:
    return await create_one(db, User, obj_in)


async def update_user(db: AsyncSession, user_id: int, obj_in: UserUpdate) -> Optional[User]:
    return await update_one(db, User, user_id, obj_in, "user_id")


async def remove_user(db: AsyncSession, user_id: int) -> User | None:
    return await delete_one(db, User, user_id, "user_id")
