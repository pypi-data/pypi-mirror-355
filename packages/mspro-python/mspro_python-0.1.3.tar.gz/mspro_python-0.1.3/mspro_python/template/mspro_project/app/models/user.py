# app/models/user.py
import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, Enum
from sqlmodel import SQLModel, Field, Relationship
from .refresh_token import RefreshToken
from .timestamp import TimestampMixin


class RoleEnum(enum.Enum):
    user = 'user'
    admin = 'admin'


class User(TimestampMixin, SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_general_ci'
    }

    user_id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    password: str = Field(nullable=False)
    nickname: Optional[str] = Field(default=None, nullable=True)
    status: Optional[int] = Field(default=1)
    role: Optional[RoleEnum] = Field(sa_column=Column(Enum(RoleEnum)), default=RoleEnum.user)
    last_login: Optional[datetime] = Field(default_factory=datetime.now)

    # Relationships
    refresh_tokens: List["RefreshToken"] = Relationship(back_populates="user", cascade_delete=True)
