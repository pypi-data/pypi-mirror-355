# app/schemas/refresh_token.py
"""
    Pydantic schemas for RefreshToken (generated).
    Author: Jena
    Date: 2025-05-10 02:20:07
"""
from datetime import datetime
from typing import Optional, Any, List, Tuple
from pydantic import BaseModel


class RefreshTokenBase(BaseModel):
    token: str
    user_id: int
    expires_at: datetime


class RefreshTokenRead(RefreshTokenBase):
    id: int
    created_at: datetime
    updated_at: datetime
    revoked: bool


class RefreshTokenCreate(RefreshTokenBase):
    pass


class RefreshTokenUpdate(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    token: Optional[str] = None
    user_id: Optional[int] = None
    expires_at: Optional[datetime] = None
    revoked: Optional[bool] = None


class RefreshTokenFilter(BaseModel):
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
    id: Optional[int] = None
    id__in: Optional[List[int]] = None
    id__not_in: Optional[List[int]] = None
    id__gte: Optional[int] = None
    id__lte: Optional[int] = None
    id__between: Optional[tuple[int, int]] = None
    token: Optional[str] = None
    token__like: Optional[str] = None
    token__in: Optional[List[str]] = None
    token__not_in: Optional[List[str]] = None
    user_id: Optional[int] = None
    user_id__in: Optional[List[int]] = None
    user_id__not_in: Optional[List[int]] = None
    user_id__gte: Optional[int] = None
    user_id__lte: Optional[int] = None
    user_id__between: Optional[tuple[int, int]] = None
    expires_at: Optional[datetime] = None
    expires_at__in: Optional[List[datetime]] = None
    expires_at__not_in: Optional[List[datetime]] = None
    expires_at__gte: Optional[datetime] = None
    expires_at__lte: Optional[datetime] = None
    expires_at__between: Optional[tuple[datetime, datetime]] = None
    revoked: Optional[bool] = None
    revoked__in: Optional[List[bool]] = None
    revoked__not_in: Optional[List[bool]] = None


class RefreshTokenReadWithRelation(RefreshTokenRead):
    user: Optional["UserRead"] = None

    class Config:
        from_attributes = True
