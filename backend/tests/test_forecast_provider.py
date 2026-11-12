"""ForecastProvider: nearest-site mapping, unvalidated-location refusal, scenario labelling preserved."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.data.zones import clone_zone_template  # noqa: E402
from app.lib.forecast_provider import apply_sargassum_forecast, risk_for_location  # noqa: E402

FORECAST = {
    "model_version": "v0.1-test-frozen",
    "issue_date": "2027-06-01",
    "disclaimer": "Experimental research forecast, not a warning system.",
    "sites": [
        {"id": "the_palms", "name": "The Palms", "lat": 26.1562, "lon": -80.0996,
         "leads": [{"lead_days": 1, "probability": 0.31, "in_validated_season": True},
                   {"lead_days": 2, "probability": 0.42, "in_validated_season": True},
                   {"lead_days": 3, "probability": 0.40, "in_validated_season": True}]},
        {"id": "county_line", "name": "County Line", "lat": 26.3209, "lon": -80.0744,
         "leads": [{"lead_days": 1, "probability": 0.99, "in_validated_season": True},
                   {"lead_days": 2, "probability": 0.10, "in_validated_season": True}]},
    ],
}


def test_nearby_municipality_gets_nearest_site_risk() -> None:
    info = risk_for_location(FORECAST, 26.16, -80.10)  # Fort Lauderdale
    assert info["available"] and info["site"] == "The Palms" and info["distanceKm"] < 2
    assert info["risk"] == {"h12": 0.31, "h24": 0.31, "h48": 0.42}


def test_risk_is_clamped_to_costa_range() -> None:
    info = risk_for_location(FORECAST, 26.32, -80.07)
    assert info["risk"]["h12"] == 0.95


def test_fajardo_is_not_given_an_unvalidated_forecast() -> None:
    info = risk_for_location(FORECAST, 18.3256, -65.6524)  # Costa default municipality
    assert info["available"] is False and "km away" in info["reason"]
    zones = clone_zone_template()
    before = [z["forecastRisk"] for z in zones]
    out = apply_sargassum_forecast(zones, info)
    assert [z["forecastRisk"] for z in out] == before
    assert all(z["forecastProvider"]["available"] is False for z in out)


def test_live_zones_are_filled_and_scenarios_stay_scenarios() -> None:
    zones = clone_zone_template()
    zones[0]["forecastOverride"] = {"h12": 0.78, "h24": 0.86, "h48": 0.91}
    zones[0]["forecastRisk"] = dict(zones[0]["forecastOverride"])
    out = apply_sargassum_forecast(zones, risk_for_location(FORECAST, 26.16, -80.10))
    assert out[0]["forecastSource"] == "scenario" and out[0]["forecastRisk"]["h12"] == 0.78
    assert out[0]["liveForecastRisk"]["h12"] == 0.31
    assert all(z["forecastSource"] == "live" and z["forecastRisk"]["h48"] == 0.42 for z in out[1:])
