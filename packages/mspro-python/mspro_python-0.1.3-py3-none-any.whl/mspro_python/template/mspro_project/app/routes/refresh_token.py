# app/routers/refresh_token.py
"""
    FastAPI routes for RefreshToken (generated).
    Author: Jena
    Date: 2025-05-10 00:10:58
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from sqlmodel.ext.asyncio.session import AsyncSession

from app.utils.dependencies import get_async_session, get_current_user
from app import crud, schemas

router = APIRouter(
    prefix="/refresh_token", 
    tags=["refresh_token"],
    dependencies=[Depends(get_current_user)]
)


@router.get("/", response_model=Page[schemas.RefreshTokenRead])
async def page_refresh_tokens(params: schemas.RefreshTokenFilter = Depends(), db: AsyncSession = Depends(get_async_session)):
    return await crud.page_refresh_token(db, params)


@router.get("/option", response_model=List[schemas.RefreshTokenRead])
async def option_refresh_tokens(params: schemas.RefreshTokenFilter = Depends(), db: AsyncSession = Depends(get_async_session)):
    return await crud.option_refresh_token(db, params)


@router.get("/{id}", response_model=schemas.RefreshTokenRead)
async def read_refresh_token(id: int, db: AsyncSession = Depends(get_async_session)):
    return await crud.read_refresh_token(db, id)


@router.post("/", response_model=schemas.RefreshTokenRead)
async def create_refresh_token(item_in: schemas.RefreshTokenCreate, db: AsyncSession = Depends(get_async_session)):
    return await crud.create_refresh_token(db, item_in)


@router.put("/{id}", response_model=schemas.RefreshTokenRead)
async def update_refresh_token(id: int, item_in: schemas.RefreshTokenUpdate, db: AsyncSession = Depends(get_async_session)):
    updated = await crud.update_refresh_token(db, id, item_in)
    if not updated:
        raise HTTPException(status_code=404, detail="RefreshToken not found")
    return updated


@router.delete("/{id}", response_model=schemas.RefreshTokenRead)
async def delete_refresh_token(id: int, db: AsyncSession = Depends(get_async_session)):
    deleted = await crud.remove_refresh_token(db, id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="RefreshToken not found")
    return deleted
