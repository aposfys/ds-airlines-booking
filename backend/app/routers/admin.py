from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.auth import get_current_admin, get_password_hash
from app.database import db
from app.models.schemas import UserCreate, UserResponse
from app.routers.auth import PASSWORD_FIELD

router = APIRouter()


@router.get("/dashboard", status_code=status.HTTP_200_OK)
async def dashboard(current_user: dict = Depends(get_current_admin)):
    return {"message": f"Welcome Admin {current_user.get('fullname')}"}


@router.post(
    "/admins", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def create_admin(user: UserCreate, current_user: dict = Depends(get_current_admin)):
    """Promote a new administrator.

    This handler previously wrote the password digest to `hashed_password`
    while the login handler read `password`, so every account created here
    raised a KeyError at login and returned 500. Both now use the single
    PASSWORD_FIELD constant.
    """
    user_dict = user.model_dump()
    user_dict[PASSWORD_FIELD] = get_password_hash(user_dict.pop("password"))
    user_dict["is_admin"] = True
    user_dict["is_active"] = True

    try:
        result = await db.users.insert_one(user_dict)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username is already registered",
        )

    return await db.users.find_one({"_id": result.inserted_id})
