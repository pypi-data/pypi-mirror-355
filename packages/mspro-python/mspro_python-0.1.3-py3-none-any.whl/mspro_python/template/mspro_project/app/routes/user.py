# app/routers/user.py
"""
    FastAPI routes for User (generated).
    Author: Jena
    Date: 2025-05-10 00:10:58
"""
import os
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import Response, JSONResponse
from fastapi_pagination import Page
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette import status

from app.models import User
from app.utils.dependencies import get_async_session, get_current_user
from app import crud, schemas
from app.utils.helper import response_error, response_success
from app.utils.security import authenticate_user, create_access_token, create_refresh_token_record, \
    verify_refresh_token, get_password_hash

router = APIRouter(
    prefix="/user",
    tags=["user"],
)


@router.get("/", response_model=Page[schemas.UserRead], dependencies=[Depends(get_current_user)])
async def page_users(params: schemas.UserFilter = Depends(), db: AsyncSession = Depends(get_async_session)):
    return await crud.page_user(db, params)


@router.get("/option", response_model=List[schemas.UserRead], dependencies=[Depends(get_current_user)])
async def option_users(params: schemas.UserFilter = Depends(), db: AsyncSession = Depends(get_async_session)):
    return await crud.option_user(db, params)


@router.post("/", response_model=schemas.UserRead)
async def create_user(item_in: schemas.UserCreate, db: AsyncSession = Depends(get_async_session)):
    item_in.password = get_password_hash(item_in.password)
    return await crud.create_user(db, item_in)


@router.post("/register", response_model=schemas.UserRead)
async def register_user(item_in: schemas.UserRegister, db: AsyncSession = Depends(get_async_session)):
    check = await crud.read_user(db, params=schemas.UserFilter(username=item_in.username))
    if check:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This email is exist")
    item_in.password = get_password_hash(item_in.password)
    item_in = schemas.UserCreate(username=item_in.username, password=item_in.password, nickname=item_in.nickname)
    return await crud.create_user(db, item_in)


@router.put("/{user_id}", response_model=schemas.UserRead)
async def update_user(item_in: schemas.UserUpdate, db: AsyncSession = Depends(get_async_session),
                      user=Depends(get_current_user)):
    updated = await crud.update_user(db, user.user_id, item_in)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated


# @router.delete("/{user_id}", response_model=schemas.UserRead)
# async def delete_user(user_id: int, db: AsyncSession = Depends(get_session)):
#     deleted = await crud.remove_user(db, user_id)
#     if deleted is None:
#         raise HTTPException(status_code=404, detail="User not found")
#     return deleted


@router.post("/token", response_model=schemas.TokenResponse)
async def login_for_access_token(
        *,
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_async_session),
        response: Response
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.status != 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Account has been disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username})
    refresh_token = await create_refresh_token_record(db, user.user_id)
    # 更新最后登录时间
    user_update = schemas.user.UserUpdate(last_login=datetime.utcnow())
    await crud.user.update_user(db, user.user_id, user_update)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token.token,
        httponly=True,
        secure=True,  # 在生产环境中使用 HTTPS 时设置
        samesite="strict",
        max_age=7 * 24 * 60 * 60  # 7 天
    )
    return {"access_token": access_token, "token_type": "bearer",
            "expired_in": os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_SECONDS")}


@router.post("/refresh", response_model=schemas.TokenResponse)
async def refresh_access_token(
        *,
        request: Request,
        db: AsyncSession = Depends(get_async_session),
        response: Response
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )
    db_token = await verify_refresh_token(db, refresh_token)
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db_token.user
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 撤销当前刷新令牌，生成新的刷新令牌
    await crud.refresh_token.revoke_refresh_token(db, refresh_token)
    new_refresh_token = await create_refresh_token_record(db, user.user_id)
    new_access_token = create_access_token(data={"sub": user.username})
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token.token,
        httponly=True,
        secure=True,  # 在生产环境中使用 HTTPS 时设置
        samesite="strict",
        max_age=7 * 24 * 60 * 60  # 7 天
    )
    return {"access_token": new_access_token, "token_type": "bearer",
            "expired_in": os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_SECONDS")}


@router.get("/me", response_model=schemas.UserRead)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/{user_id}", response_model=schemas.UserRead, dependencies=[Depends(get_current_user)])
async def read_user(user_id: int, db: AsyncSession = Depends(get_async_session)):
    return await crud.read_user(db, user_id)
