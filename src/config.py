"""
PinkbikeDeals configuration.

Centralized settings for scraping, database, and scoring.
Phase 1: Python-only config. Phase 2+ will add TOML file support.
"""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path


# Project root = parent of src/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Platform-aware data directory for the database
if sys.platform == "win32":
    _DATA_DIR = Path(os.environ.get(
        "LOCALAPPDATA",
        Path.home() / "AppData" / "Local"
    )) / "PinkbikeDeals"
else:
    _DATA_DIR = Path("/tmp")

_DATA_DIR.mkdir(parents=True, exist_ok=True)
_DEFAULT_DB_PATH = str(_DATA_DIR / "pinkbike_deals.db")


@dataclass
class ScraperConfig:
    """Scraping-related settings."""
    base_url: str = "https://www.pinkbike.com"
    buysell_list_url: str = "https://www.pinkbike.com/buysell/list/"
    buysell_detail_url: str = "https://www.pinkbike.com/buysell/{listing_id}/"

    # Rate limiting
    max_concurrent_requests: int = 3
    min_request_delay: float = 1.0      # seconds between requests
    max_request_delay: float = 2.0      # upper jitter bound
    request_timeout: int = 30           # seconds

    # Request budget
    daily_request_limit: int = 8000
    hot_scan_limit: int = 200           # per individual hot scan
    deep_refresh_limit: int = 5000      # per daily deep refresh

    # Retry
    max_retries: int = 3
    backoff_base: float = 2.0           # exponential backoff multiplier

    # Scan settings
    hot_scan_pages: int = 5             # pages per category on hot scan
    hot_scan_interval_minutes: int = 15
    deep_refresh_hour: int = 3          # 3 AM local time

    # Identity
    user_agent: str = "PinkbikeDeals/0.1 (personal-use bike deal finder)"

    # Freshness
    stale_listing_days: int = 90
    detail_refresh_days: int = 7        # re-fetch detail page after N days


@dataclass
class DatabaseConfig:
    """Database settings."""
    path: str = _DEFAULT_DB_PATH
    price_history_retention_days: int = 365


@dataclass
class Config:
    """Top-level app configuration."""
    app_name: str = "PinkbikeDeals"
    version: str = "0.3.0"
    currency: str = "CAD"               # display currency

    scraper: ScraperConfig = field(default_factory=ScraperConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)

    @property
    def project_root(self) -> Path:
        return PROJECT_ROOT
