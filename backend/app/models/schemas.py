import re
from datetime import datetime, timezone
from typing import Annotated, Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from pydantic.functional_validators import BeforeValidator

# Single-fleet A321neo configuration. Lives here so the router, the seed
# script and the fare rules cannot drift apart.
DEFAULT_SEAT_CAPACITY = 220

# Mongo returns ObjectId; the API speaks strings. Serialising through str on
# the way in is enough, and avoids the custom __get_pydantic_core_schema__
# class the previous version carried.
ObjectIdStr = Annotated[str, BeforeValidator(str)]


def _utcnow() -> datetime:
    # datetime.utcnow() is deprecated in 3.12+ and returns a naive datetime,
    # which compares incorrectly against the aware values used in auth.
    return datetime.now(timezone.utc)


# ── Users ─────────────────────────────────────────────────


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=32)
    fullname: str = Field(min_length=1, max_length=120)
    passport_num: Optional[str] = Field(default=None, max_length=20)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=72)
    passport_num: str = Field(max_length=20)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        # The frontend told users "8+ characters and a number" but nothing
        # server-side enforced it, so the API accepted "a".
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter")
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: Optional[ObjectIdStr] = Field(default=None, alias="_id")
    is_admin: bool = False
    is_active: bool = True

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


# ── Flights ───────────────────────────────────────────────


class FlightCreate(BaseModel):
    departure: str = Field(min_length=2, max_length=80)
    destination: str = Field(min_length=2, max_length=80)
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    time: str = Field(pattern=r"^\d{2}:\d{2}$")
    cost: float = Field(gt=0, le=100_000)
    duration: str

    @field_validator("date")
    @classmethod
    def date_is_parseable(cls, v: str) -> str:
        datetime.strptime(v, "%Y-%m-%d")
        return v

    @field_validator("destination")
    @classmethod
    def not_same_as_origin(cls, v: str, info: Any) -> str:
        if info.data.get("departure", "").strip().lower() == v.strip().lower():
            raise ValueError("Destination must differ from departure")
        return v


class FlightModel(FlightCreate):
    id: Optional[ObjectIdStr] = Field(default=None, alias="_id")
    unique_code: str
    availability: int = Field(default=DEFAULT_SEAT_CAPACITY, ge=0)
    created_at: datetime = Field(default_factory=_utcnow)

    model_config = ConfigDict(populate_by_name=True)


class FlightUpdate(BaseModel):
    cost: Optional[float] = Field(default=None, gt=0, le=100_000)
    availability: Optional[int] = Field(default=None, ge=0, le=DEFAULT_SEAT_CAPACITY)


# ── Bookings ──────────────────────────────────────────────


def _luhn_valid(digits: str) -> bool:
    total, parity = 0, len(digits) % 2
    for i, ch in enumerate(digits):
        d = int(ch)
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


class BookingCreate(BaseModel):
    """Booking request.

    `credit_card` is accepted, validated, and then discarded — only the last
    four digits reach the database. The previous version persisted the full
    PAN in cleartext alongside the passenger's passport number, which is a
    PCI-DSS violation on its own and, combined with the passport number,
    turns any read access to the bookings collection into a serious personal
    data breach under GDPR Art. 32.

    Phase 3 removes the field entirely: the card is tokenised in the browser
    by the payment provider and the number never reaches this server.
    """

    flight_code: str = Field(min_length=3, max_length=32)
    full_name: str = Field(min_length=1, max_length=120)
    passport_num: str = Field(min_length=4, max_length=20)
    credit_card: str = Field(min_length=12, max_length=25, exclude=True)

    @field_validator("credit_card")
    @classmethod
    def card_is_plausible(cls, v: str) -> str:
        digits = re.sub(r"[ -]", "", v)
        if not digits.isdigit() or not 12 <= len(digits) <= 19:
            raise ValueError("Card number must be 12–19 digits")
        if not _luhn_valid(digits):
            raise ValueError("Card number failed checksum validation")
        return digits

    @property
    def card_last4(self) -> str:
        return self.credit_card[-4:]


class BookingModel(BaseModel):
    id: Optional[ObjectIdStr] = Field(default=None, alias="_id")
    user_id: str
    flight_code: str
    full_name: str
    passport_num: str
    # Retained for display ("Visa ending 4242"). The full number is not
    # stored anywhere, in any form.
    card_last4: str = Field(min_length=4, max_length=4)
    booking_date: datetime = Field(default_factory=_utcnow)
    cost: float
    departure: str
    destination: str
    flight_date: str

    model_config = ConfigDict(populate_by_name=True)
