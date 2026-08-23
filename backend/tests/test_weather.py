"""The weather proxy.

Weather is decoration on a booking product, so the behaviour worth pinning
down is not that it works — it is that it cannot take anything down when the
provider misbehaves. Every test here asserts a 200.

Open-Meteo is never actually called: each test substitutes the module's own
fetch, so the suite has no network dependency and cannot go red because a
third party is having a bad afternoon. That would be the same mistake in the
test suite that the router exists to avoid in the product.
"""

import pytest

from app.routers import weather as weather_module
from app.schemas import DailyForecast, StationWeather


@pytest.fixture(autouse=True)
def clear_cache():
    """The cache is process-local, so it outlives a test unless cleared."""
    weather_module._cache.clear()
    yield
    weather_module._cache.clear()


def _station(iata: str = "LHR") -> StationWeather:
    return StationWeather(
        iata_code=iata,
        city="London",
        temperature_c=17,
        condition="Mainly clear",
        wind_kph=10,
        forecast=[DailyForecast(date="2026-08-24", condition="Rain", high_c=23, low_c=16)],
    )


class TestDescribe:
    def test_maps_known_wmo_codes_to_the_phrasing_the_interface_uses(self):
        assert weather_module.describe(0) == "Clear"
        assert weather_module.describe(2) == "Partly cloudy"
        assert weather_module.describe(95) == "Thunderstorm"

    def test_an_unknown_code_degrades_rather_than_raising(self):
        # The provider is free to add codes. Doing so must not 500 a dashboard.
        assert weather_module.describe(4242) == "Unsettled"

    def test_a_missing_code_is_not_an_error(self):
        assert weather_module.describe(None) == "Unavailable"


class TestReadWeather:
    async def test_returns_conditions_for_the_requested_station(
        self, client, reference_data, monkeypatch
    ):
        async def fake_fetch(_client, airport):
            return _station(airport.iata_code)

        monkeypatch.setattr(weather_module, "_fetch", fake_fetch)

        response = await client.get("/api/weather", params={"iata": "LHR"})
        assert response.status_code == 200

        stations = response.json()["stations"]
        assert [s["iata_code"] for s in stations] == ["LHR"]
        assert stations[0]["temperature_c"] == 17
        assert stations[0]["forecast"][0]["high_c"] == 23

    async def test_an_upstream_failure_is_silent_rather_than_a_5xx(
        self, client, reference_data, monkeypatch
    ):
        async def dead(_client, _airport):
            return None

        monkeypatch.setattr(weather_module, "_fetch", dead)

        response = await client.get("/api/weather", params={"iata": "LHR"})
        # The provider gave us nothing, so we have nothing to say — but the
        # dashboard still renders, which is the entire point.
        assert response.status_code == 200
        assert response.json()["stations"] == []

    async def test_an_exception_from_the_provider_is_contained(
        self, client, reference_data, monkeypatch
    ):
        async def explode(_client, _airport):
            raise RuntimeError("connection reset")

        monkeypatch.setattr(weather_module, "_fetch", explode)

        response = await client.get("/api/weather", params={"iata": "LHR"})
        assert response.status_code == 200
        assert response.json()["stations"] == []

    async def test_an_unknown_station_is_absent_not_an_error(
        self, client, reference_data, monkeypatch
    ):
        async def fake_fetch(_client, airport):
            return _station(airport.iata_code)

        monkeypatch.setattr(weather_module, "_fetch", fake_fetch)

        # JFK is not in the network. Asking about it is a fact about the
        # network, not a fault.
        response = await client.get("/api/weather", params={"iata": "JFK"})
        assert response.status_code == 200
        assert response.json()["stations"] == []

    async def test_a_second_request_is_served_from_the_cache(
        self, client, reference_data, monkeypatch
    ):
        calls = []

        async def counting_fetch(_client, airport):
            calls.append(airport.iata_code)
            return _station(airport.iata_code)

        monkeypatch.setattr(weather_module, "_fetch", counting_fetch)

        await client.get("/api/weather", params={"iata": "LHR"})
        await client.get("/api/weather", params={"iata": "LHR"})

        # One upstream call for two requests — the dashboard gets reloaded a
        # lot and conditions do not move in the meantime.
        assert calls == ["LHR"]

    async def test_an_expired_entry_is_fetched_again(
        self, client, reference_data, monkeypatch
    ):
        calls = []

        async def counting_fetch(_client, airport):
            calls.append(airport.iata_code)
            return _station(airport.iata_code)

        monkeypatch.setattr(weather_module, "_fetch", counting_fetch)
        monkeypatch.setattr(weather_module, "_TTL_SECONDS", -1)

        await client.get("/api/weather", params={"iata": "LHR"})
        await client.get("/api/weather", params={"iata": "LHR"})

        assert calls == ["LHR", "LHR"]

    async def test_no_station_filter_covers_the_whole_network(
        self, client, reference_data, monkeypatch
    ):
        async def fake_fetch(_client, airport):
            return _station(airport.iata_code)

        monkeypatch.setattr(weather_module, "_fetch", fake_fetch)

        response = await client.get("/api/weather")
        codes = [s["iata_code"] for s in response.json()["stations"]]
        assert "ATH" in codes and "LHR" in codes
        # Sorted, so the interface gets a stable order across requests.
        assert codes == sorted(codes)

    async def test_it_needs_no_token(self, client, reference_data, monkeypatch):
        async def fake_fetch(_client, airport):
            return _station(airport.iata_code)

        monkeypatch.setattr(weather_module, "_fetch", fake_fetch)

        # No Authorization header anywhere in this file. Weather is not
        # passenger data, and requiring a token would stop the dashboard
        # painting until login resolved.
        assert (await client.get("/api/weather")).status_code == 200
