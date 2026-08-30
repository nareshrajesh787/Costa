"""Deterministic seed reports that establish the opening operational picture."""

from copy import deepcopy

SEED_REPORTS = [
    {
        "id": "rpt-seed-01",
        "zoneId": "tourist-beach",
        "volume": "medium",
        "submitterType": "lifeguard",
        "note": "Mats accumulating at the south swim line after morning tide.",
        "timestamp": "2026-08-30T08:12:00-04:00",
        "source": "seed",
    },
    {
        "id": "rpt-seed-02",
        "zoneId": "harbor-entrance",
        "volume": "medium",
        "submitterType": "municipal_scout",
        "note": "Channel edges thickening; ferry reported reduced visibility.",
        "timestamp": "2026-08-30T08:40:00-04:00",
        "source": "seed",
    },
    {
        "id": "rpt-seed-03",
        "zoneId": "fishing-dock",
        "volume": "medium",
        "submitterType": "fisher",
        "note": "Co-op skippers delaying departure. Ice house still open.",
        "timestamp": "2026-08-30T09:05:00-04:00",
        "source": "seed",
    },
    {
        "id": "rpt-seed-04",
        "zoneId": "north-point",
        "volume": "small",
        "submitterType": "resident",
        "note": "Windrow along the cliff path, not blocking the overlook.",
        "timestamp": "2026-08-30T09:22:00-04:00",
        "source": "seed",
    },
    {
        "id": "rpt-seed-05",
        "zoneId": "residential-cove",
        "volume": "small",
        "submitterType": "resident",
        "note": "Light debris near the access path. Kids still using the ramp.",
        "timestamp": "2026-08-30T09:48:00-04:00",
        "source": "seed",
    },
]


def clone_seed_reports():
    return deepcopy(SEED_REPORTS)
