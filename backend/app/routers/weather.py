"""Current conditions and a short forecast for the stations we serve.

Server-side on purpose. The browser never calls Open-Meteo directly, which
keeps a third party out of the passenger's network path, lets one cache serve
every visitor instead of each browser warming its own, and means an outage
upstream is something this application decides how to present rather than a
console full of failed cross-origin requests.

Nothing here is authenticated. Weather is not passenger data, and requiring a
token would mean the dashboard could not paint until login resolved.

The failure mode is the important part: every path returns 200 with whatever
could be gathered. A forecast provider having a bad afternoon must not take
down a booking dashboard, so an upstream error yields an entry with no
weather rather than a 502.
"""

from __future__ import annotations

import asyncio
import time

import httpx
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..models.domain import Airport
from ..schemas import DailyForecast, StationWeather, WeatherResponse

router = APIRouter()

_ENDPOINT = "https://api.open-meteo.com/v1/forecast"
_TIMEOUT = httpx.Timeout(4.0, connect=2.0)

# Half an hour. Conditions do not move fast enough to matter sooner, and the
# dashboard is the kind of page people reload repeatedly.
_TTL_SECONDS = 30 * 60

# iata -> (expires_at, payload). Process-local by design: this is one small
# dict in front of a free public API, not a caching tier. A second worker
# keeping its own copy costs one extra upstream call per half hour.
_cache: dict[str, tuple[float, StationWeather]] = {}

# WMO 4677 weather codes, collapsed to the phrasing the interface uses.
_CONDITIONS: dict[int, str] = {
    0: "Clear",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Freezing fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    56: "Freezing drizzle",
    57: "Freezing drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    66: "Freezing rain",
    67: "Freezing rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Light showers",
    81: "Showers",
    82: "Heavy showers",
    85: "Snow showers",
    86: "Snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with hail",
}


def describe(code: int | None) -> str:
    """Never fail on an unrecognised code — the provider may add more."""
    if code is None:
        return "Unavailable"
    return _CONDITIONS.get(code, "Unsettled")


def _cached(iata: str) -> StationWeather | None:
    entry = _cache.get(iata)
    if entry is None:
        return None
    expires_at, payload = entry
    if expires_at < time.monotonic():
        del _cache[iata]
        return None
    return payload


async def _fetch(
    client: httpx.AsyncClient, airport: Airport
) -> StationWeather | None:
    """One station. Returns None on any upstream trouble, never raises."""
    try:
        response = await client.get(
            _ENDPOINT,
            params={
                "latitude": airport.latitude,
                "longitude": airport.longitude,
                "current": "temperature_2m,weather_code,wind_speed_10m",
                "daily": "weather_code,temperature_2m_max,temperature_2m_min",
                # Today plus the three days the interface shows.
                "forecast_days": 4,
                "timezone": "auto",
            },
        )
        response.raise_for_status()
        body = response.json()
    except (httpx.HTTPError, ValueError):
        return None

    current = body.get("current") or {}
    daily = body.get("daily") or {}

    dates = daily.get("time") or []
    codes = daily.get("weather_code") or []
    highs = daily.get("temperature_2m_max") or []
    lows = daily.get("temperature_2m_min") or []

    forecast: list[DailyForecast] = []
    # Skip index 0 — that is today, which `current` already covers.
    for i in range(1, min(len(dates), len(codes), len(highs), len(lows))):
        forecast.append(
            DailyForecast(
                date=dates[i],
                condition=describe(codes[i]),
                high_c=round(highs[i]),
                low_c=round(lows[i]),
            )
        )

    temperature = current.get("temperature_2m")
    if temperature is None:
        return None

    return StationWeather(
        iata_code=airport.iata_code,
        city=airport.city,
        temperature_c=round(temperature),
        condition=describe(current.get("weather_code")),
        wind_kph=round(current.get("wind_speed_10m") or 0),
        forecast=forecast,
    )


@router.get("", response_model=WeatherResponse)
async def read_weather(
    iata: list[str] = Query(
        default=[],
        description="Station codes. Empty means every station in the network.",
    ),
    session: AsyncSession = Depends(get_session),
) -> WeatherResponse:
    """Conditions for the requested stations, cached for thirty minutes.

    Unknown codes are simply absent from the response rather than an error:
    the caller asked about a station we do not serve, which is a fact about
    the network, not a fault.
    """
    wanted = {code.strip().upper() for code in iata if code.strip()}

    query = select(Airport)
    if wanted:
        query = query.where(Airport.iata_code.in_(wanted))
    airports = (await session.execute(query)).scalars().all()

    fresh = [a for a in airports if _cached(a.iata_code) is None]

    if fresh:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            results = await asyncio.gather(
                *(_fetch(client, a) for a in fresh), return_exceptions=True
            )
        expires_at = time.monotonic() + _TTL_SECONDS
        for airport, result in zip(fresh, results):
            if isinstance(result, StationWeather):
                _cache[airport.iata_code] = (expires_at, result)

    stations = [w for a in airports if (w := _cached(a.iata_code)) is not None]
    stations.sort(key=lambda s: s.iata_code)
    return WeatherResponse(stations=stations)
