# app/models/timestamp.py
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import event


class TimestampMixin:
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.now, nullable=False)


def update_timestamp(mapper, connection, target):
    target.updated_at = datetime.now()


def register_timestamp_events():
    from .user import User
    from .refresh_token import RefreshToken

    classes = [User, RefreshToken]
    for cls in classes:
        event.listen(cls, 'before_update', update_timestamp)
