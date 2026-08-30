"""Integration tests for the wired paths: weather conversion, demo playback, auth gates.

The existing test_algorithms.py exercises app/lib/algorithms.py directly. That left
the code that actually runs in production untested, and it hid a real bug: the
scripted forecast demo event wrote forecastRisk straight onto the zone, and the very
next snapshot overwrote it from live weather, so the third demo event did nothing on
screen. test_forecast_override_survives_weather_refresh is the regression test.

Run from the backend directory:
    pytest tests/ -q
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Point the database at a throwaway file BEFORE app.db resolves DB_PATH, so a test
# run never touches backend/data/sargassum.db.
_TMPDIR = tempfile.TemporaryDirectory()
import app.db as db  # noqa: E402

db.DB_PATH = Path(_TMPDIR.name) / "test.db"

from fastapi.testclient import TestClient  # noqa: E402

from app.data.demo_scenarios import DEMO_EVENTS  # noqa: E402
from app.data.zones import clone_zone_template  # noqa: E402
from app.lib.weather import (  # noqa: E402
    apply_weather_to_zones,
    compass,
    landfall_risk,
)


# --------------------------------------------------------------------------
# Weather -> zone conversion (previously untested, and load-bearing: it drives
# every zone's drift vector and forecastRisk on every single snapshot)
# --------------------------------------------------------------------------

SAMPLE_WEATHER = {
    "currentSpeedMs": 0.5,
    "currentDirection": 214.0,
    "h12": {"windSpeedMs": 6.0, "windDirection": 90.0},
    "h24": {"windSpeedMs": 6.0, "windDirection": 90.0},
    "h48": {"windSpeedMs": 6.0, "windDirection": 90.0},
}


def test_weather_populates_every_zone_vector_and_risk():
    zones = apply_weather_to_zones(clone_zone_template(), SAMPLE_WEATHER)
    assert zones, "template must not be empty"
    for zone in zones:
        assert zone["currentVector"]["direction"] == 214.0
        assert zone["currentVector"]["speed"] > 0
        for horizon in ("h12", "h24", "h48"):
            assert 0.0 <= zone["forecastRisk"][horizon] <= 0.95
        assert zone["forecastSource"] == "live"


def test_weather_risk_grows_with_horizon_for_onshore_wind():
    zones = apply_weather_to_zones(clone_zone_template(), SAMPLE_WEATHER)
    harbor = next(z for z in zones if z["id"] == "harbor-entrance")
    assert harbor["forecastRisk"]["h12"] < harbor["forecastRisk"]["h48"]


def test_landfall_risk_is_higher_when_wind_points_at_the_shore():
    onshore = landfall_risk(direction=90, speed=8, shore_facing=90, hours=24)
    offshore = landfall_risk(direction=270, speed=8, shore_facing=90, hours=24)
    assert onshore > offshore


def test_landfall_risk_stays_bounded():
    assert landfall_risk(90, 999, 90, 48) <= 0.95
    assert landfall_risk(90, 0, 90, 12) >= 0.0


def test_missing_weather_fields_do_not_crash_conversion():
    zones = apply_weather_to_zones(clone_zone_template(), {})
    for zone in zones:
        assert set(zone["forecastRisk"]) == {"h12", "h24", "h48"}


def test_compass_labels():
    assert compass(0) == "N"
    assert compass(90) == "E"
    assert compass(180) == "S"
    assert compass(270) == "W"


def test_forecast_override_survives_weather_refresh():
    """Regression: the scripted forecast event must not be erased by live weather.

    Before the fix, apply_weather_to_zones overwrote forecastRisk unconditionally,
    so playing the harbor-forecast demo event had no visible effect at all.
    """
    payload = DEMO_EVENTS[2]["payload"]
    zones = clone_zone_template()
    for zone in zones:
        if zone["id"] == payload["zoneId"]:
            zone["forecastOverride"] = payload["forecastRisk"]

    zones = apply_weather_to_zones(zones, SAMPLE_WEATHER)
    harbor = next(z for z in zones if z["id"] == payload["zoneId"])

    assert harbor["forecastRisk"] == payload["forecastRisk"]
    assert harbor["forecastSource"] == "scenario"
    # The live number is still carried alongside, so the scenario never hides it.
    assert harbor["liveForecastRisk"]["h12"] != payload["forecastRisk"]["h12"]

    # Zones without an override still track live weather.
    other = next(z for z in zones if z["id"] != payload["zoneId"])
    assert other["forecastSource"] == "live"


# --------------------------------------------------------------------------
# API: auth, role gates, demo playback
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def client():
    os.environ.setdefault("JWT_SECRET", "test-secret-for-pytest-only")
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


def _token(client, email: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": "password1"})
    assert response.status_code == 200, response.text
    return response.json()["token"]


@pytest.fixture(scope="module")
def ops_headers(client):
    return {"Authorization": f"Bearer {_token(client, 'ops@fajardo.test')}"}


@pytest.fixture(scope="module")
def citizen_headers(client):
    return {"Authorization": f"Bearer {_token(client, 'neighbor@fajardo.test')}"}


def test_seeded_demo_accounts_can_sign_in(client):
    """These are the accounts used on stage — a broken login is a dead demo."""
    for email in ("ops@fajardo.test", "neighbor@fajardo.test"):
        response = client.post("/api/auth/login", json={"email": email, "password": "password1"})
        assert response.status_code == 200, f"{email} could not sign in"
    assert client.post(
        "/api/auth/login", json={"email": "ops@fajardo.test", "password": "wrong-password"}
    ).status_code == 401


def test_state_requires_a_session(client):
    assert client.get("/api/state").status_code == 401
    assert client.get("/api/state", headers={"Authorization": "Bearer garbage"}).status_code == 401


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("post", "/api/inspect", {"zoneId": "quiet-inlet", "observedVolume": "small"}),
        ("patch", "/api/settings", {"crewBudget": 10}),
        ("patch", "/api/zones", {"zoneId": "quiet-inlet", "economicWeight": 2.0}),
        ("post", "/api/demo/seed", None),
        ("post", "/api/demo/reset", None),
        ("post", "/api/demo/play", {"eventId": "cove-surge"}),
    ],
)
def test_operations_only_routes_reject_citizens(client, citizen_headers, method, path, body):
    response = getattr(client, method)(path, json=body, headers=citizen_headers)
    assert response.status_code == 403, f"{path} should be operations-only"


def test_citizen_can_file_a_report(client, citizen_headers):
    response = client.post(
        "/api/reports",
        json={"zoneId": "quiet-inlet", "volume": "medium", "submitterType": "resident", "note": "test"},
        headers=citizen_headers,
    )
    assert response.status_code == 200
    assert response.json()["metrics"]["totalInspections"] >= 1


def test_seed_then_play_events_reallocates_crews(client, ops_headers):
    seeded = client.post("/api/demo/seed", headers=ops_headers).json()
    before = set(seeded["selection"]["ids"])
    assert before, "seeded shift should assign at least one cleanup zone"
    assert seeded["metrics"]["assignedHours"] <= seeded["metrics"]["crewBudget"]

    surge = client.post("/api/demo/play", json={"eventId": "cove-surge"}, headers=ops_headers).json()
    after = set(surge["selection"]["ids"])
    assert "residential-cove" in after, "the surge report should pull the cove onto the truck list"
    assert after != before, "event 1 must visibly change the allocation on stage"
    assert surge["changes"], "the reallocation must be reported so the UI can narrate it"


def test_scout_inspection_lowers_uncertainty_through_the_api(client, ops_headers):
    state = client.get("/api/state", headers=ops_headers).json()
    before = next(z for z in state["zones"] if z["id"] == "quiet-inlet")["uncertaintyBonus"]
    played = client.post("/api/demo/play", json={"eventId": "inlet-scout"}, headers=ops_headers).json()
    after = next(z for z in played["zones"] if z["id"] == "quiet-inlet")["uncertaintyBonus"]
    assert after < before


def test_forecast_demo_event_actually_flags_containment(client, ops_headers):
    """Regression for the demo-critical bug: event 3 used to be a silent no-op."""
    played = client.post("/api/demo/play", json={"eventId": "harbor-forecast"}, headers=ops_headers).json()
    harbor = next(z for z in played["zones"] if z["id"] == "harbor-entrance")

    assert harbor["forecastRisk"]["h12"] == pytest.approx(0.78)
    assert harbor["forecastSource"] == "scenario"
    assert "harbor-entrance" in {z["id"] for z in played["containment"]}

    # And it must still be there on the next plain snapshot, after weather refreshes.
    refreshed = client.get("/api/state", headers=ops_headers).json()
    assert "harbor-entrance" in {z["id"] for z in refreshed["containment"]}


def test_reset_clears_the_scenario_override(client, ops_headers):
    client.post("/api/demo/play", json={"eventId": "harbor-forecast"}, headers=ops_headers)
    reset = client.post("/api/demo/reset", headers=ops_headers).json()
    harbor = next(z for z in reset["zones"] if z["id"] == "harbor-entrance")
    assert harbor["forecastSource"] == "live"
    assert all(z["meanSeverity"] == 0 for z in reset["zones"])


def test_unknown_demo_event_is_a_404(client, ops_headers):
    assert client.post("/api/demo/play", json={"eventId": "nope"}, headers=ops_headers).status_code == 404


def test_budget_is_never_exceeded_across_the_whole_demo_run(client, ops_headers):
    client.post("/api/demo/reset", headers=ops_headers)
    state = client.post("/api/demo/seed", headers=ops_headers).json()
    for event in DEMO_EVENTS:
        state = client.post("/api/demo/play", json={"eventId": event["id"]}, headers=ops_headers).json()
        metrics = state["metrics"]
        assert metrics["assignedHours"] <= metrics["crewBudget"], f"{event['id']} blew the budget"


def test_settings_validation_rejects_an_out_of_range_budget(client, ops_headers):
    assert client.patch("/api/settings", json={"crewBudget": 99}, headers=ops_headers).status_code == 422


# --------------------------------------------------------------------------
# Explanation cascade: must degrade to the local template with no model at all
# --------------------------------------------------------------------------


def test_explain_falls_back_cleanly_with_no_model_configured(client, ops_headers, monkeypatch):
    """The 'kill the wi-fi' claim: no Grok key, no Ollama, still a coherent answer."""
    monkeypatch.setenv("XAI_API_KEY", "")
    monkeypatch.setenv("OLLAMA_URL", "http://127.0.0.1:9")  # nothing listens here

    response = client.post("/api/explain", json={}, headers=ops_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "local-fallback"
    for key in ("summary", "cleanupRationale", "scoutingRationale", "tradeoffs", "caveat"):
        assert body[key], f"{key} must not be empty in the offline explanation"
    assert isinstance(body["cleanupRationale"], list)


def test_ask_falls_back_cleanly_with_no_model(client, ops_headers, monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "")
    monkeypatch.setenv("OLLAMA_URL", "http://127.0.0.1:9")
    response = client.post(
        "/api/ask", json={"question": "Why is the dock unfunded?"}, headers=ops_headers
    )
    assert response.status_code == 200
    assert response.json()["answer"]


def test_dedicated_fallback_endpoint_reads_coherently(client, ops_headers):
    body = client.get("/api/explain/fallback", headers=ops_headers).json()
    assert body["source"] == "local-fallback"
    assert body["summary"].endswith(".")
    assert "estimate" in body["caveat"].lower()


def test_state_reports_the_tier_that_would_actually_answer(client, ops_headers):
    """Honesty check: with no key and no Ollama the desk must not credit Grok."""
    ai = client.get("/api/state", headers=ops_headers).json()["ai"]
    assert ai["tier"] in ("grok", "ollama", "local-fallback")
    if not (os.getenv("XAI_API_KEY") or "").strip():
        assert ai["tier"] != "grok", "claimed Grok without an API key"


def test_briefing_is_plain_text_and_readable(client, ops_headers):
    client.post("/api/demo/seed", headers=ops_headers)
    response = client.get("/api/briefing", headers=ops_headers)
    assert response.status_code == 200
    text = response.text
    for heading in ("Send the trucks", "Go look first", "Crew hours"):
        assert heading in text
    assert "does not pick the beaches" in text


def test_metrics_do_not_expose_subtractable_mixed_units(client, ops_headers):
    metrics = client.get("/api/state", headers=ops_headers).json()["metrics"]
    assert "netProtected" not in metrics, "netProtected mixed $/hour with whole-shift $"
    assert metrics["units"]["valueProtected"] == "USD per hour of exposure"
    assert metrics["units"]["operatingCost"] == "USD for the whole shift"
