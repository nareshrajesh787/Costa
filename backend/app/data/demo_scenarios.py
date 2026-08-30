"""Scripted demo events that force visible reallocation under an 8-hour budget."""

from copy import deepcopy

DEMO_EVENTS = [
    {
        "id": "cove-surge",
        "title": "Residential Cove surge",
        "narration": "A citizen report enters from Residential Cove. Severity rises, exposure is recalculated, and the optimizer re-solves the 8-hour shift.",
        "kind": "report",
        "payload": {
            "zoneId": "residential-cove",
            "volume": "large",
            "submitterType": "resident",
            "note": "Dense mat approaching shore near community access path.",
        },
    },
    {
        "id": "inlet-scout",
        "title": "Quiet Inlet inspection",
        "narration": "A scout inspects Quiet Inlet. The uncertainty bonus falls because the zone is no longer under-observed.",
        "kind": "inspection",
        "payload": {
            "zoneId": "quiet-inlet",
            "observedVolume": "small",
            "note": "Scout confirms light windrows only. Lagoon still passable.",
        },
    },
    {
        "id": "harbor-forecast",
        "title": "Harbor drift warning",
        "narration": "Scenario-based drift raises 12-hour landfall risk at Harbor Entrance. Containment is flagged before flood tide.",
        "kind": "forecast",
        "payload": {
            "zoneId": "harbor-entrance",
            "forecastRisk": {"h12": 0.78, "h24": 0.86, "h48": 0.91},
            "note": "Seeded current vector now points mats into the navigation channel within 12 hours.",
        },
    },
]


def clone_demo_events():
    return deepcopy(DEMO_EVENTS)
