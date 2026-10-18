"""
Build valuator — reconstructs the total value of a bike based on
its frame and all identified components.

Compares asking price against reconstructed value to find deals.
"""

import logging
import statistics
from datetime import date
from dataclasses import dataclass, field
from typing import Optional

from thefuzz import fuzz, process as fuzz_process

from src.scoring.component_values import (
    ALL_COMPONENT_VALUES, FRAME_BRAND_TIERS, FRAME_MATERIAL_MULT,
    COMPONENT_TIERS, TIER_SCORES, SLOT_VALUE_WEIGHTS,
)
from src.scoring.component_extractor import ExtractedBuild

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ComponentValuation:
    """Valuation of a single component."""
    slot: str
    name: str
    msrp: float = 0.0
    used_value: float = 0.0
    tier: str = "unknown"
    tier_score: float = 40.0
    matched: bool = False


@dataclass
class BuildValuation:
    """Complete valuation of a bike build."""
    frame_value: float = 0.0
    total_component_msrp: float = 0.0
    total_component_used: float = 0.0
    total_reconstructed_value: float = 0.0
    issue_deduction: float = 0.0
    components: list = field(default_factory=list)  # list[ComponentValuation]
    avg_component_tier_score: float = 40.0
    build_quality_label: str = "unknown"
    matched_count: int = 0
    imputed_count: int = 0
    total_slots: int = 12
    confidence: float = 0.0


# ---------------------------------------------------------------------------
# Used value calculation
# ---------------------------------------------------------------------------

def current_year() -> int:
    return date.today().year


def component_used_value(msrp: float, condition: str = "Good",
                         age_years: float = 2.0) -> float:
    """
    Estimate used value of a component.

    Condition and age both reduce value, but stacking two steep curves
    undervalued real bikes badly (a clean 4-year-old fork came out at ~35%
    of MSRP; it actually sells for closer to 50%). Both curves are gentler now.

    Args:
        msrp: New retail price
        condition: Listing condition (New/Excellent/Good/Fair)
        age_years: How old the bike/component is
    """
    condition_mult = {
        "New":       0.92,
        "Excellent": 0.82,
        "Good":      0.70,
        "Fair":      0.50,
    }.get(condition, 0.65)

    # Age depreciation: ~9% per year, floored at 30%
    age_mult = max(0.30, 1.0 - (age_years * 0.09))

    return round(msrp * condition_mult * age_mult, 2)


def estimate_frame_value(brand: str = "", model: str = "",
                         year: int = None, material: str = "",
                         condition: str = "Good") -> float:
    """
    Estimate the used frame value based on brand tier, material, and age.
    """
    # Find brand tier
    base_value = 1500  # Default if unknown brand
    for tier_name, tier_data in FRAME_BRAND_TIERS.items():
        for known_brand in tier_data["brands"]:
            if known_brand.lower() in (brand or "").lower():
                base_value = tier_data["base_value"]
                break

    # Material multiplier (unknown or unrecognised material: split the difference)
    mat_mult = 0.75
    if material:
        for mat_key, mult in FRAME_MATERIAL_MULT.items():
            if mat_key.lower() in material.lower():
                mat_mult = mult
                break

    # Age depreciation — frames lose ~8% per year
    age_years = 0
    if year and year > 2000:
        age_years = max(0, current_year() - year)
    age_mult = max(0.25, 1.0 - (age_years * 0.08))

    # Condition
    cond_mult = {
        "New": 0.92, "Excellent": 0.82, "Good": 0.70, "Fair": 0.50,
    }.get(condition, 0.65)

    return round(base_value * mat_mult * age_mult * cond_mult, 2)


# ---------------------------------------------------------------------------
# Component matching against value database
# ---------------------------------------------------------------------------

def match_component_value(slot: str, name: str) -> tuple[float, str]:
    """
    Match a component name against the value database.

    Returns: (msrp, matched_name) or (0, "") if no match.
    """
    if not name or slot not in ALL_COMPONENT_VALUES:
        return 0.0, ""

    value_db = ALL_COMPONENT_VALUES[slot]

    # Exact match first
    if name in value_db:
        return value_db[name], name

    # Case-insensitive exact
    name_lower = name.lower()
    for db_name, msrp in value_db.items():
        if db_name.lower() == name_lower:
            return msrp, db_name

    # Fuzzy match
    candidates = list(value_db.keys())
    if not candidates:
        return 0.0, ""

    result = fuzz_process.extractOne(
        name, candidates,
        scorer=fuzz.token_sort_ratio,
        score_cutoff=70,
    )
    if result:
        matched_name = result[0]
        return value_db[matched_name], matched_name

    return 0.0, ""


def get_component_tier(slot: str, name: str) -> str:
    """Determine the quality tier of a component."""
    if not name or slot not in COMPONENT_TIERS:
        return "unknown"

    name_lower = name.lower()
    for tier, names in COMPONENT_TIERS[slot].items():
        for tier_name in names:
            if tier_name.lower() in name_lower or name_lower in tier_name.lower():
                return tier

    # Fuzzy match against tier names
    all_tier_names = []
    tier_map = {}
    for tier, names in COMPONENT_TIERS[slot].items():
        for n in names:
            all_tier_names.append(n)
            tier_map[n] = tier

    if all_tier_names:
        tier_result = fuzz_process.extractOne(
            name, all_tier_names,
            scorer=fuzz.token_sort_ratio,
            score_cutoff=65,
        )
        if tier_result:
            return tier_map[tier_result[0]]

    return "unknown"


# ---------------------------------------------------------------------------
# Issue cost estimation
# ---------------------------------------------------------------------------

def estimate_issue_cost(issues: list[str]) -> float:
    """Estimate dollar cost of noted issues."""
    if not issues:
        return 0.0

    total = 0.0
    for issue in issues:
        issue_lower = issue.lower()
        # Chain issues
        if "chain" in issue_lower and ("worn" in issue_lower or "needs" in issue_lower
                                        or "stretched" in issue_lower):
            total += 40
        # Brake pad issues
        elif "pad" in issue_lower and ("worn" in issue_lower or "low" in issue_lower
                                        or "need" in issue_lower):
            total += 50
        # Tire issues
        elif ("tire" in issue_lower or "tyre" in issue_lower) and (
              "worn" in issue_lower or "bald" in issue_lower or "need" in issue_lower):
            total += 120
        # Scratch/cosmetic
        elif "scratch" in issue_lower or "cosmetic" in issue_lower or "chip" in issue_lower:
            total += 50
        # Dent
        elif "dent" in issue_lower:
            total += 150
        # Crack
        elif "crack" in issue_lower:
            total += 500
        # Generic damage
        elif "damage" in issue_lower:
            total += 200
        # Generic needs replacing
        elif "needs" in issue_lower or "replace" in issue_lower:
            total += 100
        else:
            total += 50  # Unknown issue

    return total


# ---------------------------------------------------------------------------
# Imputation of missing major parts
# ---------------------------------------------------------------------------

# A complete bike always has these, even when the seller doesn't list them.
# Leaving them at $0 made every partly-described bike look overpriced.
IMPUTED_SLOTS = ["fork", "shock", "drivetrain", "brakes", "wheels"]


def is_complete_bike_category(category: str) -> bool:
    cat = (category or "").lower()
    return "bike" in cat and "frame" not in cat


def typical_msrp(slot: str, tier: str) -> float:
    """Median MSRP of the known parts in a slot at a given quality tier."""
    values = ALL_COMPONENT_VALUES.get(slot, {})
    names = COMPONENT_TIERS.get(slot, {}).get(tier, [])
    msrps = [match_component_value(slot, n)[0] for n in names]
    msrps = [m for m in msrps if m > 0]
    if not msrps and values:
        msrps = list(values.values())
    return float(statistics.median(msrps)) if msrps else 0.0


def build_tier(tier_scores: list[float]) -> str:
    """Tier to assume for missing parts, based on the parts that were found."""
    if not tier_scores:
        return "entry"
    avg = sum(tier_scores) / len(tier_scores)
    if avg >= 85:
        return "premium"
    if avg >= 60:
        return "mid"
    if avg >= 35:
        return "entry"
    return "budget"


# ---------------------------------------------------------------------------
# Main valuator
# ---------------------------------------------------------------------------

class BuildValuator:
    """
    Reconstructs the total value of a bike from its frame and components.
    """

    @classmethod
    def valuate(cls, build: ExtractedBuild, brand: str = "",
                model: str = "", year: int = None,
                material: str = "", condition: str = "Good",
                asking_price: float = 0.0,
                category: str = "") -> BuildValuation:
        """
        Perform a complete build valuation.

        Args:
            build: ExtractedBuild from the component extractor
            brand: Frame brand
            model: Frame model
            year: Model year
            material: Frame material (Carbon, Aluminum, etc.)
            condition: Listing condition
            asking_price: What the seller is asking

        Returns:
            BuildValuation with complete breakdown
        """
        valuation = BuildValuation()

        # --- Frame value ---
        valuation.frame_value = estimate_frame_value(
            brand=brand, model=model, year=year,
            material=material, condition=condition,
        )

        # --- Age for component depreciation ---
        age_years = max(0, current_year() - year) if year and year > 2000 else 3.0

        # --- Valuate each component ---
        component_slots = {
            "fork": build.fork,
            "shock": build.shock,
            "drivetrain": build.drivetrain,
            "brakes": build.brakes,
            "wheels": build.wheels,
            "dropper": build.dropper,
            "handlebars": build.handlebars,
            "stem": build.stem,
            "saddle": build.saddle,
            "pedals": build.pedals,
            "cranks": build.cranks,
        }

        # Handle tires (count as 2 tires)
        tier_scores = []

        for slot, comp_name in component_slots.items():
            if not comp_name:
                continue

            msrp, matched_name = match_component_value(slot, comp_name)
            tier = get_component_tier(slot, comp_name)
            tier_score = TIER_SCORES.get(tier, 40)

            if msrp > 0:
                used_val = component_used_value(msrp, condition, age_years)
            else:
                used_val = 0.0

            cv = ComponentValuation(
                slot=slot,
                name=comp_name,
                msrp=msrp,
                used_value=used_val,
                tier=tier,
                tier_score=tier_score,
                matched=msrp > 0,
            )
            valuation.components.append(cv)
            valuation.total_component_msrp += msrp
            valuation.total_component_used += used_val
            if msrp > 0:
                valuation.matched_count += 1
            tier_scores.append(tier_score)

        # Tires (both front and rear)
        for tire_slot, tire_name in [("tires", build.tires_front),
                                      ("tires", build.tires_rear)]:
            if not tire_name:
                continue
            msrp, matched_name = match_component_value(tire_slot, tire_name)
            if msrp > 0:
                used_val = component_used_value(msrp, condition, age_years)
                valuation.total_component_msrp += msrp
                valuation.total_component_used += used_val
                valuation.matched_count += 1
                valuation.components.append(ComponentValuation(
                    slot=f"tire", name=tire_name, msrp=msrp,
                    used_value=used_val, tier="n/a", tier_score=50,
                    matched=True,
                ))

        # --- Impute missing major parts on complete bikes ---
        if is_complete_bike_category(category):
            text = " ".join(filter(None, [model, category])).lower()
            hardtail = "hardtail" in text or "dirt jump" in text or "road" in text
            assumed_tier = build_tier(tier_scores)
            for slot in IMPUTED_SLOTS:
                if component_slots.get(slot):
                    continue
                if slot == "shock" and hardtail:
                    continue
                msrp = typical_msrp(slot, assumed_tier)
                if msrp <= 0:
                    continue
                used_val = component_used_value(msrp, condition, age_years)
                valuation.components.append(ComponentValuation(
                    slot=slot, name=f"(assumed {assumed_tier} {slot})",
                    msrp=msrp, used_value=used_val, tier=assumed_tier,
                    tier_score=TIER_SCORES.get(assumed_tier, 40), matched=False,
                ))
                valuation.total_component_msrp += msrp
                valuation.total_component_used += used_val
                valuation.imputed_count += 1

        # --- Issue deductions ---
        valuation.issue_deduction = estimate_issue_cost(build.noted_issues)

        # --- Total reconstructed value ---
        valuation.total_reconstructed_value = (
            valuation.frame_value
            + valuation.total_component_used
            - valuation.issue_deduction
        )

        # --- Average tier score ---
        if tier_scores:
            valuation.avg_component_tier_score = sum(tier_scores) / len(tier_scores)
        else:
            valuation.avg_component_tier_score = 40.0

        # --- Build quality label ---
        avg = valuation.avg_component_tier_score
        if avg >= 85:
            valuation.build_quality_label = "Premium"
        elif avg >= 65:
            valuation.build_quality_label = "Mid-Range"
        elif avg >= 40:
            valuation.build_quality_label = "Entry"
        else:
            valuation.build_quality_label = "Budget"

        # --- Confidence ---
        valuation.confidence = build.confidence
        valuation.total_slots = build.total_slots

        return valuation
