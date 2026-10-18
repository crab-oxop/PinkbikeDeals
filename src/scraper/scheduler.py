"""
Scraper orchestrator — ties together HTTP client, parser, DB, and categories.

Implements the three-tier scraping strategy:
  Tier 1: Initial Harvest (full marketplace, all pages, all categories)
  Tier 2: Deep Refresh (daily, skip known-unchanged listings)
  Tier 3: Hot Scan (every 10-15 min, first few pages only)
"""

import asyncio
import json
import logging
from datetime import datetime, timezone

from src.config import Config
from src.constants import CONDITION_SCORES
from src.database.db import Database
from src.scraper.categories import CategoryManager
from src.scraper.client import AsyncHTTPClient
from src.scraper.parser import PinkbikeParser, ListingSummary, normalize_price_to_cad
from src.scoring.deal_scorer import DealScorer
from src.utils.title_parser import TitleParser

logger = logging.getLogger(__name__)


def utcnow():
    return datetime.now(timezone.utc)


class Scraper:
    """
    Main scraper orchestrator.

    Usage:
        config = Config()
        scraper = Scraper(config)
        await scraper.hot_scan()           # Quick scan of newest listings
        await scraper.harvest(max_pages=5)  # Controlled harvest
    """

    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.db = Database(self.config.database.path)
        self.db.init_db()
        self.categories = CategoryManager(self.config)
        self.title_parser = TitleParser()
        self._stopped = False

    def stop(self):
        self._stopped = True

    async def hot_scan(self, categories: list[str] = None):
        """
        Tier 3: Quick scan of newest listings.
        Checks first N pages of each category for new listings.
        """
        cat_list = categories or [c["key"] for c in self.categories.active_categories]
        max_pages = self.config.scraper.hot_scan_pages
        scan_type = "hot_scan"

        log_id = self.db.start_scrape_log(scan_type, cat_list)
        total_new = 0
        total_found = 0
        total_pages = 0
        errors = 0

        logger.info(f"Starting hot scan: {len(cat_list)} categories, "
                     f"{max_pages} pages each")

        async with AsyncHTTPClient(self.config) as client:
            for cat_key in cat_list:
                if self._stopped:
                    break

                cat_name = self.categories.get_category_name(cat_key)
                new, found, pages, errs = await self._scrape_category(
                    client, cat_key, cat_name,
                    max_pages=max_pages,
                    fetch_details=True,
                )
                total_new += new
                total_found += found
                total_pages += pages
                errors += errs

            logger.info(f"Hot scan complete. {client.get_stats_summary()}")

        self.db.update_scrape_log(
            log_id,
            completed_at=utcnow(),
            pages_scraped=total_pages,
            listings_found=total_found,
            listings_new=total_new,
            errors=errors,
            status="completed",
        )

        return {"new": total_new, "found": total_found,
                "pages": total_pages, "errors": errors}

    async def harvest(self, categories: list[str] = None,
                      max_pages: int = None):
        """
        Tier 1: Full marketplace harvest.
        Crawls all pages of all categories.
        """
        cat_list = categories or [c["key"] for c in self.categories.active_categories]
        scan_type = "harvest"

        log_id = self.db.start_scrape_log(scan_type, cat_list)
        total_new = 0
        total_found = 0
        total_pages = 0
        errors = 0

        logger.info(f"Starting harvest: {len(cat_list)} categories"
                     + (f", max {max_pages} pages each" if max_pages else ", all pages"))

        async with AsyncHTTPClient(self.config) as client:
            for cat_key in cat_list:
                if self._stopped:
                    break

                cat_name = self.categories.get_category_name(cat_key)
                new, found, pages, errs = await self._scrape_category(
                    client, cat_key, cat_name,
                    max_pages=max_pages,
                    fetch_details=True,
                )
                total_new += new
                total_found += found
                total_pages += pages
                errors += errs

                logger.info(f"  [{cat_name}] +{new} new, {found} total, "
                             f"{pages} pages, {errs} errors")

            logger.info(f"Harvest complete. {client.get_stats_summary()}")

        self.db.update_scrape_log(
            log_id,
            completed_at=utcnow(),
            pages_scraped=total_pages,
            listings_found=total_found,
            listings_new=total_new,
            errors=errors,
            status="completed",
        )

        return {"new": total_new, "found": total_found,
                "pages": total_pages, "errors": errors}

    async def deep_refresh(self, categories: list[str] = None):
        """
        Tier 2: Daily deep refresh.
        Crawls all pages but only fetches detail pages for new/changed listings.
        """
        # Same as harvest but with smart detail-page skipping
        return await self.harvest(categories=categories, max_pages=None)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _scrape_category(
        self,
        client: AsyncHTTPClient,
        category_key: str,
        category_name: str,
        max_pages: int = None,
        fetch_details: bool = True,
    ) -> tuple[int, int, int, int]:
        """
        Scrape one category.

        Returns: (new_listings, total_found, pages_scraped, errors)
        """
        new_count = 0
        found_count = 0
        pages_scraped = 0
        error_count = 0
        page = 1

        while True:
            if self._stopped:
                break
            if max_pages and page > max_pages:
                break

            url = self.categories.build_search_url(category_key, page=page)

            try:
                response = await client.get(url)
                html = response.text
            except Exception as e:
                logger.error(f"Failed to fetch {url}: {e}")
                error_count += 1
                # If it's a block/forbidden, stop this category
                if "403" in str(e):
                    logger.error(f"Blocked on {category_name}. Stopping category.")
                    break
                # Otherwise try next page
                if error_count >= 3:
                    logger.error(f"Too many errors on {category_name}. Stopping.")
                    break
                page += 1
                continue

            # Parse search results
            summaries = PinkbikeParser.parse_search_page(html, category_name)
            pages_scraped += 1

            if not summaries:
                # No listings found — either end of category or parser issue
                logger.debug(f"No listings on page {page} of {category_name}. "
                             "End of category.")
                break

            found_count += len(summaries)

            # Process each listing
            for summary in summaries:
                if self._stopped:
                    break

                try:
                    was_new = await self._process_listing(
                        client, summary, category_name, fetch_details
                    )
                    if was_new:
                        new_count += 1
                except Exception as e:
                    logger.warning(f"Error processing listing {summary.pinkbike_id}: {e}")
                    error_count += 1

            # Check if there are more pages
            if not PinkbikeParser.has_next_page(html) and len(summaries) < 20:
                break

            page += 1

        return new_count, found_count, pages_scraped, error_count

    async def _process_listing(
        self,
        client: AsyncHTTPClient,
        summary: ListingSummary,
        category_name: str,
        fetch_details: bool,
    ) -> bool:
        """
        Process a single listing from search results.

        Returns True if this was a new listing.
        """
        existing = self.db.get_listing_by_pinkbike_id(summary.pinkbike_id)

        # Decide if we need the detail page
        need_detail = False
        if existing is None:
            need_detail = True
        elif (summary.price > 0 and existing.price
              and abs(summary.price - existing.price) > 0.01):
            need_detail = True  # Price changed
        elif existing.description is None or existing.description == "":
            need_detail = True  # Never fetched details

        # Parse title
        parsed = self.title_parser.parse(summary.title)

        # Build listing data from summary
        listing_data = {
            "pinkbike_id": summary.pinkbike_id,
            "title": summary.title,
            "original_price": summary.price,
            "currency": summary.currency,
            "price": normalize_price_to_cad(summary.price, summary.currency),
            "category": category_name,
            "condition": summary.condition,
            "condition_score": CONDITION_SCORES.get(summary.condition),
            "seller_location": summary.seller_location,
            "url": summary.url,
            "is_boosted": summary.is_boosted,
            "brand": parsed.brand,
            "model": parsed.model,
            "year": parsed.year,
            "frame_size": parsed.frame_size,
        }

        # Fetch detail page if needed and allowed
        if need_detail and fetch_details:
            detail_url = self.categories.build_detail_url(summary.pinkbike_id)
            try:
                resp = await client.get(detail_url)
                detail = PinkbikeParser.parse_detail_page(
                    resp.text, summary.pinkbike_id
                )
                if detail:
                    # Merge detail data (detail page has more info)
                    listing_data.update({
                        "description": detail.description,
                        "photo_urls": json.dumps(detail.photo_urls),
                        "seller_username": detail.seller_username,
                        "seller_rating": detail.seller_rating,
                        "seller_country": detail.seller_country,
                        "seller_region": detail.seller_region,
                        "seller_city": detail.seller_city,
                        "frame_size": detail.frame_size or parsed.frame_size,
                        "wheel_size": detail.wheel_size,
                        "material": detail.material,
                        "front_travel": detail.front_travel,
                        "rear_travel": detail.rear_travel,
                        "date_posted": detail.date_posted,
                        "is_sold": detail.is_sold,
                        "views": detail.views,
                        "last_detail_fetch": utcnow(),
                    })
                    # Override condition if detail page has it
                    if detail.condition:
                        listing_data["condition"] = detail.condition
                        listing_data["condition_score"] = CONDITION_SCORES.get(
                            detail.condition
                        )
            except Exception as e:
                logger.debug(f"Couldn't fetch detail for {summary.pinkbike_id}: {e}")
                # Still save summary-only data

        # --- Phase 2: Score the listing ---
        try:
            score_result = DealScorer.score_listing(
                description=listing_data.get("description", ""),
                title=listing_data.get("title", ""),
                price=listing_data.get("price", 0.0),
                condition=listing_data.get("condition", "Good"),
                brand=listing_data.get("brand", ""),
                model=listing_data.get("model", ""),
                year=listing_data.get("year"),
                material=listing_data.get("material", ""),
                category=category_name,
                seller_username=listing_data.get("seller_username", ""),
                seller_rating=listing_data.get("seller_rating"),
                is_boosted=listing_data.get("is_boosted", False),
                date_posted=listing_data.get("date_posted", ""),
            )
            listing_data["deal_score"] = score_result["deal_score"]
            listing_data["frame_value_estimate"] = score_result["valuation"]["frame_value"]
            listing_data["component_value_estimate"] = score_result["valuation"]["component_used"]
            listing_data["total_reconstructed_value"] = score_result["valuation"]["total_reconstructed"]
            listing_data["ai_build_confidence"] = score_result["valuation"]["confidence"]
            listing_data["ai_analyzed_at"] = utcnow()

            logger.debug(
                f"Scored {summary.pinkbike_id}: {score_result['deal_score']:.1f} "
                f"(recon=${score_result['valuation']['total_reconstructed']:.0f}, "
                f"conf={score_result['valuation']['confidence']:.2f})"
            )
        except Exception as e:
            logger.warning(f"Scoring failed for {summary.pinkbike_id}: {e}")

        # Upsert to database
        _, is_new = self.db.upsert_listing(listing_data)

        if is_new:
            logger.debug(f"NEW: {summary.title[:60]} — ${listing_data['price']:.0f} CAD "
                         f"[score={listing_data.get('deal_score', 0):.1f}]")

        return is_new
