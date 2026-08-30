"""Shared constants for the decision engine. All values are simulated planning inputs."""

VOLUME_SEVERITY = {
    "small": 0.28,
    "medium": 0.58,
    "large": 0.92,
}

EMA_ALPHA = 0.48
EXPLORATION_C = 0.72
FORECAST_WEIGHT = 0.35
DEFAULT_CREW_BUDGET = 8
MIN_CREW_BUDGET = 4
MAX_CREW_BUDGET = 16
MAX_ECONOMIC_WEIGHT = 3.0
CONTAINMENT_THRESHOLD = 0.58

SUBMITTER_TYPES = ("resident", "fisher", "hotel_staff", "lifeguard", "municipal_scout")

ZONE_IDS = (
    "tourist-beach",
    "fishing-dock",
    "residential-cove",
    "quiet-inlet",
    "harbor-entrance",
    "north-point",
)
