"""
Transfer estimation service for inter-city travel.
Provides realistic transport modes, durations, and costs for Indian city pairs.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class TransferOption:
    """A single transport option between cities."""
    mode: str  # "train", "flight", "bus", "car"
    duration_hours: float
    approximate_cost_per_person: float
    frequency: str  # "hourly", "multiple_daily", "daily", "few_times_weekly"
    comfort_level: str  # "budget", "mid_range", "premium"
    notes: str


# ============================================================================
# TRANSFER DATABASE - Indian City-to-City Routes
# ============================================================================

TRANSFER_ROUTES = {
    ("delhi", "agra"): [
        TransferOption(
            mode="train",
            duration_hours=2.5,
            approximate_cost_per_person=150,
            frequency="hourly",
            comfort_level="budget",
            notes="Express trains (Gatimaan Express). Recommended."
        ),
        TransferOption(
            mode="bus",
            duration_hours=4.0,
            approximate_cost_per_person=250,
            frequency="every_30_min",
            comfort_level="budget",
            notes="UPSRTC or private operators. Road conditions variable."
        ),
        TransferOption(
            mode="car",
            duration_hours=4.0,
            approximate_cost_per_person=800,  # For 4 passengers
            frequency="on_demand",
            comfort_level="premium",
            notes="Self-drive or rented cab. Highway NH44. Scenic."
        ),
        TransferOption(
            mode="flight",
            duration_hours=1.0,  # Flight time only, excludes airport procedures
            approximate_cost_per_person=2500,
            frequency="2_3_daily",
            comfort_level="premium",
            notes="Expensive, rarely recommended for 240km distance."
        ),
    ],
    
    ("agra", "jaipur"): [
        TransferOption(
            mode="train",
            duration_hours=4.5,
            approximate_cost_per_person=200,
            frequency="2_3_daily",
            comfort_level="budget",
            notes="Pink City Express or local trains."
        ),
        TransferOption(
            mode="bus",
            duration_hours=5.5,
            approximate_cost_per_person=300,
            frequency="every_hour",
            comfort_level="budget",
            notes="Direct coaches. Scenic Rajasthan road."
        ),
        TransferOption(
            mode="car",
            duration_hours=5.0,
            approximate_cost_per_person=900,  # For 4 passengers
            frequency="on_demand",
            comfort_level="premium",
            notes="Highway NH11. Golden triangle route."
        ),
    ],

    ("delhi", "jaipur"): [
        TransferOption(
            mode="train",
            duration_hours=4.5,
            approximate_cost_per_person=250,
            frequency="multiple_daily",
            comfort_level="budget",
            notes="Raj Express or Pink City Express."
        ),
        TransferOption(
            mode="bus",
            duration_hours=5.5,
            approximate_cost_per_person=300,
            frequency="every_30_min",
            comfort_level="budget",
            notes="AC coaches available. Smooth highway."
        ),
        TransferOption(
            mode="car",
            duration_hours=5.0,
            approximate_cost_per_person=850,  # For 4 passengers
            frequency="on_demand",
            comfort_level="premium",
            notes="NH48 highway. Popular tourist route."
        ),
        TransferOption(
            mode="flight",
            duration_hours=1.0,
            approximate_cost_per_person=3000,
            frequency="3_4_daily",
            comfort_level="premium",
            notes="Not recommended; short distance."
        ),
    ],

    ("delhi", "varanasi"): [
        TransferOption(
            mode="train",
            duration_hours=13.0,
            approximate_cost_per_person=400,
            frequency="2_3_daily",
            comfort_level="budget",
            notes="Sleeper class recommended for overnight journey."
        ),
        TransferOption(
            mode="flight",
            duration_hours=2.0,
            approximate_cost_per_person=2500,
            frequency="multiple_daily",
            comfort_level="premium",
            notes="Expensive but saves time. Better for time-limited trips."
        ),
        TransferOption(
            mode="bus",
            duration_hours=16.0,
            approximate_cost_per_person=600,
            frequency="few_daily",
            comfort_level="budget",
            notes="Long journey. Bus quality variable."
        ),
    ],

    ("delhi", "kolkata"): [
        TransferOption(
            mode="train",
            duration_hours=17.0,
            approximate_cost_per_person=500,
            frequency="2_3_daily",
            comfort_level="budget",
            notes="Rajdhani Express (faster) or Duronto. Sleeper/AC recommended."
        ),
        TransferOption(
            mode="flight",
            duration_hours=2.5,
            approximate_cost_per_person=3500,
            frequency="multiple_daily",
            comfort_level="premium",
            notes="Recommended for time-limited itinerary."
        ),
    ],

    ("delhi", "goa"): [
        TransferOption(
            mode="flight",
            duration_hours=2.5,
            approximate_cost_per_person=3500,
            frequency="multiple_daily",
            comfort_level="premium",
            notes="Most practical option."
        ),
        TransferOption(
            mode="train",
            duration_hours=28.0,
            approximate_cost_per_person=700,
            frequency="few_daily",
            comfort_level="budget",
            notes="Long journey; overnight sleeper."
        ),
        TransferOption(
            mode="bus",
            duration_hours=32.0,
            approximate_cost_per_person=1000,
            frequency="few_daily",
            comfort_level="budget",
            notes="Very long; not recommended for multi-stop itinerary."
        ),
    ],

    ("agra", "delhi"): [  # Return route
        TransferOption(
            mode="train",
            duration_hours=2.5,
            approximate_cost_per_person=150,
            frequency="hourly",
            comfort_level="budget",
            notes="Express trains (Gatimaan Express). Recommended."
        ),
        TransferOption(
            mode="bus",
            duration_hours=4.0,
            approximate_cost_per_person=250,
            frequency="every_30_min",
            comfort_level="budget",
            notes="UPSRTC or private operators."
        ),
    ],

    ("jaipur", "delhi"): [  # Return route
        TransferOption(
            mode="train",
            duration_hours=4.5,
            approximate_cost_per_person=250,
            frequency="multiple_daily",
            comfort_level="budget",
            notes="Raj Express or Pink City Express."
        ),
        TransferOption(
            mode="bus",
            duration_hours=5.5,
            approximate_cost_per_person=300,
            frequency="every_30_min",
            comfort_level="budget",
            notes="AC coaches available."
        ),
    ],

    ("jaipur", "agra"): [  # Return route
        TransferOption(
            mode="train",
            duration_hours=4.5,
            approximate_cost_per_person=200,
            frequency="2_3_daily",
            comfort_level="budget",
            notes="Pink City Express or local trains."
        ),
        TransferOption(
            mode="bus",
            duration_hours=5.5,
            approximate_cost_per_person=300,
            frequency="every_hour",
            comfort_level="budget",
            notes="Direct coaches."
        ),
    ],

    ("varanasi", "delhi"): [  # Return route
        TransferOption(
            mode="train",
            duration_hours=13.0,
            approximate_cost_per_person=400,
            frequency="2_3_daily",
            comfort_level="budget",
            notes="Sleeper class recommended."
        ),
        TransferOption(
            mode="flight",
            duration_hours=2.0,
            approximate_cost_per_person=2500,
            frequency="multiple_daily",
            comfort_level="premium",
            notes="Recommended option."
        ),
    ],

    ("kolkata", "delhi"): [  # Return route
        TransferOption(
            mode="train",
            duration_hours=17.0,
            approximate_cost_per_person=500,
            frequency="2_3_daily",
            comfort_level="budget",
            notes="Rajdhani or Duronto Express."
        ),
        TransferOption(
            mode="flight",
            duration_hours=2.5,
            approximate_cost_per_person=3500,
            frequency="multiple_daily",
            comfort_level="premium",
            notes="Recommended."
        ),
    ],

    ("goa", "delhi"): [  # Return route
        TransferOption(
            mode="flight",
            duration_hours=2.5,
            approximate_cost_per_person=3500,
            frequency="multiple_daily",
            comfort_level="premium",
            notes="Most practical."
        ),
    ],
}


def get_transfer_options(origin: str, destination: str) -> List[TransferOption]:
    """
    Get available transport options between two cities.
    
    Args:
        origin: City name (case-insensitive)
        destination: City name (case-insensitive)
    
    Returns:
        List of TransferOption objects sorted by recommended order
    """
    origin_normalized = origin.lower().strip()
    dest_normalized = destination.lower().strip()
    
    # Direct match
    key = (origin_normalized, dest_normalized)
    if key in TRANSFER_ROUTES:
        options = TRANSFER_ROUTES[key]
        # Sort by recommended order: train first, then bus, then flight
        order = {"train": 0, "bus": 1, "car": 2, "flight": 3}
        return sorted(options, key=lambda x: order.get(x.mode, 99))
    
    # No data available
    return []


def estimate_transfer(origin: str, destination: str) -> Optional[Dict[str, any]]:
    """
    Estimate the most recommended transfer option between cities.
    
    Returns:
        Dictionary with mode, duration_hours, cost_per_person, and notes
        Or None if route is not in database
    """
    options = get_transfer_options(origin, destination)
    
    if not options:
        return None
    
    # Return the first (recommended) option
    opt = options[0]
    return {
        "mode": opt.mode,
        "duration_hours": opt.duration_hours,
        "duration_display": f"{opt.duration_hours:.1f} hours" if opt.duration_hours < 10 else f"{int(opt.duration_hours // 24)} days" if opt.duration_hours >= 24 else f"{opt.duration_hours:.1f} hours",
        "cost_per_person": opt.approximate_cost_per_person,
        "frequency": opt.frequency,
        "comfort_level": opt.comfort_level,
        "notes": opt.notes,
        "all_options": [
            {
                "mode": o.mode,
                "duration_hours": o.duration_hours,
                "cost_per_person": o.approximate_cost_per_person,
                "frequency": o.frequency,
                "comfort_level": o.comfort_level,
            }
            for o in options
        ]
    }


def estimate_transfer_cost(origin: str, destination: str, num_travelers: int = 1) -> Optional[float]:
    """
    Estimate total transfer cost for a group.
    """
    transfer = estimate_transfer(origin, destination)
    if not transfer:
        return None
    return transfer["cost_per_person"] * num_travelers
