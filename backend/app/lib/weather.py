"""Live coastal conditions from Open-Meteo, NOAA tides, and NWS.

Beach seaweed amounts still come from signed-in reports — there is no
public satellite API that names mats on a specific Fajardo beach.
"""

from __future__ import annotations

import asyncio
import math
import time
from typing import Any

import httpx

_cache: dict[str, tuple[float, dict[str, Any]]] = {}
TTL_SECONDS = 12 * 60

NWS_HEADERS = {
    "User-Agent": "SargassumWatch/1.0 (municipal-ops-hackathon)",
    "Accept": "application/geo+json",
}

# NOAA CO-OPS water-level stations used to pick the nearest tide gauge.
TIDE_STATIONS = (
    ("9752235", "Culebra", 18.3008, -65.3017),
    ("9751639", "San Juan", 18.4592, -66.1164),
    ("9752695", "Esperanza, Vieques", 18.0936, -65.4708),
    ("9751364", "Isabel Segunda, Vieques", 18.1525, -65.4439),
    ("9755371", "Yabucoa Harbor", 18.0550, -65.8330),
    ("9759110", "Magueyes Island", 17.9700, -67.0467),
)

WMO = {
    0: "Clear",
    1: "Mostly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Icy fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    71: "Light snow",
    80: "Rain showers",
    81: "Rain showers",
    82: "Heavy showers",
    95: "Thunderstorms",
    96: "Thunderstorms",
    99: "Thunderstorms",
}


def _angle_diff(a: float, b: float) -> float:
    return abs((a - b + 180) % 360 - 180)


def compass(degrees: float) -> str:
    labels = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
    return labels[int((degrees % 360) / 45 + 0.5) % 8]


def landfall_risk(direction: float, speed: float, shore_facing: float, hours: int) -> float:
    alignment = max(0.0, 1.0 - _angle_diff(direction, shore_facing) / 180.0)
    speed_factor = min(1.0, max(0.0, speed) / 12.0)
    horizon = {12: 0.38, 24: 0.62, 48: 0.84}.get(hours, 0.62)
    return round(min(0.95, 0.08 + alignment * speed_factor * horizon + 0.12 * (hours / 48)), 4)


def _nearest_tide(lat: float, lng: float) -> tuple[str, str, float]:
    best = TIDE_STATIONS[0]
    best_km = 1e9
    for station in TIDE_STATIONS:
        dlat = math.radians(station[2] - lat)
        dlng = math.radians(station[3] - lng)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat)) * math.cos(math.radians(station[2])) * math.sin(dlng / 2) ** 2
        km = 6371 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        if km < best_km:
            best = station
            best_km = km
    return best[0], best[1], round(best_km, 1)


async def fetch_marine_weather(lat: float, lng: float) -> dict[str, Any]:
    key = f"{round(lat, 3)}:{round(lng, 3)}"
    hit = _cache.get(key)
    now = time.time()
    if hit and now - hit[0] < TTL_SECONDS:
        return hit[1]

    open_meteo, nws, tides = await asyncio.gather(
        _open_meteo(lat, lng),
        _nws_forecast(lat, lng),
        _noaa_tides(lat, lng),
        return_exceptions=True,
    )
    payload = _empty_weather(lat, lng)
    if isinstance(open_meteo, dict):
        payload.update(open_meteo)
    if isinstance(nws, dict):
        payload["nws"] = nws
    if isinstance(tides, dict):
        payload["tide"] = tides
    payload["sources"] = [
        {"name": "Open-Meteo", "usedFor": "Wind, waves, currents, temperature"},
        {"name": "National Weather Service", "usedFor": "Official forecast wording"},
        {"name": "NOAA CO-OPS", "usedFor": "Tide at the nearest gauge"},
        {"name": "Neighbor reports", "usedFor": "How much seaweed is on each beach"},
    ]
    _cache[key] = (now, payload)
    return payload


def _empty_weather(lat: float, lng: float) -> dict[str, Any]:
    return {
        "source": "Open-Meteo",
        "fetchedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "lat": lat,
        "lng": lng,
        "summary": "Weather is loading",
        "temperatureC": None,
        "temperatureF": None,
        "humidity": None,
        "weatherCode": None,
        "windSpeedMs": 0.0,
        "windSpeedMph": 0.0,
        "windDirection": 0.0,
        "windCompass": "E",
        "currentSpeedMs": 0.0,
        "currentDirection": 0.0,
        "currentCompass": "E",
        "waveHeightM": 0.0,
        "waveHeightFt": 0.0,
        "h12": {"windSpeedMs": 0.0, "windDirection": 90.0},
        "h24": {"windSpeedMs": 0.0, "windDirection": 90.0},
        "h48": {"windSpeedMs": 0.0, "windDirection": 90.0},
        "nws": None,
        "tide": None,
        "sources": [],
    }


async def _open_meteo(lat: float, lng: float) -> dict[str, Any]:
    params = {
        "latitude": lat,
        "longitude": lng,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,wind_direction_10m",
        "hourly": "wind_speed_10m,wind_direction_10m",
        "forecast_days": 3,
        "wind_speed_unit": "ms",
        "timezone": "auto",
    }
    marine_params = {
        "latitude": lat,
        "longitude": lng,
        "hourly": "ocean_current_velocity,ocean_current_direction,wave_height",
        "forecast_days": 3,
        "timezone": "auto",
    }
    async with httpx.AsyncClient(timeout=12) as client:
        wind_res, marine_res = await asyncio.gather(
            client.get("https://api.open-meteo.com/v1/forecast", params=params),
            client.get("https://marine-api.open-meteo.com/v1/marine", params=marine_params),
        )
        wind_res.raise_for_status()
        wind = wind_res.json()
        marine = marine_res.json() if marine_res.status_code == 200 else {}

    current = wind.get("current") or {}
    hourly = wind.get("hourly") or {}
    speeds = hourly.get("wind_speed_10m") or []
    dirs = hourly.get("wind_direction_10m") or []
    marine_hourly = marine.get("hourly") or {}
    currents = marine_hourly.get("ocean_current_velocity") or []
    current_dirs = marine_hourly.get("ocean_current_direction") or []
    waves = marine_hourly.get("wave_height") or []

    def at_hour(series: list, hours: int, fallback: float) -> float:
        idx = min(len(series) - 1, max(0, hours)) if series else -1
        if idx < 0:
            return fallback
        value = series[idx]
        return float(value) if value is not None else fallback

    wind_speed = float(current.get("wind_speed_10m") or (speeds[0] if speeds else 0) or 0)
    wind_dir = float(current.get("wind_direction_10m") or (dirs[0] if dirs else 0) or 0)
    current_speed = at_hour(currents, 0, wind_speed * 0.15)
    current_dir = at_hour(current_dirs, 0, wind_dir)
    temp_c = current.get("temperature_2m")
    code = current.get("weather_code")
    summary = WMO.get(int(code), "Coastal weather") if code is not None else "Coastal weather"
    wave_m = at_hour(waves, 0, 0.0)

    return {
        "source": "Open-Meteo",
        "fetchedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "lat": lat,
        "lng": lng,
        "summary": summary,
        "temperatureC": round(float(temp_c), 1) if temp_c is not None else None,
        "temperatureF": round(float(temp_c) * 9 / 5 + 32) if temp_c is not None else None,
        "humidity": int(current["relative_humidity_2m"]) if current.get("relative_humidity_2m") is not None else None,
        "weatherCode": int(code) if code is not None else None,
        "windSpeedMs": round(wind_speed, 2),
        "windSpeedMph": round(wind_speed * 2.237, 1),
        "windDirection": round(wind_dir, 1),
        "windCompass": compass(wind_dir),
        "currentSpeedMs": round(current_speed, 3),
        "currentDirection": round(current_dir, 1),
        "currentCompass": compass(current_dir),
        "waveHeightM": round(wave_m, 2),
        "waveHeightFt": round(wave_m * 3.281, 1),
        "h12": {
            "windSpeedMs": round(at_hour(speeds, 12, wind_speed), 2),
            "windDirection": round(at_hour(dirs, 12, wind_dir), 1),
        },
        "h24": {
            "windSpeedMs": round(at_hour(speeds, 24, wind_speed), 2),
            "windDirection": round(at_hour(dirs, 24, wind_dir), 1),
        },
        "h48": {
            "windSpeedMs": round(at_hour(speeds, 48, wind_speed), 2),
            "windDirection": round(at_hour(dirs, 48, wind_dir), 1),
        },
    }


async def _nws_forecast(lat: float, lng: float) -> dict[str, Any] | None:
    async with httpx.AsyncClient(timeout=10, headers=NWS_HEADERS, follow_redirects=True) as client:
        points = await client.get(f"https://api.weather.gov/points/{lat:.4f},{lng:.4f}")
        if points.status_code >= 400:
            return None
        forecast_url = (points.json().get("properties") or {}).get("forecast")
        if not forecast_url:
            return None
        forecast = await client.get(forecast_url)
        if forecast.status_code >= 400:
            return None
        periods = (forecast.json().get("properties") or {}).get("periods") or []
        if not periods:
            return None
        now = periods[0]
        nxt = periods[1] if len(periods) > 1 else None
        return {
            "source": "National Weather Service",
            "name": now.get("name"),
            "short": now.get("shortForecast") or "",
            "detailed": (now.get("detailedForecast") or "")[:280],
            "tempF": now.get("temperature"),
            "wind": f"{now.get('windSpeed') or ''} {now.get('windDirection') or ''}".strip(),
            "nextName": (nxt or {}).get("name"),
            "nextShort": (nxt or {}).get("shortForecast") or "",
        }


async def _noaa_tides(lat: float, lng: float) -> dict[str, Any] | None:
    station_id, station_name, km = _nearest_tide(lat, lng)
    url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
    params = {
        "station": station_id,
        "product": "predictions",
        "datum": "MLLW",
        "date": "today",
        "time_zone": "lst_ldt",
        "units": "english",
        "interval": "hilo",
        "format": "json",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url, params=params)
        if response.status_code >= 400:
            return None
        rows = response.json().get("predictions") or []
    highs: list[dict[str, Any]] = []
    lows: list[dict[str, Any]] = []
    for row in rows:
        entry = {"time": row.get("t"), "heightFt": round(float(row.get("v") or 0), 2), "type": row.get("type")}
        if row.get("type") == "H":
            highs.append(entry)
        else:
            lows.append(entry)
    next_event = None
    now = time.strftime("%Y-%m-%d %H:%M")
    for row in rows:
        if (row.get("t") or "") >= now:
            next_event = {
                "when": row.get("t"),
                "heightFt": round(float(row.get("v") or 0), 2),
                "kind": "High tide" if row.get("type") == "H" else "Low tide",
            }
            break
    if next_event is None and rows:
        row = rows[-1]
        next_event = {
            "when": row.get("t"),
            "heightFt": round(float(row.get("v") or 0), 2),
            "kind": "High tide" if row.get("type") == "H" else "Low tide",
        }
    return {
        "source": "NOAA CO-OPS",
        "stationId": station_id,
        "stationName": station_name,
        "distanceKm": km,
        "next": next_event,
        "today": [*highs[:2], *lows[:2]],
    }


def apply_weather_to_zones(zones: list[dict[str, Any]], weather: dict[str, Any]) -> list[dict[str, Any]]:
    for zone in zones:
        facing = float(zone.get("shoreFacing", 90))
        zone["currentVector"] = {
            "speed": max(0.2, float(weather.get("currentSpeedMs") or 0) * 1.8),
            "direction": float(weather.get("currentDirection") or 90),
        }
        h12 = weather.get("h12") or {}
        h24 = weather.get("h24") or {}
        h48 = weather.get("h48") or {}
        zone["forecastRisk"] = {
            "h12": landfall_risk(float(h12.get("windDirection") or 90), float(h12.get("windSpeedMs") or 0), facing, 12),
            "h24": landfall_risk(float(h24.get("windDirection") or 90), float(h24.get("windSpeedMs") or 0), facing, 24),
            "h48": landfall_risk(float(h48.get("windDirection") or 90), float(h48.get("windSpeedMs") or 0), facing, 48),
        }
    return zones
