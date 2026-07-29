import logging
from datetime import datetime, timezone
from typing import List

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import get_current_active_user
from app.database import db
from app.models.schemas import BookingCreate, BookingModel

logger = logging.getLogger(__name__)

router = APIRouter()


def _user_key(user: dict) -> str:
    return str(user["_id"])


@router.post("/", response_model=BookingModel, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking: BookingCreate, current_user: dict = Depends(get_current_active_user)
):
    flight = await db.availableFlights.find_one({"unique_code": booking.flight_code})
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")

    # Claim the seat first, with the availability guard inside the filter so
    # that two concurrent requests for the last seat cannot both succeed.
    claim = await db.availableFlights.update_one(
        {"unique_code": booking.flight_code, "availability": {"$gt": 0}},
        {"$inc": {"availability": -1}},
    )
    if claim.modified_count == 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Flight is full")

    booking_doc = booking.model_dump()  # credit_card is excluded at the schema level
    booking_doc.update(
        {
            "user_id": _user_key(current_user),
            "card_last4": booking.card_last4,
            "cost": flight["cost"],
            "departure": flight["departure"],
            "destination": flight["destination"],
            "flight_date": flight["date"],
            "booking_date": datetime.now(timezone.utc),
        }
    )

    try:
        result = await db.bookings.insert_one(booking_doc)
    except Exception:
        # The seat is already claimed at this point. Without it, a failed
        # insert silently burned a seat that no passenger holds — the seat
        # count only ever drifted downwards. Release it before surfacing the
        # error. Phase 1 replaces this compensating write with a real
        # transaction once the data lives in PostgreSQL.
        await db.availableFlights.update_one(
            {"unique_code": booking.flight_code}, {"$inc": {"availability": 1}}
        )
        logger.exception("Booking insert failed; released held seat")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not complete booking",
        )

    return await db.bookings.find_one({"_id": result.inserted_id})


@router.get("/", response_model=List[BookingModel])
async def get_user_bookings(
    current_user: dict = Depends(get_current_active_user),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    cursor = db.bookings.find({"user_id": _user_key(current_user)}).skip(offset).limit(limit)
    return await cursor.to_list(length=limit)


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_booking(
    booking_id: str, current_user: dict = Depends(get_current_active_user)
):
    if not ObjectId.is_valid(booking_id):
        raise HTTPException(status_code=400, detail="Invalid booking id")

    # Ownership is part of the delete filter, so the check and the delete are
    # a single atomic operation and a booking cannot be cancelled twice.
    deleted = await db.bookings.find_one_and_delete(
        {"_id": ObjectId(booking_id), "user_id": _user_key(current_user)}
    )
    if deleted is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Only return the seat to inventory if the flight still exists.
    await db.availableFlights.update_one(
        {"unique_code": deleted["flight_code"]}, {"$inc": {"availability": 1}}
    )
