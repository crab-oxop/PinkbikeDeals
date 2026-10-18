"""
Background scraping worker thread for non-blocking GUI.

Uses QThread to run the scraper without freezing the UI.
Emits signals for progress updates, new listings, and completion.
"""

import asyncio
import logging
from datetime import datetime, timezone

from PyQt6.QtCore import QThread, pyqtSignal

from src.config import Config
from src.scraper.scheduler import Scraper

logger = logging.getLogger(__name__)


class ScrapeWorker(QThread):
    """
    Background worker that runs scraping in a separate thread.

    Signals:
        progress(str)         — Status message for the UI
        listing_found(dict)   — Emitted for each new listing found
        scan_complete(dict)   — Emitted when scan finishes with summary stats
        error(str)            — Emitted on errors
    """
    progress = pyqtSignal(str)
    listing_found = pyqtSignal(dict)
    scan_complete = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, config: Config = None, parent=None):
        super().__init__(parent)
        self.config = config or Config()
        self._categories = None
        self._max_pages = None
        self._scan_type = "hot_scan"
        self._scraper = None

    def configure(self, scan_type: str = "hot_scan",
                  categories: list[str] = None, max_pages: int = None):
        """Configure the scan before starting."""
        self._scan_type = scan_type
        self._categories = categories
        self._max_pages = max_pages

    def stop_scan(self):
        """Request the scraper to stop gracefully."""
        if self._scraper:
            self._scraper.stop()

    def run(self):
        """Execute the scraping operation."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            self._scraper = Scraper(self.config)
            self.progress.emit(f"Starting {self._scan_type}...")

            if self._scan_type == "hot_scan":
                if self._max_pages:
                    self.config.scraper.hot_scan_pages = self._max_pages
                result = loop.run_until_complete(
                    self._scraper.hot_scan(categories=self._categories)
                )
            elif self._scan_type == "harvest":
                result = loop.run_until_complete(
                    self._scraper.harvest(
                        categories=self._categories,
                        max_pages=self._max_pages,
                    )
                )
            else:
                result = loop.run_until_complete(
                    self._scraper.hot_scan(categories=self._categories)
                )

            result["scan_type"] = self._scan_type
            result["completed_at"] = datetime.now(timezone.utc).isoformat()
            self.scan_complete.emit(result)
            self.progress.emit(
                f"Scan complete: {result['new']} new, "
                f"{result['found']} found, {result['errors']} errors"
            )

        except Exception as e:
            logger.exception("Scan worker error")
            self.error.emit(str(e))
        finally:
            loop.close()
            self._scraper = None


class RescoreWorker(QThread):
    """
    Background worker that re-scores all listings.
    """
    progress = pyqtSignal(str)
    rescore_complete = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, config: Config = None, parent=None):
        super().__init__(parent)
        self.config = config or Config()

    def run(self):
        try:
            from src.database.db import Database
            from src.scoring.deal_scorer import DealScorer

            db = Database(self.config.database.path)
            db.init_db()
            listings = db.get_all_active_listings()

            if not listings:
                self.progress.emit("No active listings to score.")
                self.rescore_complete.emit({"scored": 0, "errors": 0})
                return

            self.progress.emit(f"Scoring {len(listings)} listings...")
            scored = 0
            errors = 0

            for listing in listings:
                try:
                    result = DealScorer.score_listing(
                        description=listing.description or "",
                        title=listing.title or "",
                        price=listing.price or 0.0,
                        condition=listing.condition or "Good",
                        brand=listing.brand or "",
                        model=listing.model or "",
                        year=listing.year,
                        material=listing.material or "",
                        category=listing.category or "",
                        seller_username=listing.seller_username or "",
                        seller_rating=listing.seller_rating,
                        is_boosted=listing.is_boosted or False,
                        date_posted=listing.date_posted or "",
                    )
                    db.update_listing_scores(listing.pinkbike_id, {
                        "deal_score": result["deal_score"],
                        "frame_value_estimate": result["valuation"]["frame_value"],
                        "component_value_estimate": result["valuation"]["component_used"],
                        "total_reconstructed_value": result["valuation"]["total_reconstructed"],
                        "ai_build_confidence": result["valuation"]["confidence"],
                        "ai_analyzed_at": datetime.now(timezone.utc),
                    })
                    scored += 1
                except Exception:
                    errors += 1

            self.rescore_complete.emit({"scored": scored, "errors": errors})
            self.progress.emit(f"Rescoring complete: {scored} scored, {errors} errors")

        except Exception as e:
            logger.exception("Rescore worker error")
            self.error.emit(str(e))
