"""Tests for the title parser."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils.title_parser import TitleParser


def test_full_title():
    result = TitleParser.parse("2023 Santa Cruz Megatower CC X01")
    assert result.brand == "Santa Cruz"
    assert result.year == 2023
    assert result.model is not None
    assert "Megatower" in result.model
    assert result.confidence > 0.5


def test_year_at_end():
    result = TitleParser.parse("YT Capra 29 CF Pro 2022 Large")
    assert result.brand == "YT"
    assert result.year == 2022
    assert result.frame_size == "L"
    assert result.confidence > 0.5


def test_specialized():
    result = TitleParser.parse("Specialized Enduro Expert 2024")
    assert result.brand == "Specialized"
    assert result.year == 2024


def test_no_year():
    result = TitleParser.parse("Trek Fuel EX 8 Large")
    assert result.brand == "Trek"
    assert result.year is None
    assert result.frame_size == "L"


def test_unknown_brand():
    result = TitleParser.parse("2023 SomeRandomBrand MX500")
    assert result.brand is None
    assert result.year == 2023
    assert result.confidence < 0.7


def test_empty_title():
    result = TitleParser.parse("")
    assert result.confidence == 0.0
    assert result.brand is None


def test_extract_brand_only():
    assert TitleParser.extract_brand("Santa Cruz Nomad") == "Santa Cruz"
    assert TitleParser.extract_brand("random text") is None


def test_rocky_mountain():
    """Multi-word brand name."""
    result = TitleParser.parse("2022 Rocky Mountain Altitude C70 Large")
    assert result.brand == "Rocky Mountain"
    assert result.year == 2022


def test_frame_sizes():
    for size_str, expected in [("Medium", "M"), ("XL", "XL"), ("small", "S")]:
        result = TitleParser.parse(f"2023 Trek Fuel {size_str}")
        assert result.frame_size == expected, f"Expected {expected} for '{size_str}'"


if __name__ == "__main__":
    for name, func in list(globals().items()):
        if name.startswith("test_") and callable(func):
            try:
                func()
                print(f"  ✓ {name}")
            except AssertionError as e:
                print(f"  ✗ {name}: {e}")
    print("\nDone.")
