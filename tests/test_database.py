"""Tests for the database layer."""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database.db import Database
from src.database.models import Listing

TEST_DB = "/tmp/test_pinkbike.db"


def get_test_db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    db = Database(TEST_DB)
    db.init_db()
    return db


def test_create_db():
    db = get_test_db()
    assert os.path.exists(TEST_DB)
    stats = db.get_stats()
    assert stats["total_listings"] == 0
    os.remove(TEST_DB)


def test_insert_listing():
    db = get_test_db()
    listing, is_new = db.upsert_listing({
        "pinkbike_id": "12345",
        "title": "2023 Santa Cruz Megatower CC X01",
        "price": 4500.0,
        "original_price": 4500.0,
        "currency": "CAD",
        "category": "Enduro Bikes",
        "condition": "Excellent",
        "brand": "Santa Cruz",
        "model": "Megatower",
        "year": 2023,
        "url": "https://www.pinkbike.com/buysell/12345/",
    })
    assert is_new is True
    assert listing.pinkbike_id == "12345"
    assert listing.brand == "Santa Cruz"
    os.remove(TEST_DB)


def test_upsert_updates():
    db = get_test_db()
    # Insert
    db.upsert_listing({
        "pinkbike_id": "12345",
        "title": "Test Bike",
        "price": 4500.0,
        "currency": "CAD",
        "url": "https://www.pinkbike.com/buysell/12345/",
    })
    # Update with new price
    listing, is_new = db.upsert_listing({
        "pinkbike_id": "12345",
        "title": "Test Bike",
        "price": 4000.0,
        "currency": "CAD",
    })
    assert is_new is False
    assert listing.price == 4000.0
    os.remove(TEST_DB)


def test_price_history_on_change():
    db = get_test_db()
    # Insert
    db.upsert_listing({
        "pinkbike_id": "12345",
        "title": "Test Bike",
        "price": 4500.0,
        "original_price": 4500.0,
        "currency": "CAD",
        "url": "https://www.pinkbike.com/buysell/12345/",
    })
    # Update with different price → should log history
    db.upsert_listing({
        "pinkbike_id": "12345",
        "title": "Test Bike",
        "price": 4000.0,
        "original_price": 4000.0,
        "currency": "CAD",
    })

    from src.database.models import PriceHistory
    with db.get_session() as session:
        history = session.query(PriceHistory).all()
        assert len(history) == 1
        assert history[0].price == 4500.0  # old price logged

    os.remove(TEST_DB)


def test_get_cheapest():
    db = get_test_db()
    for i, price in enumerate([5000, 2000, 8000, 1500, 3000]):
        db.upsert_listing({
            "pinkbike_id": str(10000 + i),
            "title": f"Bike {i}",
            "price": price,
            "currency": "CAD",
            "url": f"https://www.pinkbike.com/buysell/{10000 + i}/",
        })
    cheapest = db.get_cheapest(limit=3)
    assert len(cheapest) == 3
    assert cheapest[0].price == 1500
    assert cheapest[1].price == 2000
    assert cheapest[2].price == 3000
    os.remove(TEST_DB)


def test_stats():
    db = get_test_db()
    for i in range(5):
        db.upsert_listing({
            "pinkbike_id": str(20000 + i),
            "title": f"Bike {i}",
            "price": 3000 + i * 500,
            "currency": "CAD",
            "category": "Enduro Bikes",
            "url": f"https://www.pinkbike.com/buysell/{20000 + i}/",
        })
    stats = db.get_stats()
    assert stats["total_listings"] == 5
    assert stats["active_listings"] == 5
    assert stats["avg_price"] > 0
    os.remove(TEST_DB)


def test_lookup_by_pinkbike_id():
    db = get_test_db()
    db.upsert_listing({
        "pinkbike_id": "99999",
        "title": "Test",
        "price": 1000,
        "currency": "CAD",
        "url": "https://www.pinkbike.com/buysell/99999/",
    })
    found = db.get_listing_by_pinkbike_id("99999")
    assert found is not None
    assert found.pinkbike_id == "99999"

    not_found = db.get_listing_by_pinkbike_id("00000")
    assert not_found is None
    os.remove(TEST_DB)


if __name__ == "__main__":
    for name, func in list(globals().items()):
        if name.startswith("test_") and callable(func):
            try:
                func()
                print(f"  ✓ {name}")
            except Exception as e:
                print(f"  ✗ {name}: {e}")
    print("\nDone.")
