"""Authentication and authorisation.

Two defects are addressed here.

1. Tokens carried only `sub` and `exp`, but every authorisation check read
   `current_user.get("is_admin")` straight off the decoded payload. That key
   never existed, so the expression was always None and the entire admin
   surface — create/update/delete flight, the admin dashboard — returned 403
   to everyone, including the seeded administrator. The feature was shipped
   and unreachable.

2. The token payload was treated as the user record. Nothing was read back
   from the database, so a deactivated or deleted account kept full access
   until its token expired, and `is_active` was never enforced anywhere.

The fix: resolve the caller against the database on every request and treat
the stored record — not the token — as authoritative for privileges.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from app.database import db

# bcrypt truncates silently at 72 bytes, which would make every password
# sharing a 72-byte prefix equivalent. We reject instead of truncating.
BCRYPT_MAX_BYTES = 72

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except (ValueError, TypeError):
        # Malformed or missing hash in the stored record.
        return False


def get_password_hash(password: str) -> str:
    pw_bytes = password.encode("utf-8")
    if len(pw_bytes) > BCRYPT_MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be {BCRYPT_MAX_BYTES} bytes or less",
        )
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    to_encode.update(
        {
            "exp": now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)),
            "iat": now,
        }
    )
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    """Resolve the bearer token to a live user record.

    The token identifies the caller; the database decides what they are.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise _credentials_exception

    email = payload.get("sub")
    if not email:
        raise _credentials_exception

    user = await db.users.find_one({"email": email})
    if user is None:
        # Account deleted since the token was issued.
        raise _credentials_exception

    return user


async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    if not current_user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated"
        )
    return current_user


async def get_current_admin(
    current_user: dict = Depends(get_current_active_user),
) -> dict[str, Any]:
    # Read from the stored record, never from the token, so that revoking
    # admin takes effect immediately rather than at token expiry.
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action",
        )
    return current_user
