"""
Category management and URL building for Pinkbike BuySell scraping.
"""

from src.constants import CATEGORIES, DEFAULT_SCAN_CATEGORIES
from src.config import Config


class CategoryManager:
    """Manages which categories to scan and builds URLs."""

    def __init__(self, config: Config = None):
        self.config = config or Config()
        self._active_categories = DEFAULT_SCAN_CATEGORIES

    @property
    def active_categories(self) -> list[dict]:
        """Get list of active category dicts with id and name."""
        return [
            {"key": key, **CATEGORIES[key]}
            for key in self._active_categories
            if key in CATEGORIES
        ]

    def set_categories(self, category_keys: list[str]):
        """Override which categories to scan."""
        valid = [k for k in category_keys if k in CATEGORIES]
        if valid:
            self._active_categories = valid

    def build_search_url(self, category_key: str, page: int = 1,
                         region: int = None) -> str:
        """
        Build a BuySell search URL for a category and page.

        Args:
            category_key: Key from CATEGORIES dict (e.g., "enduro_bikes")
            page: Page number (1-indexed)
            region: Optional region code

        Returns:
            Full URL string
        """
        cat = CATEGORIES.get(category_key)
        if not cat:
            raise ValueError(f"Unknown category: {category_key}")

        url = f"{self.config.scraper.buysell_list_url}?category={cat['id']}"
        if page > 1:
            url += f"&page={page}"
        if region is not None:
            url += f"&region={region}"
        return url

    def build_detail_url(self, pinkbike_id: str) -> str:
        """Build URL for an individual listing page."""
        return self.config.scraper.buysell_detail_url.format(listing_id=pinkbike_id)

    def get_category_name(self, category_key: str) -> str:
        """Get display name for a category."""
        cat = CATEGORIES.get(category_key)
        return cat["name"] if cat else category_key

    def get_category_by_id(self, category_id: int) -> dict | None:
        """Look up a category by its Pinkbike numeric ID."""
        for key, cat in CATEGORIES.items():
            if cat["id"] == category_id:
                return {"key": key, **cat}
        return None
