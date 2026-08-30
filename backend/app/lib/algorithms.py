"""Deterministic decision engine for Sargassum Watch.

Every function is pure: same inputs always produce the same outputs.
Rankings and assignments are computed here. Language models never call
these functions and never invent dollar values or ranks.

Formulas
--------
EMA severity:
    severity' = α · observed + (1 − α) · severity

Immediate economic exposure ($ / hour):
    exposure = severity · economicWeight · hourlyRevenueAtRisk

UCB-inspired scout priority:
    exploit = severity · (economicWeight / MAX_ECONOMIC_WEIGHT)
    uncertainty = c · √( ln(T + 1) / max(1, inspections) )
    scoutPriority = exploit + uncertainty

    T is the sum of inspection counts across all zones. A citizen report
    is treated as an observation (inspectionCount += 1). Scout inspections
    are the same signal. This is an uncertainty-aware triage score, not
    classical UCB1 with repeated arm-pull rewards.

Cleanup value ($ equivalent for this shift):
    cleanupValue = exposure + forecastWeight · forecastRisk[horizon] · hourlyRevenueAtRisk

Crew-hour cost:
    costHours = requiredCrewHours          (integer, zone catalog)
    operatingCost = costHours · cleanupCostPerHour

Allocation:
    Exact 0/1 knapsack via DP over integer crew-hours. Selects the
    feasible set of zones that maximizes total cleanup value without
    exceeding the crew-hour budget.
"""

from __future__ import annotations

import math
from copy import deepcopy
from typing import Any

from app.lib.constants import (
    CONTAINMENT_THRESHOLD,
    DEFAULT_CREW_BUDGET,
    EMA_ALPHA,
    EXPLORATION_C,
    FORECAST_WEIGHT,
    MAX_ECONOMIC_WEIGHT,
    VOLUME_SEVERITY,
)

Horizon = str


def volume_to_severity(volume: str) -> float:
    if volume not in VOLUME_SEVERITY:
        raise ValueError(f"Unknown volume '{volume}'. Expected small|medium|large.")
    return VOLUME_SEVERITY[volume]


def update_severity_ema(current: float, observed: float, alpha: float = EMA_ALPHA) -> float:
    """Exponential moving average of zone severity in [0, 1]."""
    if not 0 <= current <= 1:
        raise ValueError("current severity must be in [0, 1]")
    if not 0 <= observed <= 1:
        raise ValueError("observed severity must be in [0, 1]")
    if not 0 < alpha <= 1:
        raise ValueError("alpha must be in (0, 1]")
    updated = alpha * observed + (1.0 - alpha) * current
    return max(0.0, min(1.0, updated))


def immediate_exposure(zone: dict[str, Any]) -> float:
    return zone["meanSeverity"] * zone["economicWeight"] * zone["hourlyRevenueAtRisk"]


def uncertainty_bonus(
    inspection_count: int,
    total_inspections: int,
    exploration_c: float = EXPLORATION_C,
) -> float:
    """UCB-style exploration term. Higher when a zone is under-inspected."""
    t = total_inspections + 1
    n = inspection_count + 1
    return exploration_c * math.sqrt(math.log(t + 1) / n)


def scout_priority(
    zone: dict[str, Any],
    total_inspections: int,
    exploration_c: float = EXPLORATION_C,
) -> tuple[float, float, float]:
    exploit = zone["meanSeverity"] * (zone["economicWeight"] / MAX_ECONOMIC_WEIGHT)
    bonus = uncertainty_bonus(zone["inspectionCount"], total_inspections, exploration_c)
    return exploit + bonus, exploit, bonus


def cleanup_value(
    zone: dict[str, Any],
    forecast_weight: float = FORECAST_WEIGHT,
    horizon: Horizon = "h24",
) -> float:
    exposure = immediate_exposure(zone)
    risk = zone["forecastRisk"][horizon]
    forecast_component = forecast_weight * risk * zone["hourlyRevenueAtRisk"]
    return exposure + forecast_component


def crew_operating_cost(zone: dict[str, Any]) -> float:
    return zone["requiredCrewHours"] * zone["cleanupCostPerHour"]


def impact_per_crew_hour(zone: dict[str, Any], value: float) -> float:
    hours = max(1, zone["requiredCrewHours"])
    return value / hours


def total_inspections(zones: list[dict[str, Any]]) -> int:
    return sum(int(z["inspectionCount"]) for z in zones)


def knapsack_select(
    items: list[dict[str, Any]],
    budget: int,
) -> tuple[list[str], float, int]:
    """Exact 0/1 knapsack via DP.

    items: dicts with id, value (float), hours (positive int)
    Returns (selected_ids in stable catalog order, total_value, hours_used)

    Tie-break: highest value, then fewer hours used, then lexicographic id set.
    """
    if budget < 0:
        raise ValueError("budget must be >= 0")
    if budget == 0 or not items:
        return [], 0.0, 0

    n = len(items)
    hours_list = []
    value_list = []
    for item in items:
        hours = int(item["hours"])
        if hours <= 0:
            raise ValueError(f"item {item.get('id')} has non-positive hours")
        hours_list.append(hours)
        value_list.append(float(item["value"]))

    # dp[i][w] = max value using the first i items with capacity w
    dp = [[0.0] * (budget + 1) for _ in range(n + 1)]
    take = [[False] * (budget + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        hours = hours_list[i - 1]
        value = value_list[i - 1]
        for w in range(budget + 1):
            dp[i][w] = dp[i - 1][w]
            take[i][w] = False
            if hours <= w:
                candidate = dp[i - 1][w - hours] + value
                skip = dp[i][w]
                if candidate > skip + 1e-12:
                    dp[i][w] = candidate
                    take[i][w] = True
                elif abs(candidate - skip) <= 1e-12:
                    # Tie on value: prefer the set that uses fewer hours after reconstruction,
                    # approximated by taking the item when remaining capacity is tighter.
                    pass

    best_w = max(range(budget + 1), key=lambda w: (dp[n][w], -w))
    selected_idx: list[int] = []
    w = best_w
    for i in range(n, 0, -1):
        if take[i][w]:
            selected_idx.append(i - 1)
            w -= hours_list[i - 1]

    selected_idx.sort()
    selected_ids = [items[i]["id"] for i in selected_idx]
    hours_used = sum(hours_list[i] for i in selected_idx)
    total_value = sum(value_list[i] for i in selected_idx)
    return selected_ids, total_value, hours_used


def _drift_offset(vector: dict[str, float], hours: float) -> dict[str, float]:
    rad = math.radians(vector["direction"])
    scale = 0.55
    return {
        "dx": vector["speed"] * hours * math.cos(rad) * scale,
        "dy": -vector["speed"] * hours * math.sin(rad) * scale,
    }


def projected_position(zone: dict[str, Any], hours: float) -> dict[str, float]:
    offset = _drift_offset(zone["currentVector"], hours)
    x = max(6.0, min(94.0, zone["position"]["x"] + offset["dx"]))
    y = max(8.0, min(88.0, zone["position"]["y"] + offset["dy"]))
    return {"x": round(x, 2), "y": round(y, 2)}


def score_zone(
    zone: dict[str, Any],
    *,
    total_insp: int,
    exploration_c: float,
    forecast_weight: float,
    horizon: Horizon,
) -> dict[str, Any]:
    exposure = immediate_exposure(zone)
    value = cleanup_value(zone, forecast_weight, horizon)
    priority, exploit, bonus = scout_priority(zone, total_insp, exploration_c)
    hours = int(zone["requiredCrewHours"])
    operating = crew_operating_cost(zone)
    density = impact_per_crew_hour(zone, value)
    risk = zone["forecastRisk"][horizon]
    return {
        "id": zone["id"],
        "name": zone["name"],
        "shortName": zone["shortName"],
        "kind": zone["kind"],
        "blurb": zone["blurb"],
        "accessNotes": zone["accessNotes"],
        "economicWeight": zone["economicWeight"],
        "hourlyRevenueAtRisk": zone["hourlyRevenueAtRisk"],
        "cleanupCostPerHour": zone["cleanupCostPerHour"],
        "requiredCrewHours": hours,
        "meanSeverity": zone["meanSeverity"],
        "inspectionCount": zone["inspectionCount"],
        "position": zone["position"],
        "currentVector": zone["currentVector"],
        "forecastRisk": zone["forecastRisk"],
        "forecastSource": zone.get("forecastSource", "live"),
        "reports": zone.get("reports", []),
        "immediateExposure": round(exposure, 2),
        "cleanupValue": round(value, 2),
        "forecastComponent": round(forecast_weight * risk * zone["hourlyRevenueAtRisk"], 2),
        "scoutPriority": round(priority, 4),
        "exploitScore": round(exploit, 4),
        "uncertaintyBonus": round(bonus, 4),
        "impactPerCrewHour": round(density, 2),
        "operatingCost": round(operating, 2),
        "forecastHorizonRisk": round(risk, 4),
        "projected": {
            "h12": projected_position(zone, 12),
            "h24": projected_position(zone, 24),
            "h48": projected_position(zone, 48),
        },
        "breakdown": {
            "severity": round(zone["meanSeverity"], 4),
            "economicWeight": zone["economicWeight"],
            "hourlyRevenueAtRisk": zone["hourlyRevenueAtRisk"],
            "immediateExposure": round(exposure, 2),
            "forecastWeight": forecast_weight,
            "forecastHorizon": horizon,
            "forecastRisk": round(risk, 4),
            "forecastComponent": round(forecast_weight * risk * zone["hourlyRevenueAtRisk"], 2),
            "cleanupValue": round(value, 2),
            "requiredCrewHours": hours,
            "impactPerCrewHour": round(density, 2),
            "operatingCost": round(operating, 2),
            "exploitScore": round(exploit, 4),
            "uncertaintyBonus": round(bonus, 4),
            "scoutPriority": round(priority, 4),
            "inspectionCount": zone["inspectionCount"],
            "totalInspections": total_insp,
            "explorationC": exploration_c,
        },
    }


def evaluate_state(
    zones: list[dict[str, Any]],
    *,
    crew_budget: int = DEFAULT_CREW_BUDGET,
    exploration_c: float = EXPLORATION_C,
    forecast_weight: float = FORECAST_WEIGHT,
    horizon: Horizon = "h24",
    previous_cleanup_ids: list[str] | None = None,
    previous_scout_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Score every zone, run exact knapsack, and produce scout / containment lists."""
    working = deepcopy(zones)
    total_insp = total_inspections(working)
    scored = [
        score_zone(
            z,
            total_insp=total_insp,
            exploration_c=exploration_c,
            forecast_weight=forecast_weight,
            horizon=horizon,
        )
        for z in working
    ]
    by_id = {z["id"]: z for z in scored}

    knapsack_items = [
        {"id": z["id"], "value": z["cleanupValue"], "hours": z["requiredCrewHours"]}
        for z in scored
    ]
    selected_ids, protected_value, hours_used = knapsack_select(knapsack_items, crew_budget)
    selected_set = set(selected_ids)

    cleanup_ranked = sorted(scored, key=lambda z: z["cleanupValue"], reverse=True)
    scout_ranked = sorted(scored, key=lambda z: z["scoutPriority"], reverse=True)

    cleanup_now = []
    for zone_id in selected_ids:
        z = by_id[zone_id]
        cleanup_now.append(
            {
                **z,
                "assigned": True,
                "role": "cleanup",
            }
        )
    cleanup_now.sort(key=lambda z: z["cleanupValue"], reverse=True)

    unfunded = [z for z in cleanup_ranked if z["id"] not in selected_set]
    unresolved_exposure = round(sum(z["cleanupValue"] for z in unfunded), 2)
    unfunded_hours = sum(z["requiredCrewHours"] for z in unfunded)

    scout_next = []
    for z in scout_ranked:
        scout_next.append(
            {
                **z,
                "assigned": z["id"] in selected_set,
                "role": "scout",
            }
        )

    containment = []
    for z in scored:
        if z["forecastRisk"]["h12"] >= CONTAINMENT_THRESHOLD or (
            horizon == "h12" and z["forecastHorizonRisk"] >= CONTAINMENT_THRESHOLD
        ):
            containment.append(
                {
                    **z,
                    "assigned": z["id"] in selected_set,
                    "role": "containment",
                    "reason": (
                        "Loaded drift scenario projects elevated landfall risk within 12 hours."
                        if z.get("forecastSource") == "scenario"
                        else "Live wind and current project elevated landfall risk within 12 hours."
                    ),
                }
            )
    containment.sort(key=lambda z: z["forecastRisk"]["h12"], reverse=True)

    operating_cost = round(sum(by_id[i]["operatingCost"] for i in selected_ids), 2)
    remaining_hours = crew_budget - hours_used
    total_exposure = round(sum(z["immediateExposure"] for z in scored), 2)

    prev_cleanup = set(previous_cleanup_ids or [])
    prev_scout_top = list(previous_scout_ids or [])
    changed = []
    for z in scored:
        now_in = z["id"] in selected_set
        was_in = z["id"] in prev_cleanup
        if previous_cleanup_ids is not None and now_in != was_in:
            changed.append(
                {
                    "zoneId": z["id"],
                    "name": z["name"],
                    "kind": "cleanup_added" if now_in else "cleanup_removed",
                }
            )
    if previous_scout_ids:
        new_top = [z["id"] for z in scout_ranked[:3]]
        if new_top != prev_scout_top[:3]:
            changed.append({"zoneId": new_top[0], "name": by_id[new_top[0]]["name"], "kind": "scout_shift"})

    for z in scored:
        z["assignedCleanup"] = z["id"] in selected_set
        z["cleanupRank"] = next(i for i, row in enumerate(cleanup_ranked, start=1) if row["id"] == z["id"])
        z["scoutRank"] = next(i for i, row in enumerate(scout_ranked, start=1) if row["id"] == z["id"])

    return {
        "zones": scored,
        "cleanupNow": cleanup_now,
        "unfunded": unfunded,
        "scoutNext": scout_next[:3],
        "scoutRanked": scout_next,
        "containment": containment,
        "metrics": {
            "crewBudget": crew_budget,
            "assignedHours": hours_used,
            "remainingHours": remaining_hours,
            "valueProtected": round(protected_value, 2),
            "unresolvedExposure": unresolved_exposure,
            "unfundedHours": unfunded_hours,
            "operatingCost": operating_cost,
            "totalImmediateExposure": total_exposure,
            "totalInspections": total_insp,
            "zoneCount": len(scored),
            "selectedCount": len(selected_ids),
            # Stated because these figures are NOT subtractable. valueProtected and
            # unresolvedExposure are hourly exposure rates ($/h, from
            # hourlyRevenueAtRisk); operatingCost is a whole-shift dollar total
            # (crew-hours x cleanupCostPerHour). An earlier "netProtected" field
            # subtracted the two and produced a meaningless number.
            "units": {
                "valueProtected": "USD per hour of exposure",
                "unresolvedExposure": "USD per hour of exposure",
                "totalImmediateExposure": "USD per hour of exposure",
                "operatingCost": "USD for the whole shift",
            },
        },
        "selection": {
            "ids": selected_ids,
            "method": "exact-0-1-knapsack-dp",
            "horizon": horizon,
            "forecastWeight": forecast_weight,
            "explorationC": exploration_c,
        },
        "changes": changed,
        "formulas": {
            "ema": "severity' = α · observed + (1 − α) · severity",
            "exposure": "severity × economicWeight × hourlyRevenueAtRisk",
            "scout": "Priority = (severity × economicWeight / 3) + c √(ln(T+1) / max(1, inspections))",
            "cleanup": "value = exposure + forecastWeight × forecastRisk × hourlyRevenueAtRisk",
            "allocation": "exact 0/1 knapsack over integer crew-hours",
        },
    }


def apply_report(zones: list[dict[str, Any]], report: dict[str, Any]) -> list[dict[str, Any]]:
    """Apply a citizen/scout report: EMA severity update + inspection increment."""
    updated = deepcopy(zones)
    zone_id = report["zoneId"]
    observed = volume_to_severity(report["volume"])
    found = False
    for zone in updated:
        if zone["id"] != zone_id:
            continue
        found = True
        zone["meanSeverity"] = update_severity_ema(zone["meanSeverity"], observed)
        zone["inspectionCount"] = int(zone["inspectionCount"]) + 1
        zone.setdefault("reports", [])
        zone["reports"] = [report, *zone["reports"]][:12]
        break
    if not found:
        raise KeyError(f"Unknown zone '{zone_id}'")
    return updated


def apply_inspection(
    zones: list[dict[str, Any]],
    zone_id: str,
    observed_volume: str,
    note: str | None = None,
    timestamp: str | None = None,
) -> list[dict[str, Any]]:
    report = {
        "id": f"insp-{zone_id}-{timestamp or 'live'}",
        "zoneId": zone_id,
        "volume": observed_volume,
        "submitterType": "municipal_scout",
        "note": note or "Scout inspection logged.",
        "timestamp": timestamp,
        "source": "inspection",
    }
    return apply_report(zones, report)


def apply_forecast_update(
    zones: list[dict[str, Any]],
    zone_id: str,
    forecast_risk: dict[str, float],
) -> list[dict[str, Any]]:
    updated = deepcopy(zones)
    found = False
    for zone in updated:
        if zone["id"] != zone_id:
            continue
        found = True
        risk = {
            "h12": float(forecast_risk["h12"]),
            "h24": float(forecast_risk["h24"]),
            "h48": float(forecast_risk["h48"]),
        }
        zone["forecastRisk"] = risk
        # Persisted so a later live-weather refresh does not silently discard it.
        zone["forecastOverride"] = risk
        zone["forecastSource"] = "scenario"
        break
    if not found:
        raise KeyError(f"Unknown zone '{zone_id}'")
    return updated
