"""
PinkbikeDeals constants.

Static data: category IDs, condition scores, brands, currencies.
"""

# ---------------------------------------------------------------------------
# Pinkbike BuySell category IDs (from URL ?category=N)
# ---------------------------------------------------------------------------
CATEGORIES = {
    # Complete bikes
    "xc_bikes":       {"id": 1, "name": "XC / Cross Country Bikes"},
    "enduro_bikes":   {"id": 2, "name": "Enduro Bikes"},
    "dh_bikes":       {"id": 3, "name": "Downhill Bikes"},
    "trail_bikes":    {"id": 75, "name": "Trail Bikes"},
    "dj_bikes":       {"id": 10, "name": "Dirt Jump Bikes"},
    "kids_bikes":     {"id": 73, "name": "Kids Bikes"},
    "fat_bikes":      {"id": 62, "name": "Fat Bikes"},
    "ebikes":         {"id": 95, "name": "E-Bikes / E-MTBs"},
    "road_gravel":    {"id": 24, "name": "Road / Gravel Bikes"},

    # Frames
    "xc_frames":      {"id": 4, "name": "XC / Cross Country Frames"},
    "enduro_frames":  {"id": 5, "name": "Enduro Frames"},
    "dh_frames":      {"id": 6, "name": "Downhill Frames"},
    "trail_frames":   {"id": 76, "name": "Trail Frames"},
    "dj_frames":      {"id": 11, "name": "Dirt Jump Frames"},

    # Key components
    "forks_single":   {"id": 7, "name": "Single Crown Forks"},
    "forks_dual":     {"id": 8, "name": "Dual Crown Forks"},
    "rear_shocks":    {"id": 9, "name": "Rear Shocks"},
    "brakes":         {"id": 13, "name": "Brakes"},
    "wheels":         {"id": 15, "name": "Wheels / Wheelsets"},
    "drivetrains":    {"id": 18, "name": "Drivetrains"},
    "dropper_posts":  {"id": 63, "name": "Dropper Posts"},
}

# Default categories to scan (all categories)
DEFAULT_SCAN_CATEGORIES = [
    # Complete bikes
    "enduro_bikes", "trail_bikes", "xc_bikes", "dh_bikes",
    "dj_bikes", "ebikes", "road_gravel", "kids_bikes", "fat_bikes",
    # Frames
    "enduro_frames", "trail_frames", "xc_frames", "dh_frames", "dj_frames",
    # Components
    "forks_single", "forks_dual", "rear_shocks", "brakes",
    "wheels", "drivetrains", "dropper_posts",
]


# ---------------------------------------------------------------------------
# Condition mappings
# ---------------------------------------------------------------------------
CONDITION_SCORES = {
    "New":       1.0,
    "Excellent": 0.85,
    "Good":      0.65,
    "Fair":      0.40,
}

CONDITION_LABELS = list(CONDITION_SCORES.keys())


# ---------------------------------------------------------------------------
# Currency
# ---------------------------------------------------------------------------
CURRENCY_SYMBOLS = {
    "CAD": "C$",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "AUD": "A$",
}

# Approximate exchange rates to USD (updated manually for Phase 1)
EXCHANGE_TO_USD = {
    "USD": 1.00,
    "CAD": 0.74,
    "EUR": 1.10,
    "GBP": 1.27,
    "AUD": 0.66,
}

EXCHANGE_TO_CAD = {
    "CAD": 1.00,
    "USD": 1.35,
    "EUR": 1.49,
    "GBP": 1.72,
    "AUD": 0.89,
}


# ---------------------------------------------------------------------------
# Known bike brands (for title parsing)
# Ordered longest-first so "Santa Cruz" matches before "Cruz"
# ---------------------------------------------------------------------------
KNOWN_BRANDS = sorted([
    # S-tier
    "Santa Cruz", "Yeti", "Ibis", "Pivot", "Evil", "Revel",
    "Forbidden", "We Are One", "Guerrilla Gravity",
    # A-tier
    "Specialized", "Trek", "Giant", "Transition", "Norco",
    "Rocky Mountain", "Cannondale", "Intense",
    # B-tier
    "Canyon", "YT", "Commencal", "Nukeproof", "Orbea", "Scott",
    "Mondraker", "Propain", "Devinci", "Banshee", "Knolly",
    "Kona", "GT",
    # C-tier
    "Polygon", "Vitus", "Marin", "Diamondback", "Fuji",
    "Merida", "Cube", "Ghost", "Lapierre", "Whyte",
    "Ragley", "Cotic", "Bird", "Stanton",
    # Road / Gravel
    "Cervelo", "Pinarello", "Colnago", "BMC", "Factor",
    "Bianchi", "Wilier", "Ridley", "Felt", "Salsa",
    "Surly", "All-City", "Niner", "Guerciotti",
    # E-bike specific
    "Specialized Turbo", "Trek Rail", "Giant Trance X",
    "Orbea Rise", "Scott Patron",
], key=lambda b: -len(b))  # longest first for greedy matching


# ---------------------------------------------------------------------------
# Frame sizes (normalized)
# ---------------------------------------------------------------------------
FRAME_SIZES = ["XS", "S", "M", "L", "XL", "XXL"]

FRAME_SIZE_ALIASES = {
    "extra small": "XS", "x-small": "XS", "xsmall": "XS",
    "small": "S",
    "medium": "M", "med": "M",
    "large": "L", "lg": "L",
    "extra large": "XL", "x-large": "XL", "xlarge": "XL",
    "extra extra large": "XXL", "xx-large": "XXL",
}

# ---------------------------------------------------------------------------
# Wheel sizes
# ---------------------------------------------------------------------------
WHEEL_SIZES = ["26\"", "27.5\"", "29\"", "Mixed"]
