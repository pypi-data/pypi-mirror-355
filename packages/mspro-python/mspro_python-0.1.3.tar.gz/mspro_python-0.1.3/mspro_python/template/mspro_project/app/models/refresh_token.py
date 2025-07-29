# app/models/refresh_token.py
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

from app.models.timestamp import TimestampMixin


class RefreshToken(TimestampMixin, SQLModel, table=True):
    __tablename__ = "refresh_tokens"
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_general_ci'
    }

    id: Optional[int] = Field(default=None, primary_key=True)
    token: str = Field(unique=True, index=True, nullable=False)
    user_id: int = Field(foreign_key="users.user_id", nullable=False)
    expires_at: datetime = Field(nullable=False)
    revoked: bool = Field(default=False, nullable=False)

    # Relationships
    user: Optional["User"] = Relationship(back_populates="refresh_tokens")
