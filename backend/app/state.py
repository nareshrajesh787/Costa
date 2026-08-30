"""In-memory municipal operating picture. Resettable, no database."""

from __future__ import annotations

import threading
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any

from app.data.demo_scenarios import clone_demo_events
from app.data.seed_reports import clone_seed_reports
from app.data.zones import clone_initial_zones
from app.lib.algorithms import (
    apply_forecast_update,
    apply_inspection,
    apply_report,
    evaluate_state,
)
from app.lib.constants import DEFAULT_CREW_BUDGET, EXPLORATION_C, FORECAST_WEIGHT

AT = timezone(timedelta(hours=-4))


def _now_iso() -> str:
    return datetime.now(AT).isoformat(timespec="seconds")


def _stamp_seed(zones: list[dict[str, Any]], reports: list[dict[str, Any]]) -> None:
    by_id = {z["id"]: z for z in zones}
    for report in reversed(reports):
        zone = by_id.get(report["zoneId"])
        if zone is None:
            continue
        zone.setdefault("reports", [])
        zone["reports"].insert(0, report)


class OperatingPicture:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.zones: list[dict[str, Any]] = []
        self.reports: list[dict[str, Any]] = []
        self.crew_budget = DEFAULT_CREW_BUDGET
        self.exploration_c = EXPLORATION_C
        self.forecast_weight = FORECAST_WEIGHT
        self.horizon = "h24"
        self.event_log: list[dict[str, Any]] = []
        self.played_events: list[str] = []
        self.report_seq = 0
        self.log_seq = 0
        self.previous_cleanup_ids: list[str] = []
        self.previous_scout_ids: list[str] = []
        self.reset()

    def reset(self) -> dict[str, Any]:
        with self._lock:
            self.zones = clone_initial_zones()
            for zone in self.zones:
                zone["reports"] = []
            self.reports = clone_seed_reports()
            _stamp_seed(self.zones, self.reports)
            self.crew_budget = DEFAULT_CREW_BUDGET
            self.exploration_c = EXPLORATION_C
            self.forecast_weight = FORECAST_WEIGHT
            self.horizon = "h24"
            self.event_log = [
                {
                    "id": "boot",
                    "kind": "system",
                    "title": "Shift briefing loaded",
                    "detail": "Seeded reports and simulated drift vectors initialized for Punta Marisol.",
                    "timestamp": _now_iso(),
                }
            ]
            self.played_events = []
            self.report_seq = len(self.reports)
            self.log_seq = 0
            snapshot = evaluate_state(
                self.zones,
                crew_budget=self.crew_budget,
                exploration_c=self.exploration_c,
                forecast_weight=self.forecast_weight,
                horizon=self.horizon,
            )
            self.previous_cleanup_ids = list(snapshot["selection"]["ids"])
            self.previous_scout_ids = [z["id"] for z in snapshot["scoutNext"]]
            return self._pack(snapshot, highlight=False)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return self._evaluate_unlocked(highlight=False)

    def update_settings(self, **kwargs: Any) -> dict[str, Any]:
        with self._lock:
            if kwargs.get("crewBudget") is not None:
                self.crew_budget = int(kwargs["crewBudget"])
            if kwargs.get("explorationC") is not None:
                self.exploration_c = float(kwargs["explorationC"])
            if kwargs.get("forecastWeight") is not None:
                self.forecast_weight = float(kwargs["forecastWeight"])
            if kwargs.get("horizon") is not None:
                self.horizon = str(kwargs["horizon"])
            self.event_log.insert(
                0,
                {
                    "id": f"settings-{self._next_log()}",
                    "kind": "settings",
                    "title": "Planning parameters updated",
                    "detail": f"Budget {self.crew_budget}h · horizon {self.horizon} · c={self.exploration_c:.2f}",
                    "timestamp": _now_iso(),
                },
            )
            return self._evaluate_unlocked(highlight=True)

    def submit_report(self, payload: dict[str, Any], *, source: str = "citizen") -> dict[str, Any]:
        with self._lock:
            self.report_seq += 1
            report = {
                "id": f"rpt-{self.report_seq:04d}",
                "zoneId": payload["zoneId"],
                "volume": payload["volume"],
                "submitterType": payload["submitterType"],
                "note": payload.get("note") or "",
                "timestamp": _now_iso(),
                "source": source,
            }
            self.zones = apply_report(self.zones, report)
            self.reports.insert(0, report)
            zone_name = next(z["name"] for z in self.zones if z["id"] == report["zoneId"])
            self.event_log.insert(
                0,
                {
                    "id": report["id"],
                    "kind": "report",
                    "title": f"{payload['volume'].title()} bloom · {zone_name}",
                    "detail": report["note"] or "Field report ingested. Severity EMA updated.",
                    "timestamp": report["timestamp"],
                    "zoneId": report["zoneId"],
                },
            )
            return self._evaluate_unlocked(highlight=True)

    def inspect_zone(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self.report_seq += 1
            stamp = _now_iso()
            self.zones = apply_inspection(
                self.zones,
                payload["zoneId"],
                payload["observedVolume"],
                payload.get("note"),
                timestamp=stamp,
            )
            zone_name = next(z["name"] for z in self.zones if z["id"] == payload["zoneId"])
            self.event_log.insert(
                0,
                {
                    "id": f"insp-{self.report_seq:04d}",
                    "kind": "inspection",
                    "title": f"Scout inspected {zone_name}",
                    "detail": payload.get("note") or "Inspection count increased; uncertainty bonus recalculated.",
                    "timestamp": stamp,
                    "zoneId": payload["zoneId"],
                },
            )
            return self._evaluate_unlocked(highlight=True)

    def play_event(self, event_id: str) -> dict[str, Any]:
        events = {e["id"]: e for e in clone_demo_events()}
        if event_id not in events:
            raise KeyError(event_id)
        event = events[event_id]
        kind = event["kind"]
        payload = event["payload"]
        if kind == "report":
            result = self.submit_report(payload, source="demo")
        elif kind == "inspection":
            result = self.inspect_zone(payload)
        elif kind == "forecast":
            result = self._apply_forecast(event)
        else:
            raise ValueError(f"Unknown demo event kind {kind}")
        with self._lock:
            if event_id not in self.played_events:
                self.played_events.append(event_id)
            result["lastDemoEvent"] = event
            result["playedEvents"] = list(self.played_events)
            return result

    def _apply_forecast(self, event: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            payload = event["payload"]
            self.zones = apply_forecast_update(self.zones, payload["zoneId"], payload["forecastRisk"])
            zone_name = next(z["name"] for z in self.zones if z["id"] == payload["zoneId"])
            self.event_log.insert(
                0,
                {
                    "id": f"forecast-{self._next_log()}",
                    "kind": "forecast",
                    "title": f"Drift scenario updated · {zone_name}",
                    "detail": payload.get("note") or event["narration"],
                    "timestamp": _now_iso(),
                    "zoneId": payload["zoneId"],
                },
            )
            return self._evaluate_unlocked(highlight=True)

    def _evaluate_unlocked(self, *, highlight: bool) -> dict[str, Any]:
        snapshot = evaluate_state(
            self.zones,
            crew_budget=self.crew_budget,
            exploration_c=self.exploration_c,
            forecast_weight=self.forecast_weight,
            horizon=self.horizon,
            previous_cleanup_ids=self.previous_cleanup_ids if highlight else None,
            previous_scout_ids=self.previous_scout_ids if highlight else None,
        )
        packed = self._pack(snapshot, highlight=highlight)
        self.previous_cleanup_ids = list(snapshot["selection"]["ids"])
        self.previous_scout_ids = [z["id"] for z in snapshot["scoutNext"]]
        return packed

    def _next_log(self) -> int:
        self.log_seq += 1
        return self.log_seq

    def _pack(self, snapshot: dict[str, Any], *, highlight: bool) -> dict[str, Any]:
        return {
            "community": {
                "name": "Punta Marisol",
                "region": "Isolated Caribbean coastal municipality",
                "shift": "Sunday operations window",
                "disclaimer": "Simulated planning data. Economic figures, reports, and drift vectors are demo inputs — not measured Punta Marisol conditions.",
            },
            "settings": {
                "crewBudget": self.crew_budget,
                "explorationC": self.exploration_c,
                "forecastWeight": self.forecast_weight,
                "horizon": self.horizon,
            },
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "highlight": highlight,
            "changes": snapshot["changes"] if highlight else [],
            "zones": snapshot["zones"],
            "cleanupNow": snapshot["cleanupNow"],
            "unfunded": snapshot["unfunded"],
            "scoutNext": snapshot["scoutNext"],
            "scoutRanked": snapshot["scoutRanked"],
            "containment": snapshot["containment"],
            "metrics": snapshot["metrics"],
            "selection": snapshot["selection"],
            "formulas": snapshot["formulas"],
            "reports": deepcopy(self.reports[:20]),
            "eventLog": deepcopy(self.event_log[:24]),
            "demoEvents": clone_demo_events(),
            "playedEvents": list(self.played_events),
        }


picture = OperatingPicture()
