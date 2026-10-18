"""Tests for the HTML parser — calibrated against real Pinkbike HTML (March 2026)."""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.scraper.parser import PinkbikeParser, parse_price, normalize_price_to_cad


# ---------------------------------------------------------------------------
# Price parsing tests
# ---------------------------------------------------------------------------

def test_parse_price_cad():
    price, currency = parse_price("$4,500 CAD")
    assert price == 4500.0
    assert currency == "CAD"


def test_parse_price_usd():
    price, currency = parse_price("$1,200 USD")
    assert price == 1200.0
    assert currency == "USD"


def test_parse_price_usd_no_comma():
    price, currency = parse_price("$3800 USD")
    assert price == 3800.0
    assert currency == "USD"


def test_parse_price_euro():
    price, currency = parse_price("€3,200")
    assert price == 3200.0
    assert currency == "EUR"


def test_parse_price_gbp():
    price, currency = parse_price("£900 GBP")
    assert price == 900.0
    assert currency == "GBP"


def test_parse_price_plain():
    price, currency = parse_price("$2500")
    assert price == 2500.0


def test_parse_price_empty():
    price, currency = parse_price("")
    assert price == 0.0


def test_normalize_to_cad():
    cad = normalize_price_to_cad(1000, "USD")
    assert cad > 1000  # USD→CAD should increase
    assert cad == 1350.0  # 1000 * 1.35


# ---------------------------------------------------------------------------
# Search page parser tests — using REAL Pinkbike bsitem structure
# ---------------------------------------------------------------------------

MOCK_BSITEM_HTML = """
<html>
<body class="page_buysell">
<div class="bsitem boosted" id="csid3849220">
  <table width="100%">
    <tr class="bsitem-table">
      <td style="padding-right:20px" valign="top" width="161">
        <ul class="uPhotoSmall">
          <li class="uImage">
            <a href="https://www.pinkbike.com/buysell/3849220/">
              <img alt="buysell photo" src="https://ep1.pinkbike.org/p3pb29000001/p3pb29000001.jpg"/>
            </a>
            <br/>
            <span class="fgrey">12 photos</span>
          </li>
        </ul>
      </td>
      <td valign="top">
        <span class="boosted_label">Boosted</span>
        <div class="bsitem-title" style="margin-bottom:5px;">
          <a href="https://www.pinkbike.com/buysell/3849220/" style="font-size: 18px;font-weight:bold;color:#000000">
            2023 Santa Cruz Megatower CC X01
          </a>
          <br/>
          Enduro Bikes
          <div class="itemdetail" style="margin-top: 5px;"><b>Condition :</b> Excellent - Lightly Ridden</div>
          <div class="itemdetail" style="margin-top: 5px;"><b>Frame Size :</b> L</div>
          <div class="itemdetail" style="margin-top: 5px;"><b>Wheel Size :</b> 29"</div>
          <div class="itemdetail" style="margin-top: 5px;"><b>Material :</b> Carbon Fiber</div>
          <div class="itemdetail" style="margin-top: 5px;"><b>Front Travel :</b> 170 mm</div>
          <div class="itemdetail" style="margin-top: 5px;"><b>Rear Travel :</b> 160 mm</div>
        </div>
        <table border="0" class="bsitem-details" width="100%">
          <tr>
            <td align="left" colspan="2">
              <img alt="flag" class="flag flag-41" height="13" src="https://es.pinkbike.org/sprt/f/0.png" width="20"/>
              Whistler, British Columbia, Canada
            </td>
          </tr>
          <tr>
            <td class="bsitem-price" colspan="2"><b>$4500 CAD</b></td>
          </tr>
          <tr>
            <td colspan="2" width="100%">
              <b>Seller:</b>
              <a href="https://www.pinkbike.com/u/shredder2026/buysell/">shredder2026</a>
            </td>
          </tr>
          <tr>
            <td class="bsitem-description" colspan="2">
              Selling my 2023 Megatower. Barely ridden, maybe 500km. Full X01 build.
              <p><a href="https://www.pinkbike.com/buysell/3849220/"><b>[Read More]</b></a></p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</div>

<div class="bsitem" id="csid3849221">
  <table width="100%">
    <tr class="bsitem-table">
      <td style="padding-right:20px" valign="top" width="161">
        <ul class="uPhotoSmall">
          <li class="uImage">
            <a href="https://www.pinkbike.com/buysell/3849221/">
              <img alt="buysell photo" src="https://ep1.pinkbike.org/p3pb29000002/p3pb29000002.jpg"/>
            </a>
            <br/>
            <span class="fgrey">5 photos</span>
          </li>
        </ul>
      </td>
      <td valign="top">
        <div class="bsitem-title" style="margin-bottom:5px;">
          <a href="https://www.pinkbike.com/buysell/3849221/" style="font-size: 18px;font-weight:bold;color:#000000">
            2022 Trek Fuel EX 8
          </a>
          <br/>
          Trail Bikes
          <div class="itemdetail" style="margin-top: 5px;"><b>Condition :</b> Good - Some Wear</div>
          <div class="itemdetail" style="margin-top: 5px;"><b>Frame Size :</b> M/L</div>
          <div class="itemdetail" style="margin-top: 5px;"><b>Wheel Size :</b> 29"</div>
          <div class="itemdetail" style="margin-top: 5px;"><b>Material :</b> Aluminum</div>
          <div class="itemdetail" style="margin-top: 5px;"><b>Front Travel :</b> 140 mm</div>
          <div class="itemdetail" style="margin-top: 5px;"><b>Rear Travel :</b> 130 mm</div>
        </div>
        <table border="0" class="bsitem-details" width="100%">
          <tr>
            <td align="left" colspan="2">
              <img alt="flag" class="flag flag-194" height="13" src="https://es.pinkbike.org/sprt/f/0.png" width="20"/>
              Denver, Colorado, United States
            </td>
          </tr>
          <tr>
            <td class="bsitem-price" colspan="2"><b>$2800 USD</b></td>
          </tr>
          <tr>
            <td colspan="2" width="100%">
              <b>Seller:</b>
              <a href="https://www.pinkbike.com/u/trailrider99/buysell/">trailrider99</a>
            </td>
          </tr>
          <tr>
            <td class="bsitem-description" colspan="2">
              Great trail bike, upgrading to full suspension enduro.
              <p><a href="https://www.pinkbike.com/buysell/3849221/"><b>[Read More]</b></a></p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</div>

<div class="paging-nav-c3">
  <table class="paging-container">
    <tr>
      <td class="pageNumbers">
        <ul class="paging-middle centertext">
          <li class="current-page"><a href="?page=1&category=2">1</a></li>
          <li><a href="?page=2&category=2" rel="next">2</a></li>
          <li><a href="?page=3&category=2">3</a></li>
          <li><a href="?page=150&category=2">150</a></li>
        </ul>
      </td>
      <td class="nowrap"><ul><li class="next-page"><a href="?page=2&category=2">Next Page</a></li></ul></td>
    </tr>
  </table>
</div>

</body>
</html>
"""


def test_search_page_parse():
    listings = PinkbikeParser.parse_search_page(MOCK_BSITEM_HTML, "Enduro Bikes")
    assert len(listings) == 2

    first = listings[0]
    assert first.pinkbike_id == "3849220"
    assert "Santa Cruz" in first.title
    assert first.price == 4500.0
    assert first.currency == "CAD"
    assert first.condition == "Excellent"
    assert first.url == "https://www.pinkbike.com/buysell/3849220/"
    assert first.is_boosted is True
    assert first.frame_size == "L"
    assert first.wheel_size == '29"'
    assert first.material == "Carbon Fiber"
    assert first.front_travel == 170
    assert first.rear_travel == 160
    assert first.photo_count == 12
    assert first.seller_username == "shredder2026"
    assert "Whistler" in first.seller_location
    assert "Megatower" in first.description_preview

    second = listings[1]
    assert second.pinkbike_id == "3849221"
    assert second.price == 2800.0
    assert second.currency == "USD"
    assert second.condition == "Good"
    assert second.is_boosted is False
    assert second.frame_size == "M/L"
    assert second.front_travel == 140
    assert second.seller_username == "trailrider99"


def test_search_page_empty():
    listings = PinkbikeParser.parse_search_page("<html><body></body></html>", "Test")
    assert len(listings) == 0


def test_pagination_has_next():
    assert PinkbikeParser.has_next_page(MOCK_BSITEM_HTML) is True


def test_pagination_total_pages():
    total = PinkbikeParser.get_total_pages(MOCK_BSITEM_HTML)
    assert total == 150


def test_pagination_no_next():
    html = '<html><body><div class="paging-nav-c3"><ul class="paging-middle"><li>1</li></ul></div></body></html>'
    assert PinkbikeParser.has_next_page(html) is False


# ---------------------------------------------------------------------------
# Fallback parser (finds links to /buysell/ID/)
# ---------------------------------------------------------------------------

MOCK_FALLBACK_HTML = """
<html><body>
<div class="unknown-structure">
    <a href="/buysell/9999901/">2024 Yeti SB160 T2 X01 AXS</a>
    <a href="/buysell/9999902/">2021 Ibis Ripmo V2 XT</a>
    <a href="/other/page/">Not a listing</a>
</div>
</body></html>
"""


def test_fallback_parse():
    listings = PinkbikeParser.parse_search_page(MOCK_FALLBACK_HTML, "Enduro")
    assert len(listings) == 2
    assert listings[0].pinkbike_id == "9999901"
    assert "Yeti" in listings[0].title


# ---------------------------------------------------------------------------
# Detail page parser tests — using REAL Pinkbike structure
# ---------------------------------------------------------------------------

MOCK_DETAIL_HTML = """
<html>
<head>
    <link rel="canonical" href="https://www.pinkbike.com/buysell/3849220/" />
</head>
<body class="page_buysell">
<h1 class="buysell-title">2023 Santa Cruz Megatower CC X01</h1>

<div class="buysell-container-left">
  <div class="buysell-images-container">
    <img src="https://ep1.pinkbike.org/p3pb29000001/p3pb29000001.jpg"/>
  </div>

  <div class="buysell-container buysell-status-banner">
    <div class="buysell-status-banner-title">Available as of 5 hours ago</div>
    <div class="buysell-status-banner-details">Posted: 3 days agoReposted: 5 hours agoViews: 142Watchers: 3</div>
  </div>

  <div class="buysell-container section-title">Item specifics</div>
  <div class="buysell-container detailsgrid">
    <div><b>Category:</b> Enduro Bikes</div>
    <div><b>Condition:</b> Excellent - Lightly Ridden</div>
    <div><b>Seller Type:</b> Private Seller</div>
    <div><b>Frame Size:</b> L</div>
    <div><b>Wheel Size:</b> 29"</div>
    <div><b>Material:</b> Carbon Fiber</div>
    <div><b>Front Travel:</b> 170 mm</div>
    <div><b>Rear Travel:</b> 160 mm</div>
  </div>

  <div class="buysell-container section-title">Item description from seller</div>
  <div class="description">
    Selling my 2023 Megatower. Barely ridden, maybe 500km.

    Build:
    - Fork: Fox 38 Factory 170mm
    - Shock: Fox Float X2 Factory
    - Drivetrain: SRAM XO1 Eagle AXS
    - Brakes: SRAM Code RSC 4-pot
    - Wheels: Reserve 30|HD i9 hubs
    - Dropper: OneUp 210mm
  </div>
</div>

<div class="buysell-container-right buysell-price">
  <div class="buysell-container buysell-price">$4,500 CAD</div>
</div>

<div class="buysell-container-right buysell-profileinfo">
  <div class="buysell-container" style="padding: 10px;">
    <a class="user-image-container" href="https://www.pinkbike.com/u/shredder2026/buysell/">
      <img alt="shredder2026 avatar" class="user-image-img" height="80" src="https://ep1.pinkbike.org/ph/hl0.jpg" width="80"/>
    </a>
    <a href="https://www.pinkbike.com/u/shredder2026/buysell/" rel="author" style="font-size: 18px;">
      shredder2026
    </a>
    <span class="f11" style="line-height: 20px;">
      Member since Jan 15, 2020
      <br/>
      <img alt="" src="https://es.pinkbike.org/sprt/f2/s/41.gif"/>
      Whistler, BC, Canada
    </span>
  </div>
</div>

</body>
</html>
"""


def test_detail_page_parse():
    detail = PinkbikeParser.parse_detail_page(MOCK_DETAIL_HTML)
    assert detail is not None
    assert detail.pinkbike_id == "3849220"
    assert detail.title == "2023 Santa Cruz Megatower CC X01"
    assert detail.price == 4500.0
    assert detail.currency == "CAD"
    assert "Fox 38 Factory" in detail.description
    assert detail.condition == "Excellent"
    assert detail.category == "Enduro Bikes"
    assert detail.seller_type == "Private Seller"
    assert detail.frame_size == "L"
    assert detail.wheel_size == '29"'
    assert detail.material == "Carbon Fiber"
    assert detail.front_travel == 170
    assert detail.rear_travel == 160
    assert detail.seller_username == "shredder2026"
    assert detail.seller_country == "Canada"
    assert detail.seller_region == "BC"
    assert detail.seller_city == "Whistler"
    assert detail.views == 142
    assert detail.date_posted == "3 days ago"
    assert detail.is_sold is False


def test_detail_page_sold():
    sold_html = MOCK_DETAIL_HTML.replace(
        "Available as of 5 hours ago",
        "SOLD on March 8, 2026"
    )
    detail = PinkbikeParser.parse_detail_page(sold_html)
    assert detail.is_sold is True


# ---------------------------------------------------------------------------
# Real HTML tests (only run if captured HTML exists)
# ---------------------------------------------------------------------------

def test_real_search_html():
    path = "/tmp/pinkbike_search.html"
    if not os.path.exists(path):
        return  # Skip if no captured HTML

    with open(path) as f:
        html = f.read()

    listings = PinkbikeParser.parse_search_page(html, "Enduro Bikes")
    assert len(listings) >= 10, f"Expected 10+ listings, got {len(listings)}"

    # Every listing should have an ID, title, and price
    for l in listings:
        assert l.pinkbike_id, "Missing pinkbike_id"
        assert l.title, "Missing title"
        assert l.price > 0, f"Missing price for {l.pinkbike_id}"
        assert l.condition, f"Missing condition for {l.pinkbike_id}"

    # Pagination should work
    assert PinkbikeParser.has_next_page(html) is True
    total = PinkbikeParser.get_total_pages(html)
    assert total and total > 100, f"Expected 100+ pages, got {total}"


def test_real_detail_html():
    path = "/tmp/pinkbike_detail.html"
    if not os.path.exists(path):
        return  # Skip if no captured HTML

    with open(path) as f:
        html = f.read()

    detail = PinkbikeParser.parse_detail_page(html)
    assert detail is not None
    assert detail.title
    assert detail.price > 0
    assert detail.description
    assert detail.condition


# ---------------------------------------------------------------------------
# Location parsing
# ---------------------------------------------------------------------------

def test_location_parse_full():
    c, r, city = PinkbikeParser._parse_location("Whistler, BC, Canada")
    assert c == "Canada"
    assert r == "BC"
    assert city == "Whistler"


def test_location_parse_us():
    c, r, city = PinkbikeParser._parse_location("Miami, Florida, United States")
    assert c == "United States"
    assert r == "Florida"
    assert city == "Miami"


def test_location_parse_two():
    c, r, city = PinkbikeParser._parse_location("Denver, USA")
    assert c == "USA"
    assert city == "Denver"


def test_location_parse_one():
    c, r, city = PinkbikeParser._parse_location("Canada")
    assert c == "Canada"


# ---------------------------------------------------------------------------
# Condition normalization
# ---------------------------------------------------------------------------

def test_condition_normalize():
    assert PinkbikeParser._normalize_condition("Excellent - Lightly Ridden") == "Excellent"
    assert PinkbikeParser._normalize_condition("Good - Some Wear") == "Good"
    assert PinkbikeParser._normalize_condition("Fair - Cosmetic Damage or Functional Issue") == "Fair"
    assert PinkbikeParser._normalize_condition("New") == "New"


if __name__ == "__main__":
    for name, func in list(globals().items()):
        if name.startswith("test_") and callable(func):
            try:
                func()
                print(f"  ✓ {name}")
            except AssertionError as e:
                print(f"  ✗ {name}: {e}")
    print("\nDone.")
