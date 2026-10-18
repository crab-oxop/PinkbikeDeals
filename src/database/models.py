"""
SQLAlchemy ORM models for PinkbikeDeals.

Matches the schema defined in docs/PROJECT_OUTLINE.md.
Phase 1 tables: Listing, PriceHistory, MarketData, ScrapeLog.
Phase 2 adds: ListingComponent, ListingIssue (AI analysis).
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text,
    Index, UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship


def utcnow():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pinkbike_id = Column(String, unique=True, nullable=False, index=True)

    # Core info
    title = Column(String, nullable=False)
    price = Column(Float)                      # normalized to display currency
    original_price = Column(Float)             # price as listed
    currency = Column(String(3))               # original currency code

    # Category
    category = Column(String)
    category_id = Column(Integer)

    # Condition
    condition = Column(String)
    condition_score = Column(Float)

    # Seller
    seller_location = Column(String)
    seller_country = Column(String)
    seller_region = Column(String)
    seller_city = Column(String)
    seller_username = Column(String)
    seller_rating = Column(Float)

    # Specs
    frame_size = Column(String)
    wheel_size = Column(String)
    material = Column(String)
    front_travel = Column(Integer)
    rear_travel = Column(Integer)

    # Parsed from title
    brand = Column(String, index=True)
    model = Column(String)
    year = Column(Integer, index=True)

    # Content
    description = Column(Text)
    photo_urls = Column(Text)                  # JSON array of URLs
    url = Column(String, unique=True)

    # Timestamps
    date_posted = Column(String)  # Relative date string from Pinkbike e.g. "3 days ago"
    date_scraped = Column(DateTime, default=utcnow)
    last_seen = Column(DateTime, default=utcnow)
    last_detail_fetch = Column(DateTime)

    # Status
    is_sold = Column(Boolean, default=False)
    is_boosted = Column(Boolean, default=False)
    views = Column(Integer)

    # Scoring (Phase 1: basic, Phase 2: AI-enhanced)
    deal_score = Column(Float, default=0.0)
    market_value_estimate = Column(Float)

    # AI fields (populated in Phase 2)
    component_value_estimate = Column(Float)
    frame_value_estimate = Column(Float)
    total_reconstructed_value = Column(Float)
    ai_build_confidence = Column(Float)
    ai_analyzed_at = Column(DateTime)

    # Relationships
    price_history = relationship("PriceHistory", back_populates="listing",
                                 cascade="all, delete-orphan")

    # Indexes for common queries
    __table_args__ = (
        Index("ix_listings_category_price", "category", "price"),
        Index("ix_listings_brand_year", "brand", "year"),
        Index("ix_listings_deal_score", "deal_score"),
        Index("ix_listings_date_posted", "date_posted"),
        Index("ix_listings_last_seen", "last_seen"),
    )

    def __repr__(self):
        return (f"<Listing(id={self.id}, pinkbike_id={self.pinkbike_id}, "
                f"title='{self.title[:40]}...', price={self.price})>")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False, index=True)
    price = Column(Float, nullable=False)
    original_price = Column(Float)
    currency = Column(String(3))
    recorded_at = Column(DateTime, default=utcnow)

    listing = relationship("Listing", back_populates="price_history")


class MarketData(Base):
    """Aggregated pricing intelligence per brand/model/year/condition."""
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    brand = Column(String)
    model = Column(String)
    year = Column(Integer)
    category = Column(String)
    condition = Column(String)
    avg_price = Column(Float)
    median_price = Column(Float)
    min_price = Column(Float)
    max_price = Column(Float)
    sample_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=utcnow)

    __table_args__ = (
        Index("ix_market_brand_model_year", "brand", "model", "year"),
    )


class ScrapeLog(Base):
    """Track each scraping run for monitoring and debugging."""
    __tablename__ = "scrape_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_type = Column(String)               # "harvest", "deep_refresh", "hot_scan"
    started_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime)
    categories_scraped = Column(Text)        # JSON array
    pages_scraped = Column(Integer, default=0)
    listings_found = Column(Integer, default=0)
    listings_new = Column(Integer, default=0)
    listings_updated = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    error_details = Column(Text)
    status = Column(String, default="running")  # running / completed / failed
