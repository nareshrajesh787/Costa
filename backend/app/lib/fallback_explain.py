"""Local, deterministic explanation templates. No model, no network."""

from __future__ import annotations

from typing import Any


def money(value: float) -> str:
    return f"${value:,.0f}"


def fallback_explanation(state: dict[str, Any]) -> dict[str, Any]:
    cleanup = state.get("cleanupNow") or []
    scouts = state.get("scoutNext") or []
    unfunded = state.get("unfunded") or []
    metrics = state.get("metrics") or {}
    changes = state.get("changes") or []
    settings = state.get("settings") or {}
    containment = state.get("containment") or []

    names = [z["name"] for z in cleanup]
    if names:
        summary = (
            f"With a {metrics.get('crewBudget', 0)}-hour crew budget, dispatch cleanup to "
            f"{_join(names)} to protect about {money(metrics.get('valueProtected', 0))} in "
            f"estimated shift exposure. Remaining capacity is {metrics.get('remainingHours', 0)} hours."
        )
    else:
        summary = "No cleanup assignment fits the current crew-hour budget."

    cleanup_rationale = []
    for zone in cleanup:
        cleanup_rationale.append(
            f"{zone['name']} is assigned because its cleanup value of {money(zone['cleanupValue'])} "
            f"({money(zone['impactPerCrewHour'])}/crew-hour) uses {zone['requiredCrewHours']} hours "
            f"at severity {zone['meanSeverity']:.2f}."
        )
    if not cleanup_rationale:
        cleanup_rationale.append("No zone cleared the knapsack constraint at this budget.")

    scout_rationale = []
    for zone in scouts:
        scout_rationale.append(
            f"{zone['name']} ranks for scouting with priority {zone['scoutPriority']:.2f}: "
            f"exploit {zone['exploitScore']:.2f} plus uncertainty bonus {zone['uncertaintyBonus']:.2f} "
            f"from {zone['inspectionCount']} inspection(s)."
        )
    if not scout_rationale:
        scout_rationale.append("No scout ranking is available.")

    tradeoffs = []
    if unfunded:
        top = unfunded[0]
        tradeoffs.append(
            f"{top['name']} is unfunded despite {money(top['cleanupValue'])} in cleanup value — "
            f"assigning its {top['requiredCrewHours']} hours would displace a higher-value set."
        )
    if changes:
        added = [c["name"] for c in changes if c["kind"] == "cleanup_added"]
        removed = [c["name"] for c in changes if c["kind"] == "cleanup_removed"]
        if added or removed:
            tradeoffs.append(
                "This update "
                + ("adds " + _join(added) if added else "adds no new cleanup zone")
                + (" and releases " + _join(removed) if removed else "")
                + " after the latest observation."
            )
    if containment:
        tradeoffs.append(
            f"Containment watch: {_join(z['name'] for z in containment)} shows elevated 12-hour "
            "scenario landfall risk. Boom staging is a forecast overlay, not a knapsack output."
        )
    if not tradeoffs:
        tradeoffs.append(
            f"Unresolved exposure is {money(metrics.get('unresolvedExposure', 0))} because "
            f"{metrics.get('unfundedHours', 0)} hours of work sit outside the shift budget."
        )

    caveat = (
        "Rankings come from the deterministic engine on live citizen reports and Open-Meteo marine weather. "
        "This text only restates those numbers. Dollar weights are municipality operations estimates. "
        f"Horizon {settings.get('horizon', 'h24')}. Method: exact 0/1 knapsack + UCB-inspired scout scores."
    )

    return {
        "summary": _clip(summary, 70),
        "cleanupRationale": cleanup_rationale[:4],
        "scoutingRationale": scout_rationale[:3],
        "tradeoffs": tradeoffs[:3],
        "caveat": caveat,
        "source": "local-fallback",
    }


def _join(parts) -> str:
    items = list(parts)
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def _clip(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]).rstrip(".,;") + "."
