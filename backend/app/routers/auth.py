from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    create_access_token,
    get_current_active_user,
    get_password_hash,
    verify_password,
)
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.db import get_session
from app.models.domain import User
from app.schemas import Token, UserCreate, UserLogin, UserResponse

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, session: AsyncSession = Depends(get_session)):
    user = User(
        email=payload.email,
        username=payload.username,
        full_name=payload.full_name,
        passport_number=payload.passport_number,
        hashed_password=get_password_hash(payload.password),
        is_admin=False,  # never client-controlled
        is_active=True,
    )
    session.add(user)

    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        # Uniqueness is decided by the case-insensitive indexes, not by a
        # read-then-write check that two concurrent requests could both pass.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username is already registered",
        )

    return user


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, session: AsyncSession = Depends(get_session)):
    user = await session.scalar(
        select(User).where(func.lower(User.username) == payload.username.lower())
    )

    # The hash comparison runs even when no such user exists, so response
    # time does not reveal which usernames are registered.
    stored_hash = user.hashed_password if user else ""
    password_ok = verify_password(payload.password, stored_hash)

    if not user or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated"
        )

    return Token(
        access_token=create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        ),
        token_type="bearer",
    )


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: AsyncSession = Depends(get_session),
):
    """OAuth2 password flow, used by the Swagger UI Authorize button."""
    return await login(
        UserLogin(username=form_data.username, password=form_data.password), session
    )


@router.get("/me", response_model=UserResponse)
async def read_current_user(current_user: User = Depends(get_current_active_user)):
    """The authenticated user's own profile.

    The frontend had no way to obtain this: AuthContext decoded the JWT and
    filled the rest with placeholders, so every session displayed the literal
    name "User" (DEF-016).
    """
    return current_user
