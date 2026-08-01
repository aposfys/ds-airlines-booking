"""API request and response models.

Distinct from app/models/domain.py, which is the persistence layer. Keeping
them separate is what stops a column rename from silently changing the API,
and stops an internal field — a password hash, a full card number — from
reaching a response because someone added it to the table.
"""

from __future__ import annotations

import re
import secrets
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# Excludes I, O, 0, 1 — a booking reference gets read aloud over the phone
# and written on paper, and those four are where transcription goes wrong.
_REFERENCE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_booking_reference() -> str:
    return "".join(secrets.choice(_REFERENCE_ALPHABET) for _ in range(6))


# ── Users ─────────────────────────────────────────────────


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_.-]+$")
    full_name: str = Field(min_length=1, max_length=120)
    passport_number: str = Field(min_length=4, max_length=20)
    password: str = Field(min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter")
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    username: str
    full_name: str
    passport_number: str | None = None
    is_admin: bool
    is_active: bool


class Token(BaseModel):
    access_token: str
    token_type: str


# ── Reference data ────────────────────────────────────────


class AirportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    iata_code: str
    name: str
    city: str
    country: str


class FareClassResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    description: str
    price_multiplier: Decimal
    cabin_bag_included: bool
    checked_bag_included: bool
    seat_selection_included: bool
    changeable: bool
    refundable: bool
    change_fee_eur: Decimal


# ── Flights ───────────────────────────────────────────────


class FareOption(BaseModel):
    """A fare class priced for a specific flight.

    The document model had one `cost` per flight and no way to express what
    the fare entitled the passenger to. Search now returns a price per
    branded fare, which is what the passenger is actually choosing between.
    """

    fare_class_code: str
    name: str
    price_eur: Decimal
    seats_available: int
    cabin_bag_included: bool
    checked_bag_included: bool
    changeable: bool
    refundable: bool


class FlightSummary(BaseModel):
    id: UUID
    flight_number: str
    origin_iata: str
    origin_city: str
    destination_iata: str
    destination_city: str
    departure_date: date
    scheduled_departure: datetime
    scheduled_arrival: datetime
    duration_minutes: int
    aircraft_type: str
    seats_available: int
    fares: list[FareOption]


class FlightCreate(BaseModel):
    flight_number: str = Field(pattern=r"^DS\d{3,4}$")
    origin_iata: str = Field(min_length=3, max_length=3)
    destination_iata: str = Field(min_length=3, max_length=3)
    departure_date: date
    departure_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    aircraft_registration: str
    base_fare_eur: Decimal = Field(gt=0, le=100_000)

    @field_validator("origin_iata", "destination_iata")
    @classmethod
    def uppercase_iata(cls, v: str) -> str:
        if not v.isalpha():
            raise ValueError("IATA code must be three letters")
        return v.upper()


class FlightUpdate(BaseModel):
    base_fare_eur: Decimal | None = Field(default=None, gt=0, le=100_000)
    status: str | None = None


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
    """The card is validated, reduced to its last four digits, and discarded.

    It is never written to the database in any form (DEF-003). Phase 3 removes
    the field entirely — the provider tokenises it in the browser and the
    number never reaches this server.
    """

    flight_id: UUID
    fare_class_code: str = Field(min_length=2, max_length=16)
    passenger_full_name: str = Field(min_length=1, max_length=120)
    passenger_passport: str = Field(min_length=4, max_length=20)
    credit_card: str = Field(min_length=12, max_length=25, exclude=True)
    seat_number: str | None = Field(default=None, max_length=4)

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


class BookingResponse(BaseModel):
    id: UUID
    booking_reference: str
    status: str
    flight_number: str
    origin_iata: str
    destination_iata: str
    scheduled_departure: datetime
    fare_class_code: str
    passenger_full_name: str
    seat_numbers: list[str]
    card_last4: str
    amount_eur: Decimal
    created_at: datetime
