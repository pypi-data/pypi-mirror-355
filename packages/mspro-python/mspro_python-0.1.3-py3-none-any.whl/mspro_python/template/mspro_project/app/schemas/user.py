# app/schemas/user.py
"""
    Pydantic schemas for User (generated).
    Author: Jena
    Date: 2025-05-10 02:20:07
"""
from datetime import datetime
from typing import Optional, Any, List, Tuple
from pydantic import BaseModel

from app.models.user import RoleEnum


class UserBase(BaseModel):
    username: str


class UserRead(UserBase):
    user_id: int
    nickname: str
    status: int
    role: RoleEnum
    last_login: datetime
    created_at: datetime
    updated_at: datetime


class UserCreate(UserBase):
    nickname: str
    password: str


class UserRegister(UserBase):
    otp: str
    password: str
    nickname: str


class UserUpdate(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    username: Optional[str] = None
    password: Optional[str] = None
    nickname: Optional[str] = None
    status: Optional[int] = None
    role: Optional[RoleEnum] = None
    last_login: Optional[datetime] = None


class UserFilter(BaseModel):
    created_at: Optional[datetime] = None
    created_at__in: Optional[List[datetime]] = None
    created_at__not_in: Optional[List[datetime]] = None
    created_at__gte: Optional[datetime] = None
    created_at__lte: Optional[datetime] = None
    created_at__between: Optional[tuple[datetime, datetime]] = None
    updated_at: Optional[datetime] = None
    updated_at__in: Optional[List[datetime]] = None
    updated_at__not_in: Optional[List[datetime]] = None
    updated_at__gte: Optional[datetime] = None
    updated_at__lte: Optional[datetime] = None
    updated_at__between: Optional[tuple[datetime, datetime]] = None
    user_id: Optional[int] = None
    user_id__in: Optional[List[int]] = None
    user_id__not_in: Optional[List[int]] = None
    user_id__gte: Optional[int] = None
    user_id__lte: Optional[int] = None
    user_id__between: Optional[tuple[int, int]] = None
    username: Optional[str] = None
    username__like: Optional[str] = None
    username__in: Optional[List[str]] = None
    username__not_in: Optional[List[str]] = None
    password: Optional[str] = None
    password__like: Optional[str] = None
    password__in: Optional[List[str]] = None
    password__not_in: Optional[List[str]] = None
    nickname: Optional[str] = None
    nickname__like: Optional[str] = None
    nickname__in: Optional[List[str]] = None
    nickname__not_in: Optional[List[str]] = None
    status: Optional[int] = None
    status__in: Optional[List[int]] = None
    status__not_in: Optional[List[int]] = None
    status__gte: Optional[int] = None
    status__lte: Optional[int] = None
    status__between: Optional[tuple[int, int]] = None
    role: Optional[RoleEnum] = None
    role__in: Optional[List[RoleEnum]] = None
    role__not_in: Optional[List[RoleEnum]] = None
    last_login: Optional[datetime] = None
    last_login__in: Optional[List[datetime]] = None
    last_login__not_in: Optional[List[datetime]] = None
    last_login__gte: Optional[datetime] = None
    last_login__lte: Optional[datetime] = None
    last_login__between: Optional[tuple[datetime, datetime]] = None


class UserReadWithRelation(UserRead):
    refresh_tokens: Optional[List["RefreshTokenRead"]] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expired_in: int
