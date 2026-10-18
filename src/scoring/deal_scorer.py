"""
Deal scoring engine — the 7-component formula.

Every listing gets a Deal Score from 0 to 100:

    deal_score = (
        price_vs_total_value  × 0.40  +  # Price vs. reconstructed build value
        component_score       × 0.20  +  # Quality of actual build
        condition_score       × 0.10  +  # Condition relative to price
        age_score             × 0.10  +  # Model year freshness
        brand_score           × 0.07  +  # Frame brand desirability
        seller_score          × 0.03  +  # Seller trust signals
        listing_freshness     × 0.10     # How recently posted
    )
"""

import logging
import re
from datetime import datetime, timezone
from typing import Optional

from src.scoring.component_extractor import ComponentExtractor, ExtractedBuild
from src.scoring.build_valuator import BuildValuator, BuildValuation, current_year, is_complete_bike_category
from src.scoring.component_values import FRAME_BRAND_TIERS, TIER_SCORES
from src.constants import CONDITION_SCORES

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Individual score components
# ---------------------------------------------------------------------------

def calc_price_value_score(asking_price: float,
                           reconstructed_value: float,
                           build_confidence: float) -> float:
    """
    Score: how the asking price compares to reconstructed build value.
    Lower price relative to value = higher score.

    Weight: 40%

    When confidence is low, the reconstructed value is still based on
    frame brand tier + material + age, so it provides a rough floor.
    We blend toward neutral more gently to allow differentiation.
    """
    if asking_price <= 0:
        return 40.0

    if reconstructed_value <= 0:
        # Can't evaluate at all — use price bracket heuristic
        # Cheaper bikes are inherently more likely to be "deals"
        if asking_price < 1500:
            return 60.0
        elif asking_price < 3000:
            return 50.0
        elif asking_price < 6000:
            return 45.0
        else:
            return 40.0

    price_ratio = asking_price / reconstructed_value

    # Continuous curve: ratio 0.4→100, 0.7→75, 1.0→50, 1.3→20, 1.6→0
    raw_score = max(0, min(100, 133 - (price_ratio * 83)))

    # Confidence blending: even at 0 confidence, still use 40% of the raw
    # score since frame value alone gives useful signal
    min_weight = 0.40
    confidence_factor = min_weight + (1.0 - min_weight) * min(1.0, build_confidence / 0.7)
    score = (raw_score * confidence_factor) + (50.0 * (1 - confidence_factor))

    return round(score, 1)


def calc_component_score(avg_tier_score: float,
                         build_confidence: float) -> float:
    """
    Score: quality of the build based on component tiers.
    Premium builds score high, budget builds score low.

    Weight: 20%
    """
    # avg_tier_score is already 0-100 based on TIER_SCORES
    # When confidence is low, blend toward neutral but still allow
    # the identified components (even 1-2) to influence the score
    min_weight = 0.30
    confidence_factor = min_weight + (1.0 - min_weight) * min(1.0, build_confidence / 0.6)
    score = (avg_tier_score * confidence_factor) + (45.0 * (1 - confidence_factor))
    return round(min(100, score), 1)


def calc_condition_score(condition: str = "", asking_price: float = 0.0) -> float:
    """
    Score: condition relative to price bracket.
    "Excellent" at $2000 is better than "Good" at $2000.

    Weight: 10%
    """
    condition_map = {
        "New":       95,
        "Excellent": 80,
        "Good":      55,
        "Fair":      30,
    }

    base = condition_map.get(condition, 45)

    # Bonus: lower price + better condition is more appealing
    if asking_price > 0 and condition in ("Excellent", "New"):
        if asking_price < 3000:
            base = min(100, base + 10)  # Cheap + excellent = great
        elif asking_price < 5000:
            base = min(100, base + 5)

    return float(base)


def calc_age_score(year: int = None) -> float:
    """
    Score: model year freshness.
    Newer = higher score, with diminishing returns.

    Weight: 10%
    """
    if not year or year < 2000:
        return 40.0  # Unknown age

    age = max(0, current_year() - year)

    if age == 0:
        return 98.0   # Current year
    elif age == 1:
        return 90.0
    elif age == 2:
        return 80.0
    elif age == 3:
        return 68.0
    elif age == 4:
        return 55.0
    elif age == 5:
        return 42.0
    elif age <= 7:
        return 30.0
    elif age <= 10:
        return 20.0
    else:
        return 10.0


def calc_brand_score(brand: str = "") -> float:
    """
    Score: frame brand desirability and resale value.

    Weight: 7%
    """
    if not brand:
        return 40.0

    brand_lower = brand.lower()

    for tier_name, tier_data in FRAME_BRAND_TIERS.items():
        for known_brand in tier_data["brands"]:
            if known_brand.lower() in brand_lower or brand_lower in known_brand.lower():
                return {
                    "premium": 95,
                    "high":    75,
                    "mid":     55,
                    "budget":  30,
                }[tier_name]

    return 45.0  # Unknown brand — slightly below average


def calc_seller_score(seller_username: str = "",
                      seller_rating: float = None,
                      is_boosted: bool = False) -> float:
    """
    Score: seller trust signals.
    Not much data in Phase 1, so this is simple.

    Weight: 3%
    """
    score = 50.0  # Neutral default

    if seller_rating and seller_rating > 0:
        # Rating out of 5 → scale to 0-100
        score = min(100, seller_rating * 20)

    # Boosted listings are from more serious sellers
    if is_boosted:
        score = min(100, score + 10)

    return score


def parse_posted_date(text: str):
    """Parse an absolute posted date into an aware UTC datetime, or None."""
    text = (text or "").strip()
    for fmt in ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        dt = datetime.fromisoformat(text)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def calc_freshness_score(date_posted: str = "", now: datetime = None) -> float:
    """
    Score: how recently the listing was posted.
    Newer listings are more relevant.

    Weight: 10%
    """
    if not date_posted:
        return 50.0

    posted_lower = date_posted.lower()

    # Parse relative time from Pinkbike format
    hours_match = re.search(r'(\d+)\s*hour', posted_lower)
    days_match = re.search(r'(\d+)\s*day', posted_lower)
    weeks_match = re.search(r'(\d+)\s*week', posted_lower)
    months_match = re.search(r'(\d+)\s*month', posted_lower)
    minutes_match = re.search(r'(\d+)\s*min', posted_lower)

    hours_ago = 999  # Default old

    if minutes_match:
        hours_ago = int(minutes_match.group(1)) / 60
    elif hours_match:
        hours_ago = int(hours_match.group(1))
    elif days_match:
        hours_ago = int(days_match.group(1)) * 24
    elif weeks_match:
        hours_ago = int(weeks_match.group(1)) * 24 * 7
    elif months_match:
        hours_ago = int(months_match.group(1)) * 24 * 30
    else:
        # The parser stores absolute dates ("Jan 2, 2026" or ISO), which the
        # relative patterns above never matched, so every listing scored 10.
        posted = parse_posted_date(date_posted)
        if posted:
            now = now or datetime.now(timezone.utc)
            hours_ago = max(0.0, (now - posted).total_seconds() / 3600)

    # Score curve: < 6 hours = 100, < 24h = 85, < 3 days = 70, etc.
    if hours_ago < 6:
        return 100.0
    elif hours_ago < 24:
        return 85.0
    elif hours_ago < 72:
        return 70.0
    elif hours_ago < 168:  # 1 week
        return 55.0
    elif hours_ago < 336:  # 2 weeks
        return 40.0
    elif hours_ago < 720:  # 1 month
        return 25.0
    else:
        return 10.0


# ---------------------------------------------------------------------------
# Not-a-bike detection
# ---------------------------------------------------------------------------

# Things people post in complete-bike categories that aren't bikes for sale.
_NOT_A_BIKE = re.compile(
    r"\b(decals?|stickers?|frame protection|invisiframe|protection kit|"
    r"wanted|wtb|looking for|poster|jersey|shirt|hoodie|"
    r"keychain|manual|owner'?s manual)\b",
    re.IGNORECASE,
)
NOT_A_BIKE_SCORE_CAP = 10.0
MIN_PLAUSIBLE_BIKE_PRICE = 150


def looks_like_not_a_bike(title: str, description: str, price: float,
                          category: str) -> bool:
    """True when a listing in a complete-bike category is clearly not a bike."""
    if not is_complete_bike_category(category):
        return False
    if _NOT_A_BIKE.search(title or ""):
        return True
    if 0 < price < MIN_PLAUSIBLE_BIKE_PRICE and "kid" not in (category or "").lower():
        return True
    return False


# ---------------------------------------------------------------------------
# Main scorer
# ---------------------------------------------------------------------------

class DealScorer:
    """
    Scores a listing using the 7-component formula.

    Usage:
        scorer = DealScorer()
        result = scorer.score_listing(
            description="...", title="...", price=3500,
            condition="Excellent", brand="Santa Cruz", year=2023, ...
        )
        print(result["deal_score"])
    """

    # Formula weights
    WEIGHTS = {
        "price_value":    0.40,
        "component":      0.20,
        "condition":      0.10,
        "age":            0.10,
        "brand":          0.07,
        "seller":         0.03,
        "freshness":      0.10,
    }

    @classmethod
    def score_listing(cls,
                      description: str = "",
                      title: str = "",
                      price: float = 0.0,
                      condition: str = "Good",
                      brand: str = "",
                      model: str = "",
                      year: int = None,
                      material: str = "",
                      category: str = "",
                      seller_username: str = "",
                      seller_rating: float = None,
                      is_boosted: bool = False,
                      date_posted: str = "",
                      ) -> dict:
        """
        Score a listing. Returns dict with deal_score and all sub-scores.
        """
        # Step 1: Extract components from description
        build = ComponentExtractor.extract(description, title, category)

        # Step 2: Valuate the build
        valuation = BuildValuator.valuate(
            build=build, brand=brand, model=model, year=year,
            material=material, condition=condition, asking_price=price,
            category=category,
        )

        # Step 3: Calculate each score component
        price_value = calc_price_value_score(
            price, valuation.total_reconstructed_value, build.confidence
        )
        component = calc_component_score(
            valuation.avg_component_tier_score, build.confidence
        )
        cond_score = calc_condition_score(condition, price)
        age = calc_age_score(year)
        brand_s = calc_brand_score(brand)
        seller = calc_seller_score(seller_username, seller_rating, is_boosted)
        freshness = calc_freshness_score(date_posted)

        # Step 4: Weighted sum
        deal_score = (
            price_value * cls.WEIGHTS["price_value"]
            + component * cls.WEIGHTS["component"]
            + cond_score * cls.WEIGHTS["condition"]
            + age * cls.WEIGHTS["age"]
            + brand_s * cls.WEIGHTS["brand"]
            + seller * cls.WEIGHTS["seller"]
            + freshness * cls.WEIGHTS["freshness"]
        )
        not_a_bike = looks_like_not_a_bike(title, description, price, category)
        if not_a_bike:
            deal_score = min(deal_score, NOT_A_BIKE_SCORE_CAP)
        deal_score = round(min(100, max(0, deal_score)), 1)

        return {
            "deal_score": deal_score,
            "not_a_bike": not_a_bike,
            # Sub-scores
            "price_value_score": price_value,
            "component_score": component,
            "condition_score": cond_score,
            "age_score": age,
            "brand_score": brand_s,
            "seller_score": seller,
            "freshness_score": freshness,
            # Build analysis
            "build": build.to_dict(),
            "valuation": {
                "frame_value": valuation.frame_value,
                "component_msrp": valuation.total_component_msrp,
                "component_used": valuation.total_component_used,
                "total_reconstructed": valuation.total_reconstructed_value,
                "issue_deduction": valuation.issue_deduction,
                "build_quality": valuation.build_quality_label,
                "matched_components": valuation.matched_count,
                "imputed_components": valuation.imputed_count,
                "confidence": valuation.confidence,
            },
        }
