"""
Title parser — extracts brand, model, year, and spec level from listing titles.

Examples:
    "2023 Santa Cruz Megatower CC X01"  →  brand="Santa Cruz", model="Megatower", year=2023
    "YT Capra 29 CF Pro 2022 Large"    →  brand="YT", model="Capra 29 CF Pro", year=2022
    "Specialized Enduro Expert 2024"    →  brand="Specialized", model="Enduro Expert", year=2024
"""

import re
from dataclasses import dataclass
from typing import Optional

from src.constants import KNOWN_BRANDS


@dataclass
class ParsedTitle:
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    spec_level: str = ""          # e.g., "CC X01", "Expert", "CF Pro"
    frame_size: Optional[str] = None
    confidence: float = 0.0       # 0.0–1.0

    @property
    def display(self) -> str:
        parts = []
        if self.year:
            parts.append(str(self.year))
        if self.brand:
            parts.append(self.brand)
        if self.model:
            parts.append(self.model)
        if self.spec_level:
            parts.append(self.spec_level)
        return " ".join(parts) if parts else "Unknown"


# Frame size patterns
_SIZE_PATTERN = re.compile(
    r'\b(XXL|XL|XS|SM|MD|LG|'
    r'X-?Small|X-?Large|Extra\s*Small|Extra\s*Large|'
    r'Small|Medium|Large|Med)\b',
    re.IGNORECASE
)

_SIZE_NORMALIZE = {
    "xs": "XS", "x-small": "XS", "xsmall": "XS", "extra small": "XS",
    "sm": "S", "small": "S", "s": "S",
    "md": "M", "medium": "M", "med": "M", "m": "M",
    "lg": "L", "large": "L", "l": "L",
    "xl": "XL", "x-large": "XL", "xlarge": "XL", "extra large": "XL",
    "xxl": "XXL",
}

# Year pattern: 4-digit number between 1995 and 2030
_YEAR_PATTERN = re.compile(r'\b(19[9][5-9]|20[0-2][0-9]|2030)\b')

# Common spec-level keywords (groupsets, trim levels)
_SPEC_KEYWORDS = [
    # SRAM groupsets
    "XX1 AXS", "XX1", "XO1 AXS", "XO1", "X01 AXS", "X01",
    "GX AXS", "GX Eagle", "GX", "NX Eagle", "NX", "SX Eagle", "SX",
    # Shimano groupsets
    "XTR", "XT", "SLX", "Deore",
    # Trim levels
    "Factory", "Performance Elite", "Performance",
    "Ultimate", "Select+", "Select",
    "CC", "C", "Expert", "Comp", "Elite", "Pro", "Race",
    "CF Pro", "CF",
    # Wheel size sometimes in title
    "29er", "29", "27.5", "Mullet",
]

# Words to strip from model extraction (noise)
_NOISE_WORDS = {
    "for", "sale", "selling", "my", "the", "a", "an", "with",
    "frame", "only", "complete", "bike", "mountain",
    "brand", "new", "used", "mint", "like",
    "size", "color", "colour",
}


class TitleParser:
    """Parse Pinkbike listing titles into structured data."""

    @staticmethod
    def parse(title: str) -> ParsedTitle:
        if not title or not title.strip():
            return ParsedTitle(confidence=0.0)

        result = ParsedTitle()
        remaining = title.strip()
        confidence = 0.2  # Base confidence for having a title at all

        # --- Extract year ---
        year_match = _YEAR_PATTERN.search(remaining)
        if year_match:
            result.year = int(year_match.group(1))
            remaining = remaining[:year_match.start()] + remaining[year_match.end():]
            confidence += 0.2

        # --- Extract frame size ---
        size_match = _SIZE_PATTERN.search(remaining)
        if size_match:
            raw_size = size_match.group(1).lower().strip()
            result.frame_size = _SIZE_NORMALIZE.get(raw_size, raw_size.upper())
            remaining = remaining[:size_match.start()] + remaining[size_match.end():]

        # --- Extract brand (longest match first) ---
        remaining_upper = remaining.upper()
        for brand in KNOWN_BRANDS:
            brand_upper = brand.upper()
            idx = remaining_upper.find(brand_upper)
            if idx != -1:
                result.brand = brand
                # Remove brand from remaining text
                remaining = remaining[:idx] + remaining[idx + len(brand):]
                remaining_upper = remaining.upper()
                confidence += 0.25
                break

        # --- Extract spec level keywords ---
        spec_parts = []
        for kw in _SPEC_KEYWORDS:
            pattern = re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
            match = pattern.search(remaining)
            if match:
                spec_parts.append(kw)
                remaining = remaining[:match.start()] + remaining[match.end():]

        if spec_parts:
            result.spec_level = " ".join(spec_parts)
            confidence += 0.1

        # --- What's left is the model name ---
        # Clean up remaining text
        model_text = remaining.strip()
        # Remove noise words and punctuation
        model_text = re.sub(r'[^\w\s-]', ' ', model_text)
        words = model_text.split()
        model_words = [w for w in words
                       if w.lower() not in _NOISE_WORDS and len(w) > 1]

        if model_words:
            result.model = " ".join(model_words).strip()
            if result.model:
                confidence += 0.25

        # Cap confidence
        result.confidence = min(1.0, confidence)

        return result

    @staticmethod
    def extract_brand(title: str) -> Optional[str]:
        """Quick extraction of just the brand name."""
        if not title:
            return None
        title_upper = title.upper()
        for brand in KNOWN_BRANDS:
            if brand.upper() in title_upper:
                return brand
        return None
