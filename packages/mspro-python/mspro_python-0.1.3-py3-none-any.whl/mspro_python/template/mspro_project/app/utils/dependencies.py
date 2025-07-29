# app/dependencies.py
import secrets

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, HTTPBasic, HTTPBasicCredentials
from jose import jwt, JWTError
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette import status

from app import models, crud, schemas
from app.utils.database import get_async_session
from app.utils.security import SECRET_KEY, ALGORITHM

# 其他依赖项可以在这里定义
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/user/token")
security = HTTPBasic()


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_async_session)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise JWTError("Missing 'sub' in token")
    except JWTError:
        raise credentials_exception
    user = await crud.user.read_user(db, params=schemas.UserFilter(username=username))
    if user is None:
        raise credentials_exception
    return user


async def get_basicauth_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "admin")
    correct_password = secrets.compare_digest(credentials.password, "123456")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
