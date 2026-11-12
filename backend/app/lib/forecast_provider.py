"""ForecastProvider: beach-level sargassum probabilities from the sargassum-forecast static API.

Source: https://github.com/nareshrajesh787/sargassum-forecast — a daily forecast for 8 Broward County, FL
beaches, scored against FIU Sargassum Watch reports. The API is static JSON:
``{SARGASSUM_FORECAST_API}/api/v1/forecast/latest.json``.

How zones are filled
- The municipality's lat/lng is matched to the nearest forecast site. Within ``MAX_DISTANCE_KM`` every zone's
  ``forecastRisk`` comes from that site: h12 and h24 use the 1-day lead, h48 the 2-day lead. Values are clamped
  to Costa's 0–0.95 risk range.
- Farther away (e.g. Costa's default Fajardo, PR, ~1,600 km from Broward) there is no validated forecast. Zones
  keep Costa's wind-based live risk, and ``forecastProvider.available`` is False with the reason. No forecast is
  invented for unvalidated coordinates.
- Scenario labelling is unchanged: a zone with ``forecastOverride`` keeps its scripted risk and stays
  ``forecastSource == "scenario"``. Only ``liveForecastRisk`` is updated.

Enabled only when the ``SARGASSUM_FORECAST_API`` env var is set (e.g. the project's Vercel URL).
The provider's own track record and caveats are on that site. The served model is experimental, not a warning system.
"""

from __future__ import annotations

import math
import os
import time
from typing import Any

import httpx

MAX_DISTANCE_KM = 30.0
CACHE_SECONDS = 1800
_cache: dict[str, tuple[float, dict[str, Any]]] = {}


def api_base() -> str | None:
    base = os.getenv("SARGASSUM_FORECAST_API", "").strip().rstrip("/")
    return base or None


def _km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


async def fetch_latest(base: str, client: httpx.AsyncClient | None = None) -> dict[str, Any]:
    now = time.monotonic()
    hit = _cache.get(base)
    if hit and now - hit[0] < CACHE_SECONDS:
        return hit[1]
    own = client is None
    client = client or httpx.AsyncClient(timeout=10.0)
    try:
        r = await client.get(f"{base}/api/v1/forecast/latest.json")
        r.raise_for_status()
        data: dict[str, Any] = r.json()
    finally:
        if own:
            await client.aclose()
    _cache[base] = (now, data)
    return data


def risk_for_location(forecast: dict[str, Any], lat: float, lng: float) -> dict[str, Any]:
    """Nearest-site risk and provenance, or ``available: False`` with the reason."""
    sites = forecast.get("sites") or []
    if not sites:
        return {"available": False, "reason": "forecast has no sites"}
    best = min(sites, key=lambda s: _km(lat, lng, float(s["lat"]), float(s["lon"])))
    km = _km(lat, lng, float(best["lat"]), float(best["lon"]))
    meta = {"source": "sargassum-forecast", "site": best["name"], "distanceKm": round(km, 1),
            "modelVersion": forecast.get("model_version"), "issueDate": forecast.get("issue_date")}
    if km > MAX_DISTANCE_KM:
        return {"available": False, **meta,
                "reason": f"nearest validated forecast site is {km:.0f} km away (limit {MAX_DISTANCE_KM:.0f} km)"}
    by_lead = {int(x["lead_days"]): x for x in best.get("leads", [])}
    if 1 not in by_lead or 2 not in by_lead:
        return {"available": False, **meta, "reason": "forecast lacks 1- and 2-day leads"}
    clamp = lambda p: max(0.0, min(0.95, float(p)))  # noqa: E731  (Costa's risk range)
    risk = {"h12": clamp(by_lead[1]["probability"]), "h24": clamp(by_lead[1]["probability"]),
            "h48": clamp(by_lead[2]["probability"])}
    return {"available": True, **meta, "risk": risk,
            "inValidatedSeason": bool(by_lead[1].get("in_validated_season", False)),
            "disclaimer": forecast.get("disclaimer", "")}


def apply_sargassum_forecast(zones: list[dict[str, Any]], info: dict[str, Any]) -> list[dict[str, Any]]:
    """Fill zones from the provider. Keeps scenario overrides and Costa's live/scenario labels."""
    for zone in zones:
        zone["forecastProvider"] = {k: v for k, v in info.items() if k != "risk"}
        if not info.get("available"):
            continue
        risk = dict(info["risk"])
        zone["liveForecastRisk"] = risk
        if zone.get("forecastOverride"):
            zone["forecastSource"] = "scenario"  # a loaded scenario still wins; the live value stays visible
        else:
            zone["forecastRisk"] = risk
            zone["forecastSource"] = "live"
    return zones
