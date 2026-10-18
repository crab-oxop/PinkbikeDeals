"""Tests for the scoring model: extraction, valuation and deal score."""

from datetime import datetime, timezone

from src.scoring.component_extractor import ComponentExtractor
from src.scoring.build_valuator import BuildValuator, estimate_frame_value
from src.scoring.deal_scorer import (
    DealScorer, calc_freshness_score, looks_like_not_a_bike,
)

MEGATOWER = (
    "2022 Santa Cruz Megatower CC carbon, Fox 38 Factory, Float X2 Factory, "
    "SRAM X01 Eagle drivetrain, SRAM Code RSC brakes, Reserve 30 carbon "
    "wheels, OneUp dropper 210. Well maintained, new pivot bearings."
)


def score(price, **kw):
    args = dict(description=MEGATOWER, title="2022 Santa Cruz Megatower CC",
                price=price, condition="Excellent", brand="Santa Cruz",
                model="Megatower", year=2022, material="Carbon",
                category="Enduro Bikes")
    args.update(kw)
    return DealScorer.score_listing(**args)


class TestExtraction:
    def test_matches_names_without_brand_prefix(self):
        build = ComponentExtractor.extract(MEGATOWER)
        assert build.shock == "Fox Float X2 Factory"

    def test_matches_wheel_names_without_hub_suffix(self):
        build = ComponentExtractor.extract(MEGATOWER)
        assert build.wheels is not None and build.wheels.startswith("Reserve 30")

    def test_finds_all_major_parts(self):
        build = ComponentExtractor.extract(MEGATOWER)
        for slot in ("fork", "shock", "drivetrain", "brakes", "wheels", "dropper"):
            assert getattr(build, slot), slot

    def test_word_boundaries_prefer_specific_name(self):
        build = ComponentExtractor.extract("Brakes are SRAM Code RSC, fresh bleed")
        assert build.brakes == "SRAM Code RSC"


class TestValuation:
    def test_aluminium_spelling_is_not_valued_as_carbon(self):
        alu = estimate_frame_value("Santa Cruz", year=2022, material="Aluminium")
        carbon = estimate_frame_value("Santa Cruz", year=2022, material="Carbon")
        assert alu < carbon * 0.6

    def test_missing_parts_are_imputed_on_complete_bikes(self):
        build = ComponentExtractor.extract("Stock bike, rides well.")
        bike = BuildValuator.valuate(build, brand="Giant", year=2020,
                                     material="Aluminium", category="Trail Bikes")
        frame = BuildValuator.valuate(build, brand="Giant", year=2020,
                                      material="Aluminium", category="Trail Frames")
        assert bike.imputed_count == 5
        assert frame.imputed_count == 0
        assert bike.total_reconstructed_value > frame.total_reconstructed_value

    def test_reconstructed_value_is_realistic(self):
        value = score(4200)["valuation"]["total_reconstructed"]
        assert 3500 < value < 7000


class TestDealScore:
    def test_price_drives_the_score(self):
        cheap, fair, steep = score(4200), score(6500), score(9500)
        assert cheap["deal_score"] > fair["deal_score"] > steep["deal_score"]
        assert cheap["deal_score"] - steep["deal_score"] >= 15

    def test_decals_in_bike_category_are_capped(self):
        r = score(45, title="Santacruz Nomad - Decals by InvisiFrame",
                  description="Selling custom decals (stickers) for Nomad")
        assert r["not_a_bike"] is True
        assert r["deal_score"] <= 10

    def test_not_a_bike_only_applies_to_bike_categories(self):
        assert not looks_like_not_a_bike("Fork decals", "", 40, "Single Crown Forks")
        assert looks_like_not_a_bike("WTB: medium Nomad", "", 0, "Enduro Bikes")
        assert not looks_like_not_a_bike("2021 Nomad", "", 4000, "Enduro Bikes")


class TestFreshness:
    NOW = datetime(2026, 10, 17, 12, tzinfo=timezone.utc)

    def test_absolute_dates_are_parsed(self):
        assert calc_freshness_score("Oct 17, 2026", now=self.NOW) >= 85
        assert calc_freshness_score("Oct 12, 2026", now=self.NOW) == 55
        assert calc_freshness_score("Jan 2, 2026", now=self.NOW) == 10

    def test_relative_dates_still_work(self):
        assert calc_freshness_score("3 hours ago") == 100
        assert calc_freshness_score("2 days ago") == 70
