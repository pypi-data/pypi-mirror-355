# app/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import Session
from sqlmodel.ext.asyncio.session import AsyncSession

from app import models, crud, schemas
from app.utils.database import async_engine, get_async_session
import os
import uuid

SECRET_KEY = os.environ.get("JWT_SECRET_KEY")  # 请使用环境变量管理
ALGORITHM = os.environ.get("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_SECONDS = os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_SECONDS")
REFRESH_TOKEN_EXPIRE_SECONDS = os.environ.get("JWT_REFRESH_TOKEN_EXPIRE_SECONDS")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[models.User]:
    user = await crud.user.read_user(db, params=schemas.UserFilter(username=username))
    if not user:
        return None
    print(user)
    if not verify_password(password, user.password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta if expires_delta else timedelta(seconds=float(ACCESS_TOKEN_EXPIRE_SECONDS)))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token() -> str:
    return str(uuid.uuid4())


async def create_refresh_token_record(db: AsyncSession, user_id: int) -> models.RefreshToken:
    refresh_token_str = create_refresh_token()
    expires_at = datetime.utcnow() + timedelta(seconds=float(REFRESH_TOKEN_EXPIRE_SECONDS))
    refresh_token = await crud.refresh_token.create_refresh_token(
        db=db,
        obj_in=schemas.RefreshTokenCreate(
            token=refresh_token_str,
            user_id=user_id,
            expires_at=expires_at
        )
    )
    return refresh_token


async def verify_refresh_token(db: AsyncSession, token: str) -> Optional[models.RefreshToken]:
    db_token = await crud.refresh_token.read_refresh_token(db, params=schemas.RefreshTokenFilter(token=token))
    if not db_token or db_token.revoked or db_token.expires_at < datetime.utcnow():
        return None
    return db_token


async def verify_user_token(token: str) -> Optional[models.User]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    # 从数据库获取用户
    from app.utils.database import async_engine
    async with AsyncSession(async_engine) as db:
        user = await crud.user.read_user(db, params=schemas.UserFilter(username=username))
        return user
