import re
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pymongo.errors import DuplicateKeyError

from app.auth import get_current_admin
from app.database import db
from app.models.schemas import DEFAULT_SEAT_CAPACITY, FlightCreate, FlightModel, FlightUpdate

router = APIRouter()

# "Athens (ATH)" -> "ATH". Falls back to letters of the city name.
_IATA_PATTERN = re.compile(r"\(([A-Z]{3})\)")


def _station_code(name: str) -> str:
    match = _IATA_PATTERN.search(name or "")
    if match:
        return match.group(1)
    letters = re.sub(r"[^A-Za-z]", "", name or "")[:3].upper()
    return letters.ljust(3, "X")


def _generate_flight_code(flight: FlightCreate) -> str:
    """Build a flight designator from route, date and departure hour.

    The original took only the first letter of each city name, so
    Athens->Berlin and Amsterdam->Brussels on the same date and hour produced
    an identical code and the second insert was rejected as a duplicate.
    Using the IATA station code makes collisions between distinct routes
    impossible.
    """
    date_part = flight.date.replace("-", "")[2:]  # YYMMDD
    time_part = flight.time.replace(":", "")[:2]  # HH
    return f"{_station_code(flight.departure)}{_station_code(flight.destination)}{date_part}{time_part}"


@router.get("/", response_model=List[FlightModel])
async def search_flights(
    departure: Optional[str] = None,
    destination: Optional[str] = None,
    date: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    query: dict = {}

    # re.escape is load-bearing. These values reach an unauthenticated
    # endpoint and were interpolated into $regex verbatim, so a caller could
    # supply a pattern such as "(a+)+$" and pin a CPU core, or use lookahead
    # to probe the collection.
    if departure:
        query["departure"] = {"$regex": re.escape(departure), "$options": "i"}
    if destination:
        query["destination"] = {"$regex": re.escape(destination), "$options": "i"}
    if date:
        query["date"] = date

    cursor = db.availableFlights.find(query).skip(offset).limit(limit)
    return await cursor.to_list(length=limit)


@router.get("/{unique_code}", response_model=FlightModel)
async def get_flight(unique_code: str):
    flight = await db.availableFlights.find_one({"unique_code": unique_code})
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    return flight


@router.post("/", response_model=FlightModel, status_code=status.HTTP_201_CREATED)
async def create_flight(
    flight: FlightCreate, current_user: dict = Depends(get_current_admin)
):
    flight_dict = flight.model_dump()
    flight_dict["unique_code"] = _generate_flight_code(flight)
    flight_dict["availability"] = DEFAULT_SEAT_CAPACITY
    flight_dict["created_at"] = datetime.now(timezone.utc)

    try:
        result = await db.availableFlights.insert_one(flight_dict)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A flight already exists for this route, date and hour",
        )

    return await db.availableFlights.find_one({"_id": result.inserted_id})


@router.put("/{unique_code}", response_model=FlightModel)
async def update_flight(
    unique_code: str,
    flight_update: FlightUpdate,
    current_user: dict = Depends(get_current_admin),
):
    flight = await db.availableFlights.find_one({"unique_code": unique_code})
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")

    # Repricing a flight that already carries passengers would leave those
    # bookings holding a fare that no longer exists.
    if flight_update.cost is not None and flight["availability"] != DEFAULT_SEAT_CAPACITY:
        raise HTTPException(
            status_code=400, detail="Cannot change the fare of a flight with bookings"
        )

    update_data = flight_update.model_dump(exclude_unset=True)
    if update_data:
        await db.availableFlights.update_one(
            {"unique_code": unique_code}, {"$set": update_data}
        )

    return await db.availableFlights.find_one({"unique_code": unique_code})


@router.delete("/{unique_code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_flight(
    unique_code: str, current_user: dict = Depends(get_current_admin)
):
    # Deleting a flight out from under its passengers orphans their bookings:
    # the booking row survives with a flight_code that resolves to nothing.
    booked = await db.bookings.count_documents({"flight_code": unique_code})
    if booked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete a flight with {booked} active booking(s)",
        )

    result = await db.availableFlights.delete_one({"unique_code": unique_code})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Flight not found")
