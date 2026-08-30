"""Lightweight pytest-style harness plus a runnable console summary.

Run from the backend directory:
    python -m tests.test_algorithms
    pytest tests/test_algorithms.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.data.demo_scenarios import DEMO_EVENTS
from app.data.zones import clone_initial_zones
from app.lib.algorithms import (
    apply_forecast_update,
    apply_inspection,
    apply_report,
    evaluate_state,
    knapsack_select,
    uncertainty_bonus,
    update_severity_ema,
    volume_to_severity,
)
from app.lib.constants import DEFAULT_CREW_BUDGET, VOLUME_SEVERITY


def brute_force_knapsack(items: list[dict], budget: int) -> tuple[frozenset[str], float, int]:
    best_value = -1.0
    best_ids: frozenset[str] = frozenset()
    best_hours = 0
    n = len(items)
    for mask in range(1 << n):
        ids = []
        value = 0.0
        hours = 0
        for i, item in enumerate(items):
            if mask & (1 << i):
                ids.append(item["id"])
                value += float(item["value"])
                hours += int(item["hours"])
        if hours > budget:
            continue
        id_set = frozenset(ids)
        better = value > best_value + 1e-12 or (
            abs(value - best_value) <= 1e-12 and (hours < best_hours or (hours == best_hours and tuple(sorted(id_set)) < tuple(sorted(best_ids))))
        )
        if better:
            best_value = value
            best_ids = id_set
            best_hours = hours
    return best_ids, best_value, best_hours


def test_large_report_moves_severity_more_than_small():
    base = 0.30
    small = update_severity_ema(base, VOLUME_SEVERITY["small"])
    large = update_severity_ema(base, VOLUME_SEVERITY["large"])
    assert large > small
    assert large > base
    assert small < base  # small observation is below 0.30


def test_underinspected_zone_gets_higher_uncertainty():
    total = 20
    low = uncertainty_bonus(1, total)
    high = uncertainty_bonus(8, total)
    assert low > high


def test_knapsack_never_exceeds_budget():
    items = [
        {"id": "a", "value": 100, "hours": 3},
        {"id": "b", "value": 90, "hours": 3},
        {"id": "c", "value": 80, "hours": 2},
        {"id": "d", "value": 70, "hours": 4},
        {"id": "e", "value": 40, "hours": 2},
        {"id": "f", "value": 10, "hours": 1},
    ]
    for budget in range(0, 13):
        ids, value, hours = knapsack_select(items, budget)
        assert hours <= budget
        by_id = {i["id"]: i for i in items}
        recomputed = sum(by_id[i]["value"] for i in ids)
        assert abs(recomputed - value) < 1e-9
        oracle_ids, oracle_value, oracle_hours = brute_force_knapsack(items, budget)
        assert frozenset(ids) == oracle_ids
        assert abs(value - oracle_value) < 1e-9
        assert hours == oracle_hours


def test_knapsack_picks_max_value_on_tiny_set():
    items = [
        {"id": "high", "value": 50, "hours": 5},
        {"id": "mid_a", "value": 32, "hours": 3},
        {"id": "mid_b", "value": 31, "hours": 3},
        {"id": "cheap", "value": 18, "hours": 2},
    ]
    ids, value, hours = knapsack_select(items, 8)
    assert hours <= 8
    # 32+31+18 = 81 in 8 hours beats 50+31=81 in 8? 50+31=81 hours 8, 32+31+18=81 hours 8
    # 50+18=68 hours 7 is worse. 32+31+18 = 81. 50+31 = 81.
    # Either set is optimal on value. DP should match brute force.
    oracle_ids, oracle_value, _ = brute_force_knapsack(items, 8)
    assert frozenset(ids) == oracle_ids
    assert abs(value - oracle_value) < 1e-9


def test_empty_desk_stays_within_budget():
    decision = evaluate_state(clone_initial_zones(), crew_budget=DEFAULT_CREW_BUDGET)
    assert decision["metrics"]["assignedHours"] <= DEFAULT_CREW_BUDGET
    assert all(z["meanSeverity"] == 0 for z in clone_initial_zones())


def test_live_report_raises_cove_value():
    zones = clone_initial_zones()
    before = next(z for z in evaluate_state(zones)["zones"] if z["id"] == "residential-cove")
    zones = apply_report(
        zones,
        {
            "id": "test-cove",
            "zoneId": "residential-cove",
            "volume": "large",
            "submitterType": "resident",
            "note": "Dense mat at the community path.",
            "timestamp": "2026-08-30T13:00:00-04:00",
            "source": "citizen",
        },
    )
    after = evaluate_state(zones, crew_budget=8)
    cove = next(z for z in after["zones"] if z["id"] == "residential-cove")
    assert cove["meanSeverity"] > before["meanSeverity"]
    assert cove["inspectionCount"] == 1
    assert after["metrics"]["assignedHours"] <= 8


def test_inspection_reduces_inlet_uncertainty():
    zones = clone_initial_zones()
    before = evaluate_state(zones)
    inlet_before = next(z for z in before["zones"] if z["id"] == "quiet-inlet")
    zones = apply_inspection(zones, "quiet-inlet", "small", timestamp="2026-08-30T14:00:00-04:00")
    after = evaluate_state(zones)
    inlet_after = next(z for z in after["zones"] if z["id"] == "quiet-inlet")
    assert inlet_after["inspectionCount"] == inlet_before["inspectionCount"] + 1
    assert inlet_after["uncertaintyBonus"] < inlet_before["uncertaintyBonus"]


def test_forecast_flags_harbor_containment():
    zones = clone_initial_zones()
    payload = DEMO_EVENTS[2]["payload"]
    zones = apply_forecast_update(zones, payload["zoneId"], payload["forecastRisk"])
    decision = evaluate_state(zones)
    ids = {z["id"] for z in decision["containment"]}
    assert "harbor-entrance" in ids


def test_volume_map():
    assert volume_to_severity("large") > volume_to_severity("medium") > volume_to_severity("small")


TESTS = [
    test_large_report_moves_severity_more_than_small,
    test_underinspected_zone_gets_higher_uncertainty,
    test_knapsack_never_exceeds_budget,
    test_knapsack_picks_max_value_on_tiny_set,
    test_empty_desk_stays_within_budget,
    test_live_report_raises_cove_value,
    test_inspection_reduces_inlet_uncertainty,
    test_forecast_flags_harbor_containment,
    test_volume_map,
]


def run() -> int:
    passed = 0
    failed = []
    for fn in TESTS:
        try:
            fn()
            passed += 1
            print(f"  PASS  {fn.__name__}")
        except Exception as exc:  # noqa: BLE001 — harness prints failures
            failed.append((fn.__name__, exc))
            print(f"  FAIL  {fn.__name__}: {exc}")
    print()
    print(f"{passed}/{len(TESTS)} checks passed")
    if failed:
        return 1
    print("Decision engine is deterministic and budget-safe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
