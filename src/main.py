#!/usr/bin/env python3
"""
PinkbikeDeals CLI — Phase 1 entry point.

Usage:
    python -m src.main scan --category enduro_bikes --pages 3
    python -m src.main harvest --pages 5
    python -m src.main top --count 20
    python -m src.main cheapest --count 20
    python -m src.main newest --count 10
    python -m src.main stats
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime

from src.config import Config
from src.constants import CATEGORIES
from src.database.db import Database
from src.scraper.scheduler import Scraper
from src.scoring.deal_scorer import DealScorer


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_listing_row(listing, idx: int) -> str:
    """Format a single listing for CLI display."""
    brand = listing.brand or "?"
    model = listing.model or ""
    year = listing.year or "?"
    condition = (listing.condition or "?")[:4]
    location = (listing.seller_location or "?")[:20]
    category = (listing.category or "?")[:15]

    title_display = f"{year} {brand} {model}".strip()[:40]
    price_display = f"${listing.price:,.0f}" if listing.price else "$?"

    score = listing.deal_score or 0

    return (
        f"  {idx:>3}. [{score:>5.1f}] {price_display:>8}  "
        f"{title_display:<40} {condition:<5} {location:<20} {category}"
    )


def print_listings(listings, header: str = "Listings"):
    """Print a table of listings."""
    if not listings:
        print(f"\n  No listings found.\n")
        return

    print(f"\n  {'─' * 110}")
    print(f"  {header} ({len(listings)} results)")
    print(f"  {'─' * 110}")
    print(f"  {'#':>5}  {'Score':>5}  {'Price':>8}  {'Title':<40} {'Cond':<5} "
          f"{'Location':<20} Category")
    print(f"  {'─' * 110}")

    for i, listing in enumerate(listings, 1):
        print(format_listing_row(listing, i))

    print(f"  {'─' * 110}\n")


def print_stats(stats: dict):
    """Print database statistics."""
    print(f"\n  {'═' * 50}")
    print(f"  PinkbikeDeals Database Stats")
    print(f"  {'═' * 50}")
    print(f"  Total listings:  {stats['total_listings']:,}")
    print(f"  Active listings: {stats['active_listings']:,}")
    print(f"  Sold listings:   {stats['sold_listings']:,}")
    print(f"  Avg price:       ${stats['avg_price']:,.0f} CAD")
    print()

    if stats["categories"]:
        print(f"  Categories:")
        for cat, count in sorted(stats["categories"].items(),
                                  key=lambda x: -x[1]):
            print(f"    {cat:<30} {count:>6} listings")

    print(f"  {'═' * 50}\n")


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------

async def cmd_scan(args, config: Config):
    """Run a quick scan (hot scan) on specific categories."""
    if args.pages:
        config.scraper.hot_scan_pages = args.pages
    scraper = Scraper(config)
    categories = [args.category] if args.category else None
    result = await scraper.hot_scan(categories=categories)
    print(f"\n  Scan complete: {result['new']} new listings, "
          f"{result['found']} total found, "
          f"{result['pages']} pages scraped, "
          f"{result['errors']} errors\n")


async def cmd_harvest(args, config: Config):
    """Run a full harvest."""
    scraper = Scraper(config)
    categories = [args.category] if args.category else None
    max_pages = args.pages if args.pages else None
    result = await scraper.harvest(categories=categories, max_pages=max_pages)
    print(f"\n  Harvest complete: {result['new']} new listings, "
          f"{result['found']} total found, "
          f"{result['pages']} pages scraped, "
          f"{result['errors']} errors\n")


def cmd_top(args, config: Config):
    """Show top deals by deal score."""
    db = Database(config.database.path)
    db.init_db()
    listings = db.get_top_deals(
        limit=args.count,
        category=args.category,
    )
    print_listings(listings, header="Top Deals (by score)")


def cmd_cheapest(args, config: Config):
    """Show cheapest listings."""
    db = Database(config.database.path)
    db.init_db()
    listings = db.get_cheapest(
        limit=args.count,
        category=args.category,
    )
    print_listings(listings, header="Cheapest Listings")


def cmd_newest(args, config: Config):
    """Show most recently scraped listings."""
    db = Database(config.database.path)
    db.init_db()
    listings = db.get_newest(limit=args.count)
    print_listings(listings, header="Newest Listings")


def cmd_stats(args, config: Config):
    """Show database statistics."""
    db = Database(config.database.path)
    db.init_db()
    stats = db.get_stats()
    print_stats(stats)


def cmd_rescore(args, config: Config):
    """Re-score all existing listings using the Phase 2 scoring engine."""
    from datetime import timezone
    db = Database(config.database.path)
    db.init_db()
    listings = db.get_all_active_listings()

    if not listings:
        print("\n  No active listings to score.\n")
        return

    print(f"\n  Scoring {len(listings)} active listings...")

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

            if args.verbose or scored <= 5:
                print(f"  [{scored:>3}] {listing.title[:50]:50} "
                      f"Score: {result['deal_score']:5.1f}  "
                      f"Recon: ${result['valuation']['total_reconstructed']:>8,.0f}  "
                      f"Conf: {result['valuation']['confidence']:.2f}")
        except Exception as e:
            errors += 1
            if args.verbose:
                print(f"  ERROR: {listing.pinkbike_id} — {e}")

    print(f"\n  Rescoring complete: {scored} scored, {errors} errors\n")

    # Show top 10 deals
    top = db.get_top_deals(limit=10)
    if top:
        print_listings(top, header="Top 10 Deals After Rescoring")


def cmd_categories(args, config: Config):
    """List available categories."""
    print(f"\n  Available categories:")
    print(f"  {'─' * 50}")
    for key, cat in sorted(CATEGORIES.items()):
        print(f"    {key:<25} (id={cat['id']:<3})  {cat['name']}")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    # Quiet down noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def main():
    parser = argparse.ArgumentParser(
        description="PinkbikeDeals — Used Bike Deal Finder (Phase 1 CLI)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable debug logging")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # scan
    p_scan = subparsers.add_parser("scan", help="Quick scan (hot scan) for new listings")
    p_scan.add_argument("-c", "--category", type=str, help="Category key to scan")
    p_scan.add_argument("-p", "--pages", type=int, default=3,
                        help="Max pages per category (default: 3)")

    # harvest
    p_harvest = subparsers.add_parser("harvest", help="Full marketplace harvest")
    p_harvest.add_argument("-c", "--category", type=str, help="Category key")
    p_harvest.add_argument("-p", "--pages", type=int, default=None,
                           help="Max pages per category (default: all)")

    # top
    p_top = subparsers.add_parser("top", help="Show top deals by score")
    p_top.add_argument("-n", "--count", type=int, default=20, help="Number to show")
    p_top.add_argument("-c", "--category", type=str, help="Filter by category")

    # cheapest
    p_cheap = subparsers.add_parser("cheapest", help="Show cheapest listings")
    p_cheap.add_argument("-n", "--count", type=int, default=20, help="Number to show")
    p_cheap.add_argument("-c", "--category", type=str, help="Filter by category")

    # newest
    p_new = subparsers.add_parser("newest", help="Show newest listings")
    p_new.add_argument("-n", "--count", type=int, default=20, help="Number to show")

    # stats
    subparsers.add_parser("stats", help="Show database statistics")

    # rescore
    p_rescore = subparsers.add_parser("rescore", help="Re-score all listings with Phase 2 engine")
    p_rescore.add_argument("-v", "--verbose", action="store_true",
                           help="Show all scoring results")

    # categories
    subparsers.add_parser("categories", help="List available categories")

    # gui
    subparsers.add_parser("gui", help="Launch the desktop GUI")

    args = parser.parse_args()
    setup_logging(args.verbose)
    config = Config()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Route to command
    if args.command == "scan":
        asyncio.run(cmd_scan(args, config))
    elif args.command == "harvest":
        asyncio.run(cmd_harvest(args, config))
    elif args.command == "top":
        cmd_top(args, config)
    elif args.command == "cheapest":
        cmd_cheapest(args, config)
    elif args.command == "newest":
        cmd_newest(args, config)
    elif args.command == "stats":
        cmd_stats(args, config)
    elif args.command == "rescore":
        cmd_rescore(args, config)
    elif args.command == "categories":
        cmd_categories(args, config)
    elif args.command == "gui":
        from src.gui.app import main as gui_main
        gui_main()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
