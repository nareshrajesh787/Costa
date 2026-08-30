"""Per-municipality operating picture, persisted in SQLite."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from app.data.demo_scenarios import clone_demo_events
from app.data.zones import clone_zone_template
from app.db import dumps, get_conn, loads, row_to_dict
from app.lib.algorithms import apply_inspection, apply_report, evaluate_state
from app.lib.weather import apply_weather_to_zones, fetch_marine_weather

AT = timezone(timedelta(hours=-4))


def _now_iso() -> str:
    return datetime.now(AT).isoformat(timespec="seconds")


def create_municipality(name: str, region: str = "", lat: float = 18.3256, lng: float = -65.6524) -> dict[str, Any]:
    conn = get_conn()
    existing = conn.execute("SELECT * FROM municipalities WHERE lower(name) = lower(?)", (name.strip(),)).fetchone()
    if existing:
        return dict(existing)
    cur = conn.execute(
        """
        INSERT INTO municipalities (name, region, lat, lng, zones_json, event_log_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            name.strip(),
            region.strip(),
            lat,
            lng,
            dumps(clone_zone_template()),
            dumps(
                [
                    {
                        "id": "boot",
                        "kind": "system",
                        "title": "Municipality desk opened",
                        "detail": "Live reports and Open-Meteo marine weather will drive dispatch.",
                        "timestamp": _now_iso(),
                    }
                ]
            ),
            _now_iso(),
        ),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM municipalities WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


def get_municipality(muni_id: int) -> dict[str, Any] | None:
    return row_to_dict(get_conn().execute("SELECT * FROM municipalities WHERE id = ?", (muni_id,)).fetchone())


def _save_muni(muni_id: int, **fields: Any) -> None:
    if not fields:
        return
    assignments = ", ".join(f"{k} = ?" for k in fields)
    get_conn().execute(f"UPDATE municipalities SET {assignments} WHERE id = ?", [*fields.values(), muni_id])
    get_conn().commit()


def _log(muni_id: int, kind: str, title: str, detail: str, zone_id: str | None = None) -> list[dict[str, Any]]:
    conn = get_conn()
    stamp = _now_iso()
    conn.execute(
        """
        INSERT INTO events (municipality_id, kind, title, detail, zone_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (muni_id, kind, title, detail, zone_id, stamp),
    )
    conn.commit()
    muni = get_municipality(muni_id)
    log = loads(muni["event_log_json"], []) if muni else []
    entry = {
        "id": f"{kind}-{uuid.uuid4().hex[:10]}",
        "kind": kind,
        "title": title,
        "detail": detail,
        "timestamp": stamp,
        **({"zoneId": zone_id} if zone_id else {}),
    }
    log.insert(0, entry)
    _save_muni(muni_id, event_log_json=dumps(log[:40]))
    return log


def _reports(muni_id: int) -> list[dict[str, Any]]:
    rows = get_conn().execute(
        """
        SELECT id, zone_id as zoneId, volume, submitter_type as submitterType, note, source, created_at as timestamp
        FROM reports WHERE municipality_id = ? ORDER BY id DESC LIMIT 40
        """,
        (muni_id,),
    ).fetchall()
    return [dict(r) for r in rows]


async def snapshot(muni: dict[str, Any], *, highlight: bool = False, user: dict[str, Any] | None = None) -> dict[str, Any]:
    zones = loads(muni["zones_json"], clone_zone_template())
    weather = loads(muni.get("weather_json") or "{}", {})
    try:
        weather = await fetch_marine_weather(float(muni["lat"]), float(muni["lng"]))
        zones = apply_weather_to_zones(zones, weather)
        _save_muni(int(muni["id"]), weather_json=dumps(weather), zones_json=dumps(zones))
        muni = get_municipality(int(muni["id"])) or muni
    except Exception:
        if weather:
            zones = apply_weather_to_zones(zones, weather)

    prev_cleanup = loads(muni["previous_cleanup_json"], [])
    prev_scout = loads(muni["previous_scout_json"], [])
    evaluated = evaluate_state(
        zones,
        crew_budget=int(muni["crew_budget"]),
        exploration_c=float(muni["exploration_c"]),
        forecast_weight=float(muni["forecast_weight"]),
        horizon=str(muni["horizon"]),
        previous_cleanup_ids=prev_cleanup if highlight else None,
        previous_scout_ids=prev_scout if highlight else None,
    )
    _save_muni(
        int(muni["id"]),
        previous_cleanup_json=dumps(evaluated["selection"]["ids"]),
        previous_scout_json=dumps([z["id"] for z in evaluated["scoutNext"]]),
        zones_json=dumps(zones),
    )
    return _pack(muni, evaluated, weather, highlight=highlight, user=user)


def _pack(
    muni: dict[str, Any],
    snapshot_data: dict[str, Any],
    weather: dict[str, Any],
    *,
    highlight: bool,
    user: dict[str, Any] | None,
) -> dict[str, Any]:
    muni_id = int(muni["id"])
    report_rows = _reports(muni_id)
    log = loads(muni["event_log_json"], [])
    community_name = muni["name"]
    return {
        "community": {
            "name": community_name,
            "region": muni["region"] or "Coastal municipality",
            "shift": "Live operations window",
            "lat": muni["lat"],
            "lng": muni["lng"],
            "disclaimer": (
                f"How much seaweed is on each beach comes from people in {community_name} who filed a report. "
                "Wind, waves, and currents are live Open-Meteo. The forecast sentence is National Weather Service. "
                "Tides are NOAA. This desk does not invent satellite bloom maps."
            ),
        },
        "weather": weather,
        "ai": {
            "provider": "xAI Grok",
            "model": "grok-4.6",
            "endpoint": "https://api.x.ai/v1",
            "role": "explains computed numbers only",
        },
        "user": (
            {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]}
            if user
            else None
        ),
        "settings": {
            "crewBudget": int(muni["crew_budget"]),
            "explorationC": float(muni["exploration_c"]),
            "forecastWeight": float(muni["forecast_weight"]),
            "horizon": muni["horizon"],
        },
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "highlight": highlight,
        "changes": snapshot_data["changes"] if highlight else [],
        "zones": snapshot_data["zones"],
        "cleanupNow": snapshot_data["cleanupNow"],
        "unfunded": snapshot_data["unfunded"],
        "scoutNext": snapshot_data["scoutNext"],
        "scoutRanked": snapshot_data["scoutRanked"],
        "containment": snapshot_data["containment"],
        "metrics": snapshot_data["metrics"],
        "selection": snapshot_data["selection"],
        "formulas": snapshot_data["formulas"],
        "reports": report_rows,
        "eventLog": log[:24],
        "demoEvents": clone_demo_events(),
        "playedEvents": [],
    }


async def submit_report(muni: dict[str, Any], payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    zones = loads(muni["zones_json"], clone_zone_template())
    report = {
        "id": f"rpt-{int(datetime.now().timestamp())}",
        "zoneId": payload["zoneId"],
        "volume": payload["volume"],
        "submitterType": payload["submitterType"],
        "note": payload.get("note") or "",
        "timestamp": _now_iso(),
        "source": "citizen",
    }
    zones = apply_report(zones, report)
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO reports (municipality_id, user_id, zone_id, volume, submitter_type, note, source, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'citizen', ?)
        """,
        (
            muni["id"],
            user["id"],
            payload["zoneId"],
            payload["volume"],
            payload["submitterType"],
            payload.get("note") or "",
            report["timestamp"],
        ),
    )
    conn.commit()
    _save_muni(int(muni["id"]), zones_json=dumps(zones))
    zone_name = next(z["name"] for z in zones if z["id"] == payload["zoneId"])
    _log(
        int(muni["id"]),
        "report",
        f"{payload['volume'].title()} bloom · {zone_name}",
        report["note"] or f"Filed by {user['name']}.",
        payload["zoneId"],
    )
    fresh = get_municipality(int(muni["id"]))
    return await snapshot(fresh, highlight=True, user=user)


async def inspect_zone(muni: dict[str, Any], payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    zones = loads(muni["zones_json"], clone_zone_template())
    stamp = _now_iso()
    zones = apply_inspection(zones, payload["zoneId"], payload["observedVolume"], payload.get("note"), timestamp=stamp)
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO reports (municipality_id, user_id, zone_id, volume, submitter_type, note, source, created_at)
        VALUES (?, ?, ?, ?, 'municipal_scout', ?, 'inspection', ?)
        """,
        (
            muni["id"],
            user["id"],
            payload["zoneId"],
            payload["observedVolume"],
            payload.get("note") or "Scout inspection",
            stamp,
        ),
    )
    conn.commit()
    _save_muni(int(muni["id"]), zones_json=dumps(zones))
    zone_name = next(z["name"] for z in zones if z["id"] == payload["zoneId"])
    _log(
        int(muni["id"]),
        "inspection",
        f"Scout inspected {zone_name}",
        payload.get("note") or f"Logged by {user['name']}.",
        payload["zoneId"],
    )
    return await snapshot(get_municipality(int(muni["id"])), highlight=True, user=user)


async def update_settings(muni: dict[str, Any], fields: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    mapping = {
        "crewBudget": "crew_budget",
        "explorationC": "exploration_c",
        "forecastWeight": "forecast_weight",
        "horizon": "horizon",
        "lat": "lat",
        "lng": "lng",
        "region": "region",
    }
    payload = {}
    for key, column in mapping.items():
        if fields.get(key) is not None:
            payload[column] = fields[key]
    if payload:
        _save_muni(int(muni["id"]), **payload)
        _log(
            int(muni["id"]),
            "settings",
            "Planning parameters updated",
            "Operations updated shift settings.",
        )
    return await snapshot(get_municipality(int(muni["id"])), highlight=True, user=user)


async def update_zone_economics(muni: dict[str, Any], zone_id: str, fields: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    zones = loads(muni["zones_json"], clone_zone_template())
    found = False
    allowed = ("economicWeight", "hourlyRevenueAtRisk", "cleanupCostPerHour", "requiredCrewHours", "name", "blurb")
    for zone in zones:
        if zone["id"] != zone_id:
            continue
        found = True
        for key in allowed:
            if key in fields and fields[key] is not None:
                zone[key] = fields[key]
        break
    if not found:
        raise KeyError(zone_id)
    _save_muni(int(muni["id"]), zones_json=dumps(zones))
    _log(int(muni["id"]), "settings", "Zone estimates updated", f"{zone_id} operations estimates saved.")
    return await snapshot(get_municipality(int(muni["id"])), highlight=True, user=user)


SHIFT_SEED_REPORTS = [
    {
        "zoneId": "tourist-beach",
        "volume": "large",
        "submitterType": "hotel_staff",
        "note": "Mats at the hotel swim line this morning.",
    },
    {
        "zoneId": "harbor-entrance",
        "volume": "medium",
        "submitterType": "lifeguard",
        "note": "Windrows along the channel markers.",
    },
    {
        "zoneId": "fishing-dock",
        "volume": "medium",
        "submitterType": "fisher",
        "note": "Co-op ice house access is narrowing.",
    },
]


def ensure_demo_accounts() -> None:
    from app.auth import hash_password

    conn = get_conn()
    muni = create_municipality("Fajardo", "Puerto Rico")
    accounts = (
        ("ops@fajardo.test", "Fajardo Operations", "operations"),
        ("neighbor@fajardo.test", "Cove Neighbor", "citizen"),
    )
    for email, name, role in accounts:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        hashed = hash_password("password1")
        if existing:
            conn.execute("UPDATE users SET password_hash = ? WHERE email = ?", (hashed, email))
            continue
        conn.execute(
            """
            INSERT INTO users (email, name, password_hash, role, municipality_id, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            """,
            (email, name, hashed, role, muni["id"]),
        )
    conn.commit()


def _insert_report(muni_id: int, user_id: int | None, payload: dict[str, Any], source: str) -> None:
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO reports (municipality_id, user_id, zone_id, volume, submitter_type, note, source, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            muni_id,
            user_id,
            payload["zoneId"],
            payload.get("volume") or payload.get("observedVolume"),
            payload.get("submitterType") or "municipal_scout",
            payload.get("note") or "",
            source,
            _now_iso(),
        ),
    )
    conn.commit()


async def reset_desk(muni: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    muni_id = int(muni["id"])
    conn = get_conn()
    conn.execute("DELETE FROM reports WHERE municipality_id = ?", (muni_id,))
    conn.execute("DELETE FROM events WHERE municipality_id = ?", (muni_id,))
    conn.commit()
    _save_muni(
        muni_id,
        zones_json=dumps(clone_zone_template()),
        event_log_json=dumps(
            [
                {
                    "id": f"boot-{uuid.uuid4().hex[:8]}",
                    "kind": "system",
                    "title": "Desk reset",
                    "detail": "Zones cleared. File reports or load the 8-hour demo shift.",
                    "timestamp": _now_iso(),
                }
            ]
        ),
        previous_cleanup_json=dumps([]),
        previous_scout_json=dumps([]),
        crew_budget=8,
        exploration_c=0.72,
        forecast_weight=0.35,
        horizon="h24",
    )
    _log(muni_id, "system", "Desk reset", f"{user['name']} cleared today’s picture.")
    return await snapshot(get_municipality(muni_id), highlight=False, user=user)


async def seed_shift(muni: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    await reset_desk(muni, user)
    muni = get_municipality(int(muni["id"])) or muni
    zones = clone_zone_template()
    for payload in SHIFT_SEED_REPORTS:
        report = {**payload, "timestamp": _now_iso(), "source": "demo"}
        zones = apply_report(zones, report)
        _insert_report(int(muni["id"]), user["id"], payload, "demo")
        zone_name = next(z["name"] for z in zones if z["id"] == payload["zoneId"])
        _log(
            int(muni["id"]),
            "report",
            f"{payload['volume'].title()} bloom · {zone_name}",
            payload["note"],
            payload["zoneId"],
        )
    _save_muni(int(muni["id"]), zones_json=dumps(zones), crew_budget=8)
    _log(
        int(muni["id"]),
        "demo",
        "8-hour demo shift loaded",
        "Hotel beach, harbor, and dock reports are in. Budget is 8 hours — not every beach fits.",
    )
    return await snapshot(get_municipality(int(muni["id"])), highlight=True, user=user)


async def play_demo(muni: dict[str, Any], event_id: str, user: dict[str, Any]) -> dict[str, Any]:
    from app.data.demo_scenarios import DEMO_EVENTS

    event = next((item for item in DEMO_EVENTS if item["id"] == event_id), None)
    if event is None:
        raise KeyError(event_id)
    kind = event["kind"]
    payload = event["payload"]
    if kind == "report":
        result = await submit_report(get_municipality(int(muni["id"])) or muni, payload, user)
    elif kind == "inspection":
        result = await inspect_zone(get_municipality(int(muni["id"])) or muni, payload, user)
    elif kind == "forecast":
        muni = get_municipality(int(muni["id"])) or muni
        zones = loads(muni["zones_json"], clone_zone_template())
        found = False
        for zone in zones:
            if zone["id"] != payload["zoneId"]:
                continue
            found = True
            zone["forecastRisk"] = payload["forecastRisk"]
            break
        if not found:
            raise KeyError(payload["zoneId"])
        _save_muni(int(muni["id"]), zones_json=dumps(zones))
        _log(int(muni["id"]), "forecast", event["title"], payload.get("note") or event["narration"], payload["zoneId"])
        result = await snapshot(get_municipality(int(muni["id"])), highlight=True, user=user)
    else:
        raise KeyError(kind)
    result["lastDemoEvent"] = event
    return result


def shift_briefing_text(state: dict[str, Any]) -> str:
    community = (state.get("community") or {}).get("name") or "Town"
    cleanup = state.get("cleanupNow") or []
    scouts = state.get("scoutNext") or []
    unfunded = state.get("unfunded") or []
    metrics = state.get("metrics") or {}
    lines = [
        f"Sargassum Watch — {community} shift briefing",
        f"Generated {state.get('generatedAt')}",
        "",
        f"Crew hours: {metrics.get('crewBudget')}  ·  assigned {metrics.get('assignedHours')}  ·  leftover {metrics.get('remainingHours')}",
        f"Value on the truck list: ${int(metrics.get('valueProtected') or 0):,}",
        f"Left outside the shift: ${int(metrics.get('unresolvedExposure') or 0):,}",
        "",
        "Send the trucks",
    ]
    if cleanup:
        for zone in cleanup:
            lines.append(f"  - {zone['name']}  {zone['requiredCrewHours']}h  value ${int(zone['cleanupValue']):,}")
    else:
        lines.append("  - none yet — file reports or load the demo shift")
    lines += ["", "Go look first"]
    if scouts:
        for zone in scouts:
            lines.append(f"  - {zone['name']}  inspections {zone['inspectionCount']}  priority {zone['scoutPriority']:.2f}")
    else:
        lines.append("  - none")
    lines += ["", "Did not fit today’s hours"]
    if unfunded:
        for zone in unfunded:
            lines.append(f"  - {zone['name']}  needs {zone['requiredCrewHours']}h")
    else:
        lines.append("  - every scored beach fit")
    lines += [
        "",
        "Grok explains these lists. It does not pick the beaches.",
        "Weather: Open-Meteo. Dollars: this town’s estimates.",
    ]
    return "\n".join(lines)
