import logging
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pymongo.errors import DuplicateKeyError

from app.auth import (
    create_access_token,
    get_current_active_user,
    get_password_hash,
    verify_password,
)
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.database import db
from app.models.schemas import Token, UserCreate, UserLogin, UserResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# Stored under a name that says what it is. The previous code wrote the
# bcrypt digest to a field called `password`, while the admin router wrote
# the same digest to `hashed_password` — so accounts created through the
# admin endpoint hit a KeyError at login and returned 500 forever.
PASSWORD_FIELD = "hashed_password"


def _issue_token(user: dict) -> Token:
    access_token = create_access_token(
        data={"sub": user["email"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=access_token, token_type="bearer")


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(user: UserCreate):
    user_dict = user.model_dump()
    user_dict[PASSWORD_FIELD] = get_password_hash(user_dict.pop("password"))
    user_dict["is_admin"] = False  # never client-controlled
    user_dict["is_active"] = True

    try:
        result = await db.users.insert_one(user_dict)
    except DuplicateKeyError:
        # Enforced by the unique indexes rather than a read-then-write check,
        # which two concurrent registrations could both pass.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username is already registered",
        )

    return await db.users.find_one({"_id": result.inserted_id})


@router.post("/login", response_model=Token)
async def login(user_login: UserLogin):
    user = await db.users.find_one({"username": user_login.username})

    # Always run the hash comparison, even when the user does not exist, so
    # that response time does not reveal which usernames are registered.
    stored_hash = user.get(PASSWORD_FIELD, "") if user else ""
    password_ok = verify_password(user_login.password, stored_hash)

    if not user or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated"
        )

    return _issue_token(user)


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    """OAuth2 password flow, used by the Swagger UI `Authorize` button."""
    return await login(
        UserLogin(username=form_data.username, password=form_data.password)
    )


@router.get("/me", response_model=UserResponse)
async def read_current_user(current_user: dict = Depends(get_current_active_user)):
    """The authenticated user's own profile.

    Added because the frontend had no way to obtain it: AuthContext decoded
    the JWT and filled the profile with placeholders, so every session
    displayed the literal name "User".
    """
    return current_user
