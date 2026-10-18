"""
Component extractor — pulls bike parts from listing descriptions using
pattern matching and fuzzy search. No API key required.

Strategy:
  1. Normalize text (lowercase, clean punctuation)
  2. For each component slot (fork, shock, drivetrain, etc.):
     a. Try keyword-triggered extraction ("fork:", "Fork -", etc.)
     b. Try known product name matching against our value DB
     c. Fuzzy match with thefuzz for close-but-not-exact names
  3. Return structured dict of all identified components
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

from thefuzz import fuzz, process as fuzz_process

from src.scoring.component_values import ALL_COMPONENT_VALUES, COMPONENT_TIERS

logger = logging.getLogger(__name__)


@dataclass
class ExtractedBuild:
    """Result of component extraction from a listing description."""
    fork: Optional[str] = None
    shock: Optional[str] = None
    drivetrain: Optional[str] = None
    brakes: Optional[str] = None
    wheels: Optional[str] = None
    dropper: Optional[str] = None
    tires_front: Optional[str] = None
    tires_rear: Optional[str] = None
    handlebars: Optional[str] = None
    stem: Optional[str] = None
    saddle: Optional[str] = None
    pedals: Optional[str] = None
    cranks: Optional[str] = None
    upgrades_from_stock: list = field(default_factory=list)
    noted_issues: list = field(default_factory=list)
    confidence: float = 0.0  # 0.0 to 1.0

    @property
    def identified_count(self) -> int:
        """Number of component slots that were identified."""
        slots = ["fork", "shock", "drivetrain", "brakes", "wheels",
                 "dropper", "tires_front", "handlebars", "stem",
                 "saddle", "pedals", "cranks"]
        return sum(1 for s in slots if getattr(self, s) is not None)

    @property
    def total_slots(self) -> int:
        return 12

    def to_dict(self) -> dict:
        return {
            "fork": self.fork,
            "shock": self.shock,
            "drivetrain": self.drivetrain,
            "brakes": self.brakes,
            "wheels": self.wheels,
            "dropper": self.dropper,
            "tires_front": self.tires_front,
            "tires_rear": self.tires_rear,
            "handlebars": self.handlebars,
            "stem": self.stem,
            "saddle": self.saddle,
            "pedals": self.pedals,
            "cranks": self.cranks,
            "upgrades_from_stock": self.upgrades_from_stock,
            "noted_issues": self.noted_issues,
            "confidence": self.confidence,
        }


# ---------------------------------------------------------------------------
# Slot-specific keyword patterns
# ---------------------------------------------------------------------------

# Each slot has trigger keywords that appear before the component name
# in typical listing descriptions. Order matters — more specific first.
SLOT_KEYWORDS = {
    "fork": [
        r"fork\s*[:;\-–—]\s*",
        r"front\s+suspension\s*[:;\-–—]\s*",
        r"forks?\s*[:;\-–—]\s*",
    ],
    "shock": [
        r"(?:rear\s+)?shock\s*[:;\-–—]\s*",
        r"rear\s+suspension\s*[:;\-–—]\s*",
        r"rear\s*[:;\-–—]\s*",
    ],
    "drivetrain": [
        r"drivetrain\s*[:;\-–—]\s*",
        r"groupset\s*[:;\-–—]\s*",
        r"group\s*[:;\-–—]\s*",
        r"shifting\s*[:;\-–—]\s*",
        r"derailleur\s*[:;\-–—]\s*",
        r"rear\s+derailleur\s*[:;\-–—]\s*",
        r"shifter[s]?\s*[:;\-–—]\s*",
    ],
    "brakes": [
        r"brakes?\s*[:;\-–—]\s*",
        r"brake\s+set\s*[:;\-–—]\s*",
        r"stopping\s*[:;\-–—]\s*",
    ],
    "wheels": [
        r"wheels?\s*[:;\-–—]\s*",
        r"wheelset\s*[:;\-–—]\s*",
        r"rims?\s*[:;\-–—]\s*",
        r"hubs?\s*[:;\-–—]\s*",
    ],
    "dropper": [
        r"dropper\s*(?:post)?\s*[:;\-–—]\s*",
        r"dropper\s+seatpost\s*[:;\-–—]\s*",
        r"seat\s*post\s*[:;\-–—]\s*",
    ],
    "tires_front": [
        r"tires?\s*[:;\-–—]\s*",
        r"front\s+tire\s*[:;\-–—]\s*",
        r"tyres?\s*[:;\-–—]\s*",
        r"rubber\s*[:;\-–—]\s*",
    ],
    "handlebars": [
        r"(?:handle)?bars?\s*[:;\-–—]\s*",
        r"handlebar\s*[:;\-–—]\s*",
        r"cockpit\s*[:;\-–—]\s*",
    ],
    "stem": [
        r"stem\s*[:;\-–—]\s*",
    ],
    "saddle": [
        r"saddle\s*[:;\-–—]\s*",
        r"seat\s*[:;\-–—]\s*",
    ],
    "pedals": [
        r"pedals?\s*[:;\-–—]\s*",
    ],
    "cranks": [
        r"cranks?\s*[:;\-–—]\s*",
        r"crankset\s*[:;\-–—]\s*",
        r"crank\s*set\s*[:;\-–—]\s*",
        r"chainset\s*[:;\-–—]\s*",
    ],
}

# Patterns that signal upgrades and issues
UPGRADE_PATTERNS = [
    r"upgrade[ds]?\s*(?:from\s+stock|from\s+original|include)?[:;\-–—]?\s*(.+)",
    r"(?:swapped|replaced|changed)\s+(?:the\s+)?(?:stock\s+)?(.+?)\s+(?:to|for|with)\s+(.+)",
    r"aftermarket\s*[:;\-–—]\s*(.+)",
]

ISSUE_PATTERNS = [
    r"(?:issue|problem|damage|scratch|dent|crack|worn|wear|needs?|replace)\w*\s*[:;\-–—]?\s*(.+)",
    r"(?:cosmetic|minor|small)\s+(?:damage|scratch|dent|mark|chip)\w*\s*[:;\-–—]?\s*(.+)?",
    r"chain\s+(?:is\s+)?(?:stretched|worn|needs?\s+replacing)",
    r"(?:brake\s+)?pads?\s+(?:are\s+)?(?:worn|low|need)",
    r"(?:tire|tyre)s?\s+(?:are\s+)?(?:worn|bald|need|low)",
]


# ---------------------------------------------------------------------------
# Build flat lookup of all known component names for each slot
# ---------------------------------------------------------------------------

# Brand prefixes that sellers often leave off ("Float X2 Factory" for
# "Fox Float X2 Factory"). Used to build brand-stripped aliases.
_BRAND_PREFIXES = [
    "Fox", "RockShox", "SRAM", "Shimano", "Maxxis", "OneUp", "Race Face",
    "Deity", "ENVE", "DT Swiss", "Industry Nine", "Hope", "Magura", "Hayes",
    "TRP", "Cane Creek", "PNW", "Bike Yoke", "Chromag", "SDG", "WTB",
    "Schwalbe", "Continental", "Ohlins", "EXT", "PUSH", "DVO", "Manitou",
    "Marzocchi", "Formula", "Crankbrothers", "Stan's", "We Are One", "Zipp",
    "e*thirteen", "Santa Cruz", "Specialized", "Bontrager", "Roval",
]
# Trailing hub designators on wheel names ("Reserve 30 i9" -> "Reserve 30")
_HUB_SUFFIXES = {"i9", "dt", "hope", "350", "240", "onyx", "hydra", "sl"}


def _aliases_for(name: str, slot: str) -> list[str]:
    """Shorter forms of a component name that sellers commonly write."""
    aliases = []
    base = name.split("|")[0].strip()
    if base != name:
        aliases.append(base)
    for brand in _BRAND_PREFIXES:
        if base.lower().startswith(brand.lower() + " "):
            aliases.append(base[len(brand):].strip())
            break
    if slot == "wheels":
        for a in [base] + aliases:
            toks = a.split()
            if len(toks) >= 3 and toks[-1].lower() in _HUB_SUFFIXES:
                aliases.append(" ".join(toks[:-1]))
    # Only keep aliases specific enough not to match random words
    return [a for a in aliases if len(a.split()) >= 2 and len(a) >= 6]


def _build_name_index():
    """
    Create a searchable index per slot: a list of names to search for,
    and a map from each searchable name (incl. aliases) to its canonical
    database name.
    """
    index, canonical = {}, {}
    for slot, value_dict in ALL_COMPONENT_VALUES.items():
        names = list(value_dict.keys())
        if slot in COMPONENT_TIERS:
            for tier_names in COMPONENT_TIERS[slot].values():
                for name in tier_names:
                    if name not in names:
                        names.append(name)
        cmap = {n.lower(): n for n in names}
        for n in names:
            for a in _aliases_for(n, slot):
                key = a.lower()
                if key in cmap:
                    # Ambiguous alias: keep the cheaper (conservative) match
                    prev = cmap[key]
                    if value_dict.get(n, 0) and value_dict.get(n, 0) < value_dict.get(prev, float("inf")):
                        cmap[key] = n
                else:
                    cmap[key] = n
        index[slot] = names
        canonical[slot] = cmap
    return index, canonical


_NAME_INDEX, _CANONICAL = _build_name_index()


# ---------------------------------------------------------------------------
# ComponentExtractor class
# ---------------------------------------------------------------------------

class ComponentExtractor:
    """
    Extract bike components from a listing description using
    pattern matching and fuzzy search.
    """

    # Minimum fuzzy match score to accept (out of 100)
    FUZZY_THRESHOLD = 75
    # Minimum score for a "confident" match
    FUZZY_CONFIDENT = 88

    @classmethod
    def extract(cls, description: str, title: str = "",
                category: str = "") -> ExtractedBuild:
        """
        Main entry point. Extracts components from description text.

        Args:
            description: Full listing description from detail page
            title: Listing title (provides extra context)
            category: Category name (for context)

        Returns:
            ExtractedBuild with all identified components
        """
        if not description:
            return ExtractedBuild(confidence=0.0)

        build = ExtractedBuild()
        text = cls._normalize(description)
        title_norm = cls._normalize(title)
        full_text = f"{title_norm}\n{text}"

        # Phase 1: Keyword-triggered extraction
        # Looks for patterns like "Fork: Fox 38 Factory" or "- Fork - RockShox ZEB"
        for slot, patterns in SLOT_KEYWORDS.items():
            if getattr(build, slot) is not None:
                continue  # Already found
            value = cls._keyword_extract(text, patterns, slot)
            if value:
                setattr(build, slot, value)

        # Phase 2: Direct name matching
        # Scan the full text for known component names
        for slot in ALL_COMPONENT_VALUES:
            attr = slot
            if slot == "tires":
                attr = "tires_front"
            if getattr(build, attr) is not None:
                continue
            match = cls._direct_name_match(full_text, slot)
            if match:
                setattr(build, attr, match)

        # Phase 3: Handle tire front/rear split
        if build.tires_front and not build.tires_rear:
            # Try to find a second tire
            build.tires_rear = cls._find_second_tire(text, build.tires_front)

        # Phase 4: Extract upgrades and issues
        build.upgrades_from_stock = cls._extract_upgrades(text)
        build.noted_issues = cls._extract_issues(text)

        # Phase 5: Calculate confidence
        build.confidence = cls._calculate_confidence(build, text)

        logger.debug(f"Extracted {build.identified_count}/{build.total_slots} "
                     f"components (confidence={build.confidence:.2f})")

        return build

    # ------------------------------------------------------------------
    # Text normalization
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize(text: str) -> str:
        """Clean up text for matching."""
        if not text:
            return ""
        # Normalize unicode dashes and quotes
        text = text.replace("–", "-").replace("—", "-")
        text = text.replace("'", "'").replace(""", '"').replace(""", '"')
        # Collapse multiple spaces/newlines
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    # ------------------------------------------------------------------
    # Keyword-triggered extraction
    # ------------------------------------------------------------------

    @classmethod
    def _keyword_extract(cls, text: str, patterns: list[str],
                         slot: str) -> Optional[str]:
        """
        Look for "keyword: value" patterns and match the value
        against known components.
        """
        text_lower = text.lower()

        for pattern in patterns:
            regex = re.compile(pattern, re.IGNORECASE)
            match = regex.search(text)
            if not match:
                continue

            # Extract the text after the keyword (up to next line/bullet/keyword)
            start = match.end()
            # Find the end of this value (next bullet, newline-ish, or another keyword)
            rest = text[start:start + 120]
            # Trim at common delimiters
            end_match = re.search(r'[|\n]|(?:[-•]\s+\w)', rest)
            if end_match:
                rest = rest[:end_match.start()]
            value = rest.strip().rstrip(".,;")

            if len(value) < 3:
                continue

            # Try to match against known names for this slot
            matched = cls._fuzzy_match_slot(value, slot)
            if matched:
                return matched

            # If no fuzzy match but looks like a real component, return cleaned
            if len(value) > 5 and len(value) < 80:
                return cls._clean_value(value)

        return None

    # ------------------------------------------------------------------
    # Direct name matching
    # ------------------------------------------------------------------

    @classmethod
    def _direct_name_match(cls, text: str, slot: str) -> Optional[str]:
        """
        Scan text for known component names (or their common short forms)
        for a given slot. Matches on word boundaries and prefers the
        longest, most specific name. Returns the canonical database name.
        """
        if slot not in _CANONICAL:
            return None

        text_lower = text.lower()
        best_match = None
        best_len = 0

        for searchable, canon in _CANONICAL[slot].items():
            if len(searchable) <= best_len:
                continue
            if re.search(r'(?<![\w])' + re.escape(searchable) + r'(?![\w])', text_lower):
                best_match = canon
                best_len = len(searchable)

        return best_match

    # ------------------------------------------------------------------
    # Fuzzy matching
    # ------------------------------------------------------------------

    @classmethod
    def _fuzzy_match_slot(cls, value: str, slot: str) -> Optional[str]:
        """
        Fuzzy match a value against known component names for a slot.
        Uses thefuzz for approximate string matching.
        """
        if slot not in _NAME_INDEX or not _NAME_INDEX[slot]:
            return None

        candidates = _NAME_INDEX[slot]
        if not candidates:
            return None

        result = fuzz_process.extractOne(
            value, candidates,
            scorer=fuzz.token_sort_ratio,
            score_cutoff=cls.FUZZY_THRESHOLD,
        )

        if result:
            match_name = result[0]
            match_score = result[1] if len(result) > 1 else 0
            logger.debug(f"Fuzzy match [{slot}]: '{value}' → '{match_name}' ({match_score})")
            return match_name

        return None

    # ------------------------------------------------------------------
    # Tire handling
    # ------------------------------------------------------------------

    @classmethod
    def _find_second_tire(cls, text: str, first_tire: str) -> Optional[str]:
        """If we found one tire, try to find a different one for front/rear."""
        text_lower = text.lower()
        first_lower = first_tire.lower()

        for name in _NAME_INDEX.get("tires", []):
            if name.lower() != first_lower and name.lower() in text_lower:
                return name

        # Check for "front/rear" pattern: "Assegai front / DHR2 rear"
        combo = re.search(
            r'([\w\s]+?)\s*(?:front|f)\s*[/&,]\s*([\w\s]+?)\s*(?:rear|r)',
            text, re.IGNORECASE
        )
        if combo:
            rear_text = combo.group(2).strip()
            matched = cls._fuzzy_match_slot(rear_text, "tires")
            if matched and matched.lower() != first_lower:
                return matched

        return None

    # ------------------------------------------------------------------
    # Upgrades and issues extraction
    # ------------------------------------------------------------------

    @classmethod
    def _extract_upgrades(cls, text: str) -> list[str]:
        """Extract any mentioned upgrades from stock."""
        upgrades = []
        text_lower = text.lower()

        # Look for upgrade section
        upgrade_section = re.search(
            r'upgrade[sd]?\s*(?:from\s+stock|include|list)?[:;\-–—]?\s*(.{10,300})',
            text_lower
        )
        if upgrade_section:
            section = upgrade_section.group(1)
            # Split by bullets, dashes, newlines
            items = re.split(r'[-•\n|]', section)
            for item in items:
                item = item.strip()
                if len(item) > 5 and len(item) < 150:
                    upgrades.append(item)

        # Look for "swapped X for Y" patterns
        for pattern in [
            r"(?:swapped|replaced|changed|switched)\s+(?:the\s+)?(?:stock\s+)?(.{5,80}?)\s+(?:to|for|with)\s+(.{5,80}?)(?:\.|$|,)",
            r"(?:went\s+from|upgraded\s+from)\s+(.{5,60}?)\s+to\s+(.{5,60}?)(?:\.|$|,)",
        ]:
            for match in re.finditer(pattern, text_lower):
                old_part = match.group(1).strip()
                new_part = match.group(2).strip()
                upgrades.append(f"{old_part} → {new_part}")

        return upgrades[:10]  # Cap at 10

    @classmethod
    def _extract_issues(cls, text: str) -> list[str]:
        """Extract any noted problems or issues."""
        issues = []
        text_lower = text.lower()

        for pattern in ISSUE_PATTERNS:
            for match in re.finditer(pattern, text_lower):
                issue = match.group(0).strip()
                if len(issue) > 5 and len(issue) < 200:
                    issues.append(issue)

        # Deduplicate similar issues
        unique = []
        for issue in issues:
            if not any(fuzz.ratio(issue, existing) > 80 for existing in unique):
                unique.append(issue)

        return unique[:5]  # Cap at 5

    # ------------------------------------------------------------------
    # Confidence calculation
    # ------------------------------------------------------------------

    @classmethod
    def _calculate_confidence(cls, build: ExtractedBuild, text: str) -> float:
        """
        Estimate how confident we are in the extraction.

        Factors:
        - How many components were identified
        - Whether the "big 5" (fork, shock, drivetrain, brakes, wheels) are present
        - Whether the description looks like it lists components at all
        """
        identified = build.identified_count
        total = build.total_slots

        # Base: ratio of identified components
        base = identified / total

        # Bonus for big 5
        big5 = ["fork", "shock", "drivetrain", "brakes", "wheels"]
        big5_found = sum(1 for s in big5 if getattr(build, s) is not None)
        big5_bonus = big5_found * 0.06  # Up to 0.30

        # Penalty if description is very short (less info to work with)
        text_len = len(text)
        if text_len < 50:
            length_factor = 0.3
        elif text_len < 150:
            length_factor = 0.6
        elif text_len < 300:
            length_factor = 0.8
        else:
            length_factor = 1.0

        # Does the text look like a component list?
        list_indicators = sum(1 for pattern in [
            r'fork\s*:', r'shock\s*:', r'drivetrain\s*:',
            r'brake\s*:', r'wheel\s*:', r'build\s*:',
            r'spec\s*:', r'component',
        ] if re.search(pattern, text, re.IGNORECASE))
        list_bonus = min(0.15, list_indicators * 0.03)

        confidence = min(1.0, (base + big5_bonus + list_bonus) * length_factor)
        return round(confidence, 2)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_value(value: str) -> str:
        """Clean an extracted value string."""
        # Remove common noise
        value = re.sub(r'\(.*?\)', '', value)  # Remove parentheticals
        value = re.sub(r'\s+', ' ', value)
        value = value.strip(" -–—:;,.")
        # Cap length
        if len(value) > 60:
            value = value[:60].rsplit(" ", 1)[0]
        return value
