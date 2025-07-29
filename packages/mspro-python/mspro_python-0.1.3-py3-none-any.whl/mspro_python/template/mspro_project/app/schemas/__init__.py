from typing import Union
from pydantic import BaseModel
from .user import *
from .refresh_token import *

__all__: list[str] = [
    "RefreshTokenBase", "RefreshTokenCreate", "RefreshTokenRead", "RefreshTokenUpdate", "RefreshTokenFilter",
    "RefreshTokenReadWithRelation",
    "UserBase", "UserCreate", "UserRead", "UserUpdate", "UserFilter", "UserReadWithRelation", "TokenResponse",
    "UserRegister",
]

# Update forward references for Pydantic v2
from .refresh_token import RefreshTokenRead
from .user import UserRead, UserReadWithRelation

UserRead.model_rebuild()
UserReadWithRelation.model_rebuild()
RefreshTokenRead.model_rebuild()


class OptionItem(BaseModel):
    label: str
    value: str | int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expired_in: int


class StandardResponse(BaseModel):
    success: bool
    message: str
    data: Union[dict[str, Any], list[Any]] = {}
