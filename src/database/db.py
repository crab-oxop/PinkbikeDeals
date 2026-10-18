"""
Database manager for PinkbikeDeals.

Handles connection, initialization, and common operations.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from .models import Base, Listing, PriceHistory, MarketData, ScrapeLog

logger = logging.getLogger(__name__)


def utcnow():
    return datetime.now(timezone.utc)


class Database:
    """SQLite database manager."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            from src.config import Config
            db_path = Config().database.path

        self.db_path = db_path
        self.engine = None
        self._SessionLocal = None

    def init_db(self):
        """Create database file and all tables."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            echo=False,
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(self.engine)
        self._SessionLocal = sessionmaker(bind=self.engine)
        logger.info(f"Database initialized at {self.db_path}")
        return self.engine

    def get_session(self) -> Session:
        """Get a new database session."""
        if self._SessionLocal is None:
            self.init_db()
        return self._SessionLocal()

    # ------------------------------------------------------------------
    # Listing operations
    # ------------------------------------------------------------------

    def get_listing_by_pinkbike_id(self, pinkbike_id: str) -> Optional[Listing]:
        """Fetch a listing by its Pinkbike ID."""
        with self.get_session() as session:
            return session.query(Listing).filter(
                Listing.pinkbike_id == pinkbike_id
            ).first()

    def upsert_listing(self, data: dict) -> tuple[Listing, bool]:
        """
        Insert or update a listing.

        Args:
            data: dict of listing fields (must include 'pinkbike_id')

        Returns:
            (listing, is_new) — the Listing object and whether it was newly created
        """
        with self.get_session() as session:
            existing = session.query(Listing).filter(
                Listing.pinkbike_id == data["pinkbike_id"]
            ).first()

            if existing:
                # Check for price change → log to history
                if (data.get("price") is not None
                        and existing.price is not None
                        and abs(data["price"] - existing.price) > 0.01):
                    history = PriceHistory(
                        listing_id=existing.id,
                        price=existing.price,
                        original_price=existing.original_price,
                        currency=existing.currency,
                        recorded_at=utcnow(),
                    )
                    session.add(history)
                    logger.debug(f"Price change for {data['pinkbike_id']}: "
                                 f"{existing.price} → {data.get('price')}")

                # Update fields
                for key, value in data.items():
                    if key != "id" and hasattr(existing, key) and value is not None:
                        setattr(existing, key, value)
                existing.last_seen = utcnow()

                session.commit()
                session.refresh(existing)
                return existing, False
            else:
                # New listing
                data.setdefault("date_scraped", utcnow())
                data.setdefault("last_seen", utcnow())
                listing = Listing(**{
                    k: v for k, v in data.items()
                    if hasattr(Listing, k) and v is not None
                })
                session.add(listing)
                session.commit()
                session.refresh(listing)
                return listing, True

    def update_last_seen(self, pinkbike_id: str):
        """Update the last_seen timestamp for a listing."""
        with self.get_session() as session:
            listing = session.query(Listing).filter(
                Listing.pinkbike_id == pinkbike_id
            ).first()
            if listing:
                listing.last_seen = utcnow()
                session.commit()

    def get_top_deals(self, limit: int = 20, category: str = None,
                      min_price: float = None, max_price: float = None) -> list[Listing]:
        """Get top listings sorted by deal score (highest first)."""
        with self.get_session() as session:
            query = session.query(Listing).filter(
                Listing.is_sold == False,
                Listing.price > 0,
            )
            if category:
                query = query.filter(Listing.category == category)
            if min_price is not None:
                query = query.filter(Listing.price >= min_price)
            if max_price is not None:
                query = query.filter(Listing.price <= max_price)

            return query.order_by(Listing.deal_score.desc()).limit(limit).all()

    def get_cheapest(self, limit: int = 20, category: str = None) -> list[Listing]:
        """Get cheapest active listings."""
        with self.get_session() as session:
            query = session.query(Listing).filter(
                Listing.is_sold == False,
                Listing.price > 0,
            )
            if category:
                query = query.filter(Listing.category == category)
            return query.order_by(Listing.price.asc()).limit(limit).all()

    def get_newest(self, limit: int = 20) -> list[Listing]:
        """Get most recently scraped listings."""
        with self.get_session() as session:
            return (session.query(Listing)
                    .filter(Listing.is_sold == False)
                    .order_by(Listing.date_scraped.desc())
                    .limit(limit).all())

    def get_all_active_listings(self) -> list[Listing]:
        """Get all active (unsold) listings for rescoring."""
        with self.get_session() as session:
            listings = session.query(Listing).filter(
                Listing.is_sold == False,
                Listing.price > 0,
            ).all()
            # Eagerly access all columns so objects survive session close
            for l in listings:
                session.expunge(l)
            return listings

    def get_all_listings_as_dicts(self) -> list[dict]:
        """Get all active listings as plain dicts (safe outside session)."""
        with self.get_session() as session:
            listings = session.query(Listing).filter(
                Listing.is_sold == False,
                Listing.price > 0,
            ).all()
            results = []
            for l in listings:
                results.append({
                    "pinkbike_id": l.pinkbike_id,
                    "title": l.title,
                    "price": l.price,
                    "original_price": l.original_price,
                    "currency": l.currency,
                    "category": l.category,
                    "condition": l.condition,
                    "condition_score": l.condition_score,
                    "seller_location": l.seller_location,
                    "seller_username": l.seller_username,
                    "seller_rating": l.seller_rating,
                    "frame_size": l.frame_size,
                    "wheel_size": l.wheel_size,
                    "material": l.material,
                    "front_travel": l.front_travel,
                    "rear_travel": l.rear_travel,
                    "brand": l.brand,
                    "model": l.model,
                    "year": l.year,
                    "description": l.description,
                    "url": l.url,
                    "date_posted": l.date_posted,
                    "is_sold": l.is_sold,
                    "is_boosted": l.is_boosted,
                    "views": l.views,
                    "deal_score": l.deal_score,
                    "total_reconstructed_value": l.total_reconstructed_value,
                    "component_value_estimate": l.component_value_estimate,
                    "frame_value_estimate": l.frame_value_estimate,
                    "ai_build_confidence": l.ai_build_confidence,
                })
            return results

    def update_listing_scores(self, pinkbike_id: str, scores: dict):
        """Update scoring fields for a listing."""
        with self.get_session() as session:
            listing = session.query(Listing).filter(
                Listing.pinkbike_id == pinkbike_id
            ).first()
            if listing:
                for key, value in scores.items():
                    if hasattr(listing, key) and value is not None:
                        setattr(listing, key, value)
                session.commit()

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> dict:
        """Get database statistics."""
        with self.get_session() as session:
            total = session.query(func.count(Listing.id)).scalar() or 0
            active = session.query(func.count(Listing.id)).filter(
                Listing.is_sold == False
            ).scalar() or 0
            sold = total - active
            categories = session.query(
                Listing.category, func.count(Listing.id)
            ).group_by(Listing.category).all()

            avg_price = session.query(func.avg(Listing.price)).filter(
                Listing.is_sold == False, Listing.price > 0
            ).scalar()

            return {
                "total_listings": total,
                "active_listings": active,
                "sold_listings": sold,
                "categories": {cat: count for cat, count in categories if cat},
                "avg_price": round(avg_price, 2) if avg_price else 0,
            }

    # ------------------------------------------------------------------
    # Scrape log
    # ------------------------------------------------------------------

    def start_scrape_log(self, scan_type: str, categories: list[str]) -> int:
        """Create a scrape log entry and return its ID."""
        with self.get_session() as session:
            log = ScrapeLog(
                scan_type=scan_type,
                categories_scraped=json.dumps(categories),
                status="running",
            )
            session.add(log)
            session.commit()
            session.refresh(log)
            return log.id

    def update_scrape_log(self, log_id: int, **kwargs):
        """Update a scrape log entry."""
        with self.get_session() as session:
            log = session.query(ScrapeLog).get(log_id)
            if log:
                for key, value in kwargs.items():
                    if hasattr(log, key):
                        setattr(log, key, value)
                session.commit()

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    def reset_db(self):
        """Drop and recreate all tables. USE ONLY FOR TESTING."""
        if self.engine is None:
            self.init_db()
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        logger.warning("Database reset — all data deleted")
